import os
import sys
import logging
from mock_pipeline import MockPipeline

print("=== 视频筛选系统简易版 ===")

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("simple_run.log"),
                        logging.StreamHandler(sys.stdout)
                    ])
logger = logging.getLogger("SimpleRun")

def run_analysis():
    print("\n请输入分析参数:")
    video_path = input("视频文件路径 (回车使用默认'示例视频.mp4'): ") or "示例视频.mp4"
    candidate_name = input("候选人姓名 (回车使用默认'测试候选人'): ") or "测试候选人"
    keywords_str = input("职位关键词，用逗号分隔 (回车使用默认关键词): ") or "技术,开发,编程,软件,系统"
    
    job_keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
    
    print("\n开始分析视频...")
    pipeline = MockPipeline(logger=logger)
    
    try:
        result = pipeline.process_video(video_path, job_keywords, candidate_name)
        
        print("\n=== 分析结果 ===")
        print(f"候选人: {result['candidate_name']}")
        print(f"视频: {result['video_path']}")
        scores = result['scores']
        
        print("\n评分:")
        print(f"总分: {scores['overall_score']:.2f}/10")
        print(f"视觉表现: {scores['component_scores']['visual']:.2f}/10")
        print(f"音频表现: {scores['component_scores']['audio']:.2f}/10")
        print(f"内容相关性: {scores['component_scores']['content']:.2f}/10")
        
        print("\n优势:")
        for strength in scores['strengths']:
            print(f"- {strength}")
        
        print("\n改进点:")
        for improvement in scores['improvements']:
            print(f"- {improvement}")
            
        return True
    except Exception as e:
        print(f"\n分析过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("系统正在启动...")
    success = run_analysis()
    if success:
        print("\n分析完成!")
    else:
        print("\n分析失败!")
    input("\n按Enter键退出...")
