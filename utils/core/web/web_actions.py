"""
Web操作类
提供常用的Web自动化操作
"""

import time
from typing import Optional, List, Dict, Any
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from utils.logging.logger import logger


class WebActions:
    """Web操作类"""
    
    def __init__(self, page: Page):
        """
        初始化Web操作类
        
        Args:
            page: Playwright页面对象
        """
        self.page = page
        self.default_timeout = 30000  # 30秒
    
    def navigate(self, url: str, timeout: Optional[int] = None) -> bool:
        """
        导航到指定URL
        
        Args:
            url: 目标URL
            timeout: 超时时间（毫秒）
            
        Returns:
            是否成功
        """
        try:
            timeout = timeout or self.default_timeout
            self.page.goto(url, timeout=timeout)
            self.page.wait_for_load_state("networkidle", timeout=timeout)
            logger.info(f"成功导航到: {url}")
            return True
        except Exception as e:
            logger.error(f"导航失败 {url}: {e}")
            return False
    
    def click(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        点击元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            是否成功
        """
        try:
            timeout = timeout or self.default_timeout
            self.page.click(selector, timeout=timeout)
            logger.info(f"成功点击元素: {selector}")
            return True
        except Exception as e:
            logger.error(f"点击元素失败 {selector}: {e}")
            return False
    
    def fill(self, selector: str, value: str, timeout: Optional[int] = None) -> bool:
        """
        填写输入框
        
        Args:
            selector: 元素选择器
            value: 填写的值
            timeout: 超时时间（毫秒）
            
        Returns:
            是否成功
        """
        try:
            timeout = timeout or self.default_timeout
            self.page.fill(selector, value, timeout=timeout)
            logger.info(f"成功填写 {selector}: {value}")
            return True
        except Exception as e:
            logger.error(f"填写失败 {selector}: {e}")
            return False
    
    def select_option(self, selector: str, value: str, timeout: Optional[int] = None) -> bool:
        """
        选择下拉框选项
        
        Args:
            selector: 选择器
            value: 选项值
            timeout: 超时时间（毫秒）
            
        Returns:
            是否成功
        """
        try:
            timeout = timeout or self.default_timeout
            self.page.select_option(selector, value, timeout=timeout)
            logger.info(f"成功选择选项 {selector}: {value}")
            return True
        except Exception as e:
            logger.error(f"选择选项失败 {selector}: {e}")
            return False
    
    def check(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        勾选复选框
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            是否成功
        """
        try:
            timeout = timeout or self.default_timeout
            self.page.check(selector, timeout=timeout)
            logger.info(f"成功勾选: {selector}")
            return True
        except Exception as e:
            logger.error(f"勾选失败 {selector}: {e}")
            return False
    
    def uncheck(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        取消勾选复选框
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            是否成功
        """
        try:
            timeout = timeout or self.default_timeout
            self.page.uncheck(selector, timeout=timeout)
            logger.info(f"成功取消勾选: {selector}")
            return True
        except Exception as e:
            logger.error(f"取消勾选失败 {selector}: {e}")
            return False
    
    def wait(self, timeout: int) -> bool:
        """
        等待指定时间
        
        Args:
            timeout: 等待时间（毫秒）
            
        Returns:
            是否成功
        """
        try:
            time.sleep(timeout / 1000)  # 转换为秒
            logger.info(f"等待 {timeout}ms")
            return True
        except Exception as e:
            logger.error(f"等待失败: {e}")
            return False
    
    def wait_for_element(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        等待元素出现
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            是否成功
        """
        try:
            timeout = timeout or self.default_timeout
            self.page.wait_for_selector(selector, timeout=timeout)
            logger.info(f"元素已出现: {selector}")
            return True
        except Exception as e:
            logger.error(f"等待元素失败 {selector}: {e}")
            return False
    
    def is_element_visible(self, selector: str) -> bool:
        """
        检查元素是否可见
        
        Args:
            selector: 元素选择器
            
        Returns:
            是否可见
        """
        try:
            element = self.page.locator(selector)
            visible = element.is_visible()
            logger.info(f"元素可见性 {selector}: {visible}")
            return visible
        except Exception as e:
            logger.error(f"检查元素可见性失败 {selector}: {e}")
            return False
    
    def is_element_enabled(self, selector: str) -> bool:
        """
        检查元素是否启用
        
        Args:
            selector: 元素选择器
            
        Returns:
            是否启用
        """
        try:
            element = self.page.locator(selector)
            enabled = element.is_enabled()
            logger.info(f"元素启用状态 {selector}: {enabled}")
            return enabled
        except Exception as e:
            logger.error(f"检查元素启用状态失败 {selector}: {e}")
            return False
    
    def get_text(self, selector: str, timeout: Optional[int] = None) -> Optional[str]:
        """
        获取元素文本
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            元素文本或None
        """
        try:
            timeout = timeout or self.default_timeout
            text = self.page.locator(selector).text_content(timeout=timeout)
            logger.info(f"获取文本 {selector}: {text}")
            return text
        except Exception as e:
            logger.error(f"获取文本失败 {selector}: {e}")
            return None
    
    def get_attribute(self, selector: str, attribute: str, timeout: Optional[int] = None) -> Optional[str]:
        """
        获取元素属性
        
        Args:
            selector: 元素选择器
            attribute: 属性名
            timeout: 超时时间（毫秒）
            
        Returns:
            属性值或None
        """
        try:
            timeout = timeout or self.default_timeout
            value = self.page.locator(selector).get_attribute(attribute, timeout=timeout)
            logger.info(f"获取属性 {selector}.{attribute}: {value}")
            return value
        except Exception as e:
            logger.error(f"获取属性失败 {selector}.{attribute}: {e}")
            return None
    
    def screenshot(self, path: Optional[str] = None) -> Optional[bytes]:
        """
        截取页面截图
        
        Args:
            path: 保存路径（可选）
            
        Returns:
            截图数据或None
        """
        try:
            screenshot_data = self.page.screenshot(path=path)
            if path:
                logger.info(f"截图已保存: {path}")
            else:
                logger.info("截图已生成")
            return screenshot_data
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
    
    def scroll_to(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        滚动到指定元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            是否成功
        """
        try:
            timeout = timeout or self.default_timeout
            self.page.locator(selector).scroll_into_view_if_needed(timeout=timeout)
            logger.info(f"滚动到元素: {selector}")
            return True
        except Exception as e:
            logger.error(f"滚动失败 {selector}: {e}")
            return False
    
    def hover(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        悬停在元素上
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            是否成功
        """
        try:
            timeout = timeout or self.default_timeout
            self.page.hover(selector, timeout=timeout)
            logger.info(f"悬停在元素: {selector}")
            return True
        except Exception as e:
            logger.error(f"悬停失败 {selector}: {e}")
            return False
    
    def double_click(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        双击元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            是否成功
        """
        try:
            timeout = timeout or self.default_timeout
            self.page.dblclick(selector, timeout=timeout)
            logger.info(f"双击元素: {selector}")
            return True
        except Exception as e:
            logger.error(f"双击失败 {selector}: {e}")
            return False
    
    def press_key(self, key: str) -> bool:
        """
        按键
        
        Args:
            key: 按键名称
            
        Returns:
            是否成功
        """
        try:
            self.page.keyboard.press(key)
            logger.info(f"按键: {key}")
            return True
        except Exception as e:
            logger.error(f"按键失败 {key}: {e}")
            return False
    
    def type_text(self, text: str, delay: int = 100) -> bool:
        """
        输入文本
        
        Args:
            text: 要输入的文本
            delay: 每个字符间的延迟（毫秒）
            
        Returns:
            是否成功
        """
        try:
            self.page.keyboard.type(text, delay=delay)
            logger.info(f"输入文本: {text}")
            return True
        except Exception as e:
            logger.error(f"输入文本失败: {e}")
            return False
