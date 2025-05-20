import os
import sys
import subprocess

def main():
    print("视频筛选系统启动脚本")
    print("====================")
    print("检查环境...")
    
    # 检查Python安装
    print("Python版本:", sys.version)
    
    # 检查文件是否存在
    required_files = ["main.py", "mock_pipeline.py", "test_pipeline.py"]
    all_files_exist = True
    
    print("\n检查必要文件...")
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} 已找到")
        else:
            print(f"✗ {file} 未找到")
            all_files_exist = False
    
    if not all_files_exist:
        print("\n错误：缺少必要文件。请确保所有文件都在当前目录。")
        return
    
    # 尝试运行主程序
    print("\n尝试启动主程序...")
    try:
        print("正在启动图形界面...")
        subprocess.run([sys.executable, "main.py"])
    except Exception as e:
        print(f"启动主程序时出错: {str(e)}")
        print("\n尝试运行测试流水线...")
        try:
            subprocess.run([sys.executable, "test_pipeline.py"])
        except Exception as e:
            print(f"运行测试流水线时出错: {str(e)}")
            print("\n尝试诊断问题...")
            
            # 检查模块导入
            try:
                import tkinter
                print("✓ tkinter 模块可用")
            except ImportError:
                print("✗ tkinter 模块不可用，可能需要安装")
            
            print("\n建议修复步骤:")
            print("1. 确保正确安装了Python")
            print("2. 检查是否安装了必要的库")
            print("3. 确保所有文件都在正确的位置")

if __name__ == "__main__":
    main()
    input("\n按Enter键退出...")
