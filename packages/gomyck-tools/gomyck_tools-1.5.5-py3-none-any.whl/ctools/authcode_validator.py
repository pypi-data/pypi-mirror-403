#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
授权码验证工具类
仅用于验证授权码的有效性
"""
__author__ = 'haoyang'
__date__ = '2026/1/26'

from typing import Optional
from datetime import datetime
import json
import ipaddress

from ctools.cipher import sm_util


class AuthCodeValidator:
    """授权码验证器"""

    def __init__(self, public_key: str = None):
        """
        初始化验证器

        Args:
            public_key: SM2公钥（用于签名验证）
        """
        if not public_key:
            raise Exception("未提供公钥，无法初始化验证器。请传入 public_key 参数。")
        self.public_key = public_key

    def validate(self, authcode_json: str) -> bool:
        """
        快速验证授权码是否有效

        Args:
            authcode_json: 授权码JSON字符串

        Returns:
            bool: 授权码是否有效
        """
        try:
            authcode_obj = json.loads(authcode_json)
        except:
            return False

        # 验证必需字段
        if 'version' not in authcode_obj or 'body' not in authcode_obj or 'signature' not in authcode_obj:
            return False

        body = authcode_obj.get('body')
        if not isinstance(body, dict):
            return False

        return self._verify_signature(authcode_json)

    def _verify_signature(self, authcode_json: str) -> bool:
        """
        验证授权码签名

        Args:
            authcode_json: 授权码JSON字符串

        Returns:
            bool: 签名是否有效
        """
        if not self.public_key:
            raise Exception("未初始化公钥，无法验证签名。请传入 public_key 参数。")

        try:
            authcode_obj = json.loads(authcode_json)
            body = authcode_obj.get('body', {})
            signature = authcode_obj.get('signature', '')
            version = authcode_obj.get('version', 'v1_1')

            # 初始化SM2
            sm_util.init(self.public_key, self.public_key)

            # 构建签名字符串
            final_val = self._build_sign_string(body, version)

            # 验证签名
            return sm_util.verify_with_sm2(signature, final_val)
        except Exception as e:
            try:
                # 重试：重新初始化SM2并验证
                authcode_obj = json.loads(authcode_json)
                body = authcode_obj.get('body', {})
                signature = authcode_obj.get('signature', '')
                version = authcode_obj.get('version', 'v1_1')

                sm_util.init(self.public_key, self.public_key)
                final_val = self._build_sign_string(body, version)
                return sm_util.verify_with_sm2(signature, final_val)
            except:
                return False

    def _build_sign_string(self, body: dict, version: str) -> str:
        """
        构建签名字符串，与app.py中的签名逻辑一致

        Args:
            body: 授权码内容
            version: 版本号

        Returns:
            str: 签名字符串
        """
        ordered_dict = sorted(body.items())
        final_val = ""

        for k, v in ordered_dict:
            if isinstance(v, list):
                value_str = ",".join(v)
            else:
                value_str = str(v)

            if version == 'v1':
                # v1: 不带换行符
                final_val += k + ":" + value_str
            elif version == 'v1_1':
                # v1_1: 带换行符
                final_val += k + ":" + value_str + '\n'
            else:
                # 默认v1_1
                final_val += k + ":" + value_str + '\n'

        return final_val

    def check_expired(self, authcode_json: str) -> bool:
        """
        检查授权码是否过期

        Args:
            authcode_json: 授权码JSON字符串

        Returns:
            bool: 是否未过期
        """
        try:
            authcode_obj = json.loads(authcode_json)
            body = authcode_obj.get('body', {})

            # 检查过期时间
            if 'expired_time' in body:
                expired_time_str = body['expired_time']
                expired_dt = self._parse_datetime(expired_time_str)

                if not expired_dt:
                    return False

                if datetime.now() > expired_dt:
                    return False

            # 检查生效时间
            if 'effect_time' in body:
                effect_time_str = body['effect_time']
                effect_dt = self._parse_datetime(effect_time_str)

                if not effect_dt:
                    return False

                if datetime.now() < effect_dt:
                    return False

            return True
        except:
            return False

    def check_ip(self, authcode_json: str, client_ip: str) -> bool:
        """
        检查客户端IP是否在授权范围内

        Args:
            authcode_json: 授权码JSON字符串
            client_ip: 客户端IP地址

        Returns:
            bool: IP是否在授权范围内
        """
        try:
            authcode_obj = json.loads(authcode_json)
            body = authcode_obj.get('body', {})

            if 'ip_range' not in body:
                return True

            ip_ranges = body['ip_range']
            if not ip_ranges:
                return False

            # 转换为列表
            if isinstance(ip_ranges, str):
                ip_list = [ip.strip() for ip in ip_ranges.split(',')]
            elif isinstance(ip_ranges, list):
                ip_list = ip_ranges
            else:
                return False

            # 支持通配符 "*"
            if '*' in ip_list:
                return True

            # 检查IP是否在范围内
            try:
                client_ip_obj = ipaddress.ip_address(client_ip)
            except:
                return False

            for ip_pattern in ip_list:
                try:
                    if '/' in ip_pattern:
                        # CIDR格式
                        ip_network = ipaddress.ip_network(ip_pattern, strict=False)
                        if client_ip_obj in ip_network:
                            return True
                    else:
                        # 精确匹配
                        if str(client_ip_obj) == ip_pattern:
                            return True
                except:
                    continue

            return False
        except:
            return False

    def check_machine_code(self, authcode_json: str, machine_code: str) -> bool:
        """
        检查机器码是否被授权

        Args:
            authcode_json: 授权码JSON字符串
            machine_code: 机器码

        Returns:
            bool: 机器码是否被授权
        """
        try:
            authcode_obj = json.loads(authcode_json)
            body = authcode_obj.get('body', {})

            if 'machine_codes' not in body:
                return True

            codes = body['machine_codes']
            if not codes:
                return False

            # 转换为列表
            if isinstance(codes, str):
                code_list = [c.strip() for c in codes.split(',')]
            elif isinstance(codes, list):
                code_list = codes
            else:
                return False

            # 支持通配符 "*"
            if '*' in code_list:
                return True

            return machine_code in code_list
        except:
            return False

    def check_module(self, authcode_json: str, module_name: str) -> bool:
        """
        检查模块是否被授权

        Args:
            authcode_json: 授权码JSON字符串
            module_name: 模块名称

        Returns:
            bool: 模块是否被授权
        """
        try:
            authcode_obj = json.loads(authcode_json)
            body = authcode_obj.get('body', {})

            if 'modules' not in body:
                return True

            modules = body['modules']
            if not modules:
                return False

            # 转换为列表
            if isinstance(modules, str):
                module_list = [m.strip() for m in modules.split(',')]
            elif isinstance(modules, list):
                module_list = modules
            else:
                return False

            # 支持通配符 "*"
            if '*' in module_list:
                return True

            return module_name in module_list
        except:
            return False

    def check_artifact(self, authcode_json: str, artifact_name: str) -> bool:
        """
        检查制品名称是否匹配

        Args:
            authcode_json: 授权码JSON字符串
            artifact_name: 制品名称

        Returns:
            bool: 制品是否被授权
        """
        try:
            authcode_obj = json.loads(authcode_json)
            body = authcode_obj.get('body', {})

            if 'artifact' not in body:
                return True

            authorized_artifact = body['artifact']

            # 支持通配符 "*"
            if authorized_artifact == '*':
                return True

            return artifact_name == authorized_artifact
        except:
            return False

    def check_version(self, authcode_json: str, version: str) -> bool:
        """
        检查版本是否被授权

        Args:
            authcode_json: 授权码JSON字符串
            version: 版本号

        Returns:
            bool: 版本是否被授权
        """
        try:
            authcode_obj = json.loads(authcode_json)
            body = authcode_obj.get('body', {})

            if 'version' not in body:
                return True

            authorized_version = body['version']

            # 支持通配符 "*"
            if authorized_version == '*':
                return True

            return version == authorized_version
        except:
            return False

    def validate_all(self, authcode_json: str, client_ip: str = None,
                     machine_code: str = None, artifact: str = None,
                     version: str = None, module: str = None) -> bool:
        """
        检查所有条件是否都满足

        Args:
            authcode_json: 授权码JSON字符串
            client_ip: 客户端IP（可选）
            machine_code: 机器码（可选）
            artifact: 制品名称（可选）
            version: 版本号（可选）
            module: 模块名称（可选）

        Returns:
            bool: 所有条件是否都满足
        """
        # 基本验证
        if not self.validate(authcode_json):
            return False

        # 检查时间
        if not self.check_expired(authcode_json):
            return False

        # 检查IP
        if client_ip and not self.check_ip(authcode_json, client_ip):
            return False

        # 检查机器码
        if machine_code and not self.check_machine_code(authcode_json, machine_code):
            return False

        # 检查制品
        if artifact and not self.check_artifact(authcode_json, artifact):
            return False

        # 检查版本
        if version and not self.check_version(authcode_json, version):
            return False

        # 检查模块
        if module and not self.check_module(authcode_json, module):
            return False

        return True

    # ============= 私有方法 =============

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """解析日期时间字符串"""
        if not date_str:
            return None

        # 尝试多种格式
        formats = [
            '%Y-%m-%dT%H:%M',           # ISO: 2026-01-26T09:23
            '%Y-%m-%dT%H:%M:%S',        # ISO: 2026-01-26T09:23:45
            '%Y-%m-%d %H:%M:%S',        # 标准: 2026-01-26 09:23:45
            '%Y-%m-%d %H:%M',           # 标准: 2026-01-26 09:23
            '%Y-%m-%d',                 # 日期: 2026-01-26
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue

        return None
