#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试框架主入口程序
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.core.test_framework_app import TestFrameworkApp
from utils.logging.logger import logger

def main():
    """主函数 - 重构后的简化版本"""
    try:
        # 创建并运行测试框架应用
        app = TestFrameworkApp()
        exit_code = app.run()
        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.warning("用户中断执行")
        sys.exit(130)
    except Exception as e:
        logger.error(f"程序执行异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
