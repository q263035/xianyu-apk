"""
测试主界面 - 添加商品 ID
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.core.window import Window

Window.size = (400, 700)


class MainScreen(Screen):
    """主屏幕"""
    
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
        scroll_view = ScrollView(size_hint=(1, 0.6))
        item_list_layout = GridLayout(
            cols=1,
            size_hint_y=None,
            spacing=5,
            padding=5
        )
        item_list_layout.bind(minimum_height=item_list_layout.setter('height'))
        scroll_view.add_widget(item_list_layout)
        layout.add_widget(scroll_view)
        
        # 添加示例商品
        for item_id in ['628394756', '739485012', '840596123']:
            item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=5)
            
            lbl = Label(
                text=f'ID: {item_id}',
                font_size='16sp',
                halign='left',
                size_hint_x=0.6
            )
            item_layout.add_widget(lbl)
            
            btn_view = Button(
                text='查看',
                font_size='14sp',
                size_hint_x=0.2
            )
            item_layout.add_widget(btn_view)
            
            btn_del = Button(
                text='删除',
                font_size='14sp',
                background_color=(1, 0.3, 0.3, 1),
                size_hint_x=0.2
            )
            item_layout.add_widget(btn_del)
            
            item_list_layout.add_widget(item_layout)
        
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
        btn_layout.add_widget(btn_start)
        
        btn_settings = Button(
            text='⚙️ 设置',
            font_size='16sp',
            background_color=(0.6, 0.6, 0.6, 1)
        )
        btn_layout.add_widget(btn_settings)
        
        layout.add_widget(btn_layout)
        
        # 状态标签
        status_label = Label(
            text='就绪',
            font_size='14sp',
            size_hint=(1, 0.08),
            color=(0.5, 0.5, 0.5, 1)
        )
        layout.add_widget(status_label)
        
        self.add_widget(layout)
    
    def show_add_popup(self, instance):
        """显示添加商品弹窗"""
        popup_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # 标题
        title = Label(
            text='添加商品 ID',
            font_size='20sp',
            size_hint=(1, 0.2)
        )
        popup_layout.add_widget(title)
        
        # 输入框
        add_input = TextInput(
            hint_text='商品 ID（数字）',
            multiline=False,
            input_filter='int',
            font_size='18sp',
            size_hint=(1, 0.3),
            padding=(15, 10)
        )
        popup_layout.add_widget(add_input)
        
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
        
        btn_confirm = Button(
            text='添加',
            font_size='16sp',
            background_color=(0.2, 0.7, 0.3, 1)
        )
        btn_confirm.bind(on_press=lambda x: popup.dismiss())
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


class TestApp(App):
    def build(self):
        self.title = '主界面测试'
        sm = ScreenManager()
        sm.add_widget(MainScreen())
        return sm


if __name__ == '__main__':
    TestApp().run()
