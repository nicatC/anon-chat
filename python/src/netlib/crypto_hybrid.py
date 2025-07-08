#sorunu cozemedigim icin su anda kullanamiyorum
import base64, json
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
from Crypto.PublicKey import RSA
from pathlib import Path

# klasör ve private key dosyası
key_folder = Path("keys")
private_key_file = key_folder / "private.pem"

def read_private_key():
    return RSA.import_key(private_key_file.read_bytes())
def to_base64(data):
    return base64.b64encode(data).decode()
def from_base64(data):
    return base64.b64decode(data)

#aes ile sifrele aes anahtarini rsa ile gonder
def encrypt(message, receivers):
    json_data= json.dumps(message, separators=(",", ":")).encode()
    aes_key= get_random_bytes(32)
    cipher= AES.new(aes_key, AES.MODE_GCM)
    encrypted_data,tag =cipher.encrypt_and_digest(json_data)

    encrypted_keys = {}
    for name, pubkey in receivers.items():
        rsa_pub= RSA.import_key(pubkey.encode())
        rsa_enc= PKCS1_OAEP.new(rsa_pub).encrypt(aes_key)
        encrypted_keys[name]= to_base64(rsa_enc)

    return {
        "cipher":to_base64(encrypted_data),
        "nonce":to_base64(cipher.nonce),
        "tag":to_base64(tag),
        "keys": encrypted_keys
    }

def decrypt(data, my_name):
    encrypted_key = data["keys"].get(my_name)
    if not encrypted_key:
        return None

    aes_key = PKCS1_OAEP.new(read_private_key()).decrypt(from_base64(encrypted_key))
    cipher = AES.new(aes_key,AES.MODE_GCM,nonce=from_base64(data["nonce"]))
    plain_text = cipher.decrypt_and_verify(from_base64(data["cipher"]),from_base64(data["tag"]))
    return json.loads(plain_text.decode())

aes_encrypt = encrypt
aes_decrypt = decrypt
