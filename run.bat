@echo off
echo 启动视频筛选系统...
echo.

:: 检查Python是否已安装
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误：未找到Python。请确保已安装Python并添加到PATH环境变量。
    echo.
    pause
    exit /b 1
)

:: 确认所有文件存在
if not exist main.py (
    echo 错误：未找到main.py文件。
    echo 请确保所有文件都已下载并位于正确位置。
    echo.
    pause
    exit /b 1
)

if not exist mock_pipeline.py (
    echo 错误：未找到mock_pipeline.py文件。
    echo 请确保所有文件都已下载并位于正确位置。
    echo.
    pause
    exit /b 1
)

echo 所有必要文件已找到。
echo 启动应用程序...
echo.

:: 优先运行图形界面版本
echo 尝试运行图形界面版本...
python main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo 图形界面版本启动失败，尝试运行命令行版本...
    python test_pipeline.py
)

pause
