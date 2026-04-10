"""
悬浮窗组件
支持：
- 系统级悬浮窗显示
- 一键开关自动化购买
- 显示当前状态
- 拖动位置
"""

from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.widget import Widget

# 尝试导入 android 模块
try:
    from jnius import autoclass, cast
    from android.runnable import run_on_ui_thread
    from android.activity import getActivity
    ANDROID_AVAILABLE = True
except ImportError:
    ANDROID_AVAILABLE = False
    def run_on_ui_thread(func):
        """非安卓环境的空装饰器"""
        return func


class FloatingWindow(Widget):
    """
    悬浮窗组件（安卓系统级）
    显示在屏幕最上层，可随时控制自动化购买开关
    """
    
    status = StringProperty('待机')
    auto_buy_enabled = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.window = None
        self.layout = None
        self.text_view = None
        self.button = None
        self.callback = None
        
        if ANDROID_AVAILABLE:
            self._create_floating_window()
    
    @run_on_ui_thread
    def _create_floating_window(self):
        """创建系统悬浮窗"""
        try:
            # 导入安卓类
            Context = autoclass('android.content.Context')
            WindowManager = autoclass('android.view.WindowManager')
            WindowManagerLayoutParams = autoclass('android.view.WindowManager$LayoutParams')
            LinearLayout = autoclass('android.widget.LinearLayout')
            TextView = autoclass('android.widget.TextView')
            Button = autoclass('android.widget.Button')
            ColorDrawable = autoclass('android.graphics.drawable.ColorDrawable')
            Color = autoclass('android.graphics.Color')
            Gravity = autoclass('android.view.Gravity')
            View = autoclass('android.view.View')
            
            # 获取 Activity 和 WindowManager
            activity = getActivity()
            window_manager = activity.getSystemService(Context.WINDOW_SERVICE)
            
            # 创建布局参数
            params = WindowManagerLayoutParams()
            params.type = WindowManagerLayoutParams.TYPE_APPLICATION_OVERLAY
            params.flags = (
                WindowManagerLayoutParams.FLAG_NOT_FOCUSABLE |
                WindowManagerLayoutParams.FLAG_LAYOUT_IN_SCREEN
            )
            params.width = 300  # 宽度
            params.height = 150  # 高度
            params.gravity = Gravity.TOP | Gravity.RIGHT  # 右上角
            params.x = 50  # X 偏移
            params.y = 200  # Y 偏移
            params.format = -3  # TRANSLUCENT
            
            # 创建主布局
            layout = LinearLayout(activity)
            layout.setOrientation(LinearLayout.VERTICAL)
            layout.setPadding(20, 20, 20, 20)
            layout.setBackgroundColor(Color.parseColor('#CC000000'))  # 半透明黑色背景
            
            # 创建状态文本
            text_view = TextView(activity)
            text_view.setText('🤖 自动化：关闭')
            text_view.setTextSize(16.0)
            text_view.setTextColor(Color.WHITE)
            text_view.setGravity(Gravity.CENTER)
            
            # 创建开关按钮
            button = Button(activity)
            button.setText('▶️ 开启自动化')
            button.setTextSize(16.0)
            button.setBackgroundColor(Color.parseColor('#00AA00'))
            button.setTextColor(Color.WHITE)
            
            # 设置按钮点击事件
            class OnClickListener(autoclass('android.view.View$OnClickListener')):
                def __init__(self, parent):
                    super().__init__()
                    self.parent = parent
                
                def onClick(self, v):
                    self.parent._on_button_click()
            
            button.setOnClickListener(OnClickListener(self))
            
            # 添加组件到布局
            layout.addView(text_view)
            layout.addView(button)
            
            # 添加到窗口管理器
            window_manager.addView(layout, params)
            
            # 保存引用
            self.window = window_manager
            self.layout = layout
            self.text_view = text_view
            self.button = button
            self.params = params
            
            print("✓ 悬浮窗创建成功")
            
        except Exception as e:
            print(f"✗ 悬浮窗创建失败：{e}")
            import traceback
            traceback.print_exc()
    
    @run_on_ui_thread
    def _on_button_click(self):
        """按钮点击事件"""
        self.auto_buy_enabled = not self.auto_buy_enabled
        
        if self.auto_buy_enabled:
            self._update_ui('🤖 自动化：开启', '⏹️ 关闭自动化', '#FF0000')
        else:
            self._update_ui('🤖 自动化：关闭', '▶️ 开启自动化', '#00AA00')
        
        # 触发回调
        if self.callback:
            self.callback(self.auto_buy_enabled)
    
    @run_on_ui_thread
    def _update_ui(self, status_text, button_text, button_color):
        """更新 UI"""
        if self.text_view:
            self.text_view.setText(status_text)
        if self.button:
            self.button.setText(button_text)
            self.button.setBackgroundColor(
                android.graphics.Color.parseColor(button_color)
            )
        self.status = status_text
    
    def set_callback(self, callback):
        """设置状态变化回调"""
        self.callback = callback
    
    @run_on_ui_thread
    def show(self):
        """显示悬浮窗"""
        if self.window and self.layout:
            try:
                self.window.addView(self.layout, self.params)
                print("✓ 悬浮窗已显示")
            except Exception as e:
                print(f"✗ 显示失败：{e}")
    
    @run_on_ui_thread
    def hide(self):
        """隐藏悬浮窗"""
        if self.window and self.layout:
            try:
                self.window.removeView(self.layout)
                print("✓ 悬浮窗已隐藏")
            except Exception as e:
                print(f"✗ 隐藏失败：{e}")
    
    @run_on_ui_thread
    def destroy(self):
        """销毁悬浮窗"""
        if self.window and self.layout:
            try:
                self.window.removeView(self.layout)
                self.window = None
                self.layout = None
                print("✓ 悬浮窗已销毁")
            except Exception as e:
                print(f"✗ 销毁失败：{e}")
    
    @run_on_ui_thread
    def set_position(self, x, y):
        """设置位置"""
        if self.params:
            self.params.x = x
            self.params.y = y
            if self.window and self.layout:
                self.window.updateViewLayout(self.layout, self.params)


