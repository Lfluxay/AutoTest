import os
import subprocess
import json
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logging.logger import logger
from utils.config_parser import config, get_merged_config


class ReportHelper:
    """报告生成辅助工具"""
    
    def __init__(self):
        self.config = get_merged_config()
        self.reports_dir = config.get_reports_dir()
        self.allure_results_dir = self.reports_dir / "allure-results"
        self.allure_report_dir = self.reports_dir / "allure-report"
        self.html_report_dir = self.reports_dir / "html"
        
    def generate_allure_report(self) -> bool:
        """
        生成Allure报告
        
        Returns:
            生成是否成功
        """
        try:
            if not self.allure_results_dir.exists() or not list(self.allure_results_dir.glob("*")):
                logger.warning("Allure结果目录为空，跳过报告生成")
                return False
            
            logger.info("开始生成Allure报告...")
            
            # 确保报告目录存在
            self.allure_report_dir.mkdir(parents=True, exist_ok=True)
            
            # 执行allure generate命令
            cmd = [
                "allure", "generate", 
                str(self.allure_results_dir),
                "-o", str(self.allure_report_dir),
                "--clean"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Allure报告生成成功: {self.allure_report_dir}")
                return True
            else:
                logger.error(f"Allure报告生成失败: {result.stderr}")
                return False
                
        except FileNotFoundError:
            logger.error("Allure命令未找到，请确保已安装Allure")
            return False
        except Exception as e:
            logger.error(f"生成Allure报告异常: {e}")
            return False
    
    def serve_allure_report(self, port: int = 0) -> bool:
        """
        启动Allure报告服务
        
        Args:
            port: 服务端口，0表示自动分配
            
        Returns:
            启动是否成功
        """
        try:
            if not self.allure_report_dir.exists():
                logger.error("Allure报告目录不存在，请先生成报告")
                return False
            
            logger.info("启动Allure报告服务...")
            
            cmd = ["allure", "serve", str(self.allure_results_dir)]
            if port > 0:
                cmd.extend(["--port", str(port)])
            
            # 在后台启动服务
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            logger.info("Allure报告服务启动成功")
            return True
            
        except FileNotFoundError:
            logger.error("Allure命令未找到，请确保已安装Allure")
            return False
        except Exception as e:
            logger.error(f"启动Allure报告服务异常: {e}")
            return False
    
    def generate_custom_html_report(self, test_results: List[Dict[str, Any]], 
                                  template_path: str = None) -> str:
        """
        生成自定义HTML报告
        
        Args:
            test_results: 测试结果数据
            template_path: 模板文件路径
            
        Returns:
            报告文件路径
        """
        try:
            from jinja2 import Template, Environment, FileSystemLoader
            
            # 准备报告数据
            report_data = self._prepare_report_data(test_results)
            
            # 加载模板
            if template_path and Path(template_path).exists():
                env = Environment(loader=FileSystemLoader(Path(template_path).parent))
                template = env.get_template(Path(template_path).name)
            else:
                # 使用默认模板
                template = Template(self._get_default_html_template())
            
            # 渲染报告
            html_content = template.render(**report_data)
            
            # 保存报告
            self.html_report_dir.mkdir(parents=True, exist_ok=True)
            report_file = self.html_report_dir / "custom_report.html"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"自定义HTML报告生成成功: {report_file}")
            return str(report_file)
            
        except ImportError:
            logger.error("jinja2库未安装，无法生成自定义HTML报告")
            return ""
        except Exception as e:
            logger.error(f"生成自定义HTML报告异常: {e}")
            return ""
    
    def generate_json_report(self, test_results: List[Dict[str, Any]]) -> str:
        """
        生成JSON格式报告
        
        Args:
            test_results: 测试结果数据
            
        Returns:
            报告文件路径
        """
        try:
            report_data = self._prepare_report_data(test_results)
            
            # 保存JSON报告
            json_report_file = self.reports_dir / "test_report.json"
            
            with open(json_report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"JSON报告生成成功: {json_report_file}")
            return str(json_report_file)
            
        except Exception as e:
            logger.error(f"生成JSON报告异常: {e}")
            return ""
    
    def generate_csv_report(self, test_results: List[Dict[str, Any]]) -> str:
        """
        生成CSV格式报告
        
        Args:
            test_results: 测试结果数据
            
        Returns:
            报告文件路径
        """
        try:
            import csv
            
            csv_report_file = self.reports_dir / "test_report.csv"
            
            with open(csv_report_file, 'w', newline='', encoding='utf-8') as f:
                if not test_results:
                    return str(csv_report_file)
                
                # 获取字段名
                fieldnames = ['case_name', 'status', 'duration', 'error_message', 'tags']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # 写入表头
                writer.writeheader()
                
                # 写入数据
                for result in test_results:
                    row = {
                        'case_name': result.get('case_name', ''),
                        'status': result.get('status', ''),
                        'duration': result.get('duration', ''),
                        'error_message': result.get('error', ''),
                        'tags': ','.join(result.get('tags', []))
                    }
                    writer.writerow(row)
            
            logger.info(f"CSV报告生成成功: {csv_report_file}")
            return str(csv_report_file)
            
        except Exception as e:
            logger.error(f"生成CSV报告异常: {e}")
            return ""
    
    def _prepare_report_data(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """准备报告数据"""
        total = len(test_results)
        passed = len([r for r in test_results if r.get('status') == 'PASS'])
        failed = len([r for r in test_results if r.get('status') == 'FAIL'])
        error = len([r for r in test_results if r.get('status') == 'ERROR'])
        skipped = len([r for r in test_results if r.get('status') == 'SKIP'])
        
        pass_rate = round(passed / total * 100, 2) if total > 0 else 0
        
        return {
            'title': '自动化测试报告',
            'generated_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total': total,
                'passed': passed,
                'failed': failed,
                'error': error,
                'skipped': skipped,
                'pass_rate': pass_rate
            },
            'test_results': test_results,
            'config': self.config
        }
    
    def _get_default_html_template(self) -> str:
        """获取默认HTML模板"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .summary-item { background: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 5px; text-align: center; }
        .pass { color: #28a745; }
        .fail { color: #dc3545; }
        .error { color: #fd7e14; }
        .skip { color: #6c757d; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .status-pass { color: #28a745; font-weight: bold; }
        .status-fail { color: #dc3545; font-weight: bold; }
        .status-error { color: #fd7e14; font-weight: bold; }
        .status-skip { color: #6c757d; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>生成时间: {{ generated_time }}</p>
    </div>
    
    <div class="summary">
        <div class="summary-item">
            <h3>总计</h3>
            <p>{{ summary.total }}</p>
        </div>
        <div class="summary-item pass">
            <h3>通过</h3>
            <p>{{ summary.passed }}</p>
        </div>
        <div class="summary-item fail">
            <h3>失败</h3>
            <p>{{ summary.failed }}</p>
        </div>
        <div class="summary-item error">
            <h3>错误</h3>
            <p>{{ summary.error }}</p>
        </div>
        <div class="summary-item skip">
            <h3>跳过</h3>
            <p>{{ summary.skipped }}</p>
        </div>
        <div class="summary-item">
            <h3>通过率</h3>
            <p>{{ summary.pass_rate }}%</p>
        </div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>用例名称</th>
                <th>状态</th>
                <th>耗时</th>
                <th>错误信息</th>
            </tr>
        </thead>
        <tbody>
            {% for result in test_results %}
            <tr>
                <td>{{ result.case_name }}</td>
                <td class="status-{{ result.status.lower() }}">{{ result.status }}</td>
                <td>{{ result.duration or '-' }}</td>
                <td>{{ result.error or '-' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
        """
    
    def get_report_url(self, report_type: str = "html") -> str:
        """
        获取报告访问URL

        Args:
            report_type: 报告类型

        Returns:
            报告URL
        """
        if report_type == "allure":
            index_file = self.allure_report_dir / "index.html"
        else:
            index_file = self.html_report_dir / "report.html"

        if index_file.exists():
            return f"file://{index_file.absolute()}"
        else:
            return ""

    def rotate_history(self, keep_last: int = 5) -> None:
        """
        归档当前报告至 history 并保留最近 keep_last 份
        // 决策理由：避免无限增长；Windows 上避免使用软链接
        """
        try:
            reports_dir = self.reports_dir
            history_dir = reports_dir / "history"
            history_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            dest = history_dir / ts
            dest.mkdir(parents=True, exist_ok=True)

            # 归档已存在的报告目录
            for sub in [self.allure_results_dir, self.allure_report_dir, self.html_report_dir]:
                if sub.exists() and any(sub.iterdir()):
                    shutil.move(str(sub), str(dest / sub.name))
                sub.mkdir(parents=True, exist_ok=True)

            # 清理历史，按目录名时间排序
            items = sorted([p for p in history_dir.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
            for idx, p in enumerate(items):
                if idx >= keep_last:
                    shutil.rmtree(p, ignore_errors=True)
        except Exception as e:
            logger.warning(f"归档报告历史失败: {e}")

    def clean_old_reports(self, keep_days: int = 7):
        """
        清理旧报告
        
        Args:
            keep_days: 保留天数
        """
        try:
            cutoff_time = datetime.datetime.now() - datetime.timedelta(days=keep_days)
            
            for report_dir in [self.allure_results_dir, self.allure_report_dir, self.html_report_dir]:
                if not report_dir.exists():
                    continue
                
                for file_path in report_dir.rglob("*"):
                    if file_path.is_file():
                        file_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_time:
                            file_path.unlink()
                            logger.debug(f"删除旧报告文件: {file_path}")
            
            logger.info(f"清理{keep_days}天前的旧报告完成")
            
        except Exception as e:
            logger.error(f"清理旧报告异常: {e}")


# 全局报告助手实例
report_helper = ReportHelper()

# 便捷函数
def generate_allure_report() -> bool:
    """生成Allure报告的便捷函数"""
    return report_helper.generate_allure_report()

def serve_allure_report(port: int = 0) -> bool:
    """启动Allure服务的便捷函数"""
    return report_helper.serve_allure_report(port)

def generate_json_report(test_results: List[Dict[str, Any]]) -> str:
    """生成JSON报告的便捷函数"""
    return report_helper.generate_json_report(test_results)
