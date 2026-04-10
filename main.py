"""
闲鱼商品访问器 - 安卓 APK 版本（带购买限制检测）
功能：
- 管理多个商品 ID（添加/删除/编辑）
- 自动轮询访问商品页面
- 可配置轮询间隔
- 账号类型选择（个人号/企业号）
- 自动化购买流程（基于 URL 变化检测）
- 购买限制检测 + 自动重试（等待 10 分钟）
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
from kivy.clock import Clock
import json
import os

# 设置窗口大小（仅桌面测试用，安卓自动全屏）
# 注册中文字体（安卓系统内置）
from kivy.core.text import LabelBase
LabelBase.register(name='Roboto', fn_regular='DroidSansFallbackFull.ttf')
LabelBase.register(name='DroidSansFallback', fn_regular='DroidSansFallbackFull.ttf')
Window.size = (400, 700)

# 数据存储文件
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'item_ids.json')

# 导入 WebView 组件
try:
    from webview import create_webview, URLPatterns
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("⚠️ WebView 模块不可用，使用模拟模式")

# 导入悬浮窗组件
try:
    from floating_window import create_floating_window
    FLOATING_WINDOW_AVAILABLE = True
except ImportError:
    FLOATING_WINDOW_AVAILABLE = False
    print("⚠️ 悬浮窗模块不可用，使用模拟模式")


def load_item_ids():
    """从文件加载商品 ID 列表"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return (
                    data.get('item_ids', []),
                    data.get('interval', 60),
                    data.get('account_type', 'personal'),
                    data.get('auto_buy', False),
                    data.get('retry_delay', 600),  # 默认 10 分钟
                    data.get('max_retries', 3),
                    data.get('loop_count', 1),  # 循环次数
                    data.get('loop_interval', 60)  # 循环间隔
                )
        except:
            pass
    return [], 60, 'personal', False, 600, 3, 1, 60


