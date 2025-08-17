import base64
import hashlib
import hmac
import json
import os
import secrets
from typing import Union, Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from utils.logging.logger import logger


class CryptoHelper:
    """加解密辅助工具类"""
    
    @staticmethod
    def generate_key() -> bytes:
        """生成Fernet加密密钥"""
        return Fernet.generate_key()
    
    @staticmethod
    def generate_password(length: int = 16, include_symbols: bool = True) -> str:
        """
        生成随机密码
        
        Args:
            length: 密码长度
            include_symbols: 是否包含特殊字符
            
        Returns:
            随机密码
        """
        import string
        
        characters = string.ascii_letters + string.digits
        if include_symbols:
            characters += "!@#$%^&*"
        
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    @staticmethod
    def generate_salt(length: int = 32) -> bytes:
        """生成随机盐值"""
        return os.urandom(length)
    
    # ========== 对称加密 ==========
    
    @staticmethod
    def fernet_encrypt(data: Union[str, bytes], key: bytes) -> str:
        """
        使用Fernet进行对称加密
        
        Args:
            data: 要加密的数据
            key: 加密密钥
            
        Returns:
            Base64编码的加密数据
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            f = Fernet(key)
            encrypted_data = f.encrypt(data)
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Fernet加密失败: {e}")
            raise
    
    @staticmethod
    def fernet_decrypt(encrypted_data: str, key: bytes) -> str:
        """
        使用Fernet进行对称解密
        
        Args:
            encrypted_data: Base64编码的加密数据
            key: 解密密钥
            
        Returns:
            解密后的字符串
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            f = Fernet(key)
            decrypted_data = f.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Fernet解密失败: {e}")
            raise
    
    @staticmethod
    def aes_encrypt(data: Union[str, bytes], key: bytes, iv: bytes = None) -> Dict[str, str]:
        """
        使用AES进行对称加密
        
        Args:
            data: 要加密的数据
            key: 加密密钥（32字节）
            iv: 初始化向量（16字节），如果为None则自动生成
            
        Returns:
            包含加密数据和IV的字典
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            if iv is None:
                iv = os.urandom(16)
            
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            
            # PKCS7填充
            padding_length = 16 - (len(data) % 16)
            padded_data = data + bytes([padding_length] * padding_length)
            
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            return {
                'data': base64.b64encode(encrypted_data).decode('utf-8'),
                'iv': base64.b64encode(iv).decode('utf-8')
            }
            
        except Exception as e:
            logger.error(f"AES加密失败: {e}")
            raise
    
    @staticmethod
    def aes_decrypt(encrypted_data: str, key: bytes, iv: str) -> str:
        """
        使用AES进行对称解密
        
        Args:
            encrypted_data: Base64编码的加密数据
            key: 解密密钥
            iv: Base64编码的初始化向量
            
        Returns:
            解密后的字符串
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            iv_bytes = base64.b64decode(iv.encode('utf-8'))
            
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv_bytes))
            decryptor = cipher.decryptor()
            
            padded_data = decryptor.update(encrypted_bytes) + decryptor.finalize()
            
            # 移除PKCS7填充
            padding_length = padded_data[-1]
            data = padded_data[:-padding_length]
            
            return data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"AES解密失败: {e}")
            raise
    
    # ========== 非对称加密 ==========
    
    @staticmethod
    def generate_rsa_keypair(key_size: int = 2048) -> Dict[str, bytes]:
        """
        生成RSA密钥对
        
        Args:
            key_size: 密钥长度
            
        Returns:
            包含公钥和私钥的字典
        """
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size
            )
            
            public_key = private_key.public_key()
            
            # 序列化密钥
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            return {
                'private_key': private_pem,
                'public_key': public_pem
            }
            
        except Exception as e:
            logger.error(f"生成RSA密钥对失败: {e}")
            raise
    
    @staticmethod
    def rsa_encrypt(data: Union[str, bytes], public_key_pem: bytes) -> str:
        """
        使用RSA公钥加密
        
        Args:
            data: 要加密的数据
            public_key_pem: PEM格式的公钥
            
        Returns:
            Base64编码的加密数据
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            public_key = serialization.load_pem_public_key(public_key_pem)
            
            encrypted_data = public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"RSA加密失败: {e}")
            raise
    
    @staticmethod
    def rsa_decrypt(encrypted_data: str, private_key_pem: bytes) -> str:
        """
        使用RSA私钥解密
        
        Args:
            encrypted_data: Base64编码的加密数据
            private_key_pem: PEM格式的私钥
            
        Returns:
            解密后的字符串
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            private_key = serialization.load_pem_private_key(private_key_pem, password=None)
            
            decrypted_data = private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"RSA解密失败: {e}")
            raise
    
    # ========== 哈希和签名 ==========
    
    @staticmethod
    def md5_hash(data: Union[str, bytes]) -> str:
        """计算MD5哈希值"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.md5(data).hexdigest()
    
    @staticmethod
    def sha1_hash(data: Union[str, bytes]) -> str:
        """计算SHA1哈希值"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha1(data).hexdigest()
    
    @staticmethod
    def sha256_hash(data: Union[str, bytes]) -> str:
        """计算SHA256哈希值"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def sha512_hash(data: Union[str, bytes]) -> str:
        """计算SHA512哈希值"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha512(data).hexdigest()
    
    @staticmethod
    def hmac_sha256(data: Union[str, bytes], key: Union[str, bytes]) -> str:
        """
        计算HMAC-SHA256
        
        Args:
            data: 要签名的数据
            key: 签名密钥
            
        Returns:
            HMAC签名的十六进制字符串
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        if isinstance(key, str):
            key = key.encode('utf-8')
        
        return hmac.new(key, data, hashlib.sha256).hexdigest()
    
    @staticmethod
    def pbkdf2_derive_key(password: Union[str, bytes], salt: bytes, 
                         iterations: int = 100000, key_length: int = 32) -> bytes:
        """
        使用PBKDF2派生密钥
        
        Args:
            password: 密码
            salt: 盐值
            iterations: 迭代次数
            key_length: 密钥长度
            
        Returns:
            派生的密钥
        """
        if isinstance(password, str):
            password = password.encode('utf-8')
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=salt,
            iterations=iterations
        )
        
        return kdf.derive(password)
    
    # ========== Base64编码 ==========
    
    @staticmethod
    def base64_encode(data: Union[str, bytes]) -> str:
        """Base64编码"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.b64encode(data).decode('utf-8')
    
    @staticmethod
    def base64_decode(encoded_data: str) -> str:
        """Base64解码"""
        decoded_bytes = base64.b64decode(encoded_data.encode('utf-8'))
        return decoded_bytes.decode('utf-8')
    
    @staticmethod
    def url_safe_base64_encode(data: Union[str, bytes]) -> str:
        """URL安全的Base64编码"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.urlsafe_b64encode(data).decode('utf-8')
    
    @staticmethod
    def url_safe_base64_decode(encoded_data: str) -> str:
        """URL安全的Base64解码"""
        decoded_bytes = base64.urlsafe_b64decode(encoded_data.encode('utf-8'))
        return decoded_bytes.decode('utf-8')
    
    # ========== JWT相关 ==========
    
    @staticmethod
    def create_jwt_token(payload: Dict[str, Any], secret: str, algorithm: str = 'HS256') -> str:
        """
        创建JWT令牌
        
        Args:
            payload: 载荷数据
            secret: 签名密钥
            algorithm: 签名算法
            
        Returns:
            JWT令牌字符串
        """
        try:
            import jwt
            return jwt.encode(payload, secret, algorithm=algorithm)
        except ImportError:
            logger.error("PyJWT库未安装，无法创建JWT令牌")
            raise
        except Exception as e:
            logger.error(f"创建JWT令牌失败: {e}")
            raise
    
    @staticmethod
    def decode_jwt_token(token: str, secret: str, algorithms: list = None) -> Dict[str, Any]:
        """
        解码JWT令牌
        
        Args:
            token: JWT令牌
            secret: 签名密钥
            algorithms: 允许的算法列表
            
        Returns:
            解码后的载荷数据
        """
        try:
            import jwt
            if algorithms is None:
                algorithms = ['HS256']
            return jwt.decode(token, secret, algorithms=algorithms)
        except ImportError:
            logger.error("PyJWT库未安装，无法解码JWT令牌")
            raise
        except Exception as e:
            logger.error(f"解码JWT令牌失败: {e}")
            raise


# 全局加密助手实例
crypto_helper = CryptoHelper()

# 便捷函数
def encrypt_password(password: str, key: bytes = None) -> Dict[str, str]:
    """加密密码的便捷函数"""
    if key is None:
        key = CryptoHelper.generate_key()
    
    encrypted = CryptoHelper.fernet_encrypt(password, key)
    return {
        'encrypted_password': encrypted,
        'key': base64.b64encode(key).decode('utf-8')
    }

def decrypt_password(encrypted_password: str, key: str) -> str:
    """解密密码的便捷函数"""
    key_bytes = base64.b64decode(key.encode('utf-8'))
    return CryptoHelper.fernet_decrypt(encrypted_password, key_bytes)

def hash_password(password: str, salt: bytes = None) -> Dict[str, str]:
    """哈希密码的便捷函数"""
    if salt is None:
        salt = CryptoHelper.generate_salt()
    
    hashed = CryptoHelper.pbkdf2_derive_key(password, salt)
    return {
        'hashed_password': base64.b64encode(hashed).decode('utf-8'),
        'salt': base64.b64encode(salt).decode('utf-8')
    }
