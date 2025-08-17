import pytest
import os
import sys
import time
from pathlib import Path

# 设置控制台编码为UTF-8
if sys.platform.startswith('win'):
    import locale
    try:
        # 尝试设置控制台编码
        os.system('chcp 65001 >nul 2>&1')
        # 设置Python的默认编码
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging.logger import logger, logger_manager
from utils.config.parser import get_merged_config
from utils.reporting.notify_helper import send_start_notification, send_test_result_notification


def pytest_configure(config):
    """pytest配置钩子"""
    # 创建必要的目录
    from pathlib import Path
    directories = ['logs', 'reports', 'reports/allure-results', 'reports/html', 'screenshots']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    # 清空截图目录
    try:
        from utils.io.file_helper import FileHelper
        FileHelper.clean_directory('screenshots')
        logger.info("已清空截图目录: screenshots")
    except Exception as e:
        logger.warning(f"清空截图目录失败: {e}")

    # 移除自定义测试结果统计，使用pytest内置统计

    # 发送测试开始通知
    try:
        send_start_notification()
    except Exception as e:
        logger.warning(f"发送开始通知失败: {e}")


def pytest_addoption(parser):
    """添加全局命令行选项"""
    parser.addoption(
        "--env",
        action="store",
        default="test",
        help="指定运行环境 (dev/test/prod)"
    )
    parser.addoption(
        "--test-data-dir",
        action="store",
        default="data",
        help="指定测试数据目录"
    )
    parser.addoption(
        "--test-type",
        action="store",
        default=None,
        choices=["api", "web", "integration", "all"],
        help="指定测试类型 (api/web/integration/all)"
    )


def pytest_sessionstart(session):
    """测试会话开始"""
    logger.info("=" * 60)
    logger.info("测试会话开始")
    logger.info("=" * 60)


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束"""
    # 使用print代替logger避免文件关闭错误
    print("=" * 60)
    print(f"测试会话结束，退出状态: {exitstatus}")
    print("=" * 60)

    # 收集测试结果并发送通知
    try:
        # 从pytest的内置统计获取结果
        if hasattr(session, 'testscollected') and hasattr(session, 'testsfailed'):
            total = session.testscollected
            failed = session.testsfailed
            passed = total - failed

            # 计算通过率
            pass_rate = round((passed / total) * 100, 2) if total > 0 else 0

            test_summary = {
                'total': total,
                'passed': passed,
                'failed': failed,
                'error': 0,  # pytest内置统计不区分error和failed
                'skipped': 0,  # 简化统计
                'pass_rate': pass_rate
            }

            # 判断测试是否成功（无失败）
            success = (failed == 0)

            # 使用print代替logger避免文件关闭错误
            print(f"测试结果统计: 总计={total}, 通过={passed}, 失败={failed}, 通过率={pass_rate}%")

            # 发送测试结果通知
            send_test_result_notification(success, test_summary)
        else:
            print("无法获取测试结果统计")

    except Exception as e:
        print(f"发送测试结果通知失败: {e}")


def pytest_runtest_setup(item):
    """测试用例设置"""
    logger.info(f"开始执行测试: {item.name}")


def pytest_runtest_teardown(item, nextitem):
    """测试用例清理"""
    logger.info(f"测试执行完成: {item.name}")


# 移除有问题的pytest_runtest_makereport hook
# 使用简单的测试结果统计


# 注意：API和Web的具体fixture已移至各自的conftest.py中
# 这里只保留全局共享的fixture

@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    config = get_merged_config()
    logger.info("加载测试配置完成")
    return config


@pytest.fixture
def test_data_loader():
    """测试数据加载器fixture"""
    from utils.data.parser import DataParser

    parser = DataParser()

    def load_data(file_path, case_filter=None):
        return parser.get_test_cases(file_path, case_filter)

    return load_data


@pytest.fixture
def variable_manager():
    """变量管理器fixture"""
    from utils.data.extractor import variable_manager

    variable_manager.clear_variables()
    yield variable_manager
    variable_manager.clear_variables()