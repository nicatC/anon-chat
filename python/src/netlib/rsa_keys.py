from pathlib import Path
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from .crypto_hybrid import encrypt as aes_encrypt, decrypt as aes_decrypt

import base64, json, uuid, sys

key_folder = Path("keys")
private_file= key_folder / "private.pem"
public_file = key_folder / "public.pem"

def check_keys():
    if not private_file.exists() or not public_file.exists():
        print("key not found, new key wil created",file=sys.stderr)
        create_keys()

def create_keys(bit_size=2048):
    key_folder.mkdir(exist_ok=True)
    key = RSA.generate(bit_size)
    private_file.write_bytes(key.export_key())
    public_file.write_bytes(key.public_key().export_key())
    return "key files created"

def read_private():
    check_keys()
    return RSA.import_key(private_file.read_bytes())

def sign_dict(data):
    check_keys()
    json_data =json.dumps(data, sort_keys=True, separators=(",",":")).encode()
    hashed = SHA256.new(json_data)
    signature =pkcs1_15.new(read_private()).sign(hashed)
    return base64.b64encode(signature).decode()


def verify_dict(data, pub_key_bytes, sig_b64):
    json_data= json.dumps(data, sort_keys=True,separators=(",",":")).encode()
    hashed= SHA256.new(json_data)
    try:
        pkcs1_15.new(RSA.import_key(pub_key_bytes)).verify(hashed,base64.b64decode(sig_b64))
        return True
    except (ValueError,TypeError):
        return False

# random mesaj idsi
def new_guid():
    return uuid.uuid4().hex
PUB_PEM = public_file