"""
Web测试通用Fixtures
"""
import pytest
from utils.logging.logger import logger
from utils.config.parser import get_merged_config
from utils.core.web.browser import get_browser_manager
from common.auth.global_login import GlobalLoginManager
from common.auth.session_manager import SessionManager
from common.navigation.navigator import NavigationManager


@pytest.fixture(scope="session")
def global_web_session(request):
    """
    全局Web会话 - session级别，支持会话复用
    """
    config = get_merged_config()
    web_config = config.get('web', {})
    
    # 应用命令行参数覆盖
    if request.config.getoption("--web-browser", default=None):
        web_config['browser'] = request.config.getoption("--web-browser")
    if request.config.getoption("--web-headless", default=None):
        web_config['headless'] = True
    elif request.config.getoption("--web-no-headless", default=False):
        web_config['headless'] = False
    
    # 创建浏览器管理器
    browser_manager = get_browser_manager(web_config)
    browser_manager.start_browser()
    
    # 创建会话管理器
    session_manager = SessionManager("global_web")
    
    # 创建全局登录管理器
    login_manager = GlobalLoginManager('web', browser_manager)
    
    # 检查是否跳过登录
    skip_login = request.config.getoption("--skip-web-login", default=False)
    
    if not skip_login:
        # 检查是否有有效会话
        if session_manager.is_session_valid('web'):
            logger.info("使用现有Web会话")
            session_data = session_manager.get_session('web')
            # 验证会话是否仍然有效
            if login_manager.is_logged_in():
                logger.info("Web会话验证成功")
            else:
                logger.info("Web会话已失效，重新登录")
                skip_login = False
        
        if not skip_login:
            # 执行登录
            success = login_manager.login()
            if success:
                logger.info("Web全局登录成功")
                # 导航到目标页面
                login_manager.navigate_to_target_page()
                
                # 保存会话
                session_data = session_manager.create_session_data('web', login_manager.get_manager())
                session_manager.save_session('web', session_data)
            else:
                logger.warning("Web全局登录失败")
    
    # 创建会话对象
    session = {
        'browser_manager': browser_manager,
        'login_manager': login_manager,
        'session_manager': session_manager,
        'page': browser_manager.page if browser_manager else None
    }
    
    yield session
    
    # 清理
    try:
        if browser_manager:
            browser_manager.close()
        logger.info("Web全局会话清理完成")
    except Exception as e:
        logger.warning(f"Web全局会话清理异常: {e}")


@pytest.fixture
def web_login_manager(global_web_session):
    """
    Web登录管理器fixture
    """
    return global_web_session['login_manager']


@pytest.fixture  
def web_navigator(global_web_session):
    """
    Web导航管理器fixture
    """
    browser_manager = global_web_session['browser_manager']
    return NavigationManager('web', browser_manager)


@pytest.fixture
def web_page(global_web_session):
    """
    Web页面对象fixture
    """
    page = global_web_session.get('page')
    if not page:
        pytest.skip("Web页面未初始化")
    return page


@pytest.fixture
def ensure_web_target_page(global_web_session):
    """
    确保在Web目标页面的fixture - 每个测试用例前调用
    """
    login_manager = global_web_session['login_manager']

    # 确保在目标页面
    success = login_manager.ensure_on_target_page()
    if not success:
        logger.warning("无法确保在Web目标页面，测试可能受影响")

    return login_manager


@pytest.fixture
def enterprise_ready_web_session(global_web_session):
    """
    企业就绪的Web会话 - 完成企业工作流的会话
    """
    from common.workflow.enterprise_workflow import EnterpriseWorkflow

    browser_manager = global_web_session['browser_manager']

    # 创建并执行企业工作流
    workflow = EnterpriseWorkflow(
        client_type='web',
        client=browser_manager
    )

    success = workflow.execute()
    if not success:
        logger.warning("企业工作流执行失败，可能影响测试")

    # 扩展会话信息
    session = global_web_session.copy()
    session['enterprise_workflow'] = workflow
    session['workflow_ready'] = success

    return session


@pytest.fixture
def universal_ready_web_session(global_web_session, request):
    """
    通用工作流就绪的Web会话 - 支持多种工作流类型
    """
    from common.workflow.workflow_factory import workflow_factory

    browser_manager = global_web_session['browser_manager']

    # 从测试标记或参数获取工作流名称
    workflow_name = getattr(request, 'param', 'saas_platform')  # 默认使用saas_platform模板

    # 也可以从pytest标记获取
    if hasattr(request.node, 'get_closest_marker'):
        marker = request.node.get_closest_marker('workflow')
        if marker and marker.args:
            workflow_name = marker.args[0]

    # 执行通用工作流
    success = workflow_factory.execute_workflow(
        workflow_name=workflow_name,
        client_type='web',
        client=browser_manager,
        username='test_user',
        password='test_pass'
    )

    if not success:
        logger.warning(f"通用工作流 {workflow_name} 执行失败，可能影响测试")

    # 扩展会话信息
    session = global_web_session.copy()
    session['workflow_name'] = workflow_name
    session['workflow_ready'] = success

    return session


@pytest.fixture(autouse=True)
def web_test_setup_teardown(request, global_web_session):
    """
    Web测试的自动setup/teardown
    """
    # Setup
    test_name = request.node.name
    logger.info(f"开始Web测试: {test_name}")
    
    # 更新会话时间戳
    session_manager = global_web_session['session_manager']
    session_manager.update_session_timestamp('web')
    
    yield
    
    # Teardown
    logger.info(f"完成Web测试: {test_name}")


def pytest_runtest_makereport(item, call):
    """Web测试失败时自动截图"""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        try:
            import allure
            from pathlib import Path
            import time as _t
            
            # 尝试获取浏览器管理器
            if hasattr(item, 'funcargs') and 'global_web_session' in item.funcargs:
                session = item.funcargs['global_web_session']
                browser_manager = session.get('browser_manager')
                
                if browser_manager and browser_manager.page:
                    screenshots_dir = Path('screenshots/web')
                    screenshots_dir.mkdir(exist_ok=True)
                    
                    # 生成截图文件名
                    test_name = item.nodeid.replace("::", ".").replace("/", "_").replace("\\", "_")
                    path = screenshots_dir / f"failure_{test_name}_{int(_t.time())}.png"
                    
                    # 截图和信息收集
                    current_url = browser_manager.page.url
                    html_content = browser_manager.page.content()
                    browser_manager.page.screenshot(path=str(path), full_page=True)
                    logger.info(f"失败截图: {path}")
                    
                    # 附加到allure报告
                    with open(path, 'rb') as f:
                        allure.attach(f.read(), name=path.name, attachment_type=allure.attachment_type.PNG)
                    allure.attach(current_url, name="当前URL", attachment_type=allure.attachment_type.TEXT)
                    
                    # 限制HTML大小
                    snippet = html_content if len(html_content) < 200000 else html_content[:200000] + "\n<!-- truncated -->"
                    allure.attach(snippet, name="页面HTML快照", attachment_type=allure.attachment_type.HTML)
                    
        except Exception as e:
            logger.warning(f"Web失败截图附加失败: {e}")
