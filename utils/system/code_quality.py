import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from utils.logging.logger import logger


class CodeQualityChecker:
    """代码质量检查器"""
    
    def __init__(self):
        self.issues = []
        self.metrics = {}
        
    def check_project(self, project_path: str) -> Dict[str, Any]:
        """
        检查整个项目的代码质量
        
        Args:
            project_path: 项目路径
            
        Returns:
            检查结果
        """
        project_path = Path(project_path)
        self.issues.clear()
        self.metrics.clear()
        
        logger.info(f"开始检查项目代码质量: {project_path}")
        
        # 获取所有Python文件
        python_files = list(project_path.rglob("*.py"))
        
        # 检查每个文件
        for file_path in python_files:
            try:
                self._check_file(file_path)
            except Exception as e:
                logger.error(f"检查文件失败: {file_path}, 错误: {e}")
                self.issues.append({
                    'type': 'file_error',
                    'file': str(file_path),
                    'message': f"文件检查异常: {e}",
                    'severity': 'error'
                })
        
        # 检查循环依赖
        self._check_circular_imports(project_path)
        
        # 生成总结
        summary = self._generate_summary()
        
        logger.info(f"代码质量检查完成，发现 {len(self.issues)} 个问题")
        
        return {
            'summary': summary,
            'issues': self.issues,
            'metrics': self.metrics
        }
    
    def _check_file(self, file_path: Path):
        """检查单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析AST
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                self.issues.append({
                    'type': 'syntax_error',
                    'file': str(file_path),
                    'line': e.lineno,
                    'message': f"语法错误: {e.msg}",
                    'severity': 'error'
                })
                return
            
            # 各种检查
            self._check_complexity(file_path, tree)
            self._check_imports(file_path, tree)
            self._check_functions(file_path, tree)
            self._check_classes(file_path, tree)
            self._check_code_style(file_path, content)
            self._check_security_issues(file_path, content)
            
        except Exception as e:
            logger.error(f"检查文件内容失败: {file_path}, 错误: {e}")
    
    def _check_complexity(self, file_path: Path, tree: ast.AST):
        """检查代码复杂度"""
        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 1  # 基础复杂度
                self.max_nesting = 0
                self.current_nesting = 0
            
            def visit_If(self, node):
                self.complexity += 1
                self.current_nesting += 1
                self.max_nesting = max(self.max_nesting, self.current_nesting)
                self.generic_visit(node)
                self.current_nesting -= 1
            
            def visit_For(self, node):
                self.complexity += 1
                self.current_nesting += 1
                self.max_nesting = max(self.max_nesting, self.current_nesting)
                self.generic_visit(node)
                self.current_nesting -= 1
            
            def visit_While(self, node):
                self.complexity += 1
                self.current_nesting += 1
                self.max_nesting = max(self.max_nesting, self.current_nesting)
                self.generic_visit(node)
                self.current_nesting -= 1
            
            def visit_Try(self, node):
                self.complexity += 1
                self.generic_visit(node)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                visitor = ComplexityVisitor()
                visitor.visit(node)
                
                # 检查圈复杂度
                if visitor.complexity > 10:
                    self.issues.append({
                        'type': 'high_complexity',
                        'file': str(file_path),
                        'line': node.lineno,
                        'function': node.name,
                        'complexity': visitor.complexity,
                        'message': f"函数 {node.name} 圈复杂度过高: {visitor.complexity}",
                        'severity': 'warning'
                    })
                
                # 检查嵌套深度
                if visitor.max_nesting > 4:
                    self.issues.append({
                        'type': 'deep_nesting',
                        'file': str(file_path),
                        'line': node.lineno,
                        'function': node.name,
                        'nesting': visitor.max_nesting,
                        'message': f"函数 {node.name} 嵌套层次过深: {visitor.max_nesting}",
                        'severity': 'warning'
                    })
    
    def _check_imports(self, file_path: Path, tree: ast.AST):
        """检查导入语句"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        imports.append(f"{node.module}.{alias.name}")
        
        # 检查未使用的导入
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for imp in imports:
            module_name = imp.split('.')[0]
            if module_name not in content.replace(f"import {module_name}", ""):
                self.issues.append({
                    'type': 'unused_import',
                    'file': str(file_path),
                    'import': imp,
                    'message': f"未使用的导入: {imp}",
                    'severity': 'info'
                })
    
    def _check_functions(self, file_path: Path, tree: ast.AST):
        """检查函数定义"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 检查函数长度
                func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                if func_lines > 50:
                    self.issues.append({
                        'type': 'long_function',
                        'file': str(file_path),
                        'line': node.lineno,
                        'function': node.name,
                        'lines': func_lines,
                        'message': f"函数 {node.name} 过长: {func_lines} 行",
                        'severity': 'warning'
                    })
                
                # 检查参数数量
                args_count = len(node.args.args)
                if args_count > 7:
                    self.issues.append({
                        'type': 'too_many_params',
                        'file': str(file_path),
                        'line': node.lineno,
                        'function': node.name,
                        'params': args_count,
                        'message': f"函数 {node.name} 参数过多: {args_count} 个",
                        'severity': 'warning'
                    })
                
                # 检查是否有文档字符串
                if not ast.get_docstring(node):
                    self.issues.append({
                        'type': 'missing_docstring',
                        'file': str(file_path),
                        'line': node.lineno,
                        'function': node.name,
                        'message': f"函数 {node.name} 缺少文档字符串",
                        'severity': 'info'
                    })
    
    def _check_classes(self, file_path: Path, tree: ast.AST):
        """检查类定义"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 检查类是否有文档字符串
                if not ast.get_docstring(node):
                    self.issues.append({
                        'type': 'missing_class_docstring',
                        'file': str(file_path),
                        'line': node.lineno,
                        'class': node.name,
                        'message': f"类 {node.name} 缺少文档字符串",
                        'severity': 'info'
                    })
                
                # 检查方法数量
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > 20:
                    self.issues.append({
                        'type': 'too_many_methods',
                        'file': str(file_path),
                        'line': node.lineno,
                        'class': node.name,
                        'methods': len(methods),
                        'message': f"类 {node.name} 方法过多: {len(methods)} 个",
                        'severity': 'warning'
                    })
    
    def _check_code_style(self, file_path: Path, content: str):
        """检查代码风格"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 检查行长度
            if len(line) > 120:
                self.issues.append({
                    'type': 'long_line',
                    'file': str(file_path),
                    'line': i,
                    'length': len(line),
                    'message': f"行过长: {len(line)} 字符",
                    'severity': 'info'
                })
            
            # 检查尾随空格
            if line.endswith(' ') or line.endswith('\t'):
                self.issues.append({
                    'type': 'trailing_whitespace',
                    'file': str(file_path),
                    'line': i,
                    'message': "行尾有多余空格",
                    'severity': 'info'
                })
    
    def _check_security_issues(self, file_path: Path, content: str):
        """检查安全问题"""
        # 检查危险函数调用
        dangerous_patterns = [
            (r'eval\s*\(', 'eval函数调用'),
            (r'exec\s*\(', 'exec函数调用'),
            (r'os\.system\s*\(', 'os.system调用'),
            (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', 'shell=True的subprocess调用'),
            (r'pickle\.loads?\s*\(', 'pickle反序列化'),
            (r'yaml\.load\s*\([^)]*Loader\s*=\s*yaml\.Loader', '不安全的YAML加载')
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, description in dangerous_patterns:
                if re.search(pattern, line):
                    self.issues.append({
                        'type': 'security_risk',
                        'file': str(file_path),
                        'line': i,
                        'pattern': description,
                        'message': f"潜在安全风险: {description}",
                        'severity': 'warning'
                    })
    
    def _check_circular_imports(self, project_path: Path):
        """检查循环导入"""
        # 简化的循环导入检查
        import_graph = {}
        
        for py_file in project_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取导入的本地模块
                imports = []
                for line in content.split('\n'):
                    if line.strip().startswith('from ') and ' import ' in line:
                        module = line.split('from ')[1].split(' import ')[0].strip()
                        if not module.startswith('.') and '.' in module:
                            imports.append(module)
                    elif line.strip().startswith('import '):
                        module = line.split('import ')[1].split()[0].strip()
                        if '.' in module:
                            imports.append(module)
                
                relative_path = py_file.relative_to(project_path)
                module_name = str(relative_path).replace('/', '.').replace('\\', '.').replace('.py', '')
                import_graph[module_name] = imports
                
            except Exception:
                continue
        
        # 检查循环依赖（简化版）
        for module, imports in import_graph.items():
            for imported in imports:
                if imported in import_graph and module in import_graph[imported]:
                    self.issues.append({
                        'type': 'circular_import',
                        'modules': [module, imported],
                        'message': f"循环导入: {module} <-> {imported}",
                        'severity': 'error'
                    })
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成检查摘要"""
        summary = {
            'total_issues': len(self.issues),
            'by_severity': {},
            'by_type': {},
            'files_with_issues': len(set(issue.get('file', '') for issue in self.issues if issue.get('file')))
        }
        
        # 按严重程度统计
        for issue in self.issues:
            severity = issue.get('severity', 'unknown')
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
        
        # 按类型统计
        for issue in self.issues:
            issue_type = issue.get('type', 'unknown')
            summary['by_type'][issue_type] = summary['by_type'].get(issue_type, 0) + 1
        
        return summary


# 便捷函数
def check_code_quality(project_path: str) -> Dict[str, Any]:
    """检查代码质量的便捷函数"""
    checker = CodeQualityChecker()
    return checker.check_project(project_path)

def generate_quality_report(project_path: str, output_file: str = None):
    """生成代码质量报告"""
    result = check_code_quality(project_path)
    
    if output_file:
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"代码质量报告已保存到: {output_file}")
    
    return result
