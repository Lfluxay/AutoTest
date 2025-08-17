import re
from typing import Any, Dict, List, Union
from playwright.sync_api import Page
from utils.logging.logger import logger, logger_manager
from core.web.browser import get_current_page


class WebAssertions:
    """Web断言类 - 提供各种Web页面断言方法"""
    
    @staticmethod
    def assert_title(page: Page, expected: str, operator: str = "eq", message: str = ""):
        """
        断言页面标题
        
        Args:
            page: 页面对象
            expected: 期望标题
            operator: 比较操作符 (eq, contains, starts_with, ends_with, regex)
            message: 自定义错误消息
        """
        actual = page.title()
        success = WebAssertions._compare_text(actual, expected, operator)
        
        logger_manager.log_assertion(f"title {operator}", expected, actual, success)
        
        if not success:
            error_msg = message or f"页面标题断言失败: 期望 {operator} '{expected}', 实际 '{actual}'"
            logger.error(error_msg)
            raise AssertionError(error_msg)
        
        return True
    
    @staticmethod
    def assert_url(page: Page, expected: str, operator: str = "eq", message: str = ""):
        """
        断言页面URL
        
        Args:
            page: 页面对象
            expected: 期望URL
            operator: 比较操作符
            message: 自定义错误消息
        """
        actual = page.url
        success = WebAssertions._compare_text(actual, expected, operator)
        
        logger_manager.log_assertion(f"url {operator}", expected, actual, success)
        
        if not success:
            error_msg = message or f"页面URL断言失败: 期望 {operator} '{expected}', 实际 '{actual}'"
            logger.error(error_msg)
            raise AssertionError(error_msg)
        
        return True
    
    @staticmethod
    def assert_element_visible(page: Page, locator: str, message: str = ""):
        """
        断言元素可见
        
        Args:
            page: 页面对象
            locator: 元素定位器
            message: 自定义错误消息
        """
        try:
            element = page.locator(locator)
            visible = element.is_visible()
            
            logger_manager.log_assertion("element_visible", locator, "可见" if visible else "不可见", visible)
            
            if not visible:
                error_msg = message or f"元素可见性断言失败: 元素 '{locator}' 不可见"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"元素可见性断言异常: {locator}, {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_element_hidden(page: Page, locator: str, message: str = ""):
        """
        断言元素隐藏
        
        Args:
            page: 页面对象
            locator: 元素定位器
            message: 自定义错误消息
        """
        try:
            element = page.locator(locator)
            hidden = element.is_hidden()
            
            logger_manager.log_assertion("element_hidden", locator, "隐藏" if hidden else "可见", hidden)
            
            if not hidden:
                error_msg = message or f"元素隐藏断言失败: 元素 '{locator}' 可见"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"元素隐藏断言异常: {locator}, {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_element_enabled(page: Page, locator: str, message: str = ""):
        """
        断言元素启用
        
        Args:
            page: 页面对象
            locator: 元素定位器
            message: 自定义错误消息
        """
        try:
            element = page.locator(locator)
            enabled = element.is_enabled()
            
            logger_manager.log_assertion("element_enabled", locator, "启用" if enabled else "禁用", enabled)
            
            if not enabled:
                error_msg = message or f"元素启用断言失败: 元素 '{locator}' 禁用"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"元素启用断言异常: {locator}, {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_element_disabled(page: Page, locator: str, message: str = ""):
        """
        断言元素禁用
        
        Args:
            page: 页面对象
            locator: 元素定位器
            message: 自定义错误消息
        """
        try:
            element = page.locator(locator)
            disabled = element.is_disabled()
            
            logger_manager.log_assertion("element_disabled", locator, "禁用" if disabled else "启用", disabled)
            
            if not disabled:
                error_msg = message or f"元素禁用断言失败: 元素 '{locator}' 启用"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"元素禁用断言异常: {locator}, {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_element_checked(page: Page, locator: str, message: str = ""):
        """
        断言元素勾选
        
        Args:
            page: 页面对象
            locator: 元素定位器
            message: 自定义错误消息
        """
        try:
            element = page.locator(locator)
            checked = element.is_checked()
            
            logger_manager.log_assertion("element_checked", locator, "已勾选" if checked else "未勾选", checked)
            
            if not checked:
                error_msg = message or f"元素勾选断言失败: 元素 '{locator}' 未勾选"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"元素勾选断言异常: {locator}, {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_element_text(page: Page, locator: str, expected: str, operator: str = "eq", message: str = ""):
        """
        断言元素文本
        
        Args:
            page: 页面对象
            locator: 元素定位器
            expected: 期望文本
            operator: 比较操作符
            message: 自定义错误消息
        """
        try:
            element = page.locator(locator)
            actual = element.text_content() or ""
            success = WebAssertions._compare_text(actual, expected, operator)
            
            logger_manager.log_assertion(f"element_text[{locator}] {operator}", expected, actual, success)
            
            if not success:
                error_msg = message or f"元素文本断言失败: {locator} {operator} '{expected}', 实际 '{actual}'"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"元素文本断言异常: {locator}, {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_element_attribute(page: Page, locator: str, attribute: str, expected: str, operator: str = "eq", message: str = ""):
        """
        断言元素属性
        
        Args:
            page: 页面对象
            locator: 元素定位器
            attribute: 属性名称
            expected: 期望值
            operator: 比较操作符
            message: 自定义错误消息
        """
        try:
            element = page.locator(locator)
            actual = element.get_attribute(attribute) or ""
            success = WebAssertions._compare_text(actual, expected, operator)
            
            logger_manager.log_assertion(f"element_attribute[{locator}][{attribute}] {operator}", expected, actual, success)
            
            if not success:
                error_msg = message or f"元素属性断言失败: {locator}[{attribute}] {operator} '{expected}', 实际 '{actual}'"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"元素属性断言异常: {locator}[{attribute}], {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_element_value(page: Page, locator: str, expected: str, operator: str = "eq", message: str = ""):
        """
        断言输入框值
        
        Args:
            page: 页面对象
            locator: 元素定位器
            expected: 期望值
            operator: 比较操作符
            message: 自定义错误消息
        """
        try:
            element = page.locator(locator)
            actual = element.input_value()
            success = WebAssertions._compare_text(actual, expected, operator)
            
            logger_manager.log_assertion(f"element_value[{locator}] {operator}", expected, actual, success)
            
            if not success:
                error_msg = message or f"元素值断言失败: {locator} {operator} '{expected}', 实际 '{actual}'"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"元素值断言异常: {locator}, {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_element_count(page: Page, locator: str, expected: int, operator: str = "eq", message: str = ""):
        """
        断言元素数量
        
        Args:
            page: 页面对象
            locator: 元素定位器
            expected: 期望数量
            operator: 比较操作符 (eq, ne, gt, ge, lt, le)
            message: 自定义错误消息
        """
        try:
            elements = page.locator(locator)
            actual = elements.count()
            success = WebAssertions._compare_number(actual, expected, operator)
            
            logger_manager.log_assertion(f"element_count[{locator}] {operator}", str(expected), str(actual), success)
            
            if not success:
                error_msg = message or f"元素数量断言失败: {locator} {operator} {expected}, 实际 {actual}"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"元素数量断言异常: {locator}, {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_page_contains_text(page: Page, text: str, case_sensitive: bool = True, message: str = ""):
        """
        断言页面包含文本
        
        Args:
            page: 页面对象
            text: 期望文本
            case_sensitive: 是否区分大小写
            message: 自定义错误消息
        """
        try:
            if case_sensitive:
                locator = page.get_by_text(text, exact=False)
            else:
                locator = page.locator(f"text=/{text}/i")
            
            count = locator.count()
            success = count > 0
            
            logger_manager.log_assertion("page_contains_text", text, f"找到{count}处" if success else "未找到", success)
            
            if not success:
                error_msg = message or f"页面文本断言失败: 页面中不包含文本 '{text}'"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"页面文本断言异常: {text}, {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_alert_text(page: Page, expected: str, operator: str = "eq", timeout: int = 5000, message: str = ""):
        """
        断言弹窗文本
        
        Args:
            page: 页面对象
            expected: 期望文本
            operator: 比较操作符
            timeout: 等待超时时间
            message: 自定义错误消息
        """
        try:
            alert_text = None
            
            def handle_dialog(dialog):
                nonlocal alert_text
                alert_text = dialog.message
                dialog.accept()
            
            page.on("dialog", handle_dialog)
            
            # 等待弹窗出现
            import time
            start_time = time.time()
            while alert_text is None and (time.time() - start_time) * 1000 < timeout:
                time.sleep(0.1)
            
            page.remove_listener("dialog", handle_dialog)
            
            if alert_text is None:
                error_msg = message or f"弹窗文本断言失败: 在{timeout}ms内未检测到弹窗"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            success = WebAssertions._compare_text(alert_text, expected, operator)
            
            logger_manager.log_assertion(f"alert_text {operator}", expected, alert_text, success)
            
            if not success:
                error_msg = message or f"弹窗文本断言失败: {operator} '{expected}', 实际 '{alert_text}'"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"弹窗文本断言异常: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_element_css_property(page: Page, locator: str, property_name: str, expected: str, operator: str = "eq", message: str = ""):
        """
        断言元素CSS属性
        
        Args:
            page: 页面对象
            locator: 元素定位器
            property_name: CSS属性名
            expected: 期望值
            operator: 比较操作符
            message: 自定义错误消息
        """
        try:
            element = page.locator(locator)
            actual = element.evaluate(f"element => window.getComputedStyle(element).{property_name}")
            success = WebAssertions._compare_text(str(actual), expected, operator)
            
            logger_manager.log_assertion(f"element_css[{locator}][{property_name}] {operator}", expected, str(actual), success)
            
            if not success:
                error_msg = message or f"元素CSS属性断言失败: {locator}[{property_name}] {operator} '{expected}', 实际 '{actual}'"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"元素CSS属性断言异常: {locator}[{property_name}], {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_element_bounding_box(page: Page, locator: str, expected_box: dict, tolerance: int = 5, message: str = ""):
        """
        断言元素边界框
        
        Args:
            page: 页面对象
            locator: 元素定位器
            expected_box: 期望边界框 {"x": 0, "y": 0, "width": 100, "height": 50}
            tolerance: 容差像素
            message: 自定义错误消息
        """
        try:
            element = page.locator(locator)
            actual_box = element.bounding_box()
            
            if actual_box is None:
                error_msg = message or f"元素边界框断言失败: 无法获取元素边界框 {locator}"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            success = True
            details = []
            
            for key in ["x", "y", "width", "height"]:
                if key in expected_box:
                    expected_val = expected_box[key]
                    actual_val = actual_box[key]
                    if abs(actual_val - expected_val) > tolerance:
                        success = False
                        details.append(f"{key}: 期望{expected_val}±{tolerance}, 实际{actual_val}")
            
            logger_manager.log_assertion(f"element_bounding_box[{locator}]", str(expected_box), str(actual_box), success)
            
            if not success:
                error_msg = message or f"元素边界框断言失败: {locator} - {', '.join(details)}"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"元素边界框断言异常: {locator}, {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_page_load_time(page: Page, max_time: float, message: str = ""):
        """
        断言页面加载时间
        
        Args:
            page: 页面对象
            max_time: 最大加载时间(秒)
            message: 自定义错误消息
        """
        try:
            load_time = page.evaluate("""
                () => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    return perfData ? (perfData.loadEventEnd - perfData.navigationStart) / 1000 : 0;
                }
            """)
            
            success = load_time <= max_time
            
            logger_manager.log_assertion("page_load_time", f"<={max_time}s", f"{load_time:.3f}s", success)
            
            if not success:
                error_msg = message or f"页面加载时间断言失败: 期望 <={max_time}s, 实际 {load_time:.3f}s"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"页面加载时间断言异常: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_page_size(page: Page, max_size_kb: int, message: str = ""):
        """
        断言页面大小
        
        Args:
            page: 页面对象
            max_size_kb: 最大页面大小(KB)
            message: 自定义错误消息
        """
        try:
            page_size = page.evaluate("""
                () => {
                    const resources = performance.getEntriesByType('resource');
                    let totalSize = 0;
                    resources.forEach(resource => {
                        if (resource.transferSize) {
                            totalSize += resource.transferSize;
                        }
                    });
                    return Math.round(totalSize / 1024);
                }
            """)
            
            success = page_size <= max_size_kb
            
            logger_manager.log_assertion("page_size", f"<={max_size_kb}KB", f"{page_size}KB", success)
            
            if not success:
                error_msg = message or f"页面大小断言失败: 期望 <={max_size_kb}KB, 实际 {page_size}KB"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"页面大小断言异常: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_table_data(page: Page, table_locator: str, expected_data: list, message: str = ""):
        """
        断言表格数据
        
        Args:
            page: 页面对象
            table_locator: 表格定位器
            expected_data: 期望数据 [["row1col1", "row1col2"], ["row2col1", "row2col2"]]
            message: 自定义错误消息
        """
        try:
            table = page.locator(table_locator)
            
            actual_data = table.evaluate("""
                table => {
                    const rows = table.querySelectorAll('tr');
                    const data = [];
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td, th');
                        const rowData = [];
                        cells.forEach(cell => rowData.push(cell.textContent.trim()));
                        if (rowData.length > 0) data.push(rowData);
                    });
                    return data;
                }
            """)
            
            success = actual_data == expected_data
            
            logger_manager.log_assertion(f"table_data[{table_locator}]", str(expected_data), str(actual_data), success)
            
            if not success:
                error_msg = message or f"表格数据断言失败: {table_locator}\n期望: {expected_data}\n实际: {actual_data}"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"表格数据断言异常: {table_locator}, {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_list_items(page: Page, list_locator: str, expected_items: list, message: str = ""):
        """
        断言列表项
        
        Args:
            page: 页面对象
            list_locator: 列表定位器
            expected_items: 期望列表项
            message: 自定义错误消息
        """
        try:
            list_element = page.locator(list_locator)
            
            actual_items = list_element.evaluate("""
                list => {
                    const items = list.querySelectorAll('li');
                    return Array.from(items).map(item => item.textContent.trim());
                }
            """)
            
            success = actual_items == expected_items
            
            logger_manager.log_assertion(f"list_items[{list_locator}]", str(expected_items), str(actual_items), success)
            
            if not success:
                error_msg = message or f"列表项断言失败: {list_locator}\n期望: {expected_items}\n实际: {actual_items}"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"列表项断言异常: {list_locator}, {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_element_in_viewport(page: Page, locator: str, message: str = ""):
        """
        断言元素在视窗内
        
        Args:
            page: 页面对象
            locator: 元素定位器
            message: 自定义错误消息
        """
        try:
            element = page.locator(locator)
            
            in_viewport = element.evaluate("""
                element => {
                    const rect = element.getBoundingClientRect();
                    return (
                        rect.top >= 0 &&
                        rect.left >= 0 &&
                        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                    );
                }
            """)
            
            logger_manager.log_assertion(f"element_in_viewport[{locator}]", "在视窗内", "在视窗内" if in_viewport else "不在视窗内", in_viewport)
            
            if not in_viewport:
                error_msg = message or f"元素视窗断言失败: 元素 {locator} 不在视窗内"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"元素视窗断言异常: {locator}, {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def assert_no_console_errors(page: Page, message: str = ""):
        """
        断言页面无控制台错误
        
        Args:
            page: 页面对象
            message: 自定义错误消息
        """
        try:
            console_errors = page.evaluate("""
                () => {
                    const errors = [];
                    const originalError = console.error;
                    console.error = function(...args) {
                        errors.push(args.join(' '));
                        originalError.apply(console, args);
                    };
                    return errors;
                }
            """)
            
            success = len(console_errors) == 0
            
            logger_manager.log_assertion("no_console_errors", "无错误", f"{len(console_errors)}个错误", success)
            
            if not success:
                error_msg = message or f"控制台错误断言失败: 发现 {len(console_errors)} 个错误: {console_errors}"
                logger.error(error_msg)
                raise AssertionError(error_msg)
            
            return True
            
        except Exception as e:
            error_msg = message or f"控制台错误断言异常: {e}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
    
    @staticmethod
    def _compare_text(actual: str, expected: str, operator: str) -> bool:
        """比较文本"""
        try:
            if operator == "eq":
                return actual == expected
            elif operator == "ne":
                return actual != expected
            elif operator == "contains":
                return expected in actual
            elif operator == "not_contains":
                return expected not in actual
            elif operator == "starts_with":
                return actual.startswith(expected)
            elif operator == "ends_with":
                return actual.endswith(expected)
            elif operator == "regex":
                return bool(re.search(expected, actual, re.DOTALL))
            elif operator == "empty":
                return len(actual.strip()) == 0
            elif operator == "not_empty":
                return len(actual.strip()) > 0
            else:
                logger.warning(f"不支持的文本比较操作符: {operator}")
                return False
        except Exception as e:
            logger.error(f"文本比较异常: {e}")
            return False
    
    @staticmethod
    def _compare_number(actual: int, expected: int, operator: str) -> bool:
        """比较数字"""
        try:
            if operator == "eq":
                return actual == expected
            elif operator == "ne":
                return actual != expected
            elif operator == "gt":
                return actual > expected
            elif operator == "ge":
                return actual >= expected
            elif operator == "lt":
                return actual < expected
            elif operator == "le":
                return actual <= expected
            else:
                logger.warning(f"不支持的数字比较操作符: {operator}")
                return False
        except Exception as e:
            logger.error(f"数字比较异常: {e}")
            return False


