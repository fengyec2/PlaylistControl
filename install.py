# install.py
import subprocess
import sys
import os

def install_dependencies():
    """安装项目依赖"""
    dependencies = [
        "winsdk"
    ]
    
    print("🔧 正在安装项目依赖...")
    
    for dep in dependencies:
        try:
            print(f"📦 安装 {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ {dep} 安装失败: {e}")
            return False
    
    print("\n🎉 所有依赖安装完成!")
    return True

def create_startup_script():
    """创建启动脚本"""
    startup_script = """@echo off
cd /d "%~dp0"
python main.py
pause
"""
    
    try:
        with open("启动媒体记录器.bat", "w", encoding="gbk") as f:
            f.write(startup_script)
        print("✅ 启动脚本已创建: 启动媒体记录器.bat")
    except Exception as e:
        print(f"⚠️ 创建启动脚本失败: {e}")

def main():
    print("🎵 Windows 媒体播放记录器 - 安装程序")
    print("=" * 50)
    
    if install_dependencies():
        create_startup_script()
        print("\n🚀 安装完成! 您可以:")
        print("1. 直接运行: python main.py")
        print("2. 双击启动: 启动媒体记录器.bat")
        print("3. 编辑配置: 修改 config.json 文件")
    else:
        print("\n❌ 安装过程中出现错误，请检查网络连接后重试")

if __name__ == "__main__":
    main()
