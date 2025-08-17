"""
API测试通用Fixtures
"""
import pytest
from utils.logging.logger import logger
from utils.config.parser import get_merged_config
from utils.core.api.client import get_api_client
from common.auth.global_login import GlobalLoginManager
from common.auth.session_manager import SessionManager
from common.navigation.navigator import NavigationManager


@pytest.fixture(scope="session")
def global_api_session(request):
    """
    全局API会话 - session级别，支持会话复用
    """
    config = get_merged_config()
    api_config = config.get('api', {})
    
    # 应用命令行参数覆盖
    if request.config.getoption("--api-base-url", default=None):
        api_config['base_url'] = request.config.getoption("--api-base-url")
    if request.config.getoption("--api-timeout", default=None):
        api_config['timeout'] = request.config.getoption("--api-timeout")
    
    # 创建API客户端
    api_client = get_api_client(api_config)
    
    # 创建会话管理器
    session_manager = SessionManager("global_api")
    
    # 创建全局登录管理器
    login_manager = GlobalLoginManager('api', api_client)
    
    # 检查是否跳过登录
    skip_login = request.config.getoption("--skip-api-login", default=False)
    
    if not skip_login:
        # 检查是否有有效会话
        if session_manager.is_session_valid('api'):
            logger.info("使用现有API会话")
            session_data = session_manager.get_session('api')
            # 验证会话是否仍然有效
            if login_manager.is_logged_in():
                logger.info("API会话验证成功")
            else:
                logger.info("API会话已失效，重新登录")
                skip_login = False
        
        if not skip_login:
            # 执行登录
            success = login_manager.login()
            if success:
                logger.info("API全局登录成功")
                
                # 保存会话
                session_data = session_manager.create_session_data('api', login_manager.get_manager())
                session_manager.save_session('api', session_data)
            else:
                logger.warning("API全局登录失败")
    
    # 创建会话对象
    session = {
        'api_client': api_client,
        'login_manager': login_manager,
        'session_manager': session_manager
    }
    
    yield session
    
    # 清理
    try:
        if api_client:
            api_client.logout()
            api_client.close()
        logger.info("API全局会话清理完成")
    except Exception as e:
        logger.warning(f"API全局会话清理异常: {e}")


@pytest.fixture
def api_login_manager(global_api_session):
    """
    API登录管理器fixture
    """
    return global_api_session['login_manager']


@pytest.fixture
def api_navigator(global_api_session):
    """
    API导航管理器fixture
    """
    api_client = global_api_session['api_client']
    return NavigationManager('api', api_client)


@pytest.fixture
def api_client(global_api_session):
    """
    API客户端fixture
    """
    client = global_api_session.get('api_client')
    if not client:
        pytest.skip("API客户端未初始化")
    return client


@pytest.fixture
def enterprise_ready_api_session(global_api_session):
    """
    企业就绪的API会话 - 完成企业工作流的会话
    """
    from common.workflow.enterprise_workflow import EnterpriseWorkflow

    api_client = global_api_session['api_client']

    # 创建并执行企业工作流
    workflow = EnterpriseWorkflow(
        client_type='api',
        client=api_client
    )

    success = workflow.execute()
    if not success:
        logger.warning("API企业工作流执行失败，可能影响测试")

    # 扩展会话信息
    session = global_api_session.copy()
    session['enterprise_workflow'] = workflow
    session['workflow_ready'] = success

    return session


@pytest.fixture
def universal_ready_api_session(global_api_session, request):
    """
    通用工作流就绪的API会话 - 支持多种工作流类型
    """
    from common.workflow.workflow_factory import workflow_factory

    api_client = global_api_session['api_client']

    # 从测试标记或参数获取工作流名称
    workflow_name = getattr(request, 'param', 'api_service')  # 默认使用api_service模板

    # 也可以从pytest标记获取
    if hasattr(request.node, 'get_closest_marker'):
        marker = request.node.get_closest_marker('workflow')
        if marker and marker.args:
            workflow_name = marker.args[0]

    # 执行通用工作流
    success = workflow_factory.execute_workflow(
        workflow_name=workflow_name,
        client_type='api',
        client=api_client,
        username='api_user',
        password='api_pass'
    )

    if not success:
        logger.warning(f"通用API工作流 {workflow_name} 执行失败，可能影响测试")

    # 扩展会话信息
    session = global_api_session.copy()
    session['workflow_name'] = workflow_name
    session['workflow_ready'] = success

    return session


@pytest.fixture(autouse=True)
def api_test_setup_teardown(request, global_api_session):
    """
    API测试的自动setup/teardown
    """
    # Setup
    test_name = request.node.name
    logger.info(f"开始API测试: {test_name}")

    # 更新会话时间戳
    session_manager = global_api_session['session_manager']
    session_manager.update_session_timestamp('api')

    yield

    # Teardown
    logger.info(f"完成API测试: {test_name}")


def pytest_runtest_makereport(item, call):
    """API测试失败时记录响应信息"""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        try:
            import allure
            
            # 尝试获取API客户端
            if hasattr(item, 'funcargs') and 'global_api_session' in item.funcargs:
                session = item.funcargs['global_api_session']
                api_client = session.get('api_client')
                
                # 尝试获取最后的API响应信息
                if api_client and hasattr(api_client, 'last_response'):
                    response = api_client.last_response
                    if response:
                        # 响应内容
                        content_type = response.headers.get('content-type', '')
                        if content_type.startswith('application/json'):
                            try:
                                content = str(response.json())
                                attachment_type = allure.attachment_type.JSON
                            except:
                                content = response.text
                                attachment_type = allure.attachment_type.TEXT
                        else:
                            content = response.text
                            attachment_type = allure.attachment_type.TEXT
                        
                        allure.attach(content, name="API响应内容", attachment_type=attachment_type)
                        allure.attach(f"状态码: {response.status_code}", name="响应状态码", attachment_type=allure.attachment_type.TEXT)
                        allure.attach(str(dict(response.headers)), name="响应头", attachment_type=allure.attachment_type.TEXT)
                        
                        # 请求信息
                        if hasattr(response, 'request'):
                            request_info = f"URL: {response.request.url}\nMethod: {response.request.method}"
                            if response.request.body:
                                request_info += f"\nBody: {response.request.body}"
                            allure.attach(request_info, name="请求信息", attachment_type=allure.attachment_type.TEXT)
                            
        except Exception as e:
            logger.warning(f"API失败信息附加失败: {e}")