def assert_web_element(assertion_config: Dict[str, Any], page: Page = None):
    """
    根据配置断言Web元素
    
    Args:
        assertion_config: 断言配置
        page: 页面对象，如果不指定则使用当前页面
    """
    if page is None:
        page = get_current_page()
    
    assertion_type = assertion_config.get("type")
    
    if assertion_type == "title":
        expected = assertion_config.get("expected")
        operator = assertion_config.get("operator", "eq")
        message = assertion_config.get("message", "")
        WebAssertions.assert_title(page, expected, operator, message)
        
    elif assertion_type == "url":
        expected = assertion_config.get("expected")
        operator = assertion_config.get("operator", "eq")
        message = assertion_config.get("message", "")
        WebAssertions.assert_url(page, expected, operator, message)
        
    elif assertion_type == "element_visible":
        locator = assertion_config.get("locator")
        message = assertion_config.get("message", "")
        WebAssertions.assert_element_visible(page, locator, message)
        
    elif assertion_type == "element_hidden":
        locator = assertion_config.get("locator")
        message = assertion_config.get("message", "")
        WebAssertions.assert_element_hidden(page, locator, message)
        
    elif assertion_type == "element_enabled":
        locator = assertion_config.get("locator")
        message = assertion_config.get("message", "")
        WebAssertions.assert_element_enabled(page, locator, message)
        
    elif assertion_type == "element_disabled":
        locator = assertion_config.get("locator")
        message = assertion_config.get("message", "")
        WebAssertions.assert_element_disabled(page, locator, message)
        
    elif assertion_type == "element_checked":
        locator = assertion_config.get("locator")
        message = assertion_config.get("message", "")
        WebAssertions.assert_element_checked(page, locator, message)
        
    elif assertion_type == "element_text":
        locator = assertion_config.get("locator")
        expected = assertion_config.get("expected")
        operator = assertion_config.get("operator", "eq")
        message = assertion_config.get("message", "")
        WebAssertions.assert_element_text(page, locator, expected, operator, message)
        
    elif assertion_type == "element_attribute":
        locator = assertion_config.get("locator")
        attribute = assertion_config.get("attribute")
        expected = assertion_config.get("expected")
        operator = assertion_config.get("operator", "eq")
        message = assertion_config.get("message", "")
        WebAssertions.assert_element_attribute(page, locator, attribute, expected, operator, message)
        
    elif assertion_type == "element_value":
        locator = assertion_config.get("locator")
        expected = assertion_config.get("expected")
        operator = assertion_config.get("operator", "eq")
        message = assertion_config.get("message", "")
        WebAssertions.assert_element_value(page, locator, expected, operator, message)
        
    elif assertion_type == "element_count":
        locator = assertion_config.get("locator")
        expected = assertion_config.get("expected")
        operator = assertion_config.get("operator", "eq")
        message = assertion_config.get("message", "")
        WebAssertions.assert_element_count(page, locator, expected, operator, message)
        
    elif assertion_type == "element_css_property":
        locator = assertion_config.get("locator")
        property_name = assertion_config.get("property_name")
        expected = assertion_config.get("expected")
        operator = assertion_config.get("operator", "eq")
        message = assertion_config.get("message", "")
        WebAssertions.assert_element_css_property(page, locator, property_name, expected, operator, message)
        
    elif assertion_type == "element_bounding_box":
        locator = assertion_config.get("locator")
        expected_box = assertion_config.get("expected_box")
        tolerance = assertion_config.get("tolerance", 5)
        message = assertion_config.get("message", "")
        WebAssertions.assert_element_bounding_box(page, locator, expected_box, tolerance, message)
        
    elif assertion_type == "element_in_viewport":
        locator = assertion_config.get("locator")
        message = assertion_config.get("message", "")
        WebAssertions.assert_element_in_viewport(page, locator, message)
        
    elif assertion_type == "page_contains_text":
        text = assertion_config.get("text")
        case_sensitive = assertion_config.get("case_sensitive", True)
        message = assertion_config.get("message", "")
        WebAssertions.assert_page_contains_text(page, text, case_sensitive, message)
        
    elif assertion_type == "page_load_time":
        max_time = assertion_config.get("max_time")
        message = assertion_config.get("message", "")
        WebAssertions.assert_page_load_time(page, max_time, message)
        
    elif assertion_type == "page_size":
        max_size_kb = assertion_config.get("max_size_kb")
        message = assertion_config.get("message", "")
        WebAssertions.assert_page_size(page, max_size_kb, message)
        
    elif assertion_type == "table_data":
        table_locator = assertion_config.get("locator")
        expected_data = assertion_config.get("expected_data")
        message = assertion_config.get("message", "")
        WebAssertions.assert_table_data(page, table_locator, expected_data, message)
        
    elif assertion_type == "list_items":
        list_locator = assertion_config.get("locator")
        expected_items = assertion_config.get("expected_items")
        message = assertion_config.get("message", "")
        WebAssertions.assert_list_items(page, list_locator, expected_items, message)
        
    elif assertion_type == "alert_text":
        expected = assertion_config.get("expected")
        operator = assertion_config.get("operator", "eq")
        timeout = assertion_config.get("timeout", 5000)
        message = assertion_config.get("message", "")
        WebAssertions.assert_alert_text(page, expected, operator, timeout, message)
        
    elif assertion_type == "no_console_errors":
        message = assertion_config.get("message", "")
        WebAssertions.assert_no_console_errors(page, message)
        
    else:
        logger.warning(f"不支持的Web断言类型: {assertion_type}")


def assert_multiple_web(assertions: List[Dict[str, Any]], page: Page = None):
    """
    执行多个Web断言
    
    Args:
        assertions: 断言配置列表
        page: 页面对象
    """
    for assertion in assertions:
        assert_web_element(assertion, page)