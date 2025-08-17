import pytest
import sys
import os
from pathlib import Path

# 设置控制台编码为UTF-8
if sys.platform.startswith('win'):
    try:
        os.system('chcp 65001 >nul 2>&1')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging.logger import logger
from utils.config.unified_config_manager import get_merged_config
from utils.core.web.browser import get_browser_manager
from utils.core.auth.login_manager import WebLoginManager


def pytest_addoption(parser):
    """添加Web测试专用命令行选项"""
    parser.addoption(
        "--web-browser",
        action="store",
        default=None,
        choices=["chromium", "firefox", "webkit"],
        help="指定浏览器类型 (chromium/firefox/webkit)"
    )
    parser.addoption(
        "--web-headless",
        action="store_true",
        default=None,
        help="启用无头模式"
    )
    parser.addoption(
        "--web-no-headless",
        action="store_true",
        default=False,
        help="禁用无头模式（显示浏览器界面）"
    )
    parser.addoption(
        "--skip-web-login",
        action="store_true",
        default=False,
        help="跳过Web全局登录"
    )


# 移除pytest_configure hook以避免重复定义
# Web测试目录创建功能将在fixture中实现

def _ensure_web_directories():
    """确保Web测试目录存在"""
    directories = ['screenshots/web']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # 清空Web测试截图目录
    try:
        from utils.io.file_helper import FileHelper
        FileHelper.clean_directory('screenshots/web')
        logger.info("已清空Web测试截图目录: screenshots/web")
    except Exception as e:
        logger.warning(f"清空Web测试截图目录失败: {e}")


@pytest.fixture(scope="session")
def browser_manager(request):
    """浏览器管理器fixture - 专用于Web测试"""
    # 确保Web测试目录存在
    _ensure_web_directories()

    config = get_merged_config()
    web_config = config.get('web', {})

    # 应用命令行参数覆盖
    if request.config.getoption("--web-browser"):
        web_config['browser'] = request.config.getoption("--web-browser")
    if request.config.getoption("--web-headless"):
        web_config['headless'] = True
    elif request.config.getoption("--web-no-headless"):
        web_config['headless'] = False

    bm = get_browser_manager()

    # 启动浏览器
    bm.start_browser()

    # 检查是否跳过登录
    skip_login = request.config.getoption("--skip-web-login")

    if not skip_login:
        # 使用登录管理器执行全局登录
        login_manager = WebLoginManager(bm)

        try:
            # 获取用户凭据
            config = get_merged_config()
            users = config.get('test_data', {}).get('users', {})
            user_data = users.get('admin', {})

            # 执行登录
            success = login_manager.login(
                username=user_data.get('username'),
                password=user_data.get('password')
            )

            if success:
                logger.info("Web全局登录成功")
                # 登录成功后导航到目标页面（首页/工作台等）
                login_manager.navigate_to_target_page()
            else:
                logger.warning("Web全局登录失败")

        except Exception as e:
            logger.error(f"Web全局登录异常: {e}")

    yield bm

    # 清理
    try:
        bm.close()
        logger.info("浏览器管理器清理完成")
    except Exception as e:
        logger.warning(f"关闭浏览器异常: {e}")


@pytest.fixture
def page(browser_manager):
    """页面fixture"""
    if browser_manager and browser_manager.page:
        return browser_manager.page
    else:
        pytest.skip("页面未初始化")


@pytest.fixture
def ensure_target_page(browser_manager):
    """确保在目标页面的fixture - 每个测试用例前调用"""
    if not browser_manager or not browser_manager.page:
        pytest.skip("浏览器未初始化")

    # 创建登录管理器并确保在目标页面
    login_manager = WebLoginManager(browser_manager)

    # 确保在目标页面（首页/工作台等）
    success = login_manager.ensure_on_target_page()
    if not success:
        logger.warning("无法确保在目标页面，测试可能受影响")

    return login_manager


# 移除pytest_runtest_makereport hook以避免插件冲突
# Web测试截图功能将通过fixture实现

@pytest.fixture
def web_screenshot_on_failure(browser_manager, request):
    """Web测试失败时自动截图的fixture - 替代hook方式"""
    yield

    # 在测试完成后检查是否失败，如果失败则截图
    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        try:
            import allure
            import time as _t

            if browser_manager and browser_manager.page:
                screenshots_dir = Path('screenshots/web')
                screenshots_dir.mkdir(exist_ok=True)

                # 生成包含测试用例信息的截图文件名
                test_name = request.node.nodeid.replace("::", ".").replace("/", "_").replace("\\", "_")
                path = screenshots_dir / f"failure_{test_name}_{int(_t.time())}.png"

                # 截图 + 采集当前URL与HTML源码
                current_url = browser_manager.page.url
                html_content = browser_manager.page.content()
                browser_manager.page.screenshot(path=str(path), full_page=True)
                logger.info(f"失败截图: {path}")

                with open(path, 'rb') as f:
                    allure.attach(f.read(), name=path.name, attachment_type=allure.attachment_type.PNG)
                allure.attach(current_url, name="当前URL", attachment_type=allure.attachment_type.TEXT)

                try:
                    # 限制HTML大小，避免报告过大
                    snippet = html_content if len(html_content) < 200000 else html_content[:200000] + "\n<!-- truncated -->"
                    allure.attach(snippet, name="页面HTML快照", attachment_type=allure.attachment_type.HTML)
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"失败截图/页面快照附加失败: {e}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """简化的测试报告hook - 仅用于记录测试结果"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
