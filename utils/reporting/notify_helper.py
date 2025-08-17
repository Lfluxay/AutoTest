import json
import smtplib
import requests
import hashlib
import hmac
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from utils.logging.logger import logger
from utils.config.parser import get_merged_config


class NotifyHelper:
    """通知辅助工具"""
    
    def __init__(self):
        self.config = get_merged_config()
        self.notification_config = self.config.get('notification', {})
        
    def send_test_result_notification(self, success: bool, test_summary: Dict[str, Any] = None):
        """
        发送测试结果通知
        
        Args:
            success: 测试是否成功
            test_summary: 测试总结信息
        """
        if not self.notification_config.get('enabled', False):
            logger.debug("通知功能未启用")
            return
        
        notification_types = self.notification_config.get('types', [])
        
        for notify_type in notification_types:
            try:
                if notify_type == 'feishu':
                    self.send_feishu_notification(success, test_summary)
                elif notify_type == 'email':
                    self.send_email_notification(success, test_summary)
                elif notify_type == 'wechat':
                    self.send_wechat_notification(success, test_summary)
                elif notify_type == 'dingtalk':
                    self.send_dingtalk_notification(success, test_summary)
                else:
                    logger.warning(f"不支持的通知类型: {notify_type}")
                    
            except Exception as e:
                logger.error(f"发送{notify_type}通知失败: {e}")
    
    def send_feishu_notification(self, success: bool, test_summary: Dict[str, Any] = None):
        """发送飞书通知"""
        feishu_config = self.notification_config.get('feishu', {})
        webhook = feishu_config.get('webhook')
        secret = feishu_config.get('secret')
        
        if not webhook:
            logger.warning("飞书Webhook未配置")
            return
        
        # 构建消息内容
        status_text = "✅ 成功" if success else "❌ 失败"
        title = f"自动化测试结果通知 - {status_text}"
        
        content = self._build_message_content(success, test_summary)
        
        # 构建飞书消息格式
        message = {
            "msg_type": "interactive",
            "card": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": content,
                            "tag": "lark_md"
                        }
                    }
                ],
                "header": {
                    "title": {
                        "content": title,
                        "tag": "plain_text"
                    },
                    "template": "green" if success else "red"
                }
            }
        }
        
        # 添加签名
        if secret:
            timestamp = str(int(time.time()))
            sign = self._generate_feishu_sign(timestamp, secret)
            message["timestamp"] = timestamp
            message["sign"] = sign
        
        # 发送请求
        response = requests.post(webhook, json=message, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                logger.info("飞书通知发送成功")
            else:
                logger.error(f"飞书通知发送失败: {result.get('msg')}")
        else:
            logger.error(f"飞书通知请求失败: {response.status_code}")
    
    def send_email_notification(self, success: bool, test_summary: Dict[str, Any] = None):
        """发送邮件通知"""
        email_config = self.notification_config.get('email', {})
        
        smtp_server = email_config.get('smtp_server')
        smtp_port = email_config.get('smtp_port', 587)
        sender = email_config.get('sender')
        password = email_config.get('password')
        receivers = email_config.get('receivers', [])
        use_tls = email_config.get('use_tls', True)
        
        if not all([smtp_server, sender, password, receivers]):
            logger.warning("邮件配置不完整")
            return
        
        # 构建邮件内容
        status_text = "成功" if success else "失败"
        subject = f"自动化测试结果通知 - {status_text}"
        content = self._build_message_content(success, test_summary)
        
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = ', '.join(receivers)
        msg['Subject'] = subject
        
        # 添加HTML内容
        html_content = f"""
        <html>
        <body>
            <h2>{subject}</h2>
            <pre>{content}</pre>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # 发送邮件
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                server.starttls()
            server.login(sender, password)
            server.sendmail(sender, receivers, msg.as_string())
            server.quit()
            
            logger.info("邮件通知发送成功")
            
        except Exception as e:
            logger.error(f"邮件通知发送失败: {e}")
    
    def send_wechat_notification(self, success: bool, test_summary: Dict[str, Any] = None):
        """发送企业微信通知"""
        wechat_config = self.notification_config.get('wechat', {})
        webhook = wechat_config.get('webhook')
        
        if not webhook:
            logger.warning("企业微信Webhook未配置")
            return
        
        # 构建消息内容
        status_text = "成功" if success else "失败"
        content = self._build_message_content(success, test_summary)
        
        # 构建企业微信消息格式
        message = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"## 自动化测试结果通知 - {status_text}\n\n{content}"
            }
        }
        
        # 发送请求
        response = requests.post(webhook, json=message, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                logger.info("企业微信通知发送成功")
            else:
                logger.error(f"企业微信通知发送失败: {result.get('errmsg')}")
        else:
            logger.error(f"企业微信通知请求失败: {response.status_code}")
    
    def send_dingtalk_notification(self, success: bool, test_summary: Dict[str, Any] = None):
        """发送钉钉通知"""
        dingtalk_config = self.notification_config.get('dingtalk', {})
        webhook = dingtalk_config.get('webhook')
        secret = dingtalk_config.get('secret')
        
        if not webhook:
            logger.warning("钉钉Webhook未配置")
            return
        
        # 构建消息内容
        status_text = "成功" if success else "失败"
        content = self._build_message_content(success, test_summary)
        
        # 构建钉钉消息格式
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"自动化测试结果通知 - {status_text}",
                "text": f"## 自动化测试结果通知 - {status_text}\n\n{content}"
            }
        }
        
        # 添加@所有人（如果配置了）
        if dingtalk_config.get('at_all', False):
            message["at"] = {
                "isAtAll": True
            }
        
        # 添加签名
        if secret:
            timestamp = str(round(time.time() * 1000))
            sign = self._generate_dingtalk_sign(timestamp, secret)
            webhook += f"&timestamp={timestamp}&sign={sign}"
        
        # 发送请求
        response = requests.post(webhook, json=message, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                logger.info("钉钉通知发送成功")
            else:
                logger.error(f"钉钉通知发送失败: {result.get('errmsg')}")
        else:
            logger.error(f"钉钉通知请求失败: {response.status_code}")
    
    def send_custom_notification(self, webhook: str, message: Dict[str, Any], 
                                headers: Dict[str, str] = None):
        """
        发送自定义通知
        
        Args:
            webhook: Webhook URL
            message: 消息内容
            headers: 请求头
        """
        try:
            if headers is None:
                headers = {'Content-Type': 'application/json'}
            
            response = requests.post(webhook, json=message, headers=headers, timeout=10)
            
            if response.status_code == 200:
                logger.info("自定义通知发送成功")
            else:
                logger.error(f"自定义通知发送失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"自定义通知发送异常: {e}")
    
    def _build_message_content(self, success: bool, test_summary: Dict[str, Any] = None) -> str:
        """构建消息内容"""
        import datetime
        
        content_lines = []
        
        # 基本信息
        content_lines.append(f"**执行时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content_lines.append(f"**执行结果**: {'✅ 成功' if success else '❌ 失败'}")
        
        # 测试总结
        if test_summary:
            content_lines.append("")
            content_lines.append("**测试总结**:")
            content_lines.append(f"- 总计: {test_summary.get('total', 0)}")
            content_lines.append(f"- 通过: {test_summary.get('passed', 0)}")
            content_lines.append(f"- 失败: {test_summary.get('failed', 0)}")
            content_lines.append(f"- 错误: {test_summary.get('error', 0)}")
            content_lines.append(f"- 跳过: {test_summary.get('skipped', 0)}")
            content_lines.append(f"- 通过率: {test_summary.get('pass_rate', 0)}%")
        
        # 报告链接
        report_url = self.notification_config.get('report_url')
        if report_url:
            content_lines.append("")
            content_lines.append(f"**报告地址**: {report_url}")
        
        # 环境信息
        test_type = self.config.get('test_type', 'unknown')
        content_lines.append("")
        content_lines.append(f"**测试类型**: {test_type}")
        
        return "\n".join(content_lines)
    
    def _generate_feishu_sign(self, timestamp: str, secret: str) -> str:
        """生成飞书签名"""
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        sign = hmac_code.hex()
        return sign
    
    def _generate_dingtalk_sign(self, timestamp: str, secret: str) -> str:
        """生成钉钉签名"""
        import base64
        import urllib.parse
        
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"), 
            string_to_sign.encode("utf-8"), 
            digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign
    
    def test_notification(self, notify_type: str = "all"):
        """
        测试通知功能
        
        Args:
            notify_type: 通知类型，all表示测试所有类型
        """
        test_summary = {
            'total': 10,
            'passed': 8,
            'failed': 1,
            'error': 1,
            'skipped': 0,
            'pass_rate': 80.0
        }
        
        if notify_type == "all":
            notification_types = self.notification_config.get('types', [])
        else:
            notification_types = [notify_type]
        
        for nt in notification_types:
            try:
                logger.info(f"测试{nt}通知...")
                if nt == 'feishu':
                    self.send_feishu_notification(True, test_summary)
                elif nt == 'email':
                    self.send_email_notification(True, test_summary)
                elif nt == 'wechat':
                    self.send_wechat_notification(True, test_summary)
                elif nt == 'dingtalk':
                    self.send_dingtalk_notification(True, test_summary)
                    
            except Exception as e:
                logger.error(f"测试{nt}通知失败: {e}")
    
    def send_start_notification(self):
        """发送测试开始通知"""
        if not self.notification_config.get('enabled', False):
            return
        
        import datetime
        
        message_content = f"""
**自动化测试开始**

**开始时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**测试类型**: {self.config.get('test_type', 'unknown')}
        """
        
        notification_types = self.notification_config.get('types', [])
        
        for notify_type in notification_types:
            try:
                if notify_type == 'feishu':
                    self._send_simple_feishu_message("🚀 自动化测试开始", message_content)
                elif notify_type == 'wechat':
                    self._send_simple_wechat_message("🚀 自动化测试开始", message_content)
                elif notify_type == 'dingtalk':
                    self._send_simple_dingtalk_message("🚀 自动化测试开始", message_content)
                    
            except Exception as e:
                logger.error(f"发送开始通知失败: {e}")
    
    def _send_simple_feishu_message(self, title: str, content: str):
        """发送简单飞书消息"""
        feishu_config = self.notification_config.get('feishu', {})
        webhook = feishu_config.get('webhook')
        
        if not webhook:
            return
        
        message = {
            "msg_type": "text",
            "content": {
                "text": f"{title}\n\n{content}"
            }
        }
        
        requests.post(webhook, json=message, timeout=10)
    
    def _send_simple_wechat_message(self, title: str, content: str):
        """发送简单企业微信消息"""
        wechat_config = self.notification_config.get('wechat', {})
        webhook = wechat_config.get('webhook')
        
        if not webhook:
            return
        
        message = {
            "msgtype": "text",
            "text": {
                "content": f"{title}\n\n{content}"
            }
        }
        
        requests.post(webhook, json=message, timeout=10)
    
    def _send_simple_dingtalk_message(self, title: str, content: str):
        """发送简单钉钉消息"""
        dingtalk_config = self.notification_config.get('dingtalk', {})
        webhook = dingtalk_config.get('webhook')
        
        if not webhook:
            return
        
        message = {
            "msgtype": "text",
            "text": {
                "content": f"{title}\n\n{content}"
            }
        }
        
        requests.post(webhook, json=message, timeout=10)


# 全局通知助手实例
notify_helper = NotifyHelper()

# 便捷函数
def send_test_result_notification(success: bool, test_summary: Dict[str, Any] = None):
    """发送测试结果通知的便捷函数"""
    notify_helper.send_test_result_notification(success, test_summary)

def send_start_notification():
    """发送测试开始通知的便捷函数"""
    notify_helper.send_start_notification()

def test_notification(notify_type: str = "all"):
    """测试通知功能的便捷函数"""
    notify_helper.test_notification(notify_type)
