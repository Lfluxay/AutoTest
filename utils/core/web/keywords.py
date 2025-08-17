from typing import Dict, Any, List, Optional, Union
from playwright.sync_api import Page
from utils.logging.logger import logger, logger_manager
from utils.data.extractor import Extractor, variable_manager
from utils.core.base.keywords_base import KeywordsBase


class WebKeywords(KeywordsBase):
    """Web关键字类 - 提供Web测试的关键字操作"""
    
    def __init__(self):
        super().__init__()
        self._browser_manager = None
        self.page = None
        self.current_page_object = None

    @property
    def browser_manager(self):
        """延迟加载浏览器管理器"""
        if self._browser_manager is None:
            from core.web.browser import get_browser_manager
            self._browser_manager = get_browser_manager()
        return self._browser_manager
        
    def execute(self, action: str, params: Dict[str, Any] = None) -> Any:
        """
        执行Web关键字操作
        
        Args:
            action: 操作名称
            params: 操作参数
            
        Returns:
            操作结果
        """
        if params is None:
            params = {}
            
        # 确保有页面对象
        if not self.page:
            self.page = self.browser_manager.get_page()
        
        logger.info(f"执行Web关键字: {action}")
        logger_manager.log_step(f"Web关键字: {action}", str(params))
        
        try:
            if action == "navigate":
                return self.navigate(params.get("url"), params.get("wait_for_load", True))
            elif action == "click":
                return self.click(params.get("locator"), params.get("timeout"), params.get("force", False))
            elif action == "input":
                return self.input_text(params.get("locator"), params.get("value"), 
                                     params.get("clear", True), params.get("timeout"))
            elif action == "select":
                return self.select_option(params.get("locator"), params.get("value"), params.get("timeout"))
            elif action == "upload":
                return self.upload_file(params.get("locator"), params.get("file_path"), params.get("timeout"))
            elif action == "wait_for_element":
                return self.wait_for_element(params.get("locator"), params.get("state", "visible"), params.get("timeout"))
            elif action == "wait_for_url":
                return self.wait_for_url(params.get("url"), params.get("timeout"))
            elif action == "wait_for_text":
                return self.wait_for_text(params.get("locator"), params.get("text"), params.get("timeout"))
            elif action == "get_text":
                return self.get_text(params.get("locator"), params.get("timeout"))
            elif action == "get_attribute":
                return self.get_attribute(params.get("locator"), params.get("attribute"), params.get("timeout"))
            elif action == "screenshot":
                return self.take_screenshot(params.get("name"))
            elif action == "scroll_to":
                return self.scroll_to_element(params.get("locator"), params.get("timeout"))
            elif action == "execute_js":
                return self.execute_javascript(params.get("script"), params.get("args", []))
            elif action == "refresh":
                return self.refresh_page()
            elif action == "go_back":
                return self.go_back()
            elif action == "go_forward":
                return self.go_forward()
            elif action == "switch_tab":
                return self.switch_tab(params.get("index", -1))
            elif action == "close_tab":
                return self.close_tab(params.get("index"))
            elif action == "handle_alert":
                return self.handle_alert(params.get("action", "accept"), params.get("text"))
            else:
                raise ValueError(f"不支持的Web关键字: {action}")
                
        except Exception as e:
            logger.error(f"Web关键字执行失败: {action}, 错误: {e}")
            raise
    
    def navigate(self, url: str, wait_for_load: bool = True) -> bool:
        """导航到页面"""
        self.validate_params({"url": url}, ["url"])
        
        logger_manager.log_web_action("导航页面", url)
        self.page.goto(url)
        
        if wait_for_load:
            self.page.wait_for_load_state('networkidle')
        
        logger.info(f"页面导航成功: {url}")
        return True
    
    def click(self, locator: str, timeout: int = None, force: bool = False) -> bool:
        """点击元素"""
        self.validate_params({"locator": locator}, ["locator"])
        
        # 替换变量
        locator = variable_manager.replace_variables(locator)
        
        logger_manager.log_web_action("点击元素", locator)
        
        element = self.page.locator(locator)
        if timeout:
            element.click(timeout=timeout, force=force)
        else:
            element.click(force=force)
        
        logger.info(f"点击元素成功: {locator}")
        return True
    
    def input_text(self, locator: str, value: str, clear: bool = True, timeout: int = None) -> bool:
        """输入文本"""
        self.validate_params({"locator": locator, "value": value}, ["locator", "value"])
        
        # 替换变量
        locator = variable_manager.replace_variables(locator)
        value = variable_manager.replace_variables(value)
        
        logger_manager.log_web_action("输入文本", f"{locator} = {value}")
        
        element = self.page.locator(locator)
        
        if clear:
            if timeout:
                element.clear(timeout=timeout)
            else:
                element.clear()
        
        if timeout:
            element.fill(value, timeout=timeout)
        else:
            element.fill(value)
        
        logger.info(f"输入文本成功: {locator}")
        return True
    
    def select_option(self, locator: str, value: Union[str, List[str]], timeout: int = None) -> bool:
        """选择下拉框选项"""
        self.validate_params({"locator": locator, "value": value}, ["locator", "value"])
        
        # 替换变量
        locator = variable_manager.replace_variables(locator)
        if isinstance(value, str):
            value = variable_manager.replace_variables(value)
        
        logger_manager.log_web_action("选择选项", f"{locator} = {value}")
        
        element = self.page.locator(locator)
        if timeout:
            element.select_option(value, timeout=timeout)
        else:
            element.select_option(value)
        
        logger.info(f"选择选项成功: {locator}")
        return True
    
    def upload_file(self, locator: str, file_path: str, timeout: int = None) -> bool:
        """上传文件"""
        self.validate_params({"locator": locator, "file_path": file_path}, ["locator", "file_path"])
        
        # 替换变量
        locator = variable_manager.replace_variables(locator)
        file_path = variable_manager.replace_variables(file_path)
        
        logger_manager.log_web_action("上传文件", f"{locator} = {file_path}")
        
        element = self.page.locator(locator)
        if timeout:
            element.set_input_files(file_path, timeout=timeout)
        else:
            element.set_input_files(file_path)
        
        logger.info(f"上传文件成功: {locator}")
        return True
    
    def wait_for_element(self, locator: str, state: str = "visible", timeout: int = None) -> bool:
        """等待元素状态"""
        self.validate_params({"locator": locator}, ["locator"])
        
        # 替换变量
        locator = variable_manager.replace_variables(locator)
        
        logger_manager.log_web_action("等待元素", f"{locator} ({state})")
        
        element = self.page.locator(locator)
        if timeout:
            element.wait_for(state=state, timeout=timeout)
        else:
            element.wait_for(state=state)
        
        logger.info(f"等待元素成功: {locator}")
        return True
    
    def wait_for_url(self, url: str, timeout: int = None) -> bool:
        """等待URL匹配"""
        self.validate_params({"url": url}, ["url"])
        
        # 替换变量
        url = variable_manager.replace_variables(url)
        
        logger_manager.log_web_action("等待URL", url)
        
        if timeout:
            self.page.wait_for_url(url, timeout=timeout)
        else:
            self.page.wait_for_url(url)
        
        logger.info(f"URL匹配成功: {url}")
        return True
    
    def wait_for_text(self, locator: str, text: str, timeout: int = None) -> bool:
        """等待元素包含指定文本"""
        self.validate_params({"locator": locator, "text": text}, ["locator", "text"])
        
        # 替换变量
        locator = variable_manager.replace_variables(locator)
        text = variable_manager.replace_variables(text)
        
        logger_manager.log_web_action("等待文本", f"{locator} 包含 {text}")
        
        element = self.page.locator(locator)
        if timeout:
            element.wait_for(state="visible", timeout=timeout)
        else:
            element.wait_for(state="visible")
        
        # 检查文本内容
        actual_text = element.text_content()
        if text not in actual_text:
            raise AssertionError(f"元素文本不匹配: 期望包含 '{text}', 实际 '{actual_text}'")
        
        logger.info(f"等待文本成功: {locator}")
        return True
    
    def get_text(self, locator: str, timeout: int = None) -> str:
        """获取元素文本"""
        self.validate_params({"locator": locator}, ["locator"])
        
        # 替换变量
        locator = variable_manager.replace_variables(locator)
        
        logger_manager.log_web_action("获取文本", locator)
        
        element = self.page.locator(locator)
        if timeout:
            element.wait_for(state="visible", timeout=timeout)
        else:
            element.wait_for(state="visible")
        
        text = element.text_content() or ""
        logger.info(f"获取文本成功: {locator} = {text}")
        return text
    
    def get_attribute(self, locator: str, attribute: str, timeout: int = None) -> Optional[str]:
        """获取元素属性"""
        self.validate_params({"locator": locator, "attribute": attribute}, ["locator", "attribute"])
        
        # 替换变量
        locator = variable_manager.replace_variables(locator)
        
        logger_manager.log_web_action("获取属性", f"{locator}.{attribute}")
        
        element = self.page.locator(locator)
        if timeout:
            element.wait_for(state="attached", timeout=timeout)
        else:
            element.wait_for(state="attached")
        
        value = element.get_attribute(attribute)
        logger.info(f"获取属性成功: {locator}.{attribute} = {value}")
        return value
    
    def take_screenshot(self, name: str = None) -> str:
        """截图"""
        from utils.config_parser import config
        import datetime
        
        if name is None:
            name = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        screenshot_dir = config.get_screenshots_dir()
        screenshot_path = screenshot_dir / name
        
        logger_manager.log_web_action("截图", str(screenshot_path))
        
        self.page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"截图成功: {screenshot_path}")
        return str(screenshot_path)
    
    def scroll_to_element(self, locator: str, timeout: int = None) -> bool:
        """滚动到元素"""
        self.validate_params({"locator": locator}, ["locator"])
        
        # 替换变量
        locator = variable_manager.replace_variables(locator)
        
        logger_manager.log_web_action("滚动到元素", locator)
        
        element = self.page.locator(locator)
        if timeout:
            element.wait_for(state="attached", timeout=timeout)
        else:
            element.wait_for(state="attached")
        
        element.scroll_into_view_if_needed()
        logger.info(f"滚动到元素成功: {locator}")
        return True
    
    def execute_javascript(self, script: str, args: List[Any] = None) -> Any:
        """执行JavaScript"""
        self.validate_params({"script": script}, ["script"])
        
        if args is None:
            args = []
        
        logger_manager.log_web_action("执行JavaScript", script[:100] + "...")
        
        result = self.page.evaluate(script, *args)
        logger.info("JavaScript执行成功")
        return result
    
    def refresh_page(self) -> bool:
        """刷新页面"""
        logger_manager.log_web_action("刷新页面", "")
        self.page.reload()
        self.page.wait_for_load_state('networkidle')
        logger.info("页面刷新成功")
        return True
    
    def go_back(self) -> bool:
        """返回上一页"""
        logger_manager.log_web_action("返回上一页", "")
        self.page.go_back()
        self.page.wait_for_load_state('networkidle')
        logger.info("返回上一页成功")
        return True
    
    def go_forward(self) -> bool:
        """前进到下一页"""
        logger_manager.log_web_action("前进下一页", "")
        self.page.go_forward()
        self.page.wait_for_load_state('networkidle')
        logger.info("前进下一页成功")
        return True

    def switch_tab(self, index: int = -1) -> bool:
        """切换标签页"""
        logger_manager.log_web_action("切换标签页", f"索引: {index}")

        context = self.browser_manager.context
        pages = context.pages

        if index == -1:
            # 切换到最新的标签页
            target_page = pages[-1]
        else:
            if index >= len(pages):
                raise IndexError(f"标签页索引超出范围: {index}, 总数: {len(pages)}")
            target_page = pages[index]

        target_page.bring_to_front()
        self.page = target_page
        logger.info(f"切换标签页成功: {index}")
        return True

    def close_tab(self, index: int = None) -> bool:
        """关闭标签页"""
        logger_manager.log_web_action("关闭标签页", f"索引: {index}")

        context = self.browser_manager.context
        pages = context.pages

        if index is None:
            # 关闭当前标签页
            target_page = self.page
        else:
            if index >= len(pages):
                raise IndexError(f"标签页索引超出范围: {index}, 总数: {len(pages)}")
            target_page = pages[index]

        target_page.close()

        # 如果关闭的是当前页面，切换到第一个可用页面
        if target_page == self.page and len(pages) > 1:
            remaining_pages = [p for p in pages if p != target_page]
            if remaining_pages:
                self.page = remaining_pages[0]
                self.page.bring_to_front()

        logger.info(f"关闭标签页成功: {index}")
        return True

    def handle_alert(self, action: str = "accept", text: str = None) -> str:
        """处理弹窗"""
        logger_manager.log_web_action("处理弹窗", f"动作: {action}")

        alert_text = ""

        def handle_dialog(dialog):
            nonlocal alert_text
            alert_text = dialog.message
            logger.info(f"弹窗内容: {alert_text}")

            if action == "accept":
                if text:
                    dialog.accept(text)
                else:
                    dialog.accept()
            elif action == "dismiss":
                dialog.dismiss()
            else:
                raise ValueError(f"不支持的弹窗操作: {action}")

        self.page.on("dialog", handle_dialog)
        logger.info(f"弹窗处理成功: {action}")
        return alert_text

    def verify_response(self, assertions: List[Dict[str, Any]]):
        """验证Web响应"""
        logger_manager.log_step("验证Web响应", f"{len(assertions)}个断言")

        try:
            from core.web.assertions import assert_multiple_web
            assert_multiple_web(assertions, self.page)
            logger.info("Web响应验证成功")
        except Exception as e:
            logger.error(f"Web响应验证失败: {e}")
            raise

    def extract_data(self, extract_config: List[Dict[str, str]]) -> Dict[str, Any]:
        """提取Web数据"""
        logger_manager.log_step("提取Web数据", f"{len(extract_config)}个提取项")

        extractor = Extractor()
        extracted_data = {}

        for config in extract_config:
            name = config.get("name")
            extract_type = config.get("type")

            if not name or not extract_type:
                logger.warning(f"提取配置不完整: {config}")
                continue

            try:
                if extract_type == "text":
                    locator = config.get("locator")
                    if locator:
                        text = self.get_text(locator)
                        extracted_data[name] = text

                elif extract_type == "attribute":
                    locator = config.get("locator")
                    attribute = config.get("attribute")
                    if locator and attribute:
                        value = self.get_attribute(locator, attribute)
                        extracted_data[name] = value

                elif extract_type == "url":
                    extracted_data[name] = self.page.url

                elif extract_type == "title":
                    extracted_data[name] = self.page.title()

                elif extract_type == "javascript":
                    script = config.get("script")
                    if script:
                        value = self.execute_javascript(script)
                        extracted_data[name] = value

                else:
                    logger.warning(f"不支持的提取类型: {extract_type}")
                    continue

                logger.info(f"数据提取成功: {name} = {extracted_data[name]}")

            except Exception as e:
                logger.error(f"数据提取失败: {name}, 错误: {e}")
                extracted_data[name] = None

        # 将提取的数据保存到变量管理器
        variable_manager.update_variables(extracted_data)

        logger.info(f"Web数据提取完成: {extracted_data}")
        return extracted_data

    def execute_steps(self, steps: List[Dict[str, Any]]):
        """执行步骤序列"""
        logger_manager.log_step("执行Web步骤序列", f"{len(steps)}个步骤")

        for i, step in enumerate(steps, 1):
            action = step.get("action")
            params = step.get("params", {})

            if not action:
                logger.warning(f"步骤{i}缺少action参数")
                continue

            try:
                logger.info(f"执行步骤{i}: {action}")
                self.execute(action, params)

            except Exception as e:
                logger.error(f"步骤{i}执行失败: {action}, 错误: {e}")
                raise

        logger.info("Web步骤序列执行完成")

    def wait_and_retry(self, action: str, params: Dict[str, Any],
                      max_retries: int = 3, retry_interval: float = 1.0) -> Any:
        """等待并重试操作"""
        import time

        for attempt in range(max_retries + 1):
            try:
                return self.execute(action, params)
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"操作重试失败: {action}, 最大重试次数: {max_retries}")
                    raise
                else:
                    logger.warning(f"操作失败，{retry_interval}秒后重试: {action}, 尝试次数: {attempt + 1}")
                    time.sleep(retry_interval)


# 全局Web关键字实例
web_keywords = WebKeywords()

# 便捷函数
def execute_web_action(action: str, params: Dict[str, Any] = None) -> Any:
    """执行Web操作便捷函数"""
    return web_keywords.execute(action, params)

def verify_web_response(assertions: List[Dict[str, Any]]):
    """验证Web响应便捷函数"""
    web_keywords.verify_response(assertions)

def extract_web_data(extract_config: List[Dict[str, str]]) -> Dict[str, Any]:
    """提取Web数据便捷函数"""
    return web_keywords.extract_data(extract_config)

def execute_web_steps(steps: List[Dict[str, Any]]):
    """执行Web步骤便捷函数"""
    web_keywords.execute_steps(steps)