class MockFloatingWindow(Widget):
    """
    悬浮窗模拟版本（桌面测试用）
    使用 Kivy 窗口模拟悬浮窗效果
    """
    
    status = StringProperty('待机')
    auto_buy_enabled = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.callback = None
        self.popup = None
        print("⚠️ 使用 MockFloatingWindow（桌面测试模式）")
    
    def _create_floating_window(self):
        """创建模拟悬浮窗"""
        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        
        # 创建布局
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.background_color = (0, 0, 0, 0.8)
        
        # 状态文本
        self.status_label = Label(
            text='🤖 自动化：关闭',
            font_size='16sp',
            color=(1, 1, 1, 1),
            size_hint=(1, 0.5)
        )
        layout.add_widget(self.status_label)
        
        # 开关按钮
        self.toggle_button = Button(
            text='▶️ 开启自动化',
            font_size='16sp',
            background_color=(0, 0.67, 0, 1),
            size_hint=(1, 0.5)
        )
        self.toggle_button.bind(on_press=self._on_button_click)
        layout.add_widget(self.toggle_button)
        
        # 创建 Popup 模拟悬浮窗
        self.popup = Popup(
            title='🎛️ 快捷控制',
            content=layout,
            size_hint=(0.7, 0.3),
            auto_dismiss=False,
            separator_color=(0, 0, 0, 0)
        )
        
        print("✓ 模拟悬浮窗创建成功")
    
    def _on_button_click(self, instance):
        """按钮点击事件"""
        self.auto_buy_enabled = not self.auto_buy_enabled
        
        if self.auto_buy_enabled:
            self.status_label.text = '🤖 自动化：开启'
            self.toggle_button.text = '⏹️ 关闭自动化'
            self.toggle_button.background_color = (1, 0, 0, 1)
            self.status = '🤖 自动化：开启'
        else:
            self.status_label.text = '🤖 自动化：关闭'
            self.toggle_button.text = '▶️ 开启自动化'
            self.toggle_button.background_color = (0, 0.67, 0, 1)
            self.status = '🤖 自动化：关闭'
        
        # 触发回调
        if self.callback:
            self.callback(self.auto_buy_enabled)
    
    def set_callback(self, callback):
        """设置状态变化回调"""
        self.callback = callback
    
    def show(self):
        """显示悬浮窗"""
        if not self.popup:
            self._create_floating_window()
        if self.popup:
            self.popup.open()
            print("✓ 模拟悬浮窗已显示")
    
    def hide(self):
        """隐藏悬浮窗"""
        if self.popup and self.popup.is_open:
            self.popup.dismiss()
            print("✓ 模拟悬浮窗已隐藏")
    
    def destroy(self):
        """销毁悬浮窗"""
        self.hide()
        self.popup = None
        print("✓ 模拟悬浮窗已销毁")
    
    def set_position(self, x, y):
        """设置位置（模拟）"""
        print(f"[Mock] 设置位置：({x}, {y})")


# 工厂函数
def create_floating_window(**kwargs):
    """创建悬浮窗实例"""
    if ANDROID_AVAILABLE:
        return FloatingWindow(**kwargs)
    else:
        return MockFloatingWindow(**kwargs)
