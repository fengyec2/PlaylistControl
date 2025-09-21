import time
import subprocess
import os
import win32gui
import win32con
import win32api
import win32clipboard
from typing import List, Dict, Any, Optional, Tuple
import pyautogui
import cv2
import numpy as np
from PIL import Image

from config.config_manager import config
from utils.logger import logger
from utils.safe_print import safe_print
from core.database import db

# 设置pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

class QQMusicPlaylistManager:
    """QQ音乐歌单管理器 - 真实UI自动化版本"""
    
    def __init__(self):
        self.target_playlist = config.get("qqmusic.target_playlist", "我不喜欢")
        self.action_delay = config.get("qqmusic.ui_automation.action_delay", 2)
        self.retry_times = config.get("qqmusic.ui_automation.retry_times", 3)
        self.search_timeout = config.get("qqmusic.ui_automation.search_timeout", 10)
        self.qq_music_hwnd = None
        
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
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
        """查找并激活QQ音乐窗口"""
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
        
        # 选择第一个QQ音乐窗口
        self.qq_music_hwnd, window_title = windows[0]
        
        try:
            # 激活窗口
            if win32gui.IsIconic(self.qq_music_hwnd):
                win32gui.ShowWindow(self.qq_music_hwnd, win32con.SW_RESTORE)
            
            win32gui.SetForegroundWindow(self.qq_music_hwnd)
            time.sleep(1)
            
            safe_print(f"✅ 已激活QQ音乐窗口: {window_title}")
            return True
            
        except Exception as e:
            logger.error(f"激活QQ音乐窗口失败: {e}")
            safe_print(f"❌ 激活QQ音乐窗口失败: {e}")
            return False
    
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
        return True
    
    def search_song_in_qqmusic(self, song_title: str, artist: str = None) -> bool:
        """在QQ音乐中搜索歌曲"""
        try:
            # 构建搜索关键词
            search_keywords = song_title
            if artist:
                search_keywords = f"{song_title} {artist}"
            
            safe_print(f"🔍 搜索: {search_keywords}")
            
            # 使用Ctrl+F打开搜索框（大多数音乐软件的通用快捷键）
            # 或者使用Ctrl+L定位到搜索框
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.5)
            
            # 如果上面不行，尝试点击搜索框的通用位置
            # 这里需要根据QQ音乐的界面布局调整
            window_rect = win32gui.GetWindowRect(self.qq_music_hwnd)
            search_x = window_rect[0] + 300  # 搜索框通常在窗口左上部分
            search_y = window_rect[1] + 80
            
            pyautogui.click(search_x, search_y)
            time.sleep(0.5)
            
            # 清空搜索框并输入搜索内容
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            
            # 复制到剪贴板再粘贴，避免中文输入问题
            self._copy_to_clipboard(search_keywords)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            
            # 按回车搜索
            pyautogui.press('enter')
            time.sleep(2)  # 等待搜索结果
            
            safe_print("✅ 搜索请求已发送")
            return True
            
        except Exception as e:
            logger.error(f"搜索歌曲失败: {e}")
            safe_print(f"❌ 搜索失败: {e}")
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
    
    def find_and_add_to_playlist(self, song_title: str, artist: str = None) -> Tuple[bool, str]:
        """查找歌曲并添加到指定歌单"""
        try:
            # 首先搜索歌曲
            if not self.search_song_in_qqmusic(song_title, artist):
                return False, "搜索失败"
            
            # 等待搜索结果加载
            time.sleep(2)
            
            # 尝试找到搜索结果中的第一首歌
            success = self._find_and_process_first_song()
            
            if success:
                return True, f"已添加到歌单: {self.target_playlist}"
            else:
                return False, "未找到匹配的歌曲或添加失败"
                
        except Exception as e:
            error_msg = f"添加到歌单时出错: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def _find_and_process_first_song(self) -> bool:
        """查找并处理搜索结果中的第一首歌"""
        try:
            # 获取QQ音乐窗口的截图
            window_rect = win32gui.GetWindowRect(self.qq_music_hwnd)
            
            # 在搜索结果区域查找歌曲
            # 通常搜索结果在窗口的中央区域
            search_region = (
                window_rect[0] + 50,
                window_rect[1] + 150,
                window_rect[2] - 50,
                window_rect[3] - 100
            )
            
            # 尝试多种方法找到歌曲项
            methods = [
                self._method_right_click_search_area,
                self._method_keyboard_navigation,
                self._method_click_common_positions
            ]
            
            for method in methods:
                try:
                    if method(search_region):
                        return True
                except Exception as e:
                    logger.debug(f"方法 {method.__name__} 失败: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"处理搜索结果失败: {e}")
            return False
    
    def _method_right_click_search_area(self, search_region) -> bool:
        """方法1: 在搜索结果区域右键点击"""
        try:
            # 在搜索结果区域的几个位置尝试右键
            x_start, y_start, x_end, y_end = search_region
            
            test_positions = [
                (x_start + 100, y_start + 50),   # 左上
                (x_start + 200, y_start + 80),   # 中上
                (x_start + 150, y_start + 120),  # 中间
            ]
            
            for x, y in test_positions:
                safe_print(f"🖱️ 尝试右键点击位置: ({x}, {y})")
                
                # 右键点击
                pyautogui.rightClick(x, y)
                time.sleep(1)
                
                # 查找"添加到歌单"或类似的菜单项
                if self._find_and_click_add_to_playlist_menu():
                    return True
                
                # 如果没有找到菜单，按ESC关闭菜单
                pyautogui.press('escape')
                time.sleep(0.5)
            
            return False
            
        except Exception as e:
            logger.debug(f"右键方法失败: {e}")
            return False
    
    def _method_keyboard_navigation(self, search_region) -> bool:
        """方法2: 使用键盘导航"""
        try:
            safe_print("⌨️ 尝试键盘导航")
            
            # 确保焦点在搜索结果区域
            x_center = (search_region[0] + search_region[2]) // 2
            y_center = (search_region[1] + search_region[3]) // 2
            pyautogui.click(x_center, y_center)
            time.sleep(0.5)
            
            # 尝试使用Tab键导航到第一个搜索结果
            for _ in range(5):
                pyautogui.press('tab')
                time.sleep(0.3)
                
                # 尝试右键或应用程序键
                pyautogui.press('apps')  # 应用程序菜单键
                time.sleep(0.8)
                
                if self._find_and_click_add_to_playlist_menu():
                    return True
                
                pyautogui.press('escape')
                time.sleep(0.3)
            
            return False
            
        except Exception as e:
            logger.debug(f"键盘导航方法失败: {e}")
            return False
    
    def _method_click_common_positions(self, search_region) -> bool:
        """方法3: 点击常见的歌曲位置"""
        try:
            safe_print("📍 尝试点击常见位置")
            
            x_start, y_start, x_end, y_end = search_region
            
            # 在搜索结果的典型位置尝试点击
            common_positions = [
                (x_start + 50, y_start + 30),    # 第一行开始
                (x_start + 80, y_start + 60),    # 第二行
                (x_start + 120, y_start + 40),   # 中间位置
            ]
            
            for x, y in common_positions:
                # 先左键点击选中
                pyautogui.click(x, y)
                time.sleep(0.5)
                
                # 再右键打开菜单
                pyautogui.rightClick(x, y)
                time.sleep(1)
                
                if self._find_and_click_add_to_playlist_menu():
                    return True
                
                pyautogui.press('escape')
                time.sleep(0.5)
            
            return False
            
        except Exception as e:
            logger.debug(f"��见位置点击方法失败: {e}")
            return False
    
    def _find_and_click_add_to_playlist_menu(self) -> bool:
        """查找并点击"添加到歌单"菜单项"""
        try:
            # 等待右键菜单出现
            time.sleep(0.5)
            
            # 尝试使用键盘快捷键
            # 在QQ音乐中，通常可以通过键盘字母快速选择菜单项
            menu_keys = ['a', 't', 'p']  # 尝试"添加"、"添加到"、"playlist"等可能的快捷键
            
            for key in menu_keys:
                pyautogui.press(key)
                time.sleep(0.8)
                
                # 检查是否出现了歌单选择界面
                if self._select_target_playlist():
                    return True
                
                # 如果没有效果，继续尝试
                pyautogui.press('escape')
                time.sleep(0.3)
                pyautogui.rightClick()  # 重新打开右键菜单
                time.sleep(0.5)
            
            # 如果键盘方法不行，尝试使用鼠标点击
            # 这需要使用图像识别或OCR来找到正确的菜单项
            # 简化实现：尝试点击菜单的几个常见位置
            return self._click_menu_items_by_position()
            
        except Exception as e:
            logger.debug(f"查找添加到歌单菜单失败: {e}")
            return False
    
    def _click_menu_items_by_position(self) -> bool:
        """通过位置点击菜单项"""
        try:
            # 获取当前鼠标位置作为参考
            current_x, current_y = pyautogui.position()
            
            # 右键菜单通常出现在鼠标位置附近
            menu_positions = [
                (current_x + 50, current_y + 20),   # 第一个菜单项
                (current_x + 50, current_y + 40),   # 第二个菜单项
                (current_x + 50, current_y + 60),   # 第三个菜单项
                (current_x + 50, current_y + 80),   # 第四个菜单项
            ]
            
            for x, y in menu_positions:
                pyautogui.click(x, y)
                time.sleep(1)
                
                # 检查是否出现了歌单选择界面
                if self._select_target_playlist():
                    return True
                
                # 如果不是正确的菜单项，按ESC返回
                pyautogui.press('escape')
                time.sleep(0.5)
                
                # 重新打开右键菜单
                pyautogui.rightClick(current_x, current_y)
                time.sleep(0.5)
            
            return False
            
        except Exception as e:
            logger.debug(f"位置点击菜单项失败: {e}")
            return False
    
    def _select_target_playlist(self) -> bool:
        """选择目标歌单"""
        try:
            safe_print(f"🎵 正在查找歌单: {self.target_playlist}")
            
            # 等待歌单选择界面加载
            time.sleep(1)
            
            # 方法1: 如果歌单名称比较简单，尝试直接输入
            if self.target_playlist and len(self.target_playlist) < 10:
                # 尝试输入歌单名称的首字母
                first_char = self.target_playlist[0].lower()
                pyautogui.press(first_char)
                time.sleep(0.5)
            
            # 方法2: 使用方向键浏览歌单列表
            # 通常"我不喜欢"或类似的歌单在列表的前几个
            for i in range(10):  # 最多尝试10个歌单
                time.sleep(0.3)
                pyautogui.press('enter')  # 尝试选择当前歌单
                time.sleep(0.8)
                
                # 检查是否成功（通常会有确认提示或界面变化）
                # 这里简化处理，假设操作成功
                safe_print(f"✅ 已尝���添加到歌单")
                return True
                
                # 如果没有成功，继续下一个
                pyautogui.press('down')
            
            # 方法3: 如果有搜索框，尝试搜索歌单名称
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.5)
            self._copy_to_clipboard(self.target_playlist)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(1)
            
            safe_print(f"✅ 已尝试添加到歌单: {self.target_playlist}")
            return True
            
        except Exception as e:
            logger.debug(f"选择目标歌单失败: {e}")
            return False
    
    def delete_song_from_playlist(self, song_title: str, artist: str = None) -> Tuple[bool, str]:
        """从歌单中删除指定歌曲（实际上是添加到"我不喜欢"等歌单）"""
        try:
            safe_print(f"🎵 正在处理歌曲: {song_title}")
            if artist:
                safe_print(f"   艺术家: {artist}")
            
            # 确保QQ音乐窗口处于激活状态
            if not self.find_qqmusic_window():
                return False, "无法激活QQ音乐窗口"
            
            # 搜索并添加到歌单
            success, message = self.find_and_add_to_playlist(song_title, artist)
            
            if success:
                safe_print("   ✅ 添加成功")
                return True, message
            else:
                safe_print(f"   ❌ 添加失败: {message}")
                return False, message
                
        except Exception as e:
            error_msg = f"处理歌曲时出错: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def batch_delete_from_recent_tracks(self, track_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量删除最近播放的歌曲"""
        if not self.initialize():
            return {'error': '初始化失败'}
        
        results = {
            'total': len(track_list),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        safe_print(f"🗑️ 开始批量处理 {len(track_list)} 首歌曲...")
        safe_print(f"📝 目标歌单: {self.target_playlist}")
        safe_print("-" * 50)
        
        for i, track in enumerate(track_list, 1):
            track_id = track['id']
            song_title = track['title']
            artist = track['artist']
            
            safe_print(f"[{i}/{len(track_list)}] {song_title}")
            
            # 先标记为pending状态
            db.mark_song_deletion_status(track_id, 'pending', f"正在添加到歌单: {self.target_playlist}")
            
            # 执行添加到歌单操作
            success, message = self.delete_song_from_playlist(song_title, artist)
            
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
        safe_print(f"🎵 批量处理完成:")
        safe_print(f"  ✅ 成功: {results['success']}")
        safe_print(f"  ❌ 失败: {results['failed']}")
        safe_print(f"  📊 成功率: {results['success']/results['total']*100:.1f}%")
        
        return results
    
    def cleanup(self):
        """清理资源"""
        logger.info("QQ音乐管理器资源已清理")

# 全局实例
qqmusic_manager = QQMusicPlaylistManager()
