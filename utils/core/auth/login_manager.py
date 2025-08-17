"""
登录管理器 - 提供API和Web的登录功能
"""
from typing import Dict, Any, Optional, Callable
from utils.logging.logger import logger
from utils.config.parser import get_merged_config


class APILoginManager:
    """API登录管理器"""
    
    def __init__(self, api_client=None):
        self.api_client = api_client
        self.config = get_merged_config().get('api', {}).get('login', {})
        self.is_logged_in = False
        self.token = None
        self.custom_login_func = None
        
    def set_custom_login(self, login_func: Callable):
        """设置自定义登录函数
        
        Args:
            login_func: 自定义登录函数，应返回(success: bool, token: str)
        """
        self.custom_login_func = login_func
        logger.info("已设置自定义API登录函数")
    
    def login(self, username: str = None, password: str = None) -> bool:
        """执行登录
        
        Args:
            username: 用户名，为空时使用配置
            password: 密码，为空时使用配置
            
        Returns:
            登录是否成功
        """
        if not self.config.get('enabled', True):
            logger.info("API登录已禁用")
            return True
            
        # 使用自定义登录函数
        if self.custom_login_func:
            try:
                success, token = self.custom_login_func(username, password)
                if success:
                    self.token = token
                    self.is_logged_in = True
                    logger.info("自定义API登录成功")
                    return True
                else:
                    logger.error("自定义API登录失败")
                    return False
            except Exception as e:
                logger.error(f"自定义API登录异常: {e}")
                return False
        
        # 使用默认登录逻辑
        return self._default_login(username, password)
    
    def _default_login(self, username: str = None, password: str = None) -> bool:
        """默认登录逻辑"""
        if not self.api_client:
            logger.error("API客户端未初始化")
            return False
            
        try:
            # 获取登录参数
            login_data = self.config.get('data', {}).copy()
            if username:
                login_data['username'] = username
            if password:
                login_data['password'] = password
                
            # 发送登录请求
            login_url = self.config.get('url', '/api/login')
            method = self.config.get('method', 'POST').upper()
            
            if method == 'POST':
                response = self.api_client.post(login_url, json=login_data)
            else:
                response = self.api_client.request(method, login_url, json=login_data)
            
            # 检查登录是否成功
            if self._check_login_success(response):
                # 提取token
                self.token = self._extract_token(response)
                if self.token:
                    # 设置全局token
                    self._set_global_token(self.token)
                    self.is_logged_in = True
                    logger.info("API默认登录成功")
                    return True
                    
            logger.error("API默认登录失败")
            return False
            
        except Exception as e:
            logger.error(f"API默认登录异常: {e}")
            return False
    
    def _check_login_success(self, response) -> bool:
        """检查登录是否成功"""
        success_flag = self.config.get('success_flag', {})
        flag_type = success_flag.get('type', 'status_code')
        
        if flag_type == 'status_code':
            return response.status_code == 200
        elif flag_type == 'json_path':
            try:
                import jsonpath
                data = response.json()
                path = success_flag.get('path', '$.code')
                expected = success_flag.get('value', 0)
                result = jsonpath.jsonpath(data, path)
                return result and result[0] == expected
            except Exception:
                return False
        elif flag_type == 'regex':
            import re
            pattern = success_flag.get('pattern', '')
            return bool(re.search(pattern, response.text))
        
        return False
    
    def _extract_token(self, response) -> Optional[str]:
        """提取token"""
        token_config = self.config.get('token_extract', {})
        extract_type = token_config.get('type', 'json_path')
        
        if extract_type == 'json_path':
            try:
                import jsonpath
                data = response.json()
                path = token_config.get('path', '$.data.token')
                result = jsonpath.jsonpath(data, path)
                return result[0] if result else None
            except Exception:
                return None
        elif extract_type == 'header':
            header_name = token_config.get('header', 'Authorization')
            return response.headers.get(header_name)
        elif extract_type == 'regex':
            import re
            pattern = token_config.get('pattern', '')
            match = re.search(pattern, response.text)
            return match.group(1) if match else None
            
        return None
    
    def _set_global_token(self, token: str):
        """设置全局token"""
        if not self.api_client:
            return
            
        token_header = self.config.get('token_header', 'Authorization')
        token_prefix = self.config.get('token_prefix', 'Bearer ')
        
        # 设置请求头
        self.api_client.session.headers[token_header] = f"{token_prefix}{token}"
        
        # 保存到变量管理器
        from utils.data.extractor import variable_manager
        variable_manager.set_variable('api_token', token)
    
    def check_token_valid(self) -> bool:
        """检查token是否有效"""
        if not self.is_logged_in or not self.token:
            return False
            
        # 可以通过发送一个简单的API请求来检查token有效性
        # 这里简化处理，实际项目中可以根据需要实现
        return True
    
    def logout(self):
        """登出"""
        self.is_logged_in = False
        self.token = None
        if self.api_client and hasattr(self.api_client, 'session'):
            # 清除token头
            token_header = self.config.get('token_header', 'Authorization')
            self.api_client.session.headers.pop(token_header, None)
        logger.info("API登出完成")