def save_item_ids(item_ids, interval=60, account_type='personal', auto_buy=False, 
                  retry_delay=600, max_retries=3, loop_count=1, loop_interval=60):
    """保存商品 ID 列表到文件"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'item_ids': item_ids,
                'interval': interval,
                'account_type': account_type,
                'auto_buy': auto_buy,
                'retry_delay': retry_delay,
                'max_retries': max_retries,
                'loop_count': loop_count,
                'loop_interval': loop_interval
            }, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存失败：{e}")
        return False


class MainScreen(Screen):
    """主屏幕 - 商品列表"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'main'
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题
        title = Label(
            text='闲鱼商品监控器',
            font_size='22sp',
            size_hint=(1, 0.1),
            bold=True
        )
        layout.add_widget(title)
        
        # 商品列表（可滚动）
        self.scroll_view = ScrollView(size_hint=(1, 0.6))
        self.item_list_layout = GridLayout(
            cols=1,
            size_hint_y=None,
            spacing=5,
            padding=5
        )
        self.item_list_layout.bind(minimum_height=self.item_list_layout.setter('height'))
        self.scroll_view.add_widget(self.item_list_layout)
        layout.add_widget(self.scroll_view)
        
        # 底部按钮区
        btn_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)
        
        btn_add = Button(
            text='➕ 添加商品',
            font_size='16sp',
            background_color=(0.2, 0.7, 0.3, 1)
        )
        btn_add.bind(on_press=self.show_add_popup)
        layout.add_widget(btn_add)
        
        btn_start = Button(
            text='▶️ 开始轮询',
            font_size='16sp',
            background_color=(0.2, 0.6, 1, 1)
        )
        btn_start.bind(on_press=self.start_polling)
        btn_layout.add_widget(btn_start)
        
        btn_settings = Button(
            text='⚙️ 设置',
            font_size='16sp',
            background_color=(0.6, 0.6, 0.6, 1)
        )
        btn_settings.bind(on_press=self.go_to_settings)
        btn_layout.add_widget(btn_settings)
        
        layout.add_widget(btn_layout)
        
        # 悬浮窗控制按钮
        btn_floating = Button(
            text='🎛️ 悬浮窗',
            font_size='16sp',
            background_color=(0.8, 0.5, 0, 1),
            size_hint=(1, 0.05)
        )
        btn_floating.bind(on_press=self.toggle_floating_window)
        layout.add_widget(btn_floating)
        
        # 状态标签
        self.status_label = Label(
            text='就绪',
            font_size='14sp',
            size_hint=(1, 0.08),
            color=(0.5, 0.5, 0.5, 1)
        )
        layout.add_widget(self.status_label)
        
        # 等待进度条（购买限制时显示）
        self.wait_progress = ProgressBar(
            max=100,
            value=0,
            size_hint=(1, 0.05)
        )
        self.wait_progress.opacity = 0  # 默认隐藏
        layout.add_widget(self.wait_progress)
        
        self.add_widget(layout)
        
        # 加载商品列表
        (self.item_ids, self.interval, self.account_type, self.auto_buy, 
         self.retry_delay, self.max_retries, self.loop_count, self.loop_interval) = load_item_ids()
        self.refresh_item_list()
        
        # 轮询相关
        self.polling = False
        self.poll_index = 0
        self.poll_event = None
        self.loop_current = 0  # 当前循环次数
        
        # WebView 实例
        self.webview = None
        if WEBVIEW_AVAILABLE:
            self.webview = create_webview()
            # 设置 URL 变化回调
            self.webview.set_url_change_callback(self.on_url_change)
            # 注册购买限制回调
            self.webview.register_callback('buy_blocked', self.on_buy_blocked)
            self.webview.register_callback('buy_blocked_waiting', self.on_buy_blocked_waiting)
            self.webview.register_callback('buy_blocked_max', self.on_buy_blocked_max)
            # 注册购买完成回调
            self.webview.register_callback('purchase_complete', self.on_purchase_complete)
            print("✓ WebView 已初始化")
        
        # 悬浮窗实例
        self.floating_window = None
        self.floating_visible = False
        if FLOATING_WINDOW_AVAILABLE:
            self.floating_window = create_floating_window()
            # 设置状态变化回调
            self.floating_window.set_callback(self.on_floating_window_toggle)
            print("✓ 悬浮窗已初始化")
    
    def go_to_settings(self, instance):
        """跳转到设置页面"""
        App.get_running_app().screen_manager.current = 'settings'
    
    def on_url_change(self, url, page_type):
        """URL 变化回调"""
        page_names = {
            'item': '📦 商品页',
            'order': '📋 订单页',
            'payment': '💰 付款页',
            'home': '🏠 首页',
            'unknown': '❓ 未知页'
        }
        page_name = page_names.get(page_type, '❓ 未知页')
        self.status_label.text = f'当前：{page_name}'
        self.status_label.color = (0, 0.6, 1, 1)
    
    def on_floating_window_toggle(self, auto_buy_enabled):
        """悬浮窗开关回调"""
        # 同步到主设置
        self.auto_buy = auto_buy_enabled
        save_item_ids(
            self.item_ids, self.interval, self.account_type, self.auto_buy,
            self.retry_delay, self.max_retries, self.loop_count, self.loop_interval
        )
        
        # 更新状态显示
        if auto_buy_enabled:
            self.status_label.text = '🤖 自动化已启用（悬浮窗）'
            self.status_label.color = (0, 0.8, 0, 1)
        else:
            self.status_label.text = '⏸️ 自动化已暂停（悬浮窗）'
            self.status_label.color = (1, 0.8, 0, 1)
    
    def on_purchase_complete(self):
        """购买完成回调"""
        print("✅ 购买完成，返回首页等待")
        
        # 重置 WebView 自动化状态
        if self.webview:
            self.webview.reset_auto_buy_state()
        
        # 更新状态显示
        self.status_label.text = f'✅ 购买完成，等待 {self.loop_interval}秒后继续...'
        self.status_label.color = (0, 0.8, 0, 1)
        
        # 如果在轮询中，等待循环间隔后继续下一个商品
        if self.polling:
            print(f"⏱️ 等待 {self.loop_interval} 秒后继续轮询...")
            Clock.schedule_once(self.resume_polling_after_purchase, self.loop_interval)
    
    def resume_polling_after_purchase(self, *args):
        """购买完成后恢复轮询"""
        if not self.polling:
            return
        
        # 移动到下一个商品
        self.poll_index = (self.poll_index + 1) % len(self.item_ids)
        
        # 检查是否需要开始新一轮
        if self.poll_index == 0:
            self.loop_current += 1
            if self.loop_current >= self.loop_count:
                # 完成所有循环
                self.stop_polling()
                self.status_label.text = f'✅ 完成 {self.loop_count} 轮轮询'
                self.status_label.color = (0, 0.8, 0, 1)
                return
            else:
                print(f"▶️ 开始第 {self.loop_current + 1}/{self.loop_count} 轮")
                self.status_label.text = f'开始第 {self.loop_current + 1}/{self.loop_count} 轮'
        
        # 继续轮询下一个商品
        self.poll_next()
    
    def toggle_floating_window(self, instance):
        """切换悬浮窗显示/隐藏"""
        if not self.floating_window:
            self.status_label.text = '❌ 悬浮窗不可用'
            self.status_label.color = (1, 0, 0, 1)
            return
        
        # 切换显示状态
        if hasattr(self, 'floating_visible') and self.floating_visible:
            self.floating_window.hide()
            self.floating_visible = False
            instance.text = '🎛️ 悬浮窗'
        else:
            self.floating_window.show()
            self.floating_visible = True
            instance.text = '❌ 关闭悬浮窗'
    
    def on_buy_blocked(self, block_count, wait_time):
        """购买被限制回调"""
        self.status_label.text = f'⚠️ 购买受限 ({block_count}/{self.max_retries})'
        self.status_label.color = (1, 0.5, 0, 1)
        
        # 显示进度条
        self.wait_progress.opacity = 1
        self.wait_progress.max = wait_time
        self.wait_progress.value = 0
        
        # 启动倒计时
        self.wait_countdown = wait_time
        self.wait_event = Clock.schedule_interval(self.update_wait_progress, 1)
        
        print(f"⚠️ 购买被限制，等待 {wait_time} 秒")
    
    def on_buy_blocked_waiting(self, block_count, wait_time):
        """等待重试回调"""
        self.status_label.text = f'⏱️ 等待中... ({block_count}/{self.max_retries})'
        self.status_label.color = (1, 0.8, 0, 1)
    
    def on_buy_blocked_max(self, block_count):
        """达到最大重试次数回调"""
        self.status_label.text = f'❌ 已达最大重试次数，已停止'
        self.status_label.color = (1, 0, 0, 1)
        
        # 隐藏进度条
        self.wait_progress.opacity = 0
        
        # 停止倒计时
        if hasattr(self, 'wait_event') and self.wait_event:
            Clock.unschedule(self.wait_event)
    
    def update_wait_progress(self, dt):
        """更新等待进度条"""
        if hasattr(self, 'wait_countdown'):
            self.wait_countdown -= 1
            self.wait_progress.value = self.retry_delay - self.wait_countdown
            
            # 更新状态显示剩余时间
            minutes = self.wait_countdown // 60
            seconds = self.wait_countdown % 60
            self.status_label.text = f'⏱️ 剩余：{minutes:02d}:{seconds:02d}'
            
            if self.wait_countdown <= 0:
                Clock.unschedule(self.update_wait_progress)
                self.wait_progress.opacity = 0
                self.status_label.text = '🔄 开始重试...'
    
    def refresh_item_list(self):
        """刷新商品列表显示"""
        self.item_list_layout.clear_widgets()
        
        if not self.item_ids:
            empty_label = Label(
                text='暂无商品，点击"添加商品"添加',
                font_size='16sp',
                color=(0.6, 0.6, 0.6, 1),
                size_hint_y=None,
                height=50
            )
            self.item_list_layout.add_widget(empty_label)
            return
        
        for idx, item_id in enumerate(self.item_ids):
            item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=5)
            
            # 商品 ID 标签
            lbl = Label(
                text=f'ID: {item_id}',
                font_size='16sp',
                halign='left',
                size_hint_x=0.6
            )
            item_layout.add_widget(lbl)
            
            # 查看按钮
            btn_view = Button(
                text='查看',
                font_size='14sp',
                size_hint_x=0.2
            )
            btn_view.bind(on_press=lambda x, iid=item_id: self.view_item(iid))
            item_layout.add_widget(btn_view)
            
            # 删除按钮
            btn_del = Button(
                text='删除',
                font_size='14sp',
                background_color=(1, 0.3, 0.3, 1),
                size_hint_x=0.2
            )
            btn_del.bind(on_press=lambda x, idx=idx: self.delete_item(idx))
            item_layout.add_widget(btn_del)
            
            self.item_list_layout.add_widget(item_layout)
    
    def show_add_popup(self, instance):
        """显示添加商品弹窗"""
        popup_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # 标题
        title = Label(text='添加商品 ID', font_size='20sp', size_hint=(1, 0.2))
        popup_layout.add_widget(title)
        
        # 输入框
        self.add_input = TextInput(
            hint_text='输入商品 ID（数字）',
            multiline=False,
            input_filter='int',
            font_size='18sp',
            size_hint=(1, 0.3),
            padding=(15, 10)
        )
        popup_layout.add_widget(self.add_input)
        
        # 批量输入提示
        hint = Label(
            text='多个 ID 用逗号或换行分隔',
            font_size='14sp',
            color=(0.6, 0.6, 0.6, 1),
            size_hint=(1, 0.15)
        )
        popup_layout.add_widget(hint)
        
        # 按钮区
        btn_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=10)
        
        btn_cancel = Button(text='取消', font_size='16sp')
        btn_cancel.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(btn_cancel)
        
        btn_confirm = Button(text='添加', font_size='16sp', background_color=(0.2, 0.7, 0.3, 1))
        btn_confirm.bind(on_press=self.confirm_add)
        btn_layout.add_widget(btn_confirm)
        
        popup_layout.add_widget(btn_layout)
        
        # 创建弹窗
        popup = Popup(
            title='添加商品',
            content=popup_layout,
            size_hint=(0.9, 0.5),
            auto_dismiss=False
        )
        popup.open()
    
    def confirm_add(self, instance):
        """确认添加商品 ID"""
        text = self.add_input.text.strip()
        if not text:
            return
        
        # 解析多个 ID（支持逗号或换行分隔）
        new_ids = []
        for line in text.replace(',', '\n').split('\n'):
            iid = line.strip()
            if iid and iid.isdigit() and iid not in self.item_ids:
                new_ids.append(iid)
        
        if new_ids:
            self.item_ids.extend(new_ids)
            save_item_ids(self.item_ids, self.interval, self.account_type, self.auto_buy, 
                         self.retry_delay, self.max_retries, self.loop_count, self.loop_interval)
            self.refresh_item_list()
            self.status_label.text = f'✓ 添加了 {len(new_ids)} 个商品'
            self.status_label.color = (0, 0.8, 0, 1)
        
        # 关闭弹窗
        instance.parent.parent.parent.parent.dismiss()
    
    def view_item(self, item_id):
        """查看商品"""
        url = f"https://2.taobao.com/item.htm?id={item_id}"
        
        if self.auto_buy and self.webview:
            # 启用自动化购买 - 使用 WebView
            self.start_auto_buy(item_id, url)
        else:
            # 普通打开 - 使用系统浏览器
            try:
                import webbrowser
                webbrowser.open(url)
            except:
                pass
            self.status_label.text = f'已打开商品 {item_id}'
            self.status_label.color = (0, 0.6, 1, 1)
    
    def delete_item(self, idx):
        """删除商品"""
        if 0 <= idx < len(self.item_ids):
            deleted = self.item_ids.pop(idx)
            save_item_ids(self.item_ids, self.interval, self.account_type, self.auto_buy,
                         self.retry_delay, self.max_retries, self.loop_count, self.loop_interval)
            self.refresh_item_list()
            self.status_label.text = f'已删除商品 {deleted}'
            self.status_label.color = (0.8, 0.6, 0, 1)
    
    def start_polling(self, instance):
        """开始轮询"""
        if self.polling:
            self.stop_polling()
            return
        
        if not self.item_ids:
            self.status_label.text = '❌ 请先添加商品'
            self.status_label.color = (1, 0, 0, 1)
            return
        
        self.polling = True
        self.poll_index = 0
        self.loop_current = 0
        instance.text = '⏹️ 停止轮询'
        instance.background_color = (1, 0.3, 0.3, 1)
        self.status_label.text = f'开始轮询（第 1/{self.loop_count} 轮，间隔 {self.interval}秒）'
        self.status_label.color = (0, 0.8, 0, 1)
        
        # 立即访问第一个
        self.poll_next()
        
        # 定时轮询
        self.poll_event = Clock.schedule_interval(self.poll_next, self.interval)
    
    def stop_polling(self):
        """停止轮询"""
        if self.poll_event:
            Clock.unschedule(self.poll_event)
            self.poll_event = None
        self.polling = False
        self.poll_index = 0
        self.loop_current = 0
        
        # 更新按钮状态
        for child in self.children[0].children:
            if isinstance(child, BoxLayout) and len(child.children) == 2:
                for btn in child.children:
                    if isinstance(btn, Button) and '轮询' in btn.text:
                        btn.text = '▶️ 开始轮询'
                        btn.background_color = (0.2, 0.6, 1, 1)
                        break
        
        self.status_label.text = '轮询已停止'
        self.status_label.color = (0.6, 0.6, 0.6, 1)
    
    def poll_next(self, *args):
        """轮询下一个商品"""
        if not self.polling or not self.item_ids:
            return
        
        # 如果正在等待限制解除，跳过
        if hasattr(self, 'wait_event') and self.wait_event:
            print("⚠️ 正在等待购买限制解除，跳过本次轮询")
            return
        
        item_id = self.item_ids[self.poll_index]
        self.view_item(item_id)
        
        self.status_label.text = f'访问中：{item_id} (第{self.loop_current + 1}/{self.loop_count}轮，{self.poll_index + 1}/{len(self.item_ids)})'
        self.status_label.color = (0, 0.6, 1, 1)
        
        # 检查是否完成一轮
        self.poll_index = (self.poll_index + 1) % len(self.item_ids)
        
        # 如果完成一轮，检查是否需要继续循环
        if self.poll_index == 0:
            self.loop_current += 1
            if self.loop_current >= self.loop_count:
                # 完成所有循环，停止轮询
                print(f"✓ 完成 {self.loop_count} 轮轮询")
                self.stop_polling()
                self.status_label.text = f'✓ 完成 {self.loop_count} 轮轮询'
                self.status_label.color = (0, 0.8, 0, 1)
                return
            else:
                # 等待循环间隔后继续下一轮
                print(f"⏱️ 第 {self.loop_current + 1} 轮开始，等待 {self.loop_interval} 秒...")
                self.status_label.text = f'⏱️ 轮询间隔：{self.loop_interval}秒后开始第 {self.loop_current + 1}/{self.loop_count} 轮'
                self.status_label.color = (1, 0.8, 0, 1)
                Clock.schedule_once(self.start_next_loop, self.loop_interval)
                # 暂停当前轮询定时器
                if self.poll_event:
                    Clock.unschedule(self.poll_event)
                    self.poll_event = None
    
    def start_next_loop(self, *args):
        """开始下一轮轮询"""
        if not self.polling:
            return
        
        print(f"▶️ 开始第 {self.loop_current + 1}/{self.loop_count} 轮")
        self.status_label.text = f'开始第 {self.loop_current + 1}/{self.loop_count} 轮'
        self.status_label.color = (0, 0.8, 0, 1)
        
        # 重新启动轮询定时器
        self.poll_event = Clock.schedule_interval(self.poll_next, self.interval)
    
    def start_auto_buy(self, item_id, url):
        """启动自动化购买流程（使用 WebView）"""
        if not self.webview:
            self.status_label.text = '❌ WebView 不可用'
            self.status_label.color = (1, 0, 0, 1)
            return
        
        self.status_label.text = f'🤖 自动化购买：{item_id}'
        self.status_label.color = (0.8, 0, 0.8, 1)
        
        # 配置 WebView
        self.webview.set_auto_buy(True, self.account_type)
        
        # 加载商品页面
        self.webview.load_url(url)
    
    def stop_auto_buy(self):
        """停止自动化购买"""
        if self.webview:
            self.webview.set_auto_buy(False)
    
    def reset_limit(self):
        """重置购买限制状态"""
        if self.webview:
            self.webview.reset_block_status()
            self.status_label.text = '✓ 限制状态已重置'
            self.status_label.color = (0, 0.8, 0, 1)
            self.wait_progress.opacity = 0
            if hasattr(self, 'wait_event') and self.wait_event:
                Clock.unschedule(self.wait_event)


