#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全日志过滤器
用于过滤敏感信息，确保日志安全
"""

import re
import json
from typing import Any, Dict, List, Union


class SecureLogFilter:
    """安全日志过滤器"""
    
    def __init__(self):
        # 敏感信息模式
        self.sensitive_patterns = [
            # 密码相关
            (r'("password"\s*:\s*")[^"]*(")', r'\1***\2'),
            (r'("pwd"\s*:\s*")[^"]*(")', r'\1***\2'),
            (r'("passwd"\s*:\s*")[^"]*(")', r'\1***\2'),
            (r'(password\s*=\s*)[^\s&]*', r'\1***'),
            (r'(pwd\s*=\s*)[^\s&]*', r'\1***'),
            
            # Token相关
            (r'("token"\s*:\s*")[^"]*(")', r'\1***\2'),
            (r'("access_token"\s*:\s*")[^"]*(")', r'\1***\2'),
            (r'("refresh_token"\s*:\s*")[^"]*(")', r'\1***\2'),
            (r'(token\s*=\s*)[^\s&]*', r'\1***'),
            (r'(Bearer\s+)[^\s]*', r'\1***'),
            
            # API Key相关
            (r'("api_key"\s*:\s*")[^"]*(")', r'\1***\2'),
            (r'("apikey"\s*:\s*")[^"]*(")', r'\1***\2'),
            (r'("key"\s*:\s*")[^"]*(")', r'\1***\2'),
            (r'(api_key\s*=\s*)[^\s&]*', r'\1***'),
            
            # 身份证号
            (r'\b\d{17}[\dXx]\b', '***身份证号***'),
            
            # 手机号
            (r'\b1[3-9]\d{9}\b', '***手机号***'),
            
            # 邮箱
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***邮箱***'),
            
            # 银行卡号
            (r'\b\d{16,19}\b', '***银行卡号***'),
            
            # IP地址（保留内网地址）
            (r'\b(?!(?:10|127|169\.254|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.)(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '***IP地址***'),
            
            # URL中的敏感参数
            (r'([?&](?:password|pwd|token|key|secret)=)[^&\s]*', r'\1***'),
        ]
        
        # 敏感字段名
        self.sensitive_fields = {
            'password', 'pwd', 'passwd', 'secret', 'token', 'access_token', 
            'refresh_token', 'api_key', 'apikey', 'key', 'private_key',
            'session_id', 'cookie', 'authorization', 'auth'
        }
    
    def filter_message(self, message: str) -> str:
        """过滤消息中的敏感信息"""
        if not message:
            return message
        
        filtered_message = message
        
        # 应用所有敏感信息模式
        for pattern, replacement in self.sensitive_patterns:
            filtered_message = re.sub(pattern, replacement, filtered_message, flags=re.IGNORECASE)
        
        return filtered_message
    
    def filter_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤字典中的敏感信息"""
        if not isinstance(data, dict):
            return data
        
        filtered_data = {}
        for key, value in data.items():
            if key.lower() in self.sensitive_fields:
                filtered_data[key] = "***"
            elif isinstance(value, dict):
                filtered_data[key] = self.filter_dict(value)
            elif isinstance(value, list):
                filtered_data[key] = self.filter_list(value)
            elif isinstance(value, str):
                filtered_data[key] = self.filter_message(value)
            else:
                filtered_data[key] = value
        
        return filtered_data
    
    def filter_list(self, data: List[Any]) -> List[Any]:
        """过滤列表中的敏感信息"""
        if not isinstance(data, list):
            return data
        
        filtered_data = []
        for item in data:
            if isinstance(item, dict):
                filtered_data.append(self.filter_dict(item))
            elif isinstance(item, list):
                filtered_data.append(self.filter_list(item))
            elif isinstance(item, str):
                filtered_data.append(self.filter_message(item))
            else:
                filtered_data.append(item)
        
        return filtered_data
    
    def filter_json(self, json_str: str) -> str:
        """过滤JSON字符串中的敏感信息"""
        try:
            data = json.loads(json_str)
            filtered_data = self.filter_dict(data) if isinstance(data, dict) else self.filter_list(data)
            return json.dumps(filtered_data, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, TypeError):
            # 如果不是有效的JSON，直接过滤字符串
            return self.filter_message(json_str)
    
    def filter_url(self, url: str) -> str:
        """过滤URL中的敏感信息"""
        if not url:
            return url
        
        # 过滤URL参数中的敏感信息
        filtered_url = url
        for pattern, replacement in self.sensitive_patterns:
            if '?' in pattern or '&' in pattern:
                filtered_url = re.sub(pattern, replacement, filtered_url, flags=re.IGNORECASE)
        
        return filtered_url
    
    def filter_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """过滤HTTP头中的敏感信息"""
        if not headers:
            return headers
        
        filtered_headers = {}
        for key, value in headers.items():
            if key.lower() in {'authorization', 'cookie', 'x-api-key', 'x-auth-token'}:
                filtered_headers[key] = "***"
            else:
                filtered_headers[key] = value
        
        return filtered_headers


# 全局过滤器实例
secure_filter = SecureLogFilter()


def safe_log_data(data: Any) -> str:
    """安全地记录数据到日志"""
    if data is None:
        return "None"
    
    if isinstance(data, str):
        return secure_filter.filter_message(data)
    elif isinstance(data, dict):
        filtered_data = secure_filter.filter_dict(data)
        return json.dumps(filtered_data, ensure_ascii=False, indent=2)
    elif isinstance(data, list):
        filtered_data = secure_filter.filter_list(data)
        return json.dumps(filtered_data, ensure_ascii=False, indent=2)
    else:
        return secure_filter.filter_message(str(data))


def safe_log_url(url: str) -> str:
    """安全地记录URL到日志"""
    return secure_filter.filter_url(url)


def safe_log_headers(headers: Dict[str, str]) -> str:
    """安全地记录HTTP头到日志"""
    filtered_headers = secure_filter.filter_headers(headers)
    return json.dumps(filtered_headers, ensure_ascii=False, indent=2)
