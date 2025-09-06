import argparse

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='PlaylistControl v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  基本使用:
    python main.py                    # 交互模式，实时显示播放信息
    python main.py -b                 # 后台监控模式
    python main.py -d                 # 守护进程模式（静默后台运行）
  
  自定义监控:
    python main.py -b -i 5            # 后台监控，5秒检测间隔
    python main.py -d --pid-file daemon.pid  # 守护进程并指定PID文件
  
  查看历史记录:
    python main.py -r 20              # 显示最近20首播放的歌曲
    python main.py -r 50 --no-emoji   # 显示最近50首歌曲，纯文本输出
    python main.py -s                 # 显示播放统计信息
  
  数据导出:
    python main.py -e output.json     # 导出播放历史到JSON文件
    python main.py -e history.json -q # 静默导出，不显示过程信息
  
  进程管理:
    python main.py --stop             # 停止后台运行的程序（自动查找）
    python main.py --stop --pid-file daemon.pid  # 使用指定PID文件停止
  
  调试和开发:
    python main.py -v                 # 详细输出模式，显示调试信息
    python main.py -b -q --no-emoji   # 后台监控，静默纯文本模式
    python main.py -b -v -i 3         # 后台监控，详细输出，3秒间隔
        '''
    )
    
    # 运行模式参数
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('-b', '--background', action='store_true',
                           help='后台监控模式')
    mode_group.add_argument('-d', '--daemon', action='store_true',
                           help='守护进程模式(静默后台运行)')
    mode_group.add_argument('-r', '--recent', type=int, metavar='N',
                           help='显示最近N首播放的歌曲')
    mode_group.add_argument('-s', '--stats', action='store_true',
                           help='显示播放统计信息')
    mode_group.add_argument('-e', '--export', type=str, metavar='FILE',
                           help='导出播放历史到指定文件')
    mode_group.add_argument('--stop', action='store_true',
                           help='停止后台运行的程序（自动查找PID文件）')
    
    # 监控参数
    parser.add_argument('-i', '--interval', type=int, metavar='SECONDS',
                       help='监控间隔(秒), 默认从配置文件读取')
    parser.add_argument('--pid-file', type=str, metavar='FILE',
                       help='PID文件路径(仅守护进程模式)')
    
    # 显示参数
    parser.add_argument('--no-emoji', action='store_true',
                       help='禁用emoji显示')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='静默模式，减少输出')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='详细输出模式')
    
    return parser.parse_args()
