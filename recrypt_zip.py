# Re-encrypt all encrypted JSON files in given .zip archive with new key.

import codecs
from io import BytesIO
from os import listdir
from os.path import join as path_join
from zipfile import ZipFile

from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long, long_to_bytes

from crypto import decrypt_json_bytes_aeskey, encrypt_json_bytes_aeskey, \
                   encrypt_new_aes_key, gen_new_aes_key, pubkey_bytes


with open('keys/server-public-key-orig.pem', 'rb') as f:
    rsa_key_old = RSA.importKey(f.read())


def decrypt_old_aes_key(c_bytes):
    """Given hexadecimal content of .c file, decrypt AES key.

    AES key is obtained using the old public key.
    """
    c_long = bytes_to_long(codecs.decode(c_bytes, 'hex'))
    return long_to_bytes(rsa_key_old._encrypt(c_long))[-32:]


def recrypt_zip(zip_path):
    """Re-encrypt .zip file at given path, overwriting it with new file."""
    out_buf = BytesIO()
    zip_in = ZipFile(zip_path, 'r')
    zip_out = ZipFile(out_buf, 'w')

    for f in zip_in.infolist():
        if f.is_dir():
            zip_out.mkdir(f)
            continue
        elif f.filename.endswith('server-public-key.pem'):
            # replace with new key
            zip_out.writestr(f, pubkey_bytes())
            continue
        elif f.filename.endswith('.c'):
            # Ignore - process alongside .json
            continue
        elif not f.filename.endswith('.json'):
            # Write directly to output
            zip_out.writestr(f, zip_in.read(f))
            continue

        json_info = f

        try:
            c_info = zip_in.getinfo(f.filename[:-5] + '.c')
        except KeyError:
            # Mo .c file: file isn't encrypted
            # Write directly to output
            zip_out.writestr(f, zip_in.read(f))
            continue

        # print(f.filename)

        c_old = zip_in.read(c_info)
        key_old = decrypt_old_aes_key(c_old)
        json_old = zip_in.read(json_info)
        json_dec = decrypt_json_bytes_aeskey(json_old, key_old)

        key_new = gen_new_aes_key(json_dec)
        c_new = encrypt_new_aes_key(key_new)
        json_new = encrypt_json_bytes_aeskey(json_dec, key_new)

        zip_out.writestr(c_info, c_new)
        zip_out.writestr(json_info, json_new)

    zip_in.close()
    zip_out.close()

    with open(zip_path, 'wb') as f:
        f.write(out_buf.getbuffer())
    print(f'{zip_path} re-encrypted with new key')


if __name__ == '__main__':
    from sys import argv

    if len(argv) != 2:
        print('Usage: python recrypt_zip.py <path>.zip')
        print('Example: python recrypt_zip.py tutorial2.zip')
        exit()

    recrypt_zip(argv[1])
