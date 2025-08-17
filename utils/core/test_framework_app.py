#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试框架应用主类
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any
from utils.logging.logger import logger
from utils.config.unified_config_manager import get_config, get_merged_config
from utils.core.exceptions import AutoTestException, ConfigException
from utils.core.exception_framework import exception_framework, retry_on_error, fallback_on_error


class ArgumentParser:
    """命令行参数解析器"""
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='自动化测试框架',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用示例:
  python main.py --type api                    # 执行API测试
  python main.py --type web                    # 执行Web测试
  python main.py --type both                   # 执行所有测试
  python main.py --tags smoke,regression       # 执行指定标签的测试
  python main.py --modules user,order          # 执行指定模块的测试
  python main.py --report allure               # 生成Allure报告
  python main.py --excel data/test_cases.xlsx  # 执行Excel测试用例
            """
        )
        self._setup_arguments()
    
    def _setup_arguments(self):
        """设置命令行参数"""
        # 测试类型参数
        self.parser.add_argument(
            '--type', '-t',
            choices=['api', 'web', 'both'],
            help='测试类型: api(接口测试), web(Web测试), both(全部测试)'
        )
        
        # 兼容别名，避免文档历史残留导致的使用错误
        self.parser.add_argument(
            '--test-type',
            dest='type',
            choices=['api', 'web', 'both'],
            help='测试类型（兼容别名）'
        )
        
        # 测试标签
        self.parser.add_argument(
            '--tags',
            help='测试标签，多个标签用逗号分隔，如: smoke,regression,critical'
        )
        
        # 测试模块
        self.parser.add_argument(
            '--modules', '-m',
            help='测试模块，多个模块用逗号分隔，如: user,order,payment'
        )
        
        # 报告类型
        self.parser.add_argument(
            '--report', '-r',
            choices=['allure', 'pytest-html', 'both'],
            help='报告类型: allure(Allure报告), pytest-html(HTML报告), both(两种报告)'
        )
        
        # 运行环境
        self.parser.add_argument(
            '--env', '-e',
            help='运行环境: dev, test, prod'
        )
        
        # 配置文件
        self.parser.add_argument(
            '--config', '-c',
            help='自定义配置文件路径'
        )
        
        # Excel测试文件
        self.parser.add_argument(
            '--excel', '-x',
            help='Excel测试文件路径，支持直接执行Excel用例'
        )

        # YAML测试文件
        self.parser.add_argument(
            '--yaml', '-y',
            help='YAML测试文件路径，支持直接执行YAML用例'
        )
        
        # 并发执行
        self.parser.add_argument(
            '--parallel', '-p',
            type=int,
            help='并发执行的进程数，默认为1（串行执行）'
        )
        
        # 详细输出
        self.parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='详细输出模式'
        )
        
        # 调试模式
        self.parser.add_argument(
            '--debug',
            action='store_true',
            help='调试模式，输出更多调试信息'
        )
        
        # 干运行模式
        self.parser.add_argument(
            '--dry-run',
            action='store_true',
            help='干运行模式，只显示将要执行的测试，不实际执行'
        )
        
        # 失败时停止
        self.parser.add_argument(
            '--fail-fast',
            action='store_true',
            help='遇到第一个失败时立即停止'
        )
        
        # 重试次数
        self.parser.add_argument(
            '--retry',
            type=int,
            default=0,
            help='失败用例的重试次数，默认为0'
        )


    
    def parse_args(self) -> argparse.Namespace:
        """解析命令行参数"""
        return self.parser.parse_args()
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """验证参数有效性"""
        try:
            # 验证Excel文件存在性
            if args.excel:
                excel_path = Path(args.excel)
                if not excel_path.exists():
                    logger.error(f"Excel文件不存在: {excel_path}")
                    return False
                if excel_path.suffix.lower() not in ['.xlsx', '.xls']:
                    logger.error(f"不支持的Excel文件格式: {excel_path.suffix}")
                    return False

            # 验证YAML文件存在性
            if args.yaml:
                yaml_path = Path(args.yaml)
                if not yaml_path.exists():
                    logger.error(f"YAML文件不存在: {yaml_path}")
                    return False
                if yaml_path.suffix.lower() not in ['.yaml', '.yml']:
                    logger.error(f"不支持的YAML文件格式: {yaml_path.suffix}")
                    return False
            
            # 验证配置文件存在性
            if args.config:
                config_path = Path(args.config)
                if not config_path.exists():
                    logger.error(f"配置文件不存在: {config_path}")
                    return False
            
            # 验证并发数
            if args.parallel and args.parallel < 1:
                logger.error("并发数必须大于0")
                return False
            
            # 验证重试次数
            if args.retry < 0:
                logger.error("重试次数不能为负数")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"参数验证失败: {e}")
            return False


class TestExecutor:
    """测试执行器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
    
    @retry_on_error(error_code="SYS_002", max_attempts=2, delay=1.0)
    def execute_pytest_tests(
        self,
        test_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        modules: Optional[List[str]] = None,
        report_type: Optional[str] = None,
        parallel: Optional[int] = None,
        verbose: bool = False,
        debug: bool = False,
        dry_run: bool = False,
        fail_fast: bool = False,
        retry: int = 0
    ) -> bool:
        """执行pytest测试"""
        import subprocess
        
        try:
            # 构建pytest命令
            cmd = self._build_pytest_command(
                test_type, tags, modules, report_type,
                parallel, verbose, debug, dry_run, fail_fast, retry
            )
            
            logger.info(f"执行测试命令: {' '.join(cmd)}")
            
            if dry_run:
                logger.info("干运行模式，不实际执行测试")
                return True
            
            # 执行测试（流式输出）
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='ignore'  # 忽略编码错误
            )
            
            # 实时输出日志
            assert process.stdout is not None
            for line in process.stdout:
                logger.info(line.rstrip())
            
            process.wait()
            return_code = process.returncode
            
            success = return_code == 0
            if success:
                logger.info("测试执行成功")
            else:
                logger.error(f"测试执行失败，退出码: {return_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"执行pytest测试失败: {e}")
            raise exception_framework.create_exception("SYS_002", {"details": str(e)})
    
    def _build_pytest_command(
        self,
        test_type: Optional[str],
        tags: Optional[List[str]],
        modules: Optional[List[str]],
        report_type: Optional[str],
        parallel: Optional[int],
        verbose: bool,
        debug: bool,
        dry_run: bool,
        fail_fast: bool,
        retry: int
    ) -> List[str]:
        """构建pytest命令"""
        cmd = ["pytest"]

        # 测试目录
        if test_type == 'api':
            cmd.append("test_case/api")
        elif test_type == 'web':
            cmd.append("test_case/web")
        elif test_type == 'both':
            cmd.append("test_case")
        else:
            cmd.append("test_case")

        # 标签过滤
        if tags:
            tag_expr = " or ".join(tags)
            cmd.extend(["-m", tag_expr])

        # 模块过滤
        if modules:
            for module in modules:
                cmd.extend(["-k", module])

        # 报告配置
        if report_type in ['allure', 'both']:
            cmd.extend(["--alluredir", "reports/allure-results"])

        if report_type in ['pytest-html', 'both']:
            cmd.extend(["--html", "reports/html/report.html", "--self-contained-html"])

        # 并发执行
        if parallel and parallel > 1:
            cmd.extend(["-n", str(parallel)])

        # 输出详细程度
        if verbose:
            cmd.append("-v")

        if debug:
            cmd.append("-s")
            cmd.append("--tb=long")

        # 干运行
        if dry_run:
            cmd.append("--collect-only")

        # 失败时停止
        if fail_fast:
            cmd.append("-x")

        # 重试配置
        if retry > 0:
            cmd.extend(["--reruns", str(retry)])

        return cmd
    
    @fallback_on_error(fallback_value=(0, 0), error_code="FILE_002")
    def execute_excel_tests(
        self,
        excel_path: str,
        modules: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        dry_run: bool = False
    ) -> tuple[int, int]:
        """执行Excel测试用例"""
        try:
            from utils.testing.excel_runner import ExcelTestRunner
            from utils.core.base.test_base import DataDrivenTestBase

            logger.info(f"开始执行Excel测试: {excel_path}")

            # 创建Excel测试运行器
            excel_runner = ExcelTestRunner()

            # 解析Excel文件为测试套件
            test_suite = excel_runner.parse_to_test_suite(excel_path, modules, tags)

            logger.info(f"解析到 {len(test_suite.test_cases)} 个测试用例")

            # 如果是干运行模式，只显示测试用例信息
            if dry_run:
                logger.info("干运行模式，显示测试用例信息:")
                for i, test_case in enumerate(test_suite.test_cases, 1):
                    logger.info(f"  {i}. {test_case.case_name} ({test_case.case_type.value})")
                return len(test_suite.test_cases), len(test_suite.test_cases)

            # 执行测试用例
            test_base = DataDrivenTestBase()
            success_count = 0
            total_count = len(test_suite.test_cases)

            for test_case in test_suite.test_cases:
                # 将TestCase对象转换为字典格式
                case_dict = {
                    'case_name': test_case.case_name,
                    'description': test_case.description,
                    'tags': test_case.tags,
                    'severity': test_case.severity
                }

                # 添加请求信息
                if test_case.request:
                    case_dict['request'] = {
                        'method': test_case.request.method,
                        'url': test_case.request.url,
                        'headers': test_case.request.headers,
                        'data': test_case.request.data,
                        'params': test_case.request.params
                    }

                # 添加断言信息
                if test_case.assertions:
                    case_dict['assertions'] = [
                        {
                            'type': assertion.type,
                            'expected': assertion.expected,
                            'path': assertion.path,
                            'operator': assertion.operator,
                            'message': assertion.message
                        }
                        for assertion in test_case.assertions
                    ]

                # 执行测试用例
                result = test_base.execute_test_case(case_dict)
                if result['status'] == 'PASS':
                    success_count += 1

            logger.info(f"Excel测试执行完成: 成功 {success_count}/{total_count}")

            return success_count, total_count

        except Exception as e:
            logger.error(f"执行Excel测试失败: {e}")
            raise exception_framework.create_exception("FILE_002", {"excel_path": excel_path, "error": str(e)})

    @fallback_on_error(fallback_value=(0, 0), error_code="FILE_004")
    def execute_yaml_tests(
        self,
        yaml_path: str,
        modules: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        dry_run: bool = False
    ) -> tuple[int, int]:
        """执行YAML测试用例"""
        try:
            from utils.core.base.test_base import DataDrivenTestBase

            logger.info(f"开始执行YAML测试: {yaml_path}")

            # 创建数据驱动测试基类实例
            test_base = DataDrivenTestBase()

            # 如果是干运行模式，只显示测试用例信息
            if dry_run:
                logger.info("干运行模式，显示YAML测试用例信息:")
                logger.info(f"  YAML文件: {yaml_path}")
                return 1, 1

            # 执行YAML测试用例
            test_base.run_data_driven_tests(yaml_path)

            # 获取测试总结
            summary = test_base.get_test_summary()

            success_count = summary['passed']
            total_count = summary['total']

            logger.info(f"YAML测试执行完成: 成功 {success_count}/{total_count}")

            return success_count, total_count

        except Exception as e:
            logger.error(f"执行YAML测试失败: {e}")
            raise exception_framework.create_exception("FILE_004", {"yaml_path": yaml_path, "error": str(e)})


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.reports_dir = self.project_root / "reports"
    
    @retry_on_error(error_code="FILE_003", max_attempts=2, delay=0.5)
    def generate_reports(self, report_type: Optional[str], success: bool):
        """生成测试报告"""
        try:
            if not report_type:
                return
            
            # 确保报告目录存在
            self.reports_dir.mkdir(exist_ok=True)
            
            if report_type in ['allure', 'both']:
                self._generate_allure_report()
            
            if report_type in ['pytest-html', 'both']:
                self._generate_html_report()
            
            # 生成摘要报告
            self._generate_summary_report(success)
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            raise exception_framework.create_exception("FILE_003", {"error": str(e)})
    
    def _generate_allure_report(self):
        """生成Allure报告"""
        import subprocess
        
        try:
            allure_results = self.reports_dir / "allure-results"
            allure_report = self.reports_dir / "allure-report"
            
            if allure_results.exists() and any(allure_results.iterdir()):
                cmd = ["allure", "generate", str(allure_results), "-o", str(allure_report), "--clean"]
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                logger.info(f"Allure报告生成成功: {allure_report}")
            else:
                logger.warning("没有找到Allure测试结果，跳过报告生成")
                
        except subprocess.CalledProcessError as e:
            logger.warning(f"Allure报告生成失败: {e}")
        except FileNotFoundError:
            logger.warning("Allure命令未找到，请确保已安装Allure")
    
    def _generate_html_report(self):
        """生成HTML报告"""
        html_report = self.reports_dir / "html" / "report.html"
        if html_report.exists():
            logger.info(f"HTML报告已生成: {html_report}")
        else:
            logger.warning("HTML报告文件不存在")
    
    def _generate_summary_report(self, success: bool):
        """生成摘要报告"""
        import json
        from datetime import datetime
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "reports": {
                "allure": str(self.reports_dir / "allure-report" / "index.html"),
                "html": str(self.reports_dir / "html" / "report.html")
            }
        }
        
        summary_file = self.reports_dir / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"摘要报告已生成: {summary_file}")


