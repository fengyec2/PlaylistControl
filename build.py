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
        'main.py',
        '--onefile',
        '--name=MediaTracker',
        '--icon=icon.ico',  # 如果有图标文件
        '--add-data=config.json;.',
        '--hidden-import=winsdk',
        '--hidden-import=sqlite3',
        '--hidden-import=psutil',  # 添加psutil
        '--console',
        '--clean',
    ]
    
    PyInstaller.__main__.run(args)
    print("✅ 打包完成！")
    print("📁 可执行文件位置: dist/MediaTracker.exe")

if __name__ == "__main__":
    build_executable()