import sys
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import logging
from mock_pipeline import MockPipeline

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("video_analyzer.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("VideoAnalyzerApp")

print("开始加载视频分析系统...")

class VideoAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("视频筛选系统")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.pipeline = MockPipeline(logger=logger)
        
        self.create_widgets()
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建输入框架
        input_frame = ttk.LabelFrame(main_frame, text="视频输入", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        
        # 视频路径选择
        ttk.Label(input_frame, text="视频文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.video_path_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.video_path_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(input_frame, text="浏览...", command=self.browse_video).grid(row=0, column=2, padx=5, pady=5)
        
        # 候选人姓名
        ttk.Label(input_frame, text="候选人姓名:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.candidate_name_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.candidate_name_var, width=50).grid(row=1, column=1, padx=5, pady=5)
        
        # 职位关键词
        ttk.Label(input_frame, text="职位关键词:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.keywords_var = tk.StringVar(value="技术,开发,编程,软件,系统")
        ttk.Entry(input_frame, textvariable=self.keywords_var, width=50).grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(input_frame, text="(用逗号分隔)").grid(row=2, column=2, sticky=tk.W, pady=5)
        
        # 分析按钮
        analyze_btn = ttk.Button(input_frame, text="分析视频", command=self.analyze_video)
        analyze_btn.grid(row=3, column=1, pady=10)
        
        # 创建结果框架
        self.result_frame = ttk.LabelFrame(main_frame, text="分析结果", padding="10")
        self.result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建进度条
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.result_frame, orient="horizontal", 
                                        length=100, mode="determinate",
                                        variable=self.progress_var)
        self.progress.pack(fill=tk.X, pady=10)
        
        # 创建文本区域显示结果
        self.result_text = tk.Text(self.result_frame, wrap=tk.WORD, height=20)
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=5)
        scrollbar = ttk.Scrollbar(self.result_text, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
        
    def browse_video(self):
        file_path = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=(("视频文件", "*.mp4 *.avi *.mov *.wmv"), ("所有文件", "*.*"))
        )
        if file_path:
            self.video_path_var.set(file_path)
    
    def analyze_video(self):
        video_path = self.video_path_var.get()
        candidate_name = self.candidate_name_var.get()
        keywords_str = self.keywords_var.get()
        
        if not video_path:
            messagebox.showerror("错误", "请选择视频文件")
            return
        
        if not candidate_name:
            messagebox.showerror("错误", "请输入候选人姓名")
            return
        
        # 解析关键词
        job_keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
        if not job_keywords:
            messagebox.showerror("错误", "请输入至少一个职位关键词")
            return
        
        # 清空结果区域
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "正在分析视频，请稍候...\n\n")
        self.root.update_idletasks()
        
        # 模拟进度
        for i in range(101):
            self.progress_var.set(i)
            self.root.update_idletasks()
            if i < 100:
                self.root.after(20)  # 模拟处理时间
        
        try:
            # 分析视频
            result = self.pipeline.process_video(video_path, job_keywords, candidate_name)
            
            # 显示结果
            self.display_results(result)
            
        except Exception as e:
            logger.error(f"分析视频时出错: {str(e)}")
            messagebox.showerror("错误", f"分析视频时出错: {str(e)}")
    
    def display_results(self, result):
        self.result_text.delete(1.0, tk.END)
        
        # 候选人信息
        self.result_text.insert(tk.END, f"候选人: {result['candidate_name']}\n")
        self.result_text.insert(tk.END, f"分析视频: {os.path.basename(result['video_path'])}\n")
        self.result_text.insert(tk.END, f"职位关键词: {', '.join(result['job_keywords'])}\n\n")
        
        # 分数结果
        self.result_text.insert(tk.END, "===== 评分结果 =====\n")
        scores = result['scores']
        component_scores = scores['component_scores']
        
        self.result_text.insert(tk.END, f"总分: {scores['overall_score']:.2f}/10\n")
        self.result_text.insert(tk.END, f"视觉表现: {component_scores['visual']:.2f}/10\n")
        self.result_text.insert(tk.END, f"音频表现: {component_scores['audio']:.2f}/10\n")
        self.result_text.insert(tk.END, f"内容相关性: {component_scores['content']:.2f}/10\n\n")
        
        # 优势和改进点
        self.result_text.insert(tk.END, "===== 候选人优势 =====\n")
        for strength in scores['strengths']:
            self.result_text.insert(tk.END, f"✓ {strength}\n")
        
        self.result_text.insert(tk.END, "\n===== 建议改进 =====\n")
        for improvement in scores['improvements']:
            self.result_text.insert(tk.END, f"→ {improvement}\n")

if __name__ == "__main__":
    try:
        print("初始化图形界面...")
        root = tk.Tk()
        app = VideoAnalyzerApp(root)
        print("启动主循环...")
        root.mainloop()
    except Exception as e:
        print(f"启动图形界面时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        input("按Enter键退出...")
