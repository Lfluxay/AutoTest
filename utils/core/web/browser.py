from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from typing import Dict, Any, Optional
from pathlib import Path
import time
from utils.logging.logger import logger, logger_manager
from utils.config.parser import get_merged_config


class BrowserManager:
    """浏览器管理器 - 管理Playwright浏览器实例"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化浏览器管理器
        
        Args:
            config: Web配置
        """
        if config is None:
            full_config = get_merged_config()
            config = full_config.get('web', {})
        
        self.config = config
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # 配置参数
        browser_config = config.get('browser', {})
        self.browser_type = browser_config.get('type', 'chromium')
        self.headless = browser_config.get('headless', False)
        self.viewport = browser_config.get('viewport', {'width': 1920, 'height': 1080})

        timeouts_config = config.get('timeouts', {})
        self.timeout = timeouts_config.get('element', 30000)

        failure_config = config.get('on_failure', {})
        self.screenshot_on_failure = failure_config.get('screenshot', True)

        # 全局登录相关
        self.is_logged_in = False
        self.home_url = None
        self.login_credentials = None

        logger.info(f"浏览器管理器初始化: {self.browser_type}, headless={self.headless}")
    
    def start_browser(self, browser_type: str = None, headless: bool = None):
        """
        启动浏览器

        Args:
            browser_type: 浏览器类型，覆盖配置中的设置
            headless: 是否无头模式，覆盖配置中的设置
        """
        try:
            # 更新配置
            if browser_type:
                self.browser_type = browser_type
            if headless is not None:
                self.headless = headless

            self.playwright = sync_playwright().start()

            # 选择浏览器类型
            if self.browser_type == 'chromium':
                browser_launcher = self.playwright.chromium
            elif self.browser_type == 'firefox':
                browser_launcher = self.playwright.firefox
            elif self.browser_type == 'webkit':
                browser_launcher = self.playwright.webkit
            else:
                raise ValueError(f"不支持的浏览器类型: {self.browser_type}")
            
            # 启动浏览器
            self.browser = browser_launcher.launch(
                headless=self.headless,
                slow_mo=100 if not self.headless else 0  # 非headless模式下添加延迟便于观察
            )

            # 创建浏览器上下文
            self.context = self.browser.new_context(
                viewport=self.viewport,
                ignore_https_errors=True,
                accept_downloads=True,
                record_video_dir=str(Path('reports') / 'videos')
            )

            # 设置默认超时
            self.context.set_default_timeout(self.timeout)
            self.context.set_default_navigation_timeout(self.timeout)

            # 启用 trace（按需在失败时停止并保存）
            try:
                self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
            except Exception:
                pass

            # 创建页面
            self.page = self.context.new_page()

            logger.info(f"浏览器启动成功: {self.browser_type}")
            
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            self.cleanup()
            raise
    
    def stop_browser(self):
        """停止浏览器"""
        try:
            if self.page:
                self.page.close()
                self.page = None
            
            if self.context:
                self.context.close()
                self.context = None
            
            if self.browser:
                self.browser.close()
                self.browser = None
            
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            
            logger.info("浏览器已关闭")

        except Exception as e:
            logger.error(f"关闭浏览器时出错: {e}")
        finally:
            # 保存 trace
            try:
                trace_path = Path('reports') / 'traces' / f"trace_{int(time.time())}.zip"
                trace_path.parent.mkdir(parents=True, exist_ok=True)
                if self.context:
                    self.context.tracing.stop(path=str(trace_path))
                    logger.info(f"Trace 已保存: {trace_path}")
            except Exception:
                pass
    
    def cleanup(self):
        """清理资源"""
        self.stop_browser()
    
    def get_page(self) -> Page:
        """获取当前页面对象"""
        if not self.page:
            raise RuntimeError("浏览器未启动或页面不存在")
        return self.page
    
    def new_page(self) -> Page:
        """创建新页面"""
        if not self.context:
            raise RuntimeError("浏览器上下文不存在")
        
        new_page = self.context.new_page()
        new_page.set_default_timeout(self.timeout)
        return new_page
    
    def switch_to_page(self, page: Page):
        """切换到指定页面"""
        self.page = page
        logger.debug(f"切换到页面: {page.url}")
    
    def take_screenshot(self, path: str = None, full_page: bool = True) -> str:
        """
        截图
        
        Args:
            path: 截图保存路径
            full_page: 是否截取整个页面
            
        Returns:
            截图文件路径
        """
        if not self.page:
            raise RuntimeError("页面不存在")
        
        if path is None:
            # 自动生成截图路径
            from utils.config_parser import config
            screenshots_dir = config.get_screenshots_dir()
            screenshots_dir.mkdir(exist_ok=True)
            
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            path = screenshots_dir / f"screenshot_{timestamp}.png"
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        self.page.screenshot(path=str(path), full_page=full_page)
        logger_manager.log_screenshot(str(path))
        
        return str(path)
    
    def login(self, login_url: str = None, username: str = None, password: str = None) -> bool:
        """
        执行全局登录
        
        Args:
            login_url: 登录页面URL（可选，如果不提供则使用配置中的URL）
            username: 用户名（可选，如果不提供则使用配置中的用户名）
            password: 密码（可选，如果不提供则使用配置中的密码）
        
        Returns:
            登录是否成功
        """
        login_config = self.config.get('login', {})
        
        if not login_config.get('enabled', False) and not login_url:
            logger.info("全局登录未启用")
            return True
        
        try:
            # 使用参数或配置中的值
            url = login_url or login_config.get('url')
            user = username or login_config.get('username')
            pwd = password or login_config.get('password')
            
            if not all([url, user, pwd]):
                logger.error("登录参数不完整")
                return False
            
            logger.info(f"开始执行全局登录: {user}")
            
            # 导航到登录页面
            self.page.goto(url)
            self.page.wait_for_load_state('networkidle')
            
            # 使用页面对象进行登录
            try:
                from pages.login_page import LoginPage
                login_page = LoginPage(self.page)
                login_page.login(user, pwd)
            except ImportError:
                # 如果没有页面对象，使用配置中的定位器
                username_locator = login_config.get('username_locator', '#username')
                password_locator = login_config.get('password_locator', '#password')
                login_button_locator = login_config.get('login_button_locator', '#login-btn')
                
                self.page.fill(username_locator, user)
                self.page.fill(password_locator, pwd)
                self.page.click(login_button_locator)
            
            # 等待登录成功
            success_url_pattern = login_config.get('success_url_pattern', '**/dashboard**')
            try:
                self.page.wait_for_url(success_url_pattern, timeout=10000)
                self.is_logged_in = True
                self.login_credentials = {'username': user, 'password': pwd}
                logger.info("全局登录成功")
                return True
            except Exception:
                # 如果没有跳转，检查登录成功标识
                try:
                    self.page.wait_for_selector(".user-info", timeout=5000)
                    self.is_logged_in = True
                    self.login_credentials = {'username': user, 'password': pwd}
                    logger.info("全局登录成功")
                    return True
                except Exception:
                    logger.error("登录失败：未检测到登录成功标识")
                    return False
                
        except Exception as e:
            logger.error(f"全局登录异常: {e}")
            if self.screenshot_on_failure:
                self.take_screenshot()
            return False
    
    # 为了保持向后兼容，添加一个别名方法
    def global_login(self, login_url: str, username: str, password: str) -> bool:
        """
        执行全局登录（向后兼容方法）
        """
        return self.login(login_url, username, password)
    
    def goto_home(self):
        """返回首页"""
        login_config = self.config.get('login', {})
        home_url = login_config.get('home_url')
        
        if home_url and self.page:
            logger.info(f"返回首页: {home_url}")
            self.page.goto(home_url)
            self.page.wait_for_load_state('networkidle')
        else:
            logger.warning("未配置首页URL或页面不存在")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type and self.screenshot_on_failure:
            # 如果发生异常且启用了失败截图，则截图
            try:
                self.take_screenshot()
            except:
                pass
        self.cleanup()


    def set_home_url(self, url: str):
        """设置首页URL"""
        self.home_url = url
        logger.info(f"设置首页URL: {url}")


    def _check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            # 检查是否有用户信息元素
            return self.page.locator(".user-info").is_visible(timeout=2000)
        except Exception:
            return False

    def ensure_logged_in(self):
        """确保处于登录状态"""
        if not self.is_logged_in:
            logger.warning("未处于登录状态")
            return False

        if not self._check_login_status():
            logger.warning("登录状态丢失，尝试重新登录")
            if self.login_credentials:
                return self.global_login(
                    self.home_url.replace('/dashboard', '/login') if self.home_url else 'https://example.com/login',
                    self.login_credentials['username'],
                    self.login_credentials['password']
                )
            return False

        return True


# 全局浏览器管理器实例
browser_manager = None

def get_browser_manager() -> BrowserManager:
    """获取浏览器管理器实例"""
    global browser_manager
    if browser_manager is None:
        browser_manager = BrowserManager()
    return browser_manager

def get_current_page() -> Page:
    """获取当前页面便捷函数"""
    return get_browser_manager().get_page()

def take_screenshot(path: str = None) -> str:
    """截图便捷函数"""
    return get_browser_manager().take_screenshot(path)