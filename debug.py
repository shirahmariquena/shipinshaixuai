import os
import sys
import importlib
import platform
import tkinter as tk

def check_system():
    print("=== 系统环境检查 ===")
    print(f"操作系统: {platform.system()} {platform.release()} {platform.version()}")
    print(f"Python版本: {sys.version}")
    print(f"Python执行路径: {sys.executable}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"项目目录文件列表: {os.listdir('.')}")
    print()

def check_tkinter():
    print("=== Tkinter检查 ===")
    try:
        root = tk.Tk()
        root.title("Tkinter测试")
        label = tk.Label(root, text="如果您看到此窗口，Tkinter工作正常！")
        label.pack(padx=20, pady=20)
        print("Tkinter初始化成功")
        btn = tk.Button(root, text="关闭", command=root.destroy)
        btn.pack(pady=10)
        root.mainloop()
    except Exception as e:
        print(f"Tkinter错误: {str(e)}")
    print()

def check_modules():
    print("=== 模块导入检查 ===")
    modules = ["mock_pipeline", "test_pipeline", "main"]
    
    for module in modules:
        try:
            print(f"尝试导入 {module}...")
            importlib.import_module(module)
            print(f"✓ 成功导入 {module}")
        except Exception as e:
            print(f"✗ 导入 {module} 失败: {str(e)}")
    print()

def check_file_content():
    print("=== 文件内容检查 ===")
    files = ["mock_pipeline.py", "test_pipeline.py", "main.py"]
    
    for file in files:
        if os.path.exists(file):
            print(f"检查 {file}...")
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"✓ 能够读取 {file}, 大小: {len(content)} 字节")
                    if "import" not in content:
                        print(f"! 警告: {file} 似乎没有导入语句")
            except Exception as e:
                print(f"✗ 无法读取 {file}: {str(e)}")
        else:
            print(f"✗ 文件不存在: {file}")
    print()

def main():
    print("视频筛选系统 - 调试工具")
    print("=====================")
    
    check_system()
    check_file_content()
    check_modules()
    check_tkinter()
    
    print("调试检查完成。")
    print("请根据以上信息排查问题。")
    
    choice = input("\n是否尝试运行测试流水线? (y/n): ")
    if choice.lower() == 'y':
        try:
            from test_pipeline import test_pipeline
            print("\n执行测试流水线...")
            test_pipeline()
        except Exception as e:
            print(f"执行测试流水线时出错: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
    input("\n按Enter键退出...")
