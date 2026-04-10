"""
闲鱼 WebView 组件（增强版 - 带限制检测）
支持：
- JavaScript 注入
- URL 变化检测
- 页面自动化操作
- 购买流程自动化
- 购买限制检测 + 自动重试
"""

from kivy.uix.widget import Widget
from kivy.clock import Clock
import re
import time

# 尝试导入 android 模块（仅在安卓环境可用）
try:
    from jnius import autoclass, cast
    from android.runnable import run_on_ui_thread
    ANDROID_AVAILABLE = True
except ImportError:
    ANDROID_AVAILABLE = False
    # 非安卓环境，创建空装饰器
    def run_on_ui_thread(func):
        """非安卓环境的空装饰器"""
        return func


# ============================================================
# URL 模式定义
# ============================================================

class URLPatterns:
    """闲鱼页面 URL 模式"""
    
    # 商品详情页
    ITEM = re.compile(r'2\.taobao\.com/item\.htm\?id=\d+')
    
    # 订单确认页
    ORDER_CONFIRM = re.compile(r'(mtop\.taobao\.com|buy\.taobao\.com).*(order|confirm)')
    
    # 付款页
    PAYMENT = re.compile(r'(cashier\.alipay\.com|mapi\.alipay\.com|pay\.taobao\.com)')
    
    # 首页/列表页
    HOME = re.compile(r'(2\.taobao\.com|s\.taobao\.com).*(index|home|search)?')
    
    @classmethod
    def detect_page_type(cls, url):
        """检测页面类型"""
        if not url:
            return 'unknown'
        
        if cls.ITEM.search(url):
            return 'item'
        elif cls.ORDER_CONFIRM.search(url):
            return 'order'
        elif cls.PAYMENT.search(url):
            return 'payment'
        elif cls.HOME.search(url):
            return 'home'
        else:
            return 'unknown'


# ============================================================
# WebView 组件
# ============================================================