class SettingsScreen(Screen):
    """设置屏幕"""
    
    def go_to_main(self, instance):
        """跳转到主页面"""
        App.get_running_app().screen_manager.current = 'main'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'settings'
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # 标题
        title = Label(
            text='⚙️ 设置',
            font_size='22sp',
            size_hint=(1, 0.08),
            bold=True
        )
        layout.add_widget(title)
        
        # 滚动区域
        scroll = ScrollView(size_hint=(1, 0.75))
        settings_content = BoxLayout(orientation='vertical', padding=10, spacing=15, size_hint_y=None)
        settings_content.bind(minimum_height=settings_content.setter('height'))
        
        # === WebView 状态 ===
        webview_status = Label(
            text=f'WebView: {"✓ 已启用" if WEBVIEW_AVAILABLE else "⚠️ 模拟模式"}',
            font_size='14sp',
            color=(0, 0.8, 0, 1) if WEBVIEW_AVAILABLE else (1, 0.8, 0, 1),
            size_hint=(1, None),
            height=40,
            halign='center'
        )
        settings_content.add_widget(webview_status)
        
        # === URL 变化检测说明 ===
        url_detect_info = Label(
            text='✓ 已启用 URL 变化检测\n自动识别：商品页 → 订单页 → 付款页',
            font_size='13sp',
            color=(0, 0.8, 0, 1),
            size_hint=(1, None),
            height=50,
            halign='center'
        )
        settings_content.add_widget(url_detect_info)
        
        # === 购买限制检测说明 ===
        limit_detect_info = Label(
            text='✓ 已启用购买限制检测\n检测到"无法购买"提示时自动等待重试',
            font_size='13sp',
            color=(0, 0.8, 0, 1),
            size_hint=(1, None),
            height=50,
            halign='center'
        )
        settings_content.add_widget(limit_detect_info)
        
        # === 账号类型选择 ===
        account_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=100, spacing=5)
        
        lbl_account = Label(
            text='账号类型',
            font_size='18sp',
            halign='left',
            size_hint=(1, 0.4)
        )
        account_layout.add_widget(lbl_account)
        
        # 账号类型选择框
        self.account_spinner = Spinner(
            text='个人号',
            values=['个人号', '企业号'],
            font_size='16sp',
            size_hint=(1, 0.6),
            background_color=(0.9, 0.9, 0.9, 1)
        )
        account_layout.add_widget(self.account_spinner)
        
        settings_content.add_widget(account_layout)
        
        # === 自动化购买开关 ===
        auto_buy_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=50, spacing=10)
        
        lbl_auto = Label(
            text='启用自动化购买',
            font_size='18sp',
            halign='left',
            size_hint_x=0.7
        )
        auto_buy_layout.add_widget(lbl_auto)
        
        self.auto_buy_checkbox = CheckBox(
            size_hint_x=0.3,
            active=False
        )
        auto_buy_layout.add_widget(self.auto_buy_checkbox)
        
        settings_content.add_widget(auto_buy_layout)
        
        # === 重试等待时间设置 ===
        retry_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=100, spacing=5)
        
        lbl_retry = Label(
            text='限制后等待时间（秒）',
            font_size='18sp',
            halign='left',
            size_hint=(1, 0.4)
        )
        retry_layout.add_widget(lbl_retry)
        
        self.retry_input = TextInput(
            text='600',
            multiline=False,
            input_filter='int',
            font_size='18sp',
            size_hint=(1, 0.6),
            padding=(15, 10)
        )
        retry_layout.add_widget(self.retry_input)
        
        settings_content.add_widget(retry_layout)
        
        # === 最大重试次数设置 ===
        max_retry_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=100, spacing=5)
        
        lbl_max_retry = Label(
            text='最大重试次数',
            font_size='18sp',
            halign='left',
            size_hint=(1, 0.4)
        )
        max_retry_layout.add_widget(lbl_max_retry)
        
        self.max_retry_input = TextInput(
            text='3',
            multiline=False,
            input_filter='int',
            font_size='18sp',
            size_hint=(1, 0.6),
            padding=(15, 10)
        )
        max_retry_layout.add_widget(self.max_retry_input)
        
        settings_content.add_widget(max_retry_layout)
        
        # === 循环次数设置 ===
        loop_count_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=100, spacing=5)
        
        lbl_loop_count = Label(
            text='循环次数（0=无限循环）',
            font_size='18sp',
            halign='left',
            size_hint=(1, 0.4)
        )
        loop_count_layout.add_widget(lbl_loop_count)
        
        self.loop_count_input = TextInput(
            text='1',
            multiline=False,
            input_filter='int',
            font_size='18sp',
            size_hint=(1, 0.6),
            padding=(15, 10)
        )
        loop_count_layout.add_widget(self.loop_count_input)
        
        settings_content.add_widget(loop_count_layout)
        
        # === 循环间隔设置 ===
        loop_interval_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=100, spacing=5)
        
        lbl_loop_interval = Label(
            text='循环间隔（秒）',
            font_size='18sp',
            halign='left',
            size_hint=(1, 0.4)
        )
        loop_interval_layout.add_widget(lbl_loop_interval)
        
        self.loop_interval_input = TextInput(
            text='60',
            multiline=False,
            input_filter='int',
            font_size='18sp',
            size_hint=(1, 0.6),
            padding=(15, 10)
        )
        loop_interval_layout.add_widget(self.loop_interval_input)
        
        settings_content.add_widget(loop_interval_layout)
        
        # === 轮询间隔设置 ===
        interval_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=100, spacing=5)
        
        lbl_interval = Label(
            text='轮询间隔（秒）',
            font_size='18sp',
            halign='left',
            size_hint=(1, 0.4)
        )
        interval_layout.add_widget(lbl_interval)
        
        self.interval_input = TextInput(
            text='60',
            multiline=False,
            input_filter='int',
            font_size='18sp',
            size_hint=(1, 0.6),
            padding=(15, 10)
        )
        interval_layout.add_widget(self.interval_input)
        
        settings_content.add_widget(interval_layout)
        
        scroll.add_widget(settings_content)
        layout.add_widget(scroll)
        
        # 保存按钮
        btn_save = Button(
            text='💾 保存设置',
            font_size='18sp',
            size_hint=(1, 0.1),
            background_color=(0.2, 0.7, 0.3, 1)
        )
        btn_save.bind(on_press=self.save_settings)
        layout.add_widget(btn_save)
        
        # 返回按钮
        btn_back = Button(
            text='← 返回',
            font_size='18sp',
            size_hint=(1, 0.1),
            background_color=(0.6, 0.6, 0.6, 1)
        )
        btn_back.bind(on_press=self.go_to_main)
        layout.add_widget(btn_back)
        
        # 状态标签
        self.status_label = Label(
            text='',
            font_size='14sp',
            size_hint=(1, 0.08),
            color=(0, 0.8, 0, 1)
        )
        layout.add_widget(self.status_label)
        
        self.add_widget(layout)
        
        # 加载当前设置
        (_, interval, account_type, auto_buy, retry_delay, max_retries, 
         loop_count, loop_interval) = load_item_ids()
        self.interval_input.text = str(interval)
        self.account_spinner.text = '个人号' if account_type == 'personal' else '企业号'
        self.auto_buy_checkbox.active = auto_buy
        self.retry_input.text = str(retry_delay)
        self.max_retry_input.text = str(max_retries)
        self.loop_count_input.text = str(loop_count)
        self.loop_interval_input.text = str(loop_interval)
    
    def save_settings(self, instance):
        """保存设置"""
        try:
            interval = int(self.interval_input.text.strip())
            retry_delay = int(self.retry_input.text.strip())
            max_retries = int(self.max_retry_input.text.strip())
            loop_count = int(self.loop_count_input.text.strip())
            loop_interval = int(self.loop_interval_input.text.strip())
            
            if interval < 10:
                self.status_label.text = '❌ 轮询间隔不能小于 10 秒'
                self.status_label.color = (1, 0, 0, 1)
                return
            
            if retry_delay < 60:
                self.status_label.text = '❌ 等待时间不能小于 60 秒'
                self.status_label.color = (1, 0, 0, 1)
                return
            
            if max_retries < 1 or max_retries > 10:
                self.status_label.text = '❌ 重试次数必须在 1-10 之间'
                self.status_label.color = (1, 0, 0, 1)
                return
            
            if loop_count < 0:
                self.status_label.text = '❌ 循环次数不能为负数'
                self.status_label.color = (1, 0, 0, 1)
                return
            
            if loop_interval < 0:
                self.status_label.text = '❌ 循环间隔不能为负数'
                self.status_label.color = (1, 0, 0, 1)
                return
            
            # 获取账号类型
            account_type = 'personal' if self.account_spinner.text == '个人号' else 'enterprise'
            auto_buy = self.auto_buy_checkbox.active
            
            item_ids, _, _, _, _, _, _, _ = load_item_ids()
            save_item_ids(item_ids, interval, account_type, auto_buy, retry_delay, max_retries, loop_count, loop_interval)
            
            self.status_label.text = '✓ 设置已保存'
            self.status_label.color = (0, 0.8, 0, 1)
            
            # 更新主屏幕的设置
            main_screen = App.get_running_app().screen_manager.get_screen('main')
            main_screen.interval = interval
            main_screen.account_type = account_type
            main_screen.auto_buy = auto_buy
            main_screen.retry_delay = retry_delay
            main_screen.max_retries = max_retries
            main_screen.loop_count = loop_count
            main_screen.loop_interval = loop_interval
            
            # 更新 WebView 配置
            if main_screen.webview:
                main_screen.webview.set_auto_buy(auto_buy, account_type)
                main_screen.webview.retry_delay_seconds = retry_delay
                main_screen.webview.max_retries = max_retries
            
        except ValueError:
            self.status_label.text = '❌ 请输入有效数字'
            self.status_label.color = (1, 0, 0, 1)


class XianyuApp(App):
    """应用主类"""
    
    def build(self):
        self.title = '闲鱼商品监控器'
        
        # 创建屏幕管理器
        self.screen_manager = ScreenManager()
        
        # 添加屏幕
        self.screen_manager.add_widget(MainScreen())
        self.screen_manager.add_widget(SettingsScreen())
        
        return self.screen_manager
    
    def on_pause(self):
        """安卓后台暂停支持"""
        return True
    
    def on_resume(self):
        """安卓前台恢复"""
        pass
    
    def on_stop(self):
        """应用停止时保存状态"""
        main_screen = self.screen_manager.get_screen('main')
        if main_screen.polling:
            main_screen.stop_polling()
        
        # 停止自动化购买
        if main_screen.webview:
            main_screen.stop_auto_buy()
        
        # 关闭悬浮窗
        if main_screen.floating_window:
            main_screen.floating_window.destroy()
        
        # 保存当前设置
        save_item_ids(
            main_screen.item_ids,
            main_screen.interval,
            main_screen.account_type,
            main_screen.auto_buy,
            main_screen.retry_delay,
            main_screen.max_retries,
            main_screen.loop_count,
            main_screen.loop_interval
        )


if __name__ == '__main__':
    XianyuApp().run()
