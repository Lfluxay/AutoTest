from playwright.sync_api import Page
from typing import Optional, Any, Dict
from utils.logging.logger import logger, logger_manager


class PageBase:
    """页面基类 - Page Object Model基类"""
    
    def __init__(self, page: Page):
        """
        初始化页面基类
        
        Args:
            page: Playwright页面对象
        """
        self.page = page
        self.url = ""
        self.title = ""
        self.timeout = 30000
        
    def goto(self, url: str = None):
        """
        打开页面
        
        Args:
            url: 页面URL，如果不指定则使用self.url
        """
        target_url = url or self.url
        if not target_url:
            raise ValueError("页面URL未设置")
        
        logger_manager.log_web_action("打开页面", target_url)
        self.page.goto(target_url)
        self.wait_for_load()
    
    def wait_for_load(self, state: str = "networkidle"):
        """
        等待页面加载完成
        
        Args:
            state: 加载状态 (load, domcontentloaded, networkidle)
        """
        self.page.wait_for_load_state(state)
        logger.debug(f"页面加载完成: {state}")
    
    def get_title(self) -> str:
        """获取页面标题"""
        title = self.page.title()
        logger.debug(f"页面标题: {title}")
        return title
    
    def get_url(self) -> str:
        """获取当前URL"""
        url = self.page.url
        logger.debug(f"当前URL: {url}")
        return url
    
    def wait_for_element(self, locator: str, timeout: Optional[int] = None) -> bool:
        """
        等待元素出现
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
            
        Returns:
            元素是否出现
        """
        try:
            timeout = timeout or self.timeout
            self.page.wait_for_selector(locator, timeout=timeout)
            return True
        except Exception as e:
            logger.warning(f"等待元素超时: {locator}, {e}")
            return False
    
    def is_element_visible(self, locator: str) -> bool:
        """
        检查元素是否可见
        
        Args:
            locator: 元素定位器
            
        Returns:
            元素是否可见
        """
        try:
            element = self.page.locator(locator)
            visible = element.is_visible()
            logger.debug(f"元素可见性: {locator} -> {visible}")
            return visible
        except Exception as e:
            logger.debug(f"检查元素可见性失败: {locator}, {e}")
            return False
    
    def is_element_enabled(self, locator: str) -> bool:
        """
        检查元素是否启用
        
        Args:
            locator: 元素定位器
            
        Returns:
            元素是否启用
        """
        try:
            element = self.page.locator(locator)
            enabled = element.is_enabled()
            logger.debug(f"元素启用状态: {locator} -> {enabled}")
            return enabled
        except Exception as e:
            logger.debug(f"检查元素启用状态失败: {locator}, {e}")
            return False
    
    def get_element_count(self, locator: str) -> int:
        """
        获取元素数量
        
        Args:
            locator: 元素定位器
            
        Returns:
            元素数量
        """
        try:
            elements = self.page.locator(locator)
            count = elements.count()
            logger.debug(f"元素数量: {locator} -> {count}")
            return count
        except Exception as e:
            logger.debug(f"获取元素数量失败: {locator}, {e}")
            return 0
    
    def click(self, locator: str, timeout: Optional[int] = None):
        """
        点击元素
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
        """
        logger_manager.log_web_action("点击", locator)
        
        if timeout:
            self.page.locator(locator).click(timeout=timeout)
        else:
            self.page.locator(locator).click()
    
    def double_click(self, locator: str, timeout: Optional[int] = None):
        """
        双击元素
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
        """
        logger_manager.log_web_action("双击", locator)
        
        if timeout:
            self.page.locator(locator).dblclick(timeout=timeout)
        else:
            self.page.locator(locator).dblclick()
    
    def right_click(self, locator: str, timeout: Optional[int] = None):
        """
        右键点击元素
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
        """
        logger_manager.log_web_action("右键点击", locator)
        
        if timeout:
            self.page.locator(locator).click(button="right", timeout=timeout)
        else:
            self.page.locator(locator).click(button="right")
    
    def hover(self, locator: str, timeout: Optional[int] = None):
        """
        鼠标悬停
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
        """
        logger_manager.log_web_action("鼠标悬停", locator)
        
        if timeout:
            self.page.locator(locator).hover(timeout=timeout)
        else:
            self.page.locator(locator).hover()
    
    def fill(self, locator: str, value: str, timeout: Optional[int] = None):
        """
        填充输入框
        
        Args:
            locator: 元素定位器
            value: 输入值
            timeout: 超时时间
        """
        logger_manager.log_web_action("填充输入框", locator, value)
        
        if timeout:
            self.page.locator(locator).fill(value, timeout=timeout)
        else:
            self.page.locator(locator).fill(value)
    
    def clear(self, locator: str, timeout: Optional[int] = None):
        """
        清空输入框
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
        """
        logger_manager.log_web_action("清空输入框", locator)
        
        if timeout:
            self.page.locator(locator).clear(timeout=timeout)
        else:
            self.page.locator(locator).clear()
    
    def type(self, locator: str, text: str, delay: int = 100, timeout: Optional[int] = None):
        """
        逐字符输入
        
        Args:
            locator: 元素定位器
            text: 输入文本
            delay: 字符间延迟(毫秒)
            timeout: 超时时间
        """
        logger_manager.log_web_action("逐字符输入", locator, text)
        
        if timeout:
            self.page.locator(locator).type(text, delay=delay, timeout=timeout)
        else:
            self.page.locator(locator).type(text, delay=delay)
    
    def press_key(self, locator: str, key: str, timeout: Optional[int] = None):
        """
        按键
        
        Args:
            locator: 元素定位器
            key: 按键名称
            timeout: 超时时间
        """
        logger_manager.log_web_action("按键", locator, key)
        
        if timeout:
            self.page.locator(locator).press(key, timeout=timeout)
        else:
            self.page.locator(locator).press(key)
    
    def select_option(self, locator: str, value: str = None, label: str = None, index: int = None, timeout: Optional[int] = None):
        """
        选择下拉选项
        
        Args:
            locator: 元素定位器
            value: 选项值
            label: 选项文本
            index: 选项索引
            timeout: 超时时间
        """
        select_by = value or label or index
        logger_manager.log_web_action("选择下拉选项", locator, str(select_by))
        
        kwargs = {}
        if timeout:
            kwargs['timeout'] = timeout
        
        if value is not None:
            self.page.locator(locator).select_option(value=value, **kwargs)
        elif label is not None:
            self.page.locator(locator).select_option(label=label, **kwargs)
        elif index is not None:
            self.page.locator(locator).select_option(index=index, **kwargs)
        else:
            raise ValueError("必须指定value, label或index中的一个")
    
    def check(self, locator: str, timeout: Optional[int] = None):
        """
        勾选复选框或单选框
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
        """
        logger_manager.log_web_action("勾选", locator)
        
        if timeout:
            self.page.locator(locator).check(timeout=timeout)
        else:
            self.page.locator(locator).check()
    
    def uncheck(self, locator: str, timeout: Optional[int] = None):
        """
        取消勾选复选框
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
        """
        logger_manager.log_web_action("取消勾选", locator)
        
        if timeout:
            self.page.locator(locator).uncheck(timeout=timeout)
        else:
            self.page.locator(locator).uncheck()
    
    def get_text(self, locator: str, timeout: Optional[int] = None) -> str:
        """
        获取元素文本
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
            
        Returns:
            元素文本内容
        """
        if timeout:
            text = self.page.locator(locator).text_content(timeout=timeout)
        else:
            text = self.page.locator(locator).text_content()
        
        logger.debug(f"获取元素文本: {locator} -> {text}")
        return text or ""
    
    def get_inner_text(self, locator: str, timeout: Optional[int] = None) -> str:
        """
        获取元素内部文本
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
            
        Returns:
            元素内部文本
        """
        if timeout:
            text = self.page.locator(locator).inner_text(timeout=timeout)
        else:
            text = self.page.locator(locator).inner_text()
        
        logger.debug(f"获取元素内部文本: {locator} -> {text}")
        return text
    
    def get_inner_html(self, locator: str, timeout: Optional[int] = None) -> str:
        """
        获取元素内部HTML
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
            
        Returns:
            元素内部HTML
        """
        if timeout:
            html = self.page.locator(locator).inner_html(timeout=timeout)
        else:
            html = self.page.locator(locator).inner_html()
        
        logger.debug(f"获取元素内部HTML: {locator} -> {html[:100]}...")
        return html
    
    def get_attribute(self, locator: str, attribute: str, timeout: Optional[int] = None) -> Optional[str]:
        """
        获取元素属性
        
        Args:
            locator: 元素定位器
            attribute: 属性名称
            timeout: 超时时间
            
        Returns:
            属性值
        """
        if timeout:
            value = self.page.locator(locator).get_attribute(attribute, timeout=timeout)
        else:
            value = self.page.locator(locator).get_attribute(attribute)
        
        logger.debug(f"获取元素属性: {locator}[{attribute}] -> {value}")
        return value
    
    def get_input_value(self, locator: str, timeout: Optional[int] = None) -> str:
        """
        获取输入框值
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
            
        Returns:
            输入框值
        """
        if timeout:
            value = self.page.locator(locator).input_value(timeout=timeout)
        else:
            value = self.page.locator(locator).input_value()
        
        logger.debug(f"获取输入框值: {locator} -> {value}")
        return value
    
    def wait_for_url(self, url_pattern: str, timeout: Optional[int] = None):
        """
        等待URL匹配
        
        Args:
            url_pattern: URL模式
            timeout: 超时时间
        """
        logger_manager.log_web_action("等待URL", url_pattern)
        
        if timeout:
            self.page.wait_for_url(url_pattern, timeout=timeout)
        else:
            self.page.wait_for_url(url_pattern)
    
    def scroll_to_element(self, locator: str):
        """
        滚动到元素
        
        Args:
            locator: 元素定位器
        """
        logger_manager.log_web_action("滚动到元素", locator)
        self.page.locator(locator).scroll_into_view_if_needed()
    
    def drag_and_drop(self, source_locator: str, target_locator: str):
        """
        拖拽元素
        
        Args:
            source_locator: 源元素定位器
            target_locator: 目标元素定位器
        """
        logger_manager.log_web_action("拖拽", f"{source_locator} -> {target_locator}")
        self.page.locator(source_locator).drag_to(self.page.locator(target_locator))
    
    def upload_file(self, locator: str, file_path: str):
        """
        上传文件
        
        Args:
            locator: 文件输入框定位器
            file_path: 文件路径
        """
        logger_manager.log_web_action("上传文件", locator, file_path)
        self.page.locator(locator).set_input_files(file_path)
    
    def execute_script(self, script: str, *args) -> Any:
        """
        执行JavaScript
        
        Args:
            script: JavaScript代码
            *args: 参数
            
        Returns:
            执行结果
        """
        logger_manager.log_web_action("执行脚本", script[:100])
        return self.page.evaluate(script, *args)
    
    def take_screenshot(self, path: str = None, full_page: bool = True) -> str:
        """
        页面截图
        
        Args:
            path: 截图保存路径
            full_page: 是否截取整个页面
            
        Returns:
            截图文件路径
        """
        from core.web.browser import get_browser_manager
        return get_browser_manager().take_screenshot(path, full_page)
    
    def refresh(self):
        """刷新页面"""
        logger_manager.log_web_action("刷新页面", self.page.url)
        self.page.reload()
    
    def go_back(self):
        """后退"""
        logger_manager.log_web_action("后退", "")
        self.page.go_back()
    
    def go_forward(self):
        """前进"""
        logger_manager.log_web_action("前进", "")
        self.page.go_forward()
    
    def close(self):
        """关闭页面"""
        logger_manager.log_web_action("关闭页面", "")
        self.page.close()