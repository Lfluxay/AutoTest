import requests
import time
from typing import Dict, Any, Optional, Union, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.logging.logger import logger
from utils.logging.test_step_logger import test_step_logger
from utils.logging.logger import logger_manager
from utils.config.unified_config_manager import get_merged_config
from utils.data.extractor import Extractor, variable_manager
from utils.core.exceptions import APIException, AuthenticationError, ConfigException


class APIClient:
    """API客户端 - 封装HTTP请求功能"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化API客户端

        Args:
            config: API配置

        Raises:
            ConfigException: 配置错误时抛出
        """
        try:
            if config is None:
                full_config = get_merged_config()
                config = full_config.get('api', {})

            self.config = config
            self.session = requests.Session()
            self.base_url = config.get('base_url', '')
            if not self.base_url:
                raise ConfigException("API base_url 配置不能为空", "MISSING_BASE_URL")

            self.timeout = config.get('timeout', 30)
            self.retry_times = config.get('retry_times', 3)
            self.verify_ssl = config.get('verify_ssl', True)

            # 设置全局请求头
            global_headers = config.get('global_headers', {})
            self.session.headers.update(global_headers)

            # 设置SSL验证
            self.session.verify = self.verify_ssl

            # 为幂等请求设置HTTP重试（连接/状态码重试）
            # 决策理由：使用 urllib3 Retry 对常见瞬时错误（5xx/429）进行自动重试，提升稳定性
            retry = Retry(
                total=self.retry_times,
                connect=self.retry_times,
                read=self.retry_times,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=frozenset(["GET", "PUT", "DELETE", "HEAD", "OPTIONS"])  # 幂等方法
            )
            adapter = HTTPAdapter(max_retries=retry)
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)

            # 全局登录token
            self.token: Optional[str] = None

            # 登录凭据
            self.username: Optional[str] = None
            self.password: Optional[str] = None

            logger.info(f"API客户端初始化完成: {self.base_url}")

        except Exception as e:
            if isinstance(e, ConfigException):
                raise
            raise ConfigException(f"API客户端初始化失败: {str(e)}", "INIT_FAILED")
    
    def _build_url(self, url: str) -> str:
        """构建完整URL"""
        if url.startswith('http'):
            return url
        
        base_url = self.base_url.rstrip('/')
        url = url.lstrip('/')
        return f"{base_url}/{url}"
    
    def _prepare_headers(self, headers: Dict[str, str] = None) -> Dict[str, str]:
        """准备请求头"""
        final_headers = self.session.headers.copy()
        
        if headers:
            final_headers.update(headers)
        
        # 添加token
        if self.token:
            token_header = self.config.get('login', {}).get('token_header', 'Authorization')
            token_prefix = self.config.get('login', {}).get('token_prefix', 'Bearer ')
            final_headers[token_header] = f"{token_prefix}{self.token}"
        
        return final_headers
    
    def request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str] = None,
        params: Dict[str, Any] = None,
        data: Any = None,
        json: Dict[str, Any] = None,
        files: Dict[str, Any] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> requests.Response:
        """
        发送HTTP请求
        
        Args:
            method: 请求方法
            url: 请求URL
            headers: 请求头
            params: URL参数
            data: 请求体数据
            json: JSON数据
            files: 文件数据
            timeout: 超时时间
            **kwargs: 其他请求参数
            
        Returns:
            响应对象
        """
        # 准备请求参数
        request_params = self._prepare_request_params(
            method, url, headers, params, data, json, files, timeout, **kwargs
        )
        
        # 执行请求（带重试机制）
        return self._execute_with_retry(**request_params)
    
    def _prepare_request_params(self, method: str, url: str, headers: Dict[str, str] = None,
                              params: Dict[str, Any] = None, data: Any = None, 
                              json: Dict[str, Any] = None, files: Dict[str, Any] = None,
                              timeout: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """准备请求参数"""
        # 构建完整URL
        full_url = self._build_url(url)
        
        # 准备请求头
        final_headers = self._prepare_headers(headers)
        
        # 使用默认超时时间
        if timeout is None:
            timeout = self.timeout
        
        # 替换变量
        if params:
            params = variable_manager.replace_variables(params)
        if data:
            data = variable_manager.replace_variables(data)
        if json:
            json = variable_manager.replace_variables(json)
        
        # 记录请求信息（敏感信息脱敏）
        headers_safe, body_safe = self._sanitize_for_logging(final_headers, json or data)
        logger_manager.log_api_request(
            method.upper(),
            full_url,
            headers_safe,
            str(body_safe)[:500] if body_safe else ''
        )

        # 详细日志记录API请求
        test_step_logger.log_api_request(
            method=method.upper(),
            url=full_url,
            headers=final_headers,
            data=json or data,
            params=params
        )
        
        return {
            'method': method.upper(),
            'url': full_url,
            'headers': final_headers,
            'params': params,
            'data': data,
            'json': json,
            'files': files,
            'timeout': timeout,
            **kwargs
        }
    
    def _execute_with_retry(self, **request_params) -> requests.Response:
        """带重试机制执行请求"""
        last_exception = None
        
        for attempt in range(self.retry_times + 1):
            try:
                start_time = time.time()
                
                response = self.session.request(**request_params)
                
                duration = time.time() - start_time

                # 记录响应信息
                response_text = self._truncate_response_text(response.text)
                logger_manager.log_api_response(response.status_code, response_text, duration)

                # 详细日志记录API响应
                try:
                    response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                except:
                    response_data = response.text

                test_step_logger.log_api_response(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    data=response_data,
                    response_time=duration
                )

                return response
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.retry_times:
                    wait_time = 2 ** attempt  # 指数退避
                    logger.warning(f"请求失败，{wait_time}秒后重试 (第{attempt + 1}次): {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"请求失败，已重试{self.retry_times}次: {e}")
        
        # 所有重试都失败
        raise last_exception
    
    def _truncate_response_text(self, text: str, max_length: int = 1000) -> str:
        """截断响应文本"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + '...'

    def _sanitize_for_logging(self, headers: Dict[str, str], body: Union[Dict[str, Any], str, None]) -> Tuple[Dict[str, str], Union[Dict[str, Any], str, None]]:
        """对日志中的敏感信息进行脱敏（如Authorization、Cookie、password、token、secret）"""
        def mask_value(val: str) -> str:
            if not val:
                return val
            return val[:3] + "***" + val[-3:] if len(val) > 6 else "***"
        sensitive_header_keys = {"authorization", "cookie", "set-cookie", "x-api-key"}
        headers_safe = {}
        for k, v in (headers or {}).items():
            if str(k).lower() in sensitive_header_keys:
                headers_safe[k] = mask_value(str(v))
            else:
                headers_safe[k] = v
        if isinstance(body, dict):
            sensitive_body_keys = {"password", "passwd", "token", "access_token", "refresh_token", "secret", "client_secret"}
            body_safe = {k: (mask_value(str(v)) if str(k).lower() in sensitive_body_keys else v) for k, v in body.items()}
        else:
            body_safe = body
        return headers_safe, body_safe

    def get(self, url: str, **kwargs) -> requests.Response:
        """GET请求"""
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """POST请求"""
        return self.request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        """PUT请求"""
        return self.request('PUT', url, **kwargs)
    
    def patch(self, url: str, **kwargs) -> requests.Response:
        """PATCH请求"""
        return self.request('PATCH', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        """DELETE请求"""
        return self.request('DELETE', url, **kwargs)
    
    def head(self, url: str, **kwargs) -> requests.Response:
        """HEAD请求"""
        return self.request('HEAD', url, **kwargs)
    
    def options(self, url: str, **kwargs) -> requests.Response:
        """OPTIONS请求"""
        return self.request('OPTIONS', url, **kwargs)
    
    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        执行全局登录

        Args:
            username: 用户名（可选，如果不提供则使用配置中的用户名）
            password: 密码（可选，如果不提供则使用配置中的密码）

        Returns:
            登录是否成功

        Raises:
            AuthenticationError: 认证失败时抛出
            APIException: API调用失败时抛出
        """
        login_config = self.config.get('login', {})
        
        if not login_config.get('enabled', False) and not username:
            logger.info("全局登录未启用")
            return True
        
        try:
            url = login_config.get('url')
            method = login_config.get('method', 'POST')
            login_data = login_config.get('data', {}).copy()
            
            # 使用参数或配置中的用户名密码
            if username:
                login_data['username'] = username
            if password:
                login_data['password'] = password
            
            logger.info(f"开始执行全局登录: {method} {url}")
            
            # 发送登录请求
            if method.upper() == 'POST':
                response = self.post(url, json=login_data)
            elif method.upper() == 'GET':
                response = self.get(url, params=login_data)
            else:
                response = self.request(method, url, json=login_data)
            
            # 检查登录是否成功
            success_flag = login_config.get('success_flag', {})
            success_type = success_flag.get('type', 'status_code')
            
            is_success = False
            if success_type == 'status_code':
                expected_code = success_flag.get('value', 200)
                is_success = response.status_code == expected_code
            elif success_type == 'json_path':
                json_path = success_flag.get('path')
                expected_value = success_flag.get('value')
                try:
                    actual_value = Extractor.extract_by_jsonpath(response.json(), json_path)
                    is_success = actual_value == expected_value
                except (ValueError, KeyError):
                    logger.error("解析响应JSON失败")
                    is_success = False
            elif success_type == 'regex':
                pattern = success_flag.get('pattern')
                is_success = Extractor.extract_by_regex(response.text, pattern) is not None
            
            if is_success:
                # 提取token
                token_extract = login_config.get('token_extract', {})
                extract_type = token_extract.get('type', 'json_path')
                
                if extract_type == 'json_path':
                    json_path = token_extract.get('path')
                    try:
                        self.token = Extractor.extract_by_jsonpath(response.json(), json_path)
                    except (ValueError, KeyError):
                        logger.warning("提取token失败：响应JSON解析错误")
                        self.token = None
                elif extract_type == 'regex':
                    pattern = token_extract.get('pattern')
                    self.token = Extractor.extract_by_regex(response.text, pattern)
                elif extract_type == 'header':
                    header_name = token_extract.get('name')
                    self.token = response.headers.get(header_name)
                
                # 将token保存到变量管理器
                token_name = token_extract.get('name', 'token')
                if self.token:
                    variable_manager.set_variable(token_name, self.token)
                
                # 保存登录凭据
                self.username = username or login_data.get('username')
                self.password = password or login_data.get('password')
                
                logger.info(f"全局登录成功，token已获取: {self.token[:20] if self.token else 'None'}...")
                return True
            else:
                logger.error(f"全局登录失败: 响应不符合成功条件，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"全局登录异常: {e}")
            return False
    
    def logout(self) -> bool:
        """
        执行登出
        
        Returns:
            登出是否成功
        """
        try:
            # 检查配置中是否有登出配置
            logout_config = self.config.get('logout', {})
            
            if logout_config.get('enabled', False):
                url = logout_config.get('url')
                method = logout_config.get('method', 'POST')
                
                logger.info(f"开始执行登出: {method} {url}")
                
                # 发送登出请求
                if method.upper() == 'POST':
                    response = self.post(url)
                elif method.upper() == 'GET':
                    response = self.get(url)
                else:
                    response = self.request(method, url)
                
                # 检查登出是否成功
                if response.status_code in [200, 204]:
                    logger.info("登出请求成功")
                else:
                    logger.warning(f"登出请求响应码异常: {response.status_code}")
            else:
                logger.info("未配置登出接口，跳过登出请求")
            
            # 清理本地状态
            self.clear_token()
            self.username = None
            self.password = None
            
            logger.info("登出操作完成")
            return True
            
        except Exception as e:
            logger.error(f"登出异常: {e}")
            # 即使登出请求失败，也要清理本地状态
            try:
                self.clear_token()
                self.username = None
                self.password = None
            except:
                pass
            return False
    
    def set_token(self, token: str) -> None:
        """
        手动设置token

        Args:
            token: 认证token
        """
        self.token = token
        variable_manager.set_variable('token', token)
        logger.info(f"手动设置token: {token[:20]}...")

    def clear_token(self) -> None:
        """清除token"""
        self.token = None
        variable_manager.remove_variable('token')
        logger.info("token已清除")

    def close(self) -> None:
        """关闭会话"""
        try:
            if self.session:
                self.session.close()
                self.session = None
                logger.info("API客户端会话已关闭")
        except Exception as e:
            logger.error(f"关闭API客户端会话异常: {e}")
        finally:
            # 清理资源
            self.token = None

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# 全局API客户端实例
api_client = None

def get_api_client() -> APIClient:
    """获取API客户端实例"""
    global api_client
    if api_client is None:
        api_client = APIClient()
    return api_client

def api_request(method: str, url: str, **kwargs) -> requests.Response:
    """API请求便捷函数"""
    return get_api_client().request(method, url, **kwargs)

def api_get(url: str, **kwargs) -> requests.Response:
    """GET请求便捷函数"""
    return get_api_client().get(url, **kwargs)

def api_post(url: str, **kwargs) -> requests.Response:
    """POST请求便捷函数"""
    return get_api_client().post(url, **kwargs)

def api_login() -> bool:
    """执行全局登录便捷函数"""
    return get_api_client().login()