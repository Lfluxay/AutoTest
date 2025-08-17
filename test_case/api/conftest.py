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
from utils.config.parser import get_merged_config
from utils.core.api.client import get_api_client
from utils.core.auth.login_manager import APILoginManager


def pytest_addoption(parser):
    """添加API测试专用命令行选项"""
    parser.addoption(
        "--api-base-url",
        action="store",
        default=None,
        help="覆盖API基础URL"
    )
    parser.addoption(
        "--api-timeout",
        action="store",
        type=int,
        default=None,
        help="设置API请求超时时间（秒）"
    )
    parser.addoption(
        "--skip-api-login",
        action="store_true",
        default=False,
        help="跳过API全局登录"
    )


@pytest.fixture(scope="session")
def api_client(request):
    """API客户端fixture - 专用于API测试"""
    config = get_merged_config()
    api_config = config.get('api', {})

    # 应用命令行参数覆盖
    if request.config.getoption("--api-base-url"):
        api_config['base_url'] = request.config.getoption("--api-base-url")
    if request.config.getoption("--api-timeout"):
        api_config['timeout'] = request.config.getoption("--api-timeout")

    client = get_api_client()

    # 检查是否跳过登录
    skip_login = request.config.getoption("--skip-api-login")

    if not skip_login:
        # 使用登录管理器执行全局登录
        login_manager = APILoginManager(client)

        try:
            # 获取用户凭据
            config = get_merged_config()
            users = config.get('test_data', {}).get('users', {})
            user_data = users.get('admin', {})

            success = login_manager.login(
                username=user_data.get('username'),
                password=user_data.get('password')
            )

            if success:
                logger.info("API全局登录成功")
            else:
                logger.warning("API全局登录失败")

        except Exception as e:
            logger.error(f"API全局登录异常: {e}")

    yield client

    # 清理
    try:
        client.logout()
        client.close()
        logger.info("API客户端清理完成")
    except Exception as e:
        logger.warning(f"关闭API客户端异常: {e}")


# 移除pytest_runtest_makereport hook以避免插件冲突
# API响应信息记录功能将通过fixture和测试用例内部实现

@pytest.fixture
def api_response_recorder():
    """API响应记录器fixture - 替代hook方式"""
    responses = []

    def record_response(response):
        """记录API响应"""
        responses.append(response)

        # 如果测试失败，在teardown时附加响应信息
        try:
            import allure
            if response:
                content_type = response.headers.get('content-type', '')
                if content_type.startswith('application/json'):
                    allure.attach(
                        str(response.json()),
                        name="API响应内容",
                        attachment_type=allure.attachment_type.JSON
                    )
                else:
                    allure.attach(
                        response.text,
                        name="API响应内容",
                        attachment_type=allure.attachment_type.TEXT
                    )
                allure.attach(
                    f"状态码: {response.status_code}",
                    name="响应状态码",
                    attachment_type=allure.attachment_type.TEXT
                )
                allure.attach(
                    str(dict(response.headers)),
                    name="响应头",
                    attachment_type=allure.attachment_type.TEXT
                )
        except Exception as e:
            logger.warning(f"记录API响应信息失败: {e}")

    yield record_response

    # 清理
    responses.clear()
