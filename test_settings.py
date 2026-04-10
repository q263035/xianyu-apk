"""
测试设置界面
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.core.window import Window

Window.size = (400, 700)


class SettingsScreen(Screen):
    """设置屏幕"""
    
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
            text='✓ WebView: 模拟模式',
            font_size='14sp',
            color=(1, 0.8, 0, 1),
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
    
    def go_to_main(self, instance):
        """跳转到主页面"""
        App.get_running_app().screen_manager.current = 'main'
    
    def save_settings(self, instance):
        """保存设置"""
        self.status_label.text = '✓ 设置已保存'
        self.status_label.color = (0, 0.8, 0, 1)


class MainScreen(Screen):
    """主屏幕"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'main'
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        title = Label(
            text='📦 闲鱼商品监控器',
            font_size='24sp',
            size_hint=(1, 0.2),
            bold=True
        )
        layout.add_widget(title)
        
        btn_settings = Button(
            text='⚙️ 进入设置页面',
            font_size='18sp',
            size_hint=(1, 0.3),
            background_color=(0.2, 0.6, 1, 1)
        )
        btn_settings.bind(on_press=self.go_to_settings)
        layout.add_widget(btn_settings)
        
        self.add_widget(layout)
    
    def go_to_settings(self, instance):
        """跳转到设置页面"""
        App.get_running_app().screen_manager.current = 'settings'


class TestApp(App):
    def build(self):
        self.title = '设置界面测试'
        sm = ScreenManager()
        sm.add_widget(MainScreen())
        sm.add_widget(SettingsScreen())
        return sm


if __name__ == '__main__':
    TestApp().run()
