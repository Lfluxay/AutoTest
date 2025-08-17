#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试步骤详细记录器
用于记录测试执行的详细步骤和结果
"""

import time
import json
from typing import Any, Dict, List, Optional, Union
from utils.logging.logger import logger
from utils.logging.secure_filter import safe_log_data, safe_log_url, safe_log_headers


class TestStepLogger:
    """测试步骤记录器"""
    
    def __init__(self, test_name: str = ""):
        self.test_name = test_name
        self.step_counter = 0
        self.start_time = time.time()
        self.steps = []
        self.current_step = None
    
    def start_test(self, test_name: str, description: str = ""):
        """开始测试"""
        self.test_name = test_name
        self.step_counter = 0
        self.start_time = time.time()
        self.steps = []
        
        logger.info("=" * 80)
        logger.info(f"🚀 开始执行测试: {test_name}")
        if description:
            logger.info(f"📝 测试描述: {description}")
        logger.info("=" * 80)
    
    def start_step(self, step_name: str, description: str = "", **kwargs):
        """开始执行步骤"""
        self.step_counter += 1
        step_info = {
            'step_number': self.step_counter,
            'step_name': step_name,
            'description': description,
            'start_time': time.time(),
            'status': 'running',
            'details': kwargs
        }
        
        self.current_step = step_info
        self.steps.append(step_info)
        
        logger.info(f"📋 步骤 {self.step_counter}: {step_name}")
        if description:
            logger.info(f"   📄 描述: {description}")
        
        # 记录步骤参数
        if kwargs:
            for key, value in kwargs.items():
                safe_value = safe_log_data(value)
                logger.info(f"   🔧 {key}: {safe_value}")
    
    def log_action(self, action: str, details: Any = None, level: str = "info"):
        """记录操作"""
        if self.current_step:
            if 'actions' not in self.current_step:
                self.current_step['actions'] = []
            
            action_info = {
                'action': action,
                'timestamp': time.time(),
                'details': details
            }
            self.current_step['actions'].append(action_info)
        
        # 安全记录到日志
        safe_details = safe_log_data(details) if details else ""
        log_message = f"   ⚡ {action}"
        if safe_details:
            log_message += f": {safe_details}"
        
        if level == "debug":
            logger.debug(log_message)
        elif level == "warning":
            logger.warning(log_message)
        elif level == "error":
            logger.error(log_message)
        else:
            logger.info(log_message)
    
    def log_api_request(self, method: str, url: str, headers: Dict = None,
                       data: Any = None, params: Dict = None):
        """记录API请求（简化版）"""
        logger.info(f"   🌐 API请求: {method.upper()} {safe_log_url(url)}")

        # 并发执行时减少详细日志记录
        # if headers:
        #     logger.info(f"   📤 请求头: {safe_log_headers(headers)}")

        # if params:
        #     logger.info(f"   🔗 请求参数: {safe_log_data(params)}")

        # if data:
        #     logger.info(f"   📦 请求体: {safe_log_data(data)}")

        if self.current_step:
            if 'api_requests' not in self.current_step:
                self.current_step['api_requests'] = []

            self.current_step['api_requests'].append({
                'method': method,
                'url': url,
                'headers': headers,
                'data': data,
                'params': params,
                'timestamp': time.time()
            })
    
    def log_api_response(self, status_code: int, headers: Dict = None,
                        data: Any = None, response_time: float = None):
        """记录API响应（简化版）"""
        status_emoji = "✅" if 200 <= status_code < 300 else "❌"
        logger.info(f"   {status_emoji} API响应: {status_code}")

        if response_time:
            logger.info(f"   ⏱️ 响应时间: {response_time:.3f}s")

        # 并发执行时减少详细日志记录
        # if headers:
        #     logger.info(f"   📥 响应头: {safe_log_headers(headers)}")

        # if data:
        #     logger.info(f"   📋 响应体: {safe_log_data(data)}")

        if self.current_step and self.current_step.get('api_requests'):
            # 将响应信息添加到最后一个请求中
            last_request = self.current_step['api_requests'][-1]
            last_request.update({
                'response_status': status_code,
                'response_headers': headers,
                'response_data': data,
                'response_time': response_time
            })
    
    def log_web_action(self, action: str, element: str = "", value: str = "", 
                      screenshot: str = ""):
        """记录Web操作"""
        logger.info(f"   🖱️ Web操作: {action}")
        
        if element:
            logger.info(f"   🎯 目标元素: {element}")
        
        if value:
            logger.info(f"   💬 输入值: {safe_log_data(value)}")
        
        if screenshot:
            logger.info(f"   📸 截图: {screenshot}")
        
        if self.current_step:
            if 'web_actions' not in self.current_step:
                self.current_step['web_actions'] = []
            
            self.current_step['web_actions'].append({
                'action': action,
                'element': element,
                'value': value,
                'screenshot': screenshot,
                'timestamp': time.time()
            })
    
    def log_assertion(self, assertion_type: str, expected: Any, actual: Any, 
                     result: bool, message: str = ""):
        """记录断言"""
        result_emoji = "✅" if result else "❌"
        logger.info(f"   {result_emoji} 断言: {assertion_type}")
        logger.info(f"   📋 期望值: {safe_log_data(expected)}")
        logger.info(f"   📊 实际值: {safe_log_data(actual)}")
        logger.info(f"   🎯 结果: {'通过' if result else '失败'}")
        
        if message:
            logger.info(f"   💬 说明: {message}")
        
        if self.current_step:
            if 'assertions' not in self.current_step:
                self.current_step['assertions'] = []
            
            self.current_step['assertions'].append({
                'type': assertion_type,
                'expected': expected,
                'actual': actual,
                'result': result,
                'message': message,
                'timestamp': time.time()
            })
    
    def end_step(self, status: str = "passed", error_message: str = ""):
        """结束当前步骤"""
        if not self.current_step:
            return
        
        self.current_step['end_time'] = time.time()
        self.current_step['duration'] = self.current_step['end_time'] - self.current_step['start_time']
        self.current_step['status'] = status
        
        if error_message:
            self.current_step['error_message'] = error_message
        
        status_emoji = "✅" if status == "passed" else "❌"
        duration = self.current_step['duration']
        
        logger.info(f"   {status_emoji} 步骤完成: {status.upper()} (耗时: {duration:.3f}s)")
        
        if error_message:
            logger.error(f"   💥 错误信息: {error_message}")
        
        self.current_step = None
    
    def end_test(self, status: str = "passed", summary: Dict = None):
        """结束测试"""
        end_time = time.time()
        total_duration = end_time - self.start_time
        
        logger.info("=" * 80)
        
        status_emoji = "✅" if status == "passed" else "❌"
        logger.info(f"{status_emoji} 测试完成: {self.test_name}")
        logger.info(f"⏱️ 总耗时: {total_duration:.3f}s")
        logger.info(f"📊 总步骤数: {self.step_counter}")
        
        # 统计步骤结果
        passed_steps = len([s for s in self.steps if s.get('status') == 'passed'])
        failed_steps = len([s for s in self.steps if s.get('status') == 'failed'])
        
        logger.info(f"✅ 通过步骤: {passed_steps}")
        logger.info(f"❌ 失败步骤: {failed_steps}")
        
        if summary:
            logger.info("📋 测试总结:")
            for key, value in summary.items():
                logger.info(f"   {key}: {safe_log_data(value)}")
        
        logger.info("=" * 80)
    
    def get_test_report(self) -> Dict:
        """获取测试报告"""
        end_time = time.time()
        total_duration = end_time - self.start_time
        
        return {
            'test_name': self.test_name,
            'start_time': self.start_time,
            'end_time': end_time,
            'total_duration': total_duration,
            'total_steps': self.step_counter,
            'steps': self.steps,
            'passed_steps': len([s for s in self.steps if s.get('status') == 'passed']),
            'failed_steps': len([s for s in self.steps if s.get('status') == 'failed'])
        }


# 全局测试步骤记录器
test_step_logger = TestStepLogger()
