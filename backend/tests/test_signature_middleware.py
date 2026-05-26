import pytest
import hmac
import hashlib
import json

from app.core.sign_utils import generate_signature, verify_signature
from app.config import get_settings


class TestSignatureVerification:
    """签名验证单元测试"""
    
    secret = "knowledge-platform-default-signature-secret-change-in-production"
    
    def test_generate_signature_with_nested_object(self):
        """测试生成嵌套对象的签名"""
        params = {
            "configs": {"host": "1", "port": "1", "user": "1", "password": "1", "name": "1"},
            "timestamp": "1779761842",
            "nonce": "w009xINFO2dSq255"
        }
        
        signature = generate_signature(params, self.secret)
        assert signature is not None
        assert len(signature) == 64
    
    def test_verify_signature_with_nested_object(self):
        """测试验证嵌套对象的签名"""
        params = {
            "configs": {"host": "1", "port": "1", "user": "1", "password": "1", "name": "1"},
            "timestamp": "1779761842",
            "nonce": "w009xINFO2dSq255"
        }
        
        signature = generate_signature(params, self.secret)
        assert verify_signature(params, signature, self.secret) is True
        assert verify_signature(params, "wrong_signature", self.secret) is False
    
    def test_signature_matching_with_curl_request(self):
        """测试与 curl 请求参数匹配的签名"""
        timestamp = "1779761842"
        nonce = "w009xINFO2dSq255"
        provided_signature = "c9b9a517be5a5d20929c8e0c1950f32bbfc81e6826a5f63650d73924bff066cf"
        
        params = {
            "configs": {"host": "1", "port": "1", "user": "1", "password": "1", "name": "1"},
            "timestamp": timestamp,
            "nonce": nonce
        }
        
        expected_signature = generate_signature(params, self.secret)
        
        print(f"\n=== 签名验证测试 ===")
        print(f"提供的签名: {provided_signature}")
        print(f"计算的签名: {expected_signature}")
        print(f"签名匹配: {provided_signature == expected_signature}")
        
        assert provided_signature == expected_signature, f"签名不匹配！提供的: {provided_signature}, 计算的: {expected_signature}"
    
    def test_json_serialization_consistency(self):
        """测试 JSON 序列化的一致性"""
        test_cases = [
            {"host": "1", "port": "1"},
            {"host": "localhost", "port": "5432", "user": "knowledge"},
            {"nested": {"a": 1, "b": [1, 2, 3]}}
        ]
        
        for data in test_cases:
            python_serialized = json.dumps(data)
            assert ' ' not in python_serialized, f"JSON 序列化包含空格: {python_serialized}"
    
    def test_signature_with_list_values(self):
        """测试包含列表值的签名"""
        params = {
            "tags": ["tag1", "tag2", "tag3"],
            "timestamp": "1234567890",
            "nonce": "test_nonce"
        }
        
        signature = generate_signature(params, self.secret)
        assert verify_signature(params, signature, self.secret) is True
    
    def test_empty_params_signature(self):
        """测试空参数的签名"""
        params = {
            "timestamp": "1234567890",
            "nonce": "test_nonce"
        }
        
        signature = generate_signature(params, self.secret)
        assert verify_signature(params, signature, self.secret) is True
