"""
银行系统自定义工作流插件示例
"""
from common.workflow.step_chain import StepChain
from utils.logging.logger import logger


def create_custom_banking_workflow(client_type: str, client=None, **kwargs):
    """
    创建银行系统自定义工作流
    
    这个工作流包含银行系统特有的复杂登录和验证流程
    """
    chain = StepChain('custom_banking', client_type, client)
    
    # 获取参数
    bank_code = kwargs.get('bank_code', 'BANK001')
    branch_code = kwargs.get('branch_code', 'BR001')
    user_level = kwargs.get('user_level', 'teller')
    
    # 添加银行系统特有的步骤
    chain.add_step(
        step_name="银行系统登录",
        step_func=banking_login_step,
        cache_key=f"banking_login_{bank_code}",
        skip_if_cached=True,
        bank_code=bank_code
    )
    
    chain.add_step(
        step_name="双因子认证",
        step_func=banking_two_factor_auth_step,
        cache_key=f"banking_2fa_{bank_code}",
        skip_if_cached=True
    )
    
    chain.add_step(
        step_name="选择分行",
        step_func=banking_select_branch_step,
        cache_key=f"banking_branch_{branch_code}",
        skip_if_cached=True,
        branch_code=branch_code
    )
    
    chain.add_step(
        step_name="验证用户权限",
        step_func=banking_verify_permissions_step,
        cache_key=f"banking_permissions_{user_level}",
        skip_if_cached=True,
        user_level=user_level
    )
    
    chain.add_step(
        step_name="初始化工作台",
        step_func=banking_init_workspace_step,
        cache_key="banking_workspace",
        skip_if_cached=False  # 工作台每次都要初始化
    )
    
    return chain


def banking_login_step(client=None, context=None, bank_code=None, **kwargs):
    """银行系统登录步骤"""
    try:
        if client_type := getattr(client, 'client_type', 'web') == 'web':
            return _banking_web_login(client, context, bank_code, **kwargs)
        else:
            return _banking_api_login(client, context, bank_code, **kwargs)
    except Exception as e:
        logger.error(f"银行系统登录异常: {e}")
        return False


def _banking_web_login(client, context, bank_code, **kwargs):
    """银行系统Web登录"""
    try:
        page = client.page
        
        # 导航到银行登录页面
        login_url = f"https://banking.example.com/{bank_code}/login"
        page.goto(login_url)
        
        # 等待页面加载
        page.wait_for_selector('#bank-login-form')
        
        # 填写银行代码
        page.fill('#bank-code', bank_code)
        
        # 填写用户凭据
        username = kwargs.get('username') or context.get('username')
        password = kwargs.get('password') or context.get('password')
        
        page.fill('#username', username)
        page.fill('#password', password)
        
        # 点击登录
        page.click('#login-btn')
        
        # 等待登录成功
        page.wait_for_selector('.login-success', timeout=15000)
        
        context['banking_logged_in'] = True
        context['bank_code'] = bank_code
        logger.info(f"银行系统Web登录成功: {bank_code}")
        return True
        
    except Exception as e:
        logger.error(f"银行系统Web登录失败: {e}")
        return False


def _banking_api_login(client, context, bank_code, **kwargs):
    """银行系统API登录"""
    try:
        # 银行API登录
        login_data = {
            'bank_code': bank_code,
            'username': kwargs.get('username') or context.get('username'),
            'password': kwargs.get('password') or context.get('password'),
            'client_type': 'api'
        }
        
        response = client.post('/api/banking/auth/login', json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            
            if token:
                # 设置认证头
                client.session.headers['Authorization'] = f'Bearer {token}'
                context['banking_api_token'] = token
                context['bank_code'] = bank_code
                logger.info(f"银行系统API登录成功: {bank_code}")
                return True
        
        logger.error(f"银行系统API登录失败: {response.status_code}")
        return False
        
    except Exception as e:
        logger.error(f"银行系统API登录异常: {e}")
        return False


def banking_two_factor_auth_step(client=None, context=None, **kwargs):
    """银行双因子认证步骤"""
    try:
        if hasattr(client, 'page'):
            # Web端双因子认证
            page = client.page
            
            # 等待双因子认证页面
            page.wait_for_selector('#two-factor-form')
            
            # 模拟获取验证码（实际项目中可能需要从短信或邮件获取）
            verification_code = kwargs.get('verification_code', '123456')
            
            # 填写验证码
            page.fill('#verification-code', verification_code)
            page.click('#verify-btn')
            
            # 等待验证成功
            page.wait_for_selector('.auth-success')
            
        else:
            # API端双因子认证
            auth_data = {
                'verification_code': kwargs.get('verification_code', '123456')
            }
            
            response = client.post('/api/banking/auth/verify', json=auth_data)
            
            if response.status_code != 200:
                logger.error(f"API双因子认证失败: {response.status_code}")
                return False
        
        context['two_factor_verified'] = True
        logger.info("银行双因子认证成功")
        return True
        
    except Exception as e:
        logger.error(f"银行双因子认证异常: {e}")
        return False


def banking_select_branch_step(client=None, context=None, branch_code=None, **kwargs):
    """选择银行分行步骤"""
    try:
        if hasattr(client, 'page'):
            # Web端选择分行
            page = client.page
            
            # 等待分行选择器
            page.wait_for_selector('#branch-selector')
            
            # 选择分行
            page.select_option('#branch-selector', branch_code)
            
            # 确认选择
            page.click('#confirm-branch')
            
            # 等待分行切换完成
            page.wait_for_selector(f'.current-branch[data-branch="{branch_code}"]')
            
        else:
            # API端设置分行上下文
            branch_data = {
                'branch_code': branch_code
            }
            
            response = client.post('/api/banking/context/branch', json=branch_data)
            
            if response.status_code != 200:
                logger.error(f"API设置分行失败: {response.status_code}")
                return False
        
        context['selected_branch'] = branch_code
        logger.info(f"银行分行选择成功: {branch_code}")
        return True
        
    except Exception as e:
        logger.error(f"银行分行选择异常: {e}")
        return False


def banking_verify_permissions_step(client=None, context=None, user_level=None, **kwargs):
    """验证银行用户权限步骤"""
    try:
        if hasattr(client, 'page'):
            # Web端权限验证
            page = client.page
            
            # 检查用户权限标识
            permission_selector = f'.user-permissions[data-level="{user_level}"]'
            
            if page.is_visible(permission_selector):
                context['user_permissions_verified'] = True
                logger.info(f"银行用户权限验证成功: {user_level}")
                return True
            else:
                logger.error(f"银行用户权限不足: {user_level}")
                return False
                
        else:
            # API端权限验证
            response = client.get('/api/banking/user/permissions')
            
            if response.status_code == 200:
                data = response.json()
                user_permissions = data.get('permissions', [])
                
                if user_level in user_permissions:
                    context['user_permissions_verified'] = True
                    logger.info(f"银行API用户权限验证成功: {user_level}")
                    return True
                else:
                    logger.error(f"银行API用户权限不足: {user_level}")
                    return False
            else:
                logger.error(f"银行API权限查询失败: {response.status_code}")
                return False
        
    except Exception as e:
        logger.error(f"银行用户权限验证异常: {e}")
        return False


def banking_init_workspace_step(client=None, context=None, **kwargs):
    """初始化银行工作台步骤"""
    try:
        if hasattr(client, 'page'):
            # Web端工作台初始化
            page = client.page
            
            # 导航到工作台
            page.goto('/banking/workspace')
            
            # 等待工作台加载
            page.wait_for_selector('.workspace-dashboard')
            
            # 检查必要的工作台组件
            required_components = ['.account-summary', '.transaction-panel', '.customer-search']
            
            for component in required_components:
                if not page.is_visible(component):
                    logger.error(f"工作台组件未加载: {component}")
                    return False
            
        else:
            # API端工作台初始化
            response = client.get('/api/banking/workspace/init')
            
            if response.status_code != 200:
                logger.error(f"API工作台初始化失败: {response.status_code}")
                return False
            
            # 验证工作台数据
            data = response.json()
            if not data.get('workspace_ready'):
                logger.error("API工作台未就绪")
                return False
        
        context['workspace_initialized'] = True
        logger.info("银行工作台初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"银行工作台初始化异常: {e}")
        return False
