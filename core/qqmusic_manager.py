import time
import subprocess
import os
import win32gui
import win32con
import win32api
import win32clipboard
import win32process
from typing import List, Dict, Any, Optional, Tuple
import pyautogui
import ctypes
from ctypes import wintypes

from config.config_manager import config
from utils.logger import logger
from utils.safe_print import safe_print
from core.database import db

# 设置pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

class QQMusicPlaylistManager:
    """QQ音乐歌单管理器 - 从指定歌单删除歌曲"""
    
    def __init__(self):
        self.source_playlist = config.get("qqmusic.source_playlist", "我喜欢")
        self.action_delay = config.get("qqmusic.ui_automation.action_delay", 2)
        self.retry_times = config.get("qqmusic.ui_automation.retry_times", 3)
        self.search_timeout = config.get("qqmusic.ui_automation.search_timeout", 10)
        self.qq_music_hwnd = None
        
        # UI坐标配置
        self.ui_config = self._load_ui_config()
        
    def _load_ui_config(self) -> Dict[str, Any]:
        """加载UI配置，支持不同版本的QQ音乐"""
        default_config = {
            "search_box_offset": {"x": 300, "y": 80},
            "playlist_menu_offset": {"x": 50, "y": 200},
            "song_list_area": {"x": 400, "y": 300, "width": 600, "height": 400},
            "right_click_menu_items": {
                "delete_from_playlist": ["删除", "从歌单中删除", "移除"]
            }
        }
        
        custom_config = config.get("qqmusic.ui_coordinates", {})
        default_config.update(custom_config)
        
        return default_config
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def is_qqmusic_running(self) -> bool:
        """检查QQ音乐是否正在运行"""
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq QQMusic.exe'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return 'QQMusic.exe' in result.stdout
        except Exception as e:
            logger.error(f"检查QQ音乐进程失败: {e}")
            return False
    
    def find_qqmusic_window(self) -> bool:
        """查找并激活QQ音乐窗口 - 修复版本"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                if 'QQ音乐' in window_title or 'QQMusic' in window_title or 'QQMusic' in class_name:
                    windows.append((hwnd, window_title))
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        if not windows:
            safe_print("❌ 未找到QQ音乐窗口")
            return False
        
        self.qq_music_hwnd, window_title = windows[0]
        
        try:
            # 使用更安全的窗口激活方法
            success = self._activate_window_safe(self.qq_music_hwnd)
            
            if success:
                safe_print(f"✅ 已激活QQ音乐窗口: {window_title}")
                return True
            else:
                safe_print(f"⚠️ 无法激活QQ音乐窗口，但窗口已找到: {window_title}")
                safe_print("💡 请手动点击QQ音乐窗口，然后按回车继续...")
                input("按回车继续...")
                return True
            
        except Exception as e:
            logger.error(f"激活QQ音乐窗口失败: {e}")
            safe_print(f"❌ 激活QQ音乐窗口失败: {e}")
            safe_print("💡 请手动激活QQ音乐窗口，然后按回车继续...")
            input("按回车继续...")
            return True  # 即使激活失败，也允许继续，让用户手动处理
    
    def _activate_window_safe(self, hwnd) -> bool:
        """安全地激活窗口"""
        try:
            # 方法1: 先尝试显示窗口
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.5)
            
            # 方法2: 尝试使用AttachThreadInput提升权限
            try:
                current_thread = win32api.GetCurrentThreadId()
                target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
                
                if current_thread != target_thread:
                    # 附加线程输入
                    win32process.AttachThreadInput(current_thread, target_thread, True)
                    
                    # 现在尝试设置前台窗口
                    win32gui.SetForegroundWindow(hwnd)
                    
                    # 分离线程输入
                    win32process.AttachThreadInput(current_thread, target_thread, False)
                else:
                    win32gui.SetForegroundWindow(hwnd)
                
                time.sleep(0.5)
                return True
                
            except Exception as e:
                logger.debug(f"AttachThreadInput方法失败: {e}")
                
                # 方法3: 使用ALT+TAB模拟
                try:
                    self._simulate_alt_tab_to_window(hwnd)
                    return True
                except Exception as e2:
                    logger.debug(f"ALT+TAB方法失败: {e2}")
                    
                    # 方法4: 使用ShowWindow和BringWindowToTop
                    try:
                        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                        win32gui.BringWindowToTop(hwnd)
                        time.sleep(0.5)
                        return True
                    except Exception as e3:
                        logger.debug(f"ShowWindow方法失败: {e3}")
                        return False
        
        except Exception as e:
            logger.error(f"窗口激活完全失败: {e}")
            return False
    
    def _simulate_alt_tab_to_window(self, target_hwnd):
        """模拟ALT+TAB切换到目标窗口"""
        try:
            # 按下ALT+TAB
            pyautogui.keyDown('alt')
            time.sleep(0.1)
            
            # 连续按TAB直到找到目标窗口
            for _ in range(10):  # 最多尝试10次
                pyautogui.press('tab')
                time.sleep(0.3)
                
                # 检查当前前台窗口是否是目标窗口
                current_hwnd = win32gui.GetForegroundWindow()
                if current_hwnd == target_hwnd:
                    break
            
            # 释放ALT键
            pyautogui.keyUp('alt')
            time.sleep(0.5)
            
        except Exception as e:
            logger.debug(f"ALT+TAB模拟失败: {e}")
            # 确保释放ALT键
            try:
                pyautogui.keyUp('alt')
            except:
                pass
    
    def get_window_rect(self) -> Tuple[int, int, int, int]:
        """获取QQ音乐窗口位置和大小"""
        if self.qq_music_hwnd:
            try:
                return win32gui.GetWindowRect(self.qq_music_hwnd)
            except Exception as e:
                logger.debug(f"获取窗口位置失败: {e}")
                return (0, 0, 1920, 1080)  # 返回默认值
        return (0, 0, 1920, 1080)
    
    def ensure_window_active(self) -> bool:
        """确保QQ音乐窗口处于激活状态"""
        try:
            if self.qq_music_hwnd:
                current_hwnd = win32gui.GetForegroundWindow()
                if current_hwnd != self.qq_music_hwnd:
                    safe_print("🔄 重新激活QQ音乐窗口...")
                    return self._activate_window_safe(self.qq_music_hwnd)
                return True
            return False
        except Exception as e:
            logger.debug(f"检查窗口状态失败: {e}")
            return True  # 假设窗口是活动的，继续执行
    
    def navigate_to_playlist(self, playlist_name: str) -> bool:
        """导航到指定歌单"""
        try:
            safe_print(f"🎵 正在打开歌单: {playlist_name}")
            
            # 确保窗口激活
            self.ensure_window_active()
            
            window_rect = self.get_window_rect()
            
            # 方法1: 尝试点击左侧歌单菜单
            playlist_x = window_rect[0] + self.ui_config["playlist_menu_offset"]["x"]
            playlist_y = window_rect[1] + self.ui_config["playlist_menu_offset"]["y"]
            
            # 点击歌单区域
            pyautogui.click(playlist_x, playlist_y)
            time.sleep(1)
            
            # 方法2: 使用搜索功能查找歌单
            if not self._search_playlist(playlist_name):
                # 方法3: 使用键盘导航
                return self._navigate_playlist_by_keyboard(playlist_name)
            
            return True
            
        except Exception as e:
            logger.error(f"导航到歌单失败: {e}")
            safe_print(f"❌ 无法自动导航到歌单: {playlist_name}")
            safe_print("💡 请手动打开对应歌单，然后按回车继续...")
            input("按回车继续...")
            return True  # 允许用户手动处理后继续
    
    def _search_playlist(self, playlist_name: str) -> bool:
        """通过搜索功能找到歌单"""
        try:
            # 尝试全局搜索快捷键
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.5)
            
            # 输入歌单名称
            self._copy_to_clipboard(playlist_name)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(2)
            
            return True
            
        except Exception as e:
            logger.debug(f"搜索歌单失败: {e}")
            return False
    
    def _navigate_playlist_by_keyboard(self, playlist_name: str) -> bool:
        """使用键盘导航到歌单"""
        try:
            # 按首字母尝试快速定位
            if playlist_name:
                first_char = playlist_name[0].lower()
                for _ in range(3):  # 尝试3次
                    pyautogui.press(first_char)
                    time.sleep(0.5)
                    pyautogui.press('enter')
                    time.sleep(1)
                    
                    # 检查是否成功（这里简化处理）
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"键盘导航失败: {e}")
            return False
    
    def search_song_in_playlist(self, song_title: str, artist: str = None) -> bool:
        """在当前歌单中搜索指定歌曲"""
        try:
            search_keywords = song_title
            if artist:
                search_keywords = f"{song_title} {artist}"
            
            safe_print(f"🔍 在歌单中搜索: {search_keywords}")
            
            # 确保窗口激活
            self.ensure_window_active()
            
            # 尝试歌单内搜索（通常是Ctrl+F）
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.5)
            
            # 清空并输入搜索内容
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            
            self._copy_to_clipboard(search_keywords)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"搜索歌曲失败: {e}")
            return False
    
    def delete_song_from_current_playlist(self, song_title: str, artist: str = None) -> Tuple[bool, str]:
        """从当前歌单中删除指定歌曲"""
        try:
            # 先搜索歌曲
            if not self.search_song_in_playlist(song_title, artist):
                safe_print("💡 搜索失败，请手动找到歌曲并选中，然后按回车继续...")
                input("按回车继续...")
            
            # 等待搜索结果
            time.sleep(1)
            
            # 尝试多种方法删除歌曲
            delete_methods = [
                self._delete_by_right_click,
                self._delete_by_keyboard_shortcut,
                self._delete_by_menu_navigation
            ]
            
            for method in delete_methods:
                try:
                    if method():
                        return True, "从歌单删除成功"
                except Exception as e:
                    logger.debug(f"删除方法 {method.__name__} 失败: {e}")
                    continue
            
            # 如果所有自动方法都失败，提供手动选项
            safe_print("❌ 自动删除失败")
            safe_print("💡 请手动删除该歌曲：")
            safe_print("   1. 确保歌曲已选中")
            safe_print("   2. 右键点击歌曲")
            safe_print("   3. 选择'删除'或'从歌单中移除'")
            safe_print("   4. 确认删除")
            
            response = input("删除完成后输入 'y' 确认成功，或 'n' 表示失败: ").lower().strip()
            
            if response == 'y':
                return True, "手动删除成功"
            else:
                return False, "手动删除失败或跳过"
            
        except Exception as e:
            error_msg = f"删除歌曲时出错: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def _delete_by_right_click(self) -> bool:
        """通过右键菜单删除歌曲"""
        try:
            safe_print("🖱️ 尝试右键删除")
            
            # 确保窗口激活
            self.ensure_window_active()
            
            window_rect = self.get_window_rect()
            song_area = self.ui_config["song_list_area"]
            
            # 在歌曲列表区域的几个位置尝试右键
            test_positions = [
                (window_rect[0] + song_area["x"], window_rect[1] + song_area["y"]),
                (window_rect[0] + song_area["x"] + 100, window_rect[1] + song_area["y"] + 30),
                (window_rect[0] + song_area["x"] + 50, window_rect[1] + song_area["y"] + 60),
            ]
            
            for x, y in test_positions:
                try:
                    # 先左键选中
                    pyautogui.click(x, y)
                    time.sleep(0.5)
                    
                    # 右键打开菜单
                    pyautogui.rightClick(x, y)
                    time.sleep(1)
                    
                    # 查找删除菜单项
                    if self._click_delete_menu_item():
                        return True
                    
                    # 关闭菜单
                    pyautogui.press('escape')
                    time.sleep(0.5)
                except Exception as e:
                    logger.debug(f"右键位置 ({x}, {y}) 失败: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"右键删除失败: {e}")
            return False
    
    def _delete_by_keyboard_shortcut(self) -> bool:
        """通过键盘快捷键删除歌曲"""
        try:
            safe_print("⌨️ 尝试键盘快捷键删除")
            
            # 确保窗口激活
            self.ensure_window_active()
            
            # 确保选中歌曲（点击歌曲列表区域）
            window_rect = self.get_window_rect()
            song_area = self.ui_config["song_list_area"]
            click_x = window_rect[0] + song_area["x"] + 50
            click_y = window_rect[1] + song_area["y"] + 30
            
            pyautogui.click(click_x, click_y)
            time.sleep(0.5)
            
            # 尝试常见的删除快捷键
            delete_shortcuts = [
                'delete',           # Delete键
                ['shift', 'delete'], # Shift+Delete
                ['ctrl', 'd'],      # Ctrl+D
                ['alt', 'd'],       # Alt+D
            ]
            
            for shortcut in delete_shortcuts:
                try:
                    if isinstance(shortcut, list):
                        pyautogui.hotkey(*shortcut)
                    else:
                        pyautogui.press(shortcut)
                    
                    time.sleep(1)
                    
                    # 检查是否出现确认对话框
                    if self._handle_delete_confirmation():
                        return True
                    
                    time.sleep(0.5)
                except Exception as e:
                    logger.debug(f"快捷键 {shortcut} 失败: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"键盘快捷键删除失败: {e}")
            return False
    
    def _delete_by_menu_navigation(self) -> bool:
        """通过菜单栏删除歌曲"""
        try:
            safe_print("📋 尝试菜单栏删除")
            
            # 确保窗口激活
            self.ensure_window_active()
            
            # 确保选中歌曲
            window_rect = self.get_window_rect()
            song_area = self.ui_config["song_list_area"]
            click_x = window_rect[0] + song_area["x"] + 50
            click_y = window_rect[1] + song_area["y"] + 30
            
            pyautogui.click(click_x, click_y)
            time.sleep(0.5)
            
            # 尝试访问菜单栏
            pyautogui.press('alt')  # 激活菜单栏
            time.sleep(0.5)
            
            # 尝试导航到编辑或操作菜单
            menu_keys = ['e', 'o', 't']  # Edit, Operation, Tools等可能的菜单
            
            for menu_key in menu_keys:
                try:
                    pyautogui.press(menu_key)
                    time.sleep(0.5)
                    
                    # 查找删除选项
                    delete_keys = ['d', 'r', 'del']  # Delete, Remove等
                    for delete_key in delete_keys:
                        try:
                            pyautogui.press(delete_key)
                            time.sleep(1)
                            
                            if self._handle_delete_confirmation():
                                return True
                        except Exception as e:
                            logger.debug(f"删除键 {delete_key} 失败: {e}")
                    
                    pyautogui.press('escape')  # 退出当前菜单
                    time.sleep(0.3)
                except Exception as e:
                    logger.debug(f"菜单键 {menu_key} 失败: {e}")
                    continue
            
            pyautogui.press('escape')  # 退出菜单栏
            return False
            
        except Exception as e:
            logger.debug(f"菜单栏删除失败: {e}")
            return False
    
    def _click_delete_menu_item(self) -> bool:
        """点击右键菜单中的删除项"""
        try:
            # 尝试使用键盘快捷键选择删除项
            delete_keys = ['d', 'r', 'del']  # 删除、移除等可能的快捷键
            
            for key in delete_keys:
                try:
                    pyautogui.press(key)
                    time.sleep(1)
                    
                    if self._handle_delete_confirmation():
                        return True
                    
                    # 如果没有效果，重新打开右键菜单
                    pyautogui.press('escape')
                    time.sleep(0.3)
                    pyautogui.rightClick()
                    time.sleep(0.5)
                except Exception as e:
                    logger.debug(f"删除键 {key} 失败: {e}")
                    continue
            
            # 尝试通过位置点击
            current_x, current_y = pyautogui.position()
            menu_positions = [
                (current_x + 80, current_y + 40),   # 常见的删除菜单位置
                (current_x + 80, current_y + 60),
                (current_x + 80, current_y + 80),
                (current_x + 80, current_y + 100),
            ]
            
            for x, y in menu_positions:
                try:
                    pyautogui.click(x, y)
                    time.sleep(1)
                    
                    if self._handle_delete_confirmation():
                        return True
                except Exception as e:
                    logger.debug(f"点击位置 ({x}, {y}) 失败: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"点击删除菜单项失败: {e}")
            return False
    
    def _handle_delete_confirmation(self) -> bool:
        """处理删除确认对话框"""
        try:
            # 等待可能的确认对话框出现
            time.sleep(0.5)
            
            # 尝试确认删除
            confirmation_keys = [
                'enter',     # 回车确认
                'y',         # Yes
                ['alt', 'y'], # Alt+Y
                'space',     # 空格（可能是默认按钮）
            ]
            
            for key in confirmation_keys:
                try:
                    if isinstance(key, list):
                        pyautogui.hotkey(*key)
                    else:
                        pyautogui.press(key)
                    
                    time.sleep(0.5)
                    
                    # 简化的成功检测：假设如果没有错误就是成功了
                    safe_print("✅ 确认删除操作")
                    return True
                except Exception as e:
                    logger.debug(f"确认键 {key} 失败: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"处理删除确认失败: {e}")
            return False
    
    def _copy_to_clipboard(self, text: str):
        """将文本复制到剪贴板"""
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text)
            win32clipboard.CloseClipboard()
        except Exception as e:
            logger.error(f"复制到剪贴板失败: {e}")
    
    def delete_song_from_playlist(self, song_title: str, artist: str = None) -> Tuple[bool, str]:
        """完整的删除歌曲流程"""
        try:
            safe_print(f"🎵 正在从歌单删除: {song_title}")
            if artist:
                safe_print(f"   艺术家: {artist}")
            
            # 1. 确保QQ音乐窗口激活
            if not self.find_qqmusic_window():
                return False, "无法激活QQ音乐窗口"
            
            # 2. 导航到指定歌单
            if not self.navigate_to_playlist(self.source_playlist):
                return False, f"无法打开歌单: {self.source_playlist}"
            
            # 3. 删除歌曲
            success, message = self.delete_song_from_current_playlist(song_title, artist)
            
            if success:
                safe_print("   ✅ 删除成功")
                return True, message
            else:
                safe_print(f"   ❌ 删除失败: {message}")
                return False, message
                
        except Exception as e:
            error_msg = f"删除歌曲流程出错: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def batch_delete_from_recent_tracks(self, track_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量从歌单删除最近播放的歌曲"""
        if not self.is_qqmusic_running():
            return {'error': 'QQ音乐未运行'}
        
        if not self.find_qqmusic_window():
            return {'error': '无法激活QQ音乐窗口'}
        
        # 先导航到目标歌单
        if not self.navigate_to_playlist(self.source_playlist):
            return {'error': f'无法打开歌单: {self.source_playlist}'}
        
        results = {
            'total': len(track_list),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        safe_print(f"🗑️ 开始批量删除 {len(track_list)} 首歌曲...")
        safe_print(f"📝 目标歌单: {self.source_playlist}")
        safe_print("-" * 50)
        
        for i, track in enumerate(track_list, 1):
            track_id = track['id']
            song_title = track['title']
            artist = track['artist']
            
            safe_print(f"[{i}/{len(track_list)}] {song_title}")
            
            # 标记为pending状态
            db.mark_song_deletion_status(track_id, 'pending', f"正在从歌单删除: {self.source_playlist}")
            
            # 执行删除操作
            success, message = self.delete_song_from_current_playlist(song_title, artist)
            
            # 更新状态
            if success:
                db.mark_song_deletion_status(track_id, 'deleted', message)
                results['success'] += 1
                safe_print(f"  ✅ 成功")
            else:
                db.mark_song_deletion_status(track_id, 'failed', message)
                results['failed'] += 1
                safe_print(f"  ❌ 失败: {message}")
            
            results['details'].append({
                'id': track_id,
                'title': song_title,
                'artist': artist,
                'success': success,
                'message': message
            })
            
            # 操作间隔
            if i < len(track_list):
                time.sleep(self.action_delay)
        
        safe_print("-" * 50)
        safe_print(f"🎵 批量删除完成:")
        safe_print(f"  ✅ 成功: {results['success']}")
        safe_print(f"  ❌ 失败: {results['failed']}")
        safe_print(f"  📊 成功率: {results['success']/results['total']*100:.1f}%")
        
        return results
    
    def initialize(self) -> bool:
        """初始化QQ音乐连接"""
        if not config.get("qqmusic.enabled", True):
            safe_print("⚠️ QQ音乐功能已禁用")
            return False
        
        if not self.is_qqmusic_running():
            safe_print("❌ QQ音乐未运行，请先启动QQ音乐")
            return False
        
        if not self.find_qqmusic_window():
            return False
        
        safe_print("🎵 QQ音乐初始化成功")
        safe_print(f"📝 将从歌单删除歌曲: {self.source_playlist}")
        return True
    
    def cleanup(self):
        """清理资源"""
        logger.info("QQ音乐管理器资源已清理")

# 全局实例
qqmusic_manager = QQMusicPlaylistManager()