class WebLoginManager:
    """Web登录管理器"""
    
    def __init__(self, browser_manager=None):
        self.browser_manager = browser_manager
        self.config = get_merged_config().get('web', {}).get('login', {})
        self.is_logged_in = False
        self.custom_login_func = None
        self.custom_navigate_func = None
        
    def set_custom_login(self, login_func: Callable):
        """设置自定义登录函数
        
        Args:
            login_func: 自定义登录函数，应返回bool表示是否成功
        """
        self.custom_login_func = login_func
        logger.info("已设置自定义Web登录函数")
    
    def set_custom_navigate(self, navigate_func: Callable):
        """设置自定义导航函数
        
        Args:
            navigate_func: 自定义导航函数，用于导航到指定页面
        """
        self.custom_navigate_func = navigate_func
        logger.info("已设置自定义Web导航函数")
    
    def login(self, username: str = None, password: str = None) -> bool:
        """执行登录
        
        Args:
            username: 用户名，为空时使用配置
            password: 密码，为空时使用配置
            
        Returns:
            登录是否成功
        """
        if not self.config.get('enabled', True):
            logger.info("Web登录已禁用")
            return True
            
        # 使用自定义登录函数
        if self.custom_login_func:
            try:
                success = self.custom_login_func(username, password)
                if success:
                    self.is_logged_in = True
                    logger.info("自定义Web登录成功")
                    return True
                else:
                    logger.error("自定义Web登录失败")
                    return False
            except Exception as e:
                logger.error(f"自定义Web登录异常: {e}")
                return False
        
        # 使用默认登录逻辑
        return self._default_login(username, password)
    
    def _default_login(self, username: str = None, password: str = None) -> bool:
        """默认登录逻辑"""
        if not self.browser_manager or not self.browser_manager.page:
            logger.error("浏览器未初始化")
            return False
            
        try:
            page = self.browser_manager.page
            
            # 导航到登录页面
            login_url = self.config.get('url', '')
            if login_url:
                page.goto(login_url)
                page.wait_for_load_state('networkidle')
            
            # 获取登录凭据
            username = username or self.config.get('username', '')
            password = password or self.config.get('password', '')
            
            # 填写登录表单
            username_locator = self.config.get('username_locator', '#username')
            password_locator = self.config.get('password_locator', '#password')
            login_button_locator = self.config.get('login_button_locator', '#login-btn')
            
            page.fill(username_locator, username)
            page.fill(password_locator, password)
            page.click(login_button_locator)
            
            # 等待登录完成
            success_url_pattern = self.config.get('success_url_pattern', '')
            if success_url_pattern:
                page.wait_for_url(success_url_pattern, timeout=10000)
            else:
                page.wait_for_load_state('networkidle')
            
            self.is_logged_in = True
            logger.info("Web默认登录成功")
            return True
            
        except Exception as e:
            logger.error(f"Web默认登录异常: {e}")
            return False
    
    def navigate_to_target_page(self, target_url: str = None) -> bool:
        """导航到目标页面（如首页、工作台等）
        
        Args:
            target_url: 目标页面URL，为空时使用配置中的home_url
            
        Returns:
            导航是否成功
        """
        if not self.browser_manager or not self.browser_manager.page:
            logger.error("浏览器未初始化")
            return False
            
        # 使用自定义导航函数
        if self.custom_navigate_func:
            try:
                success = self.custom_navigate_func(target_url)
                if success:
                    logger.info("自定义导航成功")
                    return True
                else:
                    logger.error("自定义导航失败")
                    return False
            except Exception as e:
                logger.error(f"自定义导航异常: {e}")
                return False
        
        # 使用默认导航逻辑
        return self._default_navigate(target_url)
    
    def _default_navigate(self, target_url: str = None) -> bool:
        """默认导航逻辑"""
        try:
            page = self.browser_manager.page
            target_url = target_url or self.config.get('home_url', '')
            
            if not target_url:
                logger.warning("未配置目标页面URL")
                return True
                
            page.goto(target_url)
            page.wait_for_load_state('networkidle')
            
            logger.info(f"导航到目标页面成功: {target_url}")
            return True
            
        except Exception as e:
            logger.error(f"导航到目标页面失败: {e}")
            return False
    
    def ensure_on_target_page(self, target_url: str = None, url_pattern: str = None) -> bool:
        """确保当前在目标页面
        
        Args:
            target_url: 目标页面URL
            url_pattern: URL匹配模式，支持通配符
            
        Returns:
            是否在目标页面
        """
        if not self.browser_manager or not self.browser_manager.page:
            return False
            
        try:
            page = self.browser_manager.page
            current_url = page.url
            
            # 确定检查的URL和模式
            target_url = target_url or self.config.get('home_url', '')
            url_pattern = url_pattern or self.config.get('home_url_pattern', '')
            
            # 检查是否在目标页面
            if target_url and target_url in current_url:
                logger.debug(f"已在目标页面: {current_url}")
                return True
            
            if url_pattern:
                import fnmatch
                if fnmatch.fnmatch(current_url, url_pattern):
                    logger.debug(f"当前页面匹配模式: {current_url}")
                    return True
            
            # 不在目标页面，尝试导航
            logger.info(f"当前不在目标页面({current_url})，尝试导航")
            return self.navigate_to_target_page(target_url)
            
        except Exception as e:
            logger.error(f"检查目标页面失败: {e}")
            return False
