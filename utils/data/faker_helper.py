from faker import Faker
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from utils.logging.logger import logger


class FakerHelper:
    """Faker数据生成辅助类"""
    
    def __init__(self, locale: str = 'zh_CN'):
        """
        初始化Faker
        
        Args:
            locale: 地区设置，默认中文
        """
        self.fake = Faker(locale)
        self.fake.seed_instance(random.randint(1, 10000))
        
    def name(self) -> str:
        """生成姓名"""
        return self.fake.name()
    
    def first_name(self) -> str:
        """生成名"""
        return self.fake.first_name()
    
    def last_name(self) -> str:
        """生成姓"""
        return self.fake.last_name()
    
    def email(self, domain: str = None) -> str:
        """
        生成邮箱地址
        
        Args:
            domain: 指定域名
        """
        if domain:
            return f"{self.fake.user_name()}@{domain}"
        return self.fake.email()
    
    def phone_number(self) -> str:
        """生成手机号"""
        return self.fake.phone_number()
    
    def address(self) -> str:
        """生成地址"""
        return self.fake.address()
    
    def company(self) -> str:
        """生成公司名"""
        return self.fake.company()
    
    def text(self, max_chars: int = 100) -> str:
        """
        生成文本
        
        Args:
            max_chars: 最大字符数
        """
        return self.fake.text(max_nb_chars=max_chars)
    
    def paragraph(self, nb_sentences: int = 3) -> str:
        """
        生成段落
        
        Args:
            nb_sentences: 句子数量
        """
        return self.fake.paragraph(nb_sentences=nb_sentences)
    
    def word(self) -> str:
        """生成单词"""
        return self.fake.word()
    
    def words(self, nb: int = 3) -> list:
        """
        生成多个单词
        
        Args:
            nb: 单词数量
        """
        return self.fake.words(nb=nb)
    
    def sentence(self, nb_words: int = 6) -> str:
        """
        生成句子
        
        Args:
            nb_words: 单词数量
        """
        return self.fake.sentence(nb_words=nb_words)
    
    def url(self) -> str:
        """生成URL"""
        return self.fake.url()
    
    def username(self) -> str:
        """生成用户名"""
        return self.fake.user_name()
    
    def password(self, length: int = 8, special_chars: bool = True) -> str:
        """
        生成密码
        
        Args:
            length: 密码长度
            special_chars: 是否包含特殊字符
        """
        if special_chars:
            return self.fake.password(length=length, special_chars=True, digits=True, upper_case=True, lower_case=True)
        else:
            return self.fake.password(length=length, special_chars=False, digits=True, upper_case=True, lower_case=True)
    
    def uuid4(self) -> str:
        """生成UUID"""
        return str(uuid.uuid4())
    
    def random_int(self, min_value: int = 1, max_value: int = 1000) -> int:
        """
        生成随机整数
        
        Args:
            min_value: 最小值
            max_value: 最大值
        """
        return random.randint(min_value, max_value)
    
    def random_float(self, min_value: float = 1.0, max_value: float = 1000.0, digits: int = 2) -> float:
        """
        生成随机浮点数
        
        Args:
            min_value: 最小值
            max_value: 最大值
            digits: 小数位数
        """
        return round(random.uniform(min_value, max_value), digits)
    
    def random_string(self, length: int = 10, chars: str = None) -> str:
        """
        生成随机字符串
        
        Args:
            length: 字符串长度
            chars: 字符集合，默认为字母和数字
        """
        if chars is None:
            chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def random_choice(self, choices: list) -> Any:
        """
        从列表中随机选择
        
        Args:
            choices: 选择列表
        """
        return random.choice(choices)
    
    def date(self, pattern: str = "%Y-%m-%d") -> str:
        """
        生成日期
        
        Args:
            pattern: 日期格式
        """
        return self.fake.date().strftime(pattern)
    
    def datetime(self, pattern: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        生成日期时间
        
        Args:
            pattern: 日期时间格式
        """
        return self.fake.date_time().strftime(pattern)
    
    def future_date(self, days: int = 30, pattern: str = "%Y-%m-%d") -> str:
        """
        生成未来日期
        
        Args:
            days: 未来天数
            pattern: 日期格式
        """
        future_date = datetime.now() + timedelta(days=random.randint(1, days))
        return future_date.strftime(pattern)
    
    def past_date(self, days: int = 30, pattern: str = "%Y-%m-%d") -> str:
        """
        生成过去日期
        
        Args:
            days: 过去天数
            pattern: 日期格式
        """
        past_date = datetime.now() - timedelta(days=random.randint(1, days))
        return past_date.strftime(pattern)
    
    def credit_card_number(self, card_type: str = None) -> str:
        """
        生成信用卡号
        
        Args:
            card_type: 卡类型 (visa, mastercard, amex, discover)
        """
        return self.fake.credit_card_number(card_type=card_type)
    
    def bank_country(self) -> str:
        """生成银行国家代码"""
        return self.fake.bank_country()
    
    def iban(self) -> str:
        """生成IBAN银行账号"""
        return self.fake.iban()
    
    def license_plate(self) -> str:
        """生成车牌号"""
        return self.fake.license_plate()
    
    def color_name(self) -> str:
        """生成颜色名称"""
        return self.fake.color_name()
    
    def hex_color(self) -> str:
        """生成十六进制颜色"""
        return self.fake.hex_color()
    
    def ipv4(self) -> str:
        """生成IPv4地址"""
        return self.fake.ipv4()
    
    def ipv6(self) -> str:
        """生成IPv6地址"""
        return self.fake.ipv6()
    
    def mac_address(self) -> str:
        """生成MAC地址"""
        return self.fake.mac_address()
    
    def isbn10(self) -> str:
        """生成ISBN10"""
        return self.fake.isbn10()
    
    def isbn13(self) -> str:
        """生成ISBN13"""
        return self.fake.isbn13()
    
    def ssn(self) -> str:
        """生成社会安全号码"""
        return self.fake.ssn()
    
    def custom_data(self, template: Dict[str, str]) -> Dict[str, Any]:
        """
        根据模板生成自定义数据
        
        Args:
            template: 数据模板，格式为 {"field": "faker_method"}
            
        Returns:
            生成的数据字典
        """
        result = {}
        for field, method in template.items():
            try:
                # 解析方法和参数
                if '(' in method:
                    method_name = method.split('(')[0]
                    # 这里可以扩展参数解析
                    result[field] = getattr(self, method_name)()
                else:
                    result[field] = getattr(self, method)()
            except AttributeError:
                logger.warning(f"未知的faker方法: {method}")
                result[field] = self.fake.word()
        
        return result
    
    def generate_test_user(self) -> Dict[str, str]:
        """生成测试用户数据"""
        return {
            "username": self.username(),
            "password": self.password(),
            "email": self.email(),
            "phone": self.phone_number(),
            "name": self.name(),
            "address": self.address(),
            "company": self.company()
        }
    
    def generate_product_data(self) -> Dict[str, Any]:
        """生成产品数据"""
        return {
            "name": self.fake.catch_phrase(),
            "description": self.text(200),
            "price": self.random_float(10.0, 9999.0, 2),
            "category": self.random_choice(['电子产品', '服装', '食品', '图书', '家具']),
            "sku": self.random_string(8, string.ascii_uppercase + string.digits),
            "stock": self.random_int(0, 1000),
            "status": self.random_choice(['active', 'inactive', 'draft'])
        }


# 全局faker实例
faker_helper = FakerHelper()

# 便捷函数
def fake_name() -> str:
    return faker_helper.name()

def fake_email() -> str:
    return faker_helper.email()

def fake_phone() -> str:
    return faker_helper.phone_number()

def fake_text(length: int = 100) -> str:
    return faker_helper.text(length)

def fake_int(min_val: int = 1, max_val: int = 1000) -> int:
    return faker_helper.random_int(min_val, max_val)

def fake_string(length: int = 10) -> str:
    return faker_helper.random_string(length)

def fake_uuid() -> str:
    return faker_helper.uuid4()

def fake_date() -> str:
    return faker_helper.date()

def fake_datetime() -> str:
    return faker_helper.datetime()

def fake_user() -> Dict[str, str]:
    return faker_helper.generate_test_user()

def fake_product() -> Dict[str, Any]:
    return faker_helper.generate_product_data()