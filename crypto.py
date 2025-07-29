# Decrypt/encrypt extracted json file(s) without changing key.
# Operation is inferred based on presence/lack of '.dec.json' extension.

import codecs
from hashlib import sha256

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Util.number import bytes_to_long, long_to_bytes
from Crypto.Util.Padding import pad, unpad

def pubkey_bytes():
    with open('keys/server-public-key.pem', 'rb') as f:
        return f.read()

def privkey_bytes():
    with open('keys/server-private-key.pem', 'rb') as f:
        return f.read()

pubkey_cipher = RSA.importKey(pubkey_bytes())
privkey_cipher = RSA.importKey(privkey_bytes())


def gen_new_aes_key(json_bytes):
    """Generate new AES key by hashing bytes.

    Should use decrypted bytes as input.
    """
    hash = sha256()
    hash.update(json_bytes)
    return codecs.encode(hash.digest()[:16], 'hex')

def encrypt_new_aes_key(key_bytes):
    """Encrypt AES key to hexadecimal .c file content."""
    key_bytes = b'\x00\x01' + b'\xff'*(256-32-3) + b'\x00' + key_bytes
    key_long = bytes_to_long(key_bytes)
    key_enc = privkey_cipher._decrypt_to_bytes(key_long)
    return codecs.encode(key_enc, 'hex')


def get_aes_key(c_bytes):
    """Get AES key for decryption, given .c file content."""
    c_long = bytes_to_long(codecs.decode(c_bytes, 'hex'))
    key = long_to_bytes(pubkey_cipher._encrypt(c_long))
    return key[-32:]


def decrypt_json_bytes_aeskey(json_bytes, key):
    """Decrypt JSON file bytes to bytes, using given AES key directly (not .c contents)."""
    cipher = AES.new(key, AES.MODE_ECB)
    dec = cipher.decrypt(codecs.decode(json_bytes, 'hex'))
    return unpad(dec, 16)

def encrypt_json_bytes_aeskey(json_bytes, key):
    """Encrypt bytes to JSON file bytes, using given AES key directly (not .c contents)."""
    cipher = AES.new(key, AES.MODE_ECB)
    enc = cipher.encrypt(pad(json_bytes, 16))
    return codecs.encode(enc, 'hex')


def decrypt_json(json_bytes, c_bytes):
    """Decrypt JSON file bytes to string, using key from .c file contents."""
    return decrypt_json_bytes_aeskey(json_bytes, get_aes_key(c_bytes)).decode('utf-8')


if __name__ == '__main__':
    from sys import argv

    if len(argv) < 1:
        print('Usage: python crypto.py <json_files>')
        exit()

    for arg in argv[1:]:
        if arg.endswith('.dec.json'):
            mode = 'encrypt'
            arg_noext = arg[:-9]

        elif arg.endswith('.enc.json'):
            mode = 'decrypt'
            arg_noext = arg[:-9]

        elif arg.endswith('.json'):
            mode = 'decrypt'
            arg_noext = arg[:-5]

        else:
            print(f'unsupported file extension (arg="{arg}")')
            continue


        if mode == 'decrypt':
            json_path = arg
            c_path = arg_noext + '.c'
            dec_path = arg_noext + '.dec.json'

            with open(json_path, 'rb') as f:
                json_bytes = f.read()

            with open(c_path, 'rb') as f:
                c_bytes = f.read()

            dec_str = decrypt_json(json_bytes, c_bytes)

            # Quality of life feature: un-escape unicode sequences
            # (not really required, but makes files more legible in text editor)
            from re import sub as re_sub
            dec_str = re_sub(r'\\[Uu]([0-9A-Fa-f]{4})',
                lambda m: str(chr(int(m.group(1), 16))),
                dec_str)

            with open(dec_path, 'w', encoding='utf-8') as f:
                f.write(dec_str)

        elif mode == 'encrypt':
            json_path = arg
            c_path = arg_noext + '.c'
            enc_path = arg_noext + '.json'

            with open(json_path, 'rb') as f:
                json_bytes = f.read()

            aeskey = gen_new_aes_key(json_bytes)
            c_bytes = encrypt_new_aes_key(aeskey)
            enc_bytes = encrypt_json_bytes_aeskey(json_bytes, aeskey)

            with open(c_path, 'wb') as f:
                f.write(c_bytes)
            with open(enc_path, 'wb') as f:
                f.write(enc_bytes)

        else:
            print(f'internal error: invalid mode (mode="{mode}")')