class NotificationSender:
    """通知发送器"""
    
    def __init__(self):
        self.config = get_merged_config()
        self.notification_config = self.config.get('notification', {})
    
    @fallback_on_error(fallback_value=None, error_code="NETWORK_003")
    def send_notifications(self, success: bool, summary: Dict[str, Any] = None):
        """发送测试结果通知"""
        try:
            if not self.notification_config.get('enabled', False):
                logger.debug("通知功能未启用")
                return
            
            # 准备通知内容
            status = "成功" if success else "失败"
            title = f"自动化测试执行{status}"
            
            message = f"测试执行{status}"
            if summary:
                message += f"\n详细信息: {summary}"
            
            # 发送邮件通知
            if self.notification_config.get('email', {}).get('enabled', False):
                self._send_email_notification(title, message)
            
            # 发送钉钉通知
            if self.notification_config.get('dingtalk', {}).get('enabled', False):
                self._send_dingtalk_notification(title, message)
            
            # 发送企业微信通知
            if self.notification_config.get('wechat', {}).get('enabled', False):
                self._send_wechat_notification(title, message)
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            # 通知失败不应该影响主流程，所以不抛出异常
    
    def _send_email_notification(self, title: str, message: str):
        """发送邮件通知"""
        # 实现邮件发送逻辑
        logger.info(f"邮件通知: {title}")
    
    def _send_dingtalk_notification(self, title: str, message: str):
        """发送钉钉通知"""
        # 实现钉钉通知逻辑
        logger.info(f"钉钉通知: {title}")
    
    def _send_wechat_notification(self, title: str, message: str):
        """发送企业微信通知"""
        # 实现企业微信通知逻辑
        logger.info(f"企业微信通知: {title}")


class TestFrameworkApp:
    """测试框架应用主类"""
    
    def __init__(self):
        self.arg_parser = ArgumentParser()
        self.test_executor = TestExecutor()
        self.report_generator = ReportGenerator()
        self.notification_sender = NotificationSender()
    
    def run(self) -> int:
        """运行测试框架"""
        try:
            # 解析命令行参数
            args = self.arg_parser.parse_args()

            # 验证参数
            if not self.arg_parser.validate_args(args):
                return 1



            # 设置环境变量
            if args.env:
                os.environ['ENV'] = args.env

            # 设置日志级别
            if args.debug:
                logger.info("调试模式已启用")
            
            # 执行测试
            logger.info("=" * 60)
            logger.info("自动化测试框架启动")
            logger.info("=" * 60)
            
            success = self._execute_tests(args)
            
            # 生成报告
            self.report_generator.generate_reports(args.report, success)
            
            # 发送通知
            self.notification_sender.send_notifications(success)
            
            # 输出结果
            if success:
                logger.info("=" * 60)
                logger.info("测试执行完成 - 成功")
                logger.info("=" * 60)
                return 0
            else:
                logger.error("=" * 60)
                logger.error("测试执行完成 - 失败")
                logger.error("=" * 60)
                return 1
                
        except KeyboardInterrupt:
            logger.warning("用户中断执行")
            return 130
        except Exception as e:
            logger.error(f"测试框架执行异常: {e}")
            return 1
    
    def _execute_tests(self, args: argparse.Namespace) -> bool:
        """执行测试"""
        # Excel测试模式
        if args.excel:
            modules = args.modules.split(',') if args.modules else None
            tags = args.tags.split(',') if args.tags else None

            success_count, total_count = self.test_executor.execute_excel_tests(
                args.excel, modules, tags, args.dry_run
            )

            return success_count == total_count

        # YAML测试模式
        elif args.yaml:
            modules = args.modules.split(',') if args.modules else None
            tags = args.tags.split(',') if args.tags else None

            success_count, total_count = self.test_executor.execute_yaml_tests(
                args.yaml, modules, tags, args.dry_run
            )

            return success_count == total_count

        # pytest测试模式
        else:
            tags = args.tags.split(',') if args.tags else None
            modules = args.modules.split(',') if args.modules else None
            
            return self.test_executor.execute_pytest_tests(
                test_type=args.type,
                tags=tags,
                modules=modules,
                report_type=args.report,
                parallel=args.parallel,
                verbose=args.verbose,
                debug=args.debug,
                dry_run=args.dry_run,
                fail_fast=args.fail_fast,
                retry=args.retry
            )


