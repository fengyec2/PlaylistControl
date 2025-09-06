# build.py - 打包脚本
import PyInstaller.__main__
import os
import shutil

def build_executable():
    """构建可执行文件"""
    
    # 清理之前的构建
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # PyInstaller 参数
    args = [
        'main.py',                    # 主程序文件
        '--onefile',                  # 打包成单个exe文件
        '--name=MediaTracker',        # exe文件名
        '--icon=icon.ico',            # 图标文件（可选）
        '--add-data=config.json;.',   # 包含配置文件
        '--hidden-import=winsdk',     # 确保包含winsdk
        '--hidden-import=sqlite3',    # 确保包含sqlite3
        '--console',                  # 保留控制台窗口
        '--clean',                    # 清理临时文件
    ]
    
    PyInstaller.__main__.run(args)
    print("✅ 打包完成！")
    print("📁 可执行文件位置: dist/MediaTracker.exe")

if __name__ == "__main__":
    build_executable()
