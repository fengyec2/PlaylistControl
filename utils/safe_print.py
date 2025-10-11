import sys
import os

def safe_print(*args, **kwargs):
    """安全的打印函数，处理编码问题"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 如果遇到编码错误，移除emoji并重试
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                # 移除常见的emoji字符
                safe_arg = (arg.replace('✅', '[OK]')
                              .replace('❌', '[ERROR]')
                              .replace('⚠️', '[WARNING]')
                              .replace('ℹ️', '[INFO]')
                              .replace('🔧', '[DEBUG]')
                              .replace('🚀', '[START]')
                              .replace('💡', '[INFO]')
                              .replace('🎧', '[MUSIC]')
                              .replace('🎵', '[MUSIC]')
                              .replace('🎤', '[ARTIST]')
                              .replace('💿', '[ALBUM]')
                              .replace('👥', '[ALBUM_ARTIST]')
                              .replace('🔢', '[TRACK_NUMBER]')
                              .replace('🎭', '[GENRE]')
                              .replace('📅', '[YEAR]')
                              .replace('📱', '[APP]')
                              .replace('⚡', '[STATUS]')
                              .replace('⏱️', '[PROGRESS]')
                              .replace('✨', '[NEW]')
                              .replace('📋', '[LOG]')
                              .replace('🔍', '[DETECTING]'))
                safe_args.append(safe_arg)
            else:
                safe_args.append(arg)
        print(*safe_args, **kwargs)

def init_console_encoding():
    """初始化控制台编码"""
    if sys.platform == 'win32':
        try:
            # 尝试设置控制台为UTF-8
            os.system('chcp 65001 > nul 2>&1')
        except:
            pass
