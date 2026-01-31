
import os
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import os,base64,hashlib,keyring  # 操作系统安全存储
import json
import copy

class CryptoManager:
    """
    此类负责所有加密相关功能：
    - 生成 RSA4096 公私钥
    - 加载/保存 PEM 密钥
    - AES-256-GCM 加密解密
    - RSA-OAEP 加密/解密 AES Key

    所有路径由 App 实例传入，不使用全局变量。
    """

    def __init__(self, private_key_path, public_key_path):
        self.private_key_path = private_key_path   # 私钥文件路径
        self.public_key_path = public_key_path     # 公钥文件路径

    # -----------------------------------------
    #             RSA 相关操作
    # -----------------------------------------
    def generate_rsa_keypair(self):
        """生成 RSA4096 公私钥对象"""
        private = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        public = private.public_key()
        return private, public


    def load_key(self, pin=None):
        if not os.path.exists(self.private_key_path) or not os.path.exists(self.public_key_path):
            return None, None, "密钥文件不存在"

        if pin is None:pin = "TIMLES"
        try:
            with open(self.private_key_path, "rb") as f:
                private_key = serialization.load_pem_private_key(f.read(), password=pin.encode())

            with open(self.public_key_path, "rb") as f:
                public_key = serialization.load_pem_public_key(f.read())
            return private_key, public_key, None
        except Exception as e:
            print("加载密钥失败:", e)
            return None, None, e



    def save_key(self, private_key, public_key, pin=None, pri_key_path=None, pub_key_path=None):
        """将私钥和公钥保存为 PEM 文件"""

        # 保存私钥
        if pri_key_path is None:
            pri_key_path = self.private_key_path
        if pub_key_path is None:
            pub_key_path = self.public_key_path
        if pin is None:
            pin = "TIMLES"
        with open(pri_key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(pin.encode())
            ))

        # 保存公钥
        with open(pub_key_path, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))


    # ============================================
    #  使用混合加密算法对字符串进行加密：先用 AES-GCM 加密数据，再用 RSA-OAEP 加密 AES_key 密钥。  
    #  text->AES->RSA     
    # ============================================
    def AES_RSA_encrypt(self, text: str, pubkey):
        """
         参数：
            text (str): 要加密的明文字符串。
            pubkey: RSA 公钥对象。
        返回：
            dict:
                {
                    "aes_key_rsa":  用 RSA-OAEP 加密后的 AES 密钥（Base64 编码）,
                    "nonce":        AES-GCM 用的随机数（Base64 编码，长度 12 字节）,
                    "ciphertext":   加密后的密文（Base64 编码）,
                    "tag":          AES-GCM 认证标签（Base64 编码，长度 16 字节）
                }
        """
        # -----------------------------------------
        #      AES-256-GCM 加密   
        # -----------------------------------------
        aes_key = AESGCM.generate_key(bit_length=256)
        # 用这个密钥初始化一个 AES-GCM 加密器
        aes = AESGCM(aes_key)
        nonce = os.urandom(12)  # 标准 GCM 的推荐长度
        data = aes.encrypt(nonce, text.encode(), None)

        # 官方实现中 tag 固定 16 字节，这里拆分
        ciphertext, tag = data[:-16], data[-16:]

        # -----------------------------------------
        #           RSA-OAEP 加密
        # -----------------------------------------
        # 使用 RSA 公钥加密 AES Key
        rsa_key = pubkey.encrypt(
                aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        js_data = {
            "aes_key_rsa": base64.b64encode(rsa_key).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "tag": base64.b64encode(tag).decode()
        }
        return js_data

    # ============================================
    #  解密算法：先用 RSA-OAEP 解密 AES_key，再用 AES-GCM 解密数据。  
    #  RSA -> AES -> text 
    # ============================================
    def AES_RSA_decrypt(self, obj: dict, privkey):
        # -----------------------------------------
        # 使用 RSA 私钥解密 AES Key
        # ----------------------------------------- 
        data_bytes=base64.b64decode(obj["aes_key_rsa"])
        aes_key = privkey.decrypt(
            data_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        # -----------------------------------------
        # 使用解密得到的 AES Key 进行 AES 解密
        # -----------------------------------------
        nonce=base64.b64decode(obj["nonce"])
        ciphertext=base64.b64decode(obj["ciphertext"])
        tag=base64.b64decode(obj["tag"])

        aes = AESGCM(aes_key)
        # 把密文和标签重新拼接成加密时的 data 格式
        data = ciphertext + tag
        # 解密并解码
        try:
            plaintext = aes.decrypt(nonce, data, None).decode()
            return plaintext
        except Exception as e:
            print("解密失败:", e)
            return None

    # -----------------------------------------
    #           RSA签名 / 验证
    # -----------------------------------------
    def rsa_sign(self, data_js: dict, privkey) -> dict:
        """使用私钥对数据签名"""
        signature = privkey.sign(
            json.dumps(data_js, sort_keys=True, separators=(',', ':')).encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()    #hash算法
        )
        signed_js = copy.deepcopy(data_js)
        signed_js["signature"] = base64.b64encode(signature).decode()
        return signed_js

    def rsa_verify(self, obj: dict, pubkey) -> bool:
        """使用公钥验证签名，返回True/False"""
        sig = base64.b64decode(obj["signature"])
        # 去掉signature字段后再验证
        data_no_sig = {k: obj[k] for k in obj if k != "signature"}
        data_bytes = json.dumps(data_no_sig, sort_keys=True, separators=(',', ':')).encode()

        try:
            pubkey.verify(
                sig,
                data_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False




class PinManager:
    """
    只负责 PIN 的生成、验证、修改。
    使用操作系统安全存储 (keyring) 保存哈希，提高安全性。
    """

    def __init__(self, service_name):
        # service_name 用来区分你的程序名称
        self.service_name = service_name

    # ============================================================
    #                     PIN 生成 / 保存
    # ============================================================
    def set_pin(self, pin: str, iterations: int = 200_000):
        """生成新的 PIN 哈希并保存到系统安全存储"""
        salt = os.urandom(16)
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256", pin.encode("utf-8"), salt, iterations
        )

        data = {
            "salt": base64.b64encode(salt).decode(),
            "hash": base64.b64encode(hash_bytes).decode(),
            "iterations": iterations,
        }

        # 以字符串方式保存到系统安全存储
        keyring.set_password(self.service_name, "pin_data", json.dumps(data))
        print("PIN 已保存到系统安全存储。")
        return data

    # ============================================================
    #                     PIN 验证
    # ============================================================
    def verify_pin(self, pin: str)-> str:
        """从系统安全存储读取哈希验证输入的 PIN"""
        stored_json = keyring.get_password(self.service_name, "pin_data")
        if not stored_json:
            print("没有检测到保存的 PIN，已经使用默认 PIN。")
            self.set_pin("TIMLES")
            return "not_set"

        stored = json.loads(stored_json)
        salt = base64.b64decode(stored["salt"])
        iterations = stored["iterations"]
        stored_hash = base64.b64decode(stored["hash"])

        test_hash = hashlib.pbkdf2_hmac(
            "sha256", pin.encode("utf-8"), salt, iterations
        )
        return "OK" if test_hash == stored_hash else "FAIL"

    # ============================================================
    #                     修改 PIN
    # ============================================================
    def change_pin(self, old_pin: str, new_pin: str):
        """验证旧 PIN 并更新新的 PIN"""
        if self.verify_pin(old_pin) == "OK":
            return self.set_pin(new_pin)


if __name__ == "__main__":
    pm = PinManager("RayPassApp")

    # 设置 PIN
    pm.set_pin("TIMLES")

    # 验证 PIN
    print("验证正确 PIN：", pm.verify_pin("TIMLES"))
    print("验证错误 PIN：", pm.verify_pin("TIMLEs"))
