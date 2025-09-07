# build.py - 打包脚本
import PyInstaller.__main__
import os
import shutil
from config_manager import version_info
from safe_print import safe_print

def create_version_file():
    """创建版本信息文件"""
    version_info_content = f'''
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_info.get_version_tuple()},
    prodvers={version_info.get_version_tuple()},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'{version_info.COMPANY}'),
          StringStruct(u'FileDescription', u'{version_info.DESCRIPTION}'),
          StringStruct(u'FileVersion', u'{version_info.VERSION}.0'),
          StringStruct(u'InternalName', u'{version_info.APP_NAME}'),
          StringStruct(u'LegalCopyright', u'{version_info.get_copyright()}'),
          StringStruct(u'OriginalFilename', u'{version_info.APP_NAME}.exe'),
          StringStruct(u'ProductName', u'{version_info.APP_NAME}'),
          StringStruct(u'ProductVersion', u'{version_info.VERSION}.0'),
          StringStruct(u'Comments', u'A powerful media file tracking application'),
          StringStruct(u'LegalTrademarks', u''),])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info_content)
    
    safe_print("✅ 版本信息文件已创建")

def build_executable():
    """构建可执行文件"""
    
    # 创建版本信息文件
    create_version_file()
    
    # 清理之前的构建
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # PyInstaller 参数
    args = [
        'main.py',
        '--onefile',
        f'--name={version_info.APP_NAME}',
        '--icon=icon.ico',  # 如果有图标文件
        '--version-file=version_info.txt',  # 添加版本信息文件
        '--add-data=config.json;.',
        '--hidden-import=winsdk',
        '--hidden-import=sqlite3',
        '--hidden-import=psutil',
        '--console',
        '--clean',
    ]
    
    PyInstaller.__main__.run(args)
    
    # 清理临时文件
    if os.path.exists('version_info.txt'):
        os.remove('version_info.txt')
    
    safe_print("✅ 打包完成！")
    safe_print(f"📁 可执行文件位置: dist/{version_info.APP_NAME}.exe")
    safe_print(f"ℹ️  程序版本: {version_info.get_full_name()}")

if __name__ == "__main__":
    build_executable()