class XianyuWebView(Widget):
    """
    闲鱼专用 WebView 组件
    支持 URL 变化检测和页面自动化
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.webview = None
        self.current_url = None
        self.previous_url = None
        self.auto_buy_enabled = False
        self.account_type = 'personal'
        self.callbacks = {}
        self.url_change_callback = None
        
        # 自动化流程状态
        self.auto_step = 0
        self.last_detected_page = None
        
        # 购买限制检测
        self.buy_blocked = False
        self.block_count = 0
        self.last_block_time = None
        self.retry_delay_seconds = 600  # 10 分钟
        self.max_retries = 3
        
        if ANDROID_AVAILABLE:
            self._create_webview()
    
    @run_on_ui_thread
    def _create_webview(self):
        """在 UI 线程创建 WebView"""
        try:
            # 导入安卓类
            Context = autoclass('android.content.Context')
            WebView = autoclass('android.webkit.WebView')
            WebViewClient = autoclass('android.webkit.WebViewClient')
            WebChromeClient = autoclass('android.webkit.WebChromeClient')
            WebSettings = autoclass('android.webkit.WebSettings')
            
            # 获取当前 Activity 的 Context
            from android.activity import getActivity
            activity = getActivity()
            context = activity.getApplicationContext()
            
            # 创建 WebView
            self.webview = WebView(context)
            
            # 配置 WebViewClient（包含 URL 变化检测）
            class XianyuWebViewClient(WebViewClient):
                def __init__(self, parent):
                    super().__init__()
                    self.parent = parent
                
                def shouldOverrideUrlLoading(self, view, url):
                    """拦截 URL 加载"""
                    url_str = str(url)
                    print(f"[URL 拦截] {url_str}")
                    
                    # 检测 URL 变化
                    self.parent._on_url_change(url_str)
                    
                    # 允许加载
                    return False
                
                def onPageFinished(self, view, url):
                    """页面加载完成"""
                    super().onPageFinished(view, url)
                    url_str = str(url)
                    print(f"[页面完成] {url_str}")
                    
                    # 触发页面加载回调
                    self.parent._on_page_loaded(url_str)
                    
                    # 检测购买限制提示
                    if self.parent.auto_buy_enabled:
                        Clock.schedule_once(lambda dt: self.parent._check_buy_limit(), 1.5)
            
            # 配置 WebChromeClient
            class XianyuWebChromeClient(WebChromeClient):
                def __init__(self, parent):
                    super().__init__()
                    self.parent = parent
                
                def onConsoleMessage(self, consoleMessage):
                    msg = consoleMessage.message()
                    line = consoleMessage.lineNumber()
                    source = consoleMessage.sourceId()
                    print(f"[WebView 控制台] {source}:{line} - {msg}")
                    return True
            
            # 设置客户端
            self.webview.setWebViewClient(XianyuWebViewClient(self))
            self.webview.setWebChromeClient(XianyuWebChromeClient(self))
            
            # 配置设置
            settings = self.webview.getSettings()
            settings.setJavaScriptEnabled(True)
            settings.setDomStorageEnabled(True)
            settings.setDatabaseEnabled(True)
            settings.setAllowFileAccess(True)
            settings.setLoadWithOverviewMode(True)
            settings.setUseWideViewPort(True)
            settings.setBuiltInZoomControls(True)
            settings.setDisplayZoomControls(False)
            
            # 启用混合内容
            if hasattr(WebSettings, 'MIXED_CONTENT_ALWAYS_ALLOW'):
                settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW)
            
            print("✓ WebView 创建成功")
            
        except Exception as e:
            print(f"✗ WebView 创建失败：{e}")
    
    @run_on_ui_thread
    def load_url(self, url):
        """加载 URL"""
        if self.webview:
            self.previous_url = self.current_url
            self.current_url = url
            self.webview.loadUrl(url)
            print(f"加载 URL: {url}")
    
    @run_on_ui_thread
    def load_data(self, html_data, base_url='about:blank'):
        """加载 HTML 数据"""
        if self.webview:
            self.webview.loadDataWithBaseURL(base_url, html_data, 'text/html', 'UTF-8', None)
    
    @run_on_ui_thread
    def execute_js(self, script, callback=None):
        """执行 JavaScript 代码"""
        if not self.webview:
            if callback:
                callback(None)
            return
        
        try:
            if callback:
                class JsCallback(autoclass('android.webkit.ValueCallback')):
                    def onReceiveValue(self, value):
                        callback(value)
                
                self.webview.evaluateJavascript(script, JsCallback())
            else:
                self.webview.evaluateJavascript(script, None)
            
            print(f"执行 JS: {script[:50]}...")
            
        except Exception as e:
            print(f"✗ JS 执行失败：{e}")
            if callback:
                callback(None)
    
    def _on_url_change(self, url):
        """URL 变化检测回调"""
        print(f"[URL 变化] {self.previous_url} → {url}")
        
        self.previous_url = self.current_url
        self.current_url = url
        
        # 检测页面类型
        page_type = URLPatterns.detect_page_type(url)
        print(f"[页面类型] {page_type}")
        
        # 触发 URL 变化回调
        if self.url_change_callback:
            self.url_change_callback(url, page_type)
        
        # 如果启用了自动化购买，根据页面类型执行对应步骤
        if self.auto_buy_enabled and not self.buy_blocked:
            self._handle_auto_step_by_page(page_type)
    
    def _on_page_loaded(self, url):
        """页面加载完成回调"""
        print(f"✓ 页面加载完成：{url}")
        
        # 触发回调
        if 'page_loaded' in self.callbacks:
            self.callbacks['page_loaded'](url)
    
    def _check_buy_limit(self):
        """检查购买限制提示"""
        if not self.auto_buy_enabled:
            return
        
        script = """
        (function() {
            // 检查页面中是否包含购买限制提示
            var text = document.body.innerText || '';
            var messages = [
                '亲，暂时无法购买',
                '暂时无法购买',
                '无法购买',
                '购买失败',
                '操作太频繁',
                '请稍后再试',
                '系统繁忙',
                '活动太火爆'
            ];
            
            for (var i = 0; i < messages.length; i++) {
                if (text.includes(messages[i])) {
                    return 'BLOCKED:' + messages[i];
                }
            }
            
            // 检查弹窗
            var dialogs = document.querySelectorAll('.dialog, .modal, .popup, .toast, .tip');
            for (var i = 0; i < dialogs.length; i++) {
                var dialogText = dialogs[i].innerText || '';
                for (var j = 0; j < messages.length; j++) {
                    if (dialogText.includes(messages[j])) {
                        return 'BLOCKED:' + messages[j];
                    }
                }
            }
            
            return 'OK';
        })();
        """
        
        def on_result(result):
            result_str = str(result) if result else 'OK'
            print(f"✓ 购买限制检测：{result_str}")
            
            if result_str and 'BLOCKED' in result_str:
                self._handle_buy_blocked(result_str)
            else:
                print("  → 可以正常购买")
        
        self.execute_js(script, on_result)
    
    def _handle_buy_blocked(self, reason):
        """处理购买被限制"""
        self.buy_blocked = True
        self.block_count += 1
        self.last_block_time = time.time()
        
        print(f"⚠️ 购买被限制：{reason}")
        print(f"   被限制次数：{self.block_count}")
        print(f"   最大重试次数：{self.max_retries}")
        
        # 触发回调通知用户
        if 'buy_blocked' in self.callbacks:
            self.callbacks['buy_blocked'](self.block_count, self.retry_delay_seconds)
        
        if self.block_count >= self.max_retries:
            print(f"❌ 已达到最大重试次数 ({self.max_retries})，停止自动化")
            if 'buy_blocked_max' in self.callbacks:
                self.callbacks['buy_blocked_max'](self.block_count)
            return
        
        # 计算等待时间
        wait_time = self.retry_delay_seconds
        print(f"⏱️ 等待 {wait_time} 秒后重试...")
        
        # 触发等待回调
        if 'buy_blocked_waiting' in self.callbacks:
            self.callbacks['buy_blocked_waiting'](self.block_count, wait_time)
        
        # 设置定时器继续执行
        Clock.schedule_once(lambda dt: self._retry_after_block(), wait_time)
    
    def _retry_after_block(self):
        """限制解除后重试"""
        print(f"⏰ 等待结束，开始第 {self.block_count + 1} 次重试")
        
        # 重置限制状态
        self.buy_blocked = False
        
        # 重新执行当前步骤
        if self.last_detected_page == 'item':
            print("🔄 重试：点击立即购买")
            self._find_and_click_buy_button()
        elif self.last_detected_page == 'order':
            print("🔄 重试：点击确认购买")
            self._find_and_click_confirm_button()
        elif self.last_detected_page == 'payment':
            print("🔄 重试：点击支付")
            self._find_and_click_payment_button()
    
    def _handle_auto_step_by_page(self, page_type):
        """根据页面类型处理自动化步骤"""
        if not self.auto_buy_enabled or self.buy_blocked:
            return
        
        print(f"🤖 检测到页面：{page_type}")
        
        if self.account_type == 'personal':
            self._personal_flow_by_page(page_type)
        else:
            self._enterprise_flow_by_page(page_type)
    
    # ============================================================
    # 个人号购买流程（基于 URL 检测）
    # ============================================================
    
    def _personal_flow_by_page(self, page_type):
        """个人号购买流程 - 基于页面类型"""
        
        if page_type == 'item':
            # 商品详情页 - 点击立即购买
            print("🤖 [个人号] 步骤 1/3: 商品详情页")
            self._find_and_click_buy_button()
            self.last_detected_page = 'item'
            
        elif page_type == 'order' and self.last_detected_page == 'item':
            # 订单确认页 - 点击确认购买
            print("🤖 [个人号] 步骤 2/3: 订单确认页")
            Clock.schedule_once(lambda dt: self._find_and_click_confirm_button(), 1)
            self.last_detected_page = 'order'
            
        elif page_type == 'payment' and self.last_detected_page in ['item', 'order']:
            # 付款页 - 点击支付
            print("🤖 [个人号] 步骤 3/3: 付款页")
            Clock.schedule_once(lambda dt: self._find_and_click_payment_button(), 1)
            self.last_detected_page = 'payment'
    
    # ============================================================
    # 企业号购买流程（基于 URL 检测）
    # ============================================================
    
    def _enterprise_flow_by_page(self, page_type):
        """企业号购买流程 - 基于页面类型"""
        
        if page_type == 'item':
            # 商品详情页 - 点击立即购买
            print("🤖 [企业号] 步骤 1/2: 商品详情页")
            self._find_and_click_buy_button()
            self.last_detected_page = 'item'
            
        elif page_type == 'payment' and self.last_detected_page == 'item':
            # 付款页 - 点击支付（跳过订单确认）
            print("🤖 [企业号] 步骤 2/2: 付款页")
            Clock.schedule_once(lambda dt: self._find_and_click_payment_button(), 1)
            self.last_detected_page = 'payment'
    
    # ============================================================
    # 按钮查找和点击
    # ============================================================
    
    def _find_and_click_buy_button(self):
        """查找并点击立即购买按钮"""
        script = """
        (function() {
            var buttons = document.querySelectorAll('button, div[role="button"], a.button, .btn, .action-btn');
            for (var i = 0; i < buttons.length; i++) {
                var text = buttons[i].innerText || buttons[i].textContent || '';
                if (text.includes('立即购买') || text.includes('马上抢') || text.includes('去抢购')) {
                    buttons[i].click();
                    return 'FOUND:' + text;
                }
            }
            return 'NOT_FOUND';
        })();
        """
        
        def on_result(result):
            print(f"✓ 立即购买按钮：{result}")
            if result and 'FOUND' in str(result):
                print("  → 已点击立即购买")
                # 点击后检测购买限制
                Clock.schedule_once(lambda dt: self._check_buy_limit(), 2)
        
        self.execute_js(script, on_result)
    
    def _find_and_click_confirm_button(self):
        """查找并点击确认购买按钮"""
        script = """
        (function() {
            var buttons = document.querySelectorAll('button, div[role="button"], .submit-btn, .confirm-btn');
            for (var i = 0; i < buttons.length; i++) {
                var text = buttons[i].innerText || buttons[i].textContent || '';
                if (text.includes('确认购买') || text.includes('确认订单') || text.includes('提交订单')) {
                    buttons[i].click();
                    return 'FOUND:' + text;
                }
            }
            return 'NOT_FOUND';
        })();
        """
        
        def on_result(result):
            print(f"✓ 确认购买按钮：{result}")
            if result and 'FOUND' in str(result):
                print("  → 已点击确认购买")
        
        self.execute_js(script, on_result)
    
    def _find_and_click_payment_button(self):
        """查找并点击支付按钮"""
        script = """
        (function() {
            var buttons = document.querySelectorAll('button, div[role="button"], .pay-btn, .payment-btn');
            for (var i = 0; i < buttons.length; i++) {
                var text = buttons[i].innerText || buttons[i].textContent || '';
                if (text.includes('支付') || text.includes('付款') || text.includes('立即支付') || text.includes('免密支付') || text.includes('确认支付')) {
                    buttons[i].click();
                    return 'FOUND:' + text;
                }
            }
            return 'NOT_FOUND';
        })();
        """
        
        def on_result(result):
            print(f"✓ 支付按钮：{result}")
            if result and 'FOUND' in str(result):
                print("  → 已点击支付")
                # 支付成功后，等待 3 秒返回首页
                print("  ⏱️ 支付完成，3 秒后返回首页...")
                Clock.schedule_once(lambda dt: self._go_to_home(), 3)
        
        self.execute_js(script, on_result)
    
    def _go_to_home(self):
        """返回首页"""
        print("🏠 返回首页")
        
        # 方式 1: 尝试通过 URL 跳转
        home_url = "https://2.taobao.com"
        self.load_url(home_url)
        
        # 触发回调通知主界面
        if 'purchase_complete' in self.callbacks:
            self.callbacks['purchase_complete']()
        
        print("  ✓ 已返回首页，等待下一轮...")
    
    # ============================================================
    # 控制方法
    # ============================================================
    
    def set_auto_buy(self, enabled, account_type='personal'):
        """设置自动化购买"""
        self.auto_buy_enabled = enabled
        self.account_type = account_type
        if not enabled:
            # 禁用时重置状态
            self.buy_blocked = False
            self.block_count = 0
            self.last_detected_page = None
        print(f"自动化购买：{'启用' if enabled else '禁用'} ({account_type})")
    
    def register_callback(self, event, callback):
        """注册事件回调"""
        self.callbacks[event] = callback
    
    def reset_auto_buy_state(self):
        """重置自动化购买状态（购买完成后调用）"""
        self.last_detected_page = None
        print("✓ 自动化状态已重置")
    
    def set_url_change_callback(self, callback):
        """设置 URL 变化回调"""
        self.url_change_callback = callback
    
    def reset_block_status(self):
        """重置限制状态（用户手动调用）"""
        self.buy_blocked = False
        self.block_count = 0
        self.last_block_time = None
        print("✓ 限制状态已重置")
    
    @run_on_ui_thread
    def go_back(self):
        """返回上一页"""
        if self.webview and self.webview.canGoBack():
            self.webview.goBack()
    
    @run_on_ui_thread
    def go_forward(self):
        """前进一页"""
        if self.webview and self.webview.canGoForward():
            self.webview.goForward()
    
    @run_on_ui_thread
    def reload(self):
        """刷新页面"""
        if self.webview:
            self.webview.reload()
    
    @run_on_ui_thread
    def clear_cache(self):
        """清除缓存"""
        if self.webview:
            self.webview.clearCache(True)
    
    @run_on_ui_thread
    def get_view(self):
        """获取原生 WebView 对象"""
        return self.webview


# ============================================================
# 桌面测试版本（非安卓环境）
# ============================================================

class MockWebView(Widget):
    """WebView 模拟版本（用于桌面测试）"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_url = None
        self.previous_url = None
        self.auto_buy_enabled = False
        self.account_type = 'personal'
        self.callbacks = {}
        self.url_change_callback = None
        self.last_detected_page = None
        self.buy_blocked = False
        self.block_count = 0
        print("⚠️ 使用 MockWebView（桌面测试模式）")
    
    def load_url(self, url):
        self.previous_url = self.current_url
        self.current_url = url
        print(f"[Mock] 加载 URL: {url}")
        
        # 模拟 URL 变化检测
        page_type = URLPatterns.detect_page_type(url)
        self._on_url_change(url, page_type)
        
        # 模拟页面加载完成
        Clock.schedule_once(lambda dt: self._on_page_loaded(url), 0.5)
    
    def _on_url_change(self, url, page_type):
        """模拟 URL 变化"""
        print(f"[Mock] [URL 变化] {self.previous_url} → {url}")
        print(f"[Mock] [页面类型] {page_type}")
        
        if self.url_change_callback:
            self.url_change_callback(url, page_type)
        
        if self.auto_buy_enabled and not self.buy_blocked:
            self._handle_auto_step_by_page(page_type)
    
    def _on_page_loaded(self, url):
        print(f"[Mock] 页面加载完成：{url}")
        if 'page_loaded' in self.callbacks:
            self.callbacks['page_loaded'](url)
        
        # 模拟购买限制检测
        if self.auto_buy_enabled:
            Clock.schedule_once(lambda dt: self._check_buy_limit(), 1)
    
    def _check_buy_limit(self):
        """模拟购买限制检测"""
        # 模拟检测（实际使用时不会触发）
        print("[Mock] 购买限制检测：OK")
    
    def _handle_buy_blocked(self, reason):
        """模拟处理购买被限制"""
        self.buy_blocked = True
        self.block_count += 1
        print(f"[Mock] ⚠️ 购买被限制：{reason}")
        print(f"[Mock]    被限制次数：{self.block_count}")
        
        if 'buy_blocked' in self.callbacks:
            self.callbacks['buy_blocked'](self.block_count, 600)
        
        if self.block_count >= 3:
            print(f"[Mock] ❌ 已达到最大重试次数")
            return
        
        print(f"[Mock] ⏱️ 等待 600 秒后重试...")
        
        if 'buy_blocked_waiting' in self.callbacks:
            self.callbacks['buy_blocked_waiting'](self.block_count, 600)
        
        Clock.schedule_once(lambda dt: self._retry_after_block(), 600)
    
    def _retry_after_block(self):
        """模拟限制解除后重试"""
        print(f"[Mock] ⏰ 等待结束，开始重试")
        self.buy_blocked = False
        
        if self.last_detected_page == 'item':
            print("[Mock] 🔄 重试：点击立即购买")
            self._find_and_click_buy_button()
    
    def _handle_auto_step_by_page(self, page_type):
        if not self.auto_buy_enabled:
            return
        
        if self.account_type == 'personal':
            self._personal_flow_by_page(page_type)
        else:
            self._enterprise_flow_by_page(page_type)
    
    def _personal_flow_by_page(self, page_type):
        if page_type == 'item':
            print("[Mock] [个人号] 步骤 1/3: 商品详情页")
            self._find_and_click_buy_button()
            self.last_detected_page = 'item'
        elif page_type == 'order' and self.last_detected_page == 'item':
            print("[Mock] [个人号] 步骤 2/3: 订单确认页")
            Clock.schedule_once(lambda dt: self._find_and_click_confirm_button(), 0.5)
            self.last_detected_page = 'order'
        elif page_type == 'payment' and self.last_detected_page in ['item', 'order']:
            print("[Mock] [个人号] 步骤 3/3: 付款页")
            Clock.schedule_once(lambda dt: self._find_and_click_payment_button(), 0.5)
            self.last_detected_page = 'payment'
    
    def _enterprise_flow_by_page(self, page_type):
        if page_type == 'item':
            print("[Mock] [企业号] 步骤 1/2: 商品详情页")
            self._find_and_click_buy_button()
            self.last_detected_page = 'item'
        elif page_type == 'payment' and self.last_detected_page == 'item':
            print("[Mock] [企业号] 步骤 2/2: 付款页")
            Clock.schedule_once(lambda dt: self._find_and_click_payment_button(), 0.5)
            self.last_detected_page = 'payment'
    
    def execute_js(self, script, callback=None):
        print(f"[Mock] 执行 JS: {script[:50]}...")
        if callback:
            Clock.schedule_once(lambda dt: callback('MOCK_RESULT'), 0.3)
    
    def _find_and_click_buy_button(self):
        print("[Mock] 点击立即购买")
    
    def _find_and_click_confirm_button(self):
        print("[Mock] 点击确认购买")
    
    def _find_and_click_payment_button(self):
        print("[Mock] 点击支付")
    
    def set_auto_buy(self, enabled, account_type='personal'):
        self.auto_buy_enabled = enabled
        self.account_type = account_type
        if not enabled:
            self.buy_blocked = False
            self.block_count = 0
        print(f"[Mock] 自动化购买：{'启用' if enabled else '禁用'} ({account_type})")
    
    def register_callback(self, event, callback):
        self.callbacks[event] = callback
    
    def set_url_change_callback(self, callback):
        self.url_change_callback = callback
    
    def reset_block_status(self):
        self.buy_blocked = False
        self.block_count = 0
        print("[Mock] ✓ 限制状态已重置")
    
    def go_back(self):
        print("[Mock] 返回")
    
    def go_forward(self):
        print("[Mock] 前进")
    
    def reload(self):
        print("[Mock] 刷新")
    
    def clear_cache(self):
        print("[Mock] 清除缓存")
    
    def get_view(self):
        return None


# ============================================================
# 工厂函数
# ============================================================

def create_webview(**kwargs):
    """创建 WebView 实例"""
    if ANDROID_AVAILABLE:
        return XianyuWebView(**kwargs)
    else:
        return MockWebView(**kwargs)
