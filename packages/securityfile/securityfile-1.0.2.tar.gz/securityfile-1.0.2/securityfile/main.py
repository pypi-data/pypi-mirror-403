import argparse
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from time import time
from datetime import datetime
import json
import os

# 格式: 标志区 | 预留区 | 信息区(大小|数据) | 标志区 | 数据区
# ASE:16B
# SHA256:64B
BLOCK_SIZE = 1024 * 1024 * 2
# 标志区数据
ENC_FLAG_DATA = b"\xca\xde\x02\xf0\x9d\x05\x0d"
# 预留区大小 由于后续拓展配置使用
EXTRA_DATA_LEN = 30
# 信息区数据大小长度
CONFIG_SIZE_LEN = 4


def log(text: str) -> None:
    """
    日志输出
    """
    format = "%Y-%m-%d %H:%M:%S"
    format_text = f"[{datetime.now().strftime(format)}] {text}"
    print(format_text)


def pad_key(key: str) -> bytes:
    """ """
    result = key.encode("utf-8")
    if len(result) <= 16:
        result = result + b"\x00" * (16 - len(result))
    elif len(result) <= 24:
        result == result + b"\x00" * (24 - len(result))
    elif len(result) <= 32:
        result == result + b"\x00" * (32 - len(result))
    else:
        result = result[0:32]
    return result


def pad_iv(iv: str = None) -> bytes:
    if not iv:
        return b"\x00" * 16
    result = iv.encode("utf-8")
    if len(result) <= 16:
        result = result + b"\x00" * (16 - len(result))
    else:
        result = result[0:16]
    return result


def pad_byte(data: bytes, size: int) -> bytes:
    """
    字节
    """
    if len(data) < size:
        data = b"\x00" * (size - len(data)) + data
    return data


def unpad_byte(data: bytes) -> bytes:
    return data.lstrip(b"\x00")


def simple_aes_decrypt(key: str, data: bytes) -> bytes:
    """
    简单AES/CBC/PKCS5Padding解密
    """
    # 创建cipher对象
    cipher = AES.new(key=pad_key(key), mode=AES.MODE_CBC, iv=pad_iv(key))
    # 对输入数据进行解密
    decrypted_data = cipher.decrypt(data)
    return unpad(decrypted_data, AES.block_size)


def simple_aes_encrypt(key: str, data: bytes) -> bytes:
    """
    简单AES/CBC/PKCS5Padding加密
    """
    # 创建cipher对象
    cipher = AES.new(key=pad_key(key), mode=AES.MODE_CBC, iv=pad_iv(key))
    # 对输入数据进行加密
    encrypted_data = cipher.encrypt(pad(data, AES.block_size))
    return encrypted_data


def encrypt_file(file_path: str, key: str, output_name: str = None) -> None:
    """
    AES/CBC/PKCS5Padding encrypt file
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        log(f"file not found: {file_path}")
        return
    elif not os.path.isfile(file_path):
        log(f"path is dir: {file_path}")
        return

    log("===> encrypting...")
    # 文件属性
    file_input = open(file_path, "rb")
    file_input_name = os.path.basename(file_path)
    file_input_size = os.path.getsize(file_path)
    # 如果没有指定输出文件名，则使用20位Hash值作为文件名
    if not output_name:
        output_name = sha256(
            f"{file_input_name}_{file_input_size}".encode()
        ).hexdigest()[:20]
    output_name += ".enc"
    if os.path.exists(output_name):
        os.remove(output_name)
    file_output = open(output_name + ".tmp", "wb")

    # 同时进行Hash计算和AES加密
    t1 = time()
    cipher_hash = sha256()
    cipher_encrypt = AES.new(key=pad_key(key), mode=AES.MODE_CBC, iv=pad_iv(key))
    while True:
        blocks = file_input.read(BLOCK_SIZE)
        if not blocks:
            break
        cipher_hash.update(blocks)
        blocks = pad(blocks, AES.block_size)
        encrypt_bytes = cipher_encrypt.encrypt(blocks)
        file_output.write(encrypt_bytes)
    file_input.close()
    file_output.close()

    # 保存参数，用于解密时恢复文件名、完整性验证
    hash = cipher_hash.hexdigest()
    config = {
        "filename": file_input_name,
        "size": file_input_size,
        "hash": hash,
        "time": int(time() * 1000),
    }
    config = json.dumps(config, ensure_ascii=False)
    config = simple_aes_encrypt(key, config.encode())
    # 不能直接seek到头部写入 先写入新文件 然后将加密文件追加
    file_output = open(output_name + ".tmp1", "wb")
    file_output.write(ENC_FLAG_DATA)
    file_output.write(b"\x00" * EXTRA_DATA_LEN)
    file_output.write(pad_byte(hex(len(config))[2:].encode("utf-8"), CONFIG_SIZE_LEN))
    file_output.write(config)
    file_output.write(ENC_FLAG_DATA)
    file = open(output_name + ".tmp", "rb")
    while True:
        blocks = file.read(BLOCK_SIZE)
        if not blocks:
            break
        file_output.write(blocks)
    file.close()
    file_output.close()
    os.remove(output_name + ".tmp")
    os.rename(output_name + ".tmp1", output_name)

    log(f"filename: {output_name}")
    log(f"hash: {hash}")
    log(f"size: {file_input_size}")
    log(f"cost time: {time() - t1}s")


def decrypt_file(file_path: str, key: str) -> None:
    """
    AES/CBC/PKCS5Padding decrypt file
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        log("file not found")
        return
    elif not os.path.isfile(file_path):
        log("path is dir")
        return
    elif not key:
        log("please provide key")
        return

    log("===> decrypting...")
    # # 检查标志区
    file_input = open(file_path, "rb")
    flag = file_input.read(len(ENC_FLAG_DATA))
    if flag != ENC_FLAG_DATA:
        log("head check, file is not encrypted")
        return

    # 读取预留区
    file_input.read(EXTRA_DATA_LEN)

    # 读取配置
    config_size = file_input.read(CONFIG_SIZE_LEN)
    config_size = int(unpad_byte(config_size).decode("utf-8"), 16)
    config = file_input.read(config_size)
    try:
        config = simple_aes_decrypt(key, config)
        config = json.loads(config.decode())
        filename = config["filename"]
        log(f"filename: {config['filename']}")
        log(f"hash: {config['hash']}")
        log(f"time: {config['time']}")
        log(f"size: {config['size']}")
    except:
        log("file config is not valid")
        return

    # 检查标志区
    flag = file_input.read(len(ENC_FLAG_DATA))
    if flag != ENC_FLAG_DATA:
        log("start check, file is not encrypted")
        return

    # 检查文件是否存在
    if os.path.exists(filename):
        log("decrypted file exists")
        return
    file_output = open(filename + ".tmp", "wb")

    # 同时进行Hash计算和AES加密
    t1 = time()
    cipher_hash = sha256()
    cipher_decrypt = AES.new(key=pad_key(key), mode=AES.MODE_CBC, iv=pad_iv(key))
    while True:
        blocks = file_input.read(BLOCK_SIZE + AES.block_size)
        if not blocks:
            break
        decrypt_bytes = unpad(cipher_decrypt.decrypt(blocks), AES.block_size)
        cipher_hash.update(decrypt_bytes)
        file_output.write(decrypt_bytes)
    file_input.close()
    file_output.close()
    os.rename(filename + ".tmp", filename)

    log(f"cost time: {time() - t1}s")

    # 验证文件完整性
    hash = cipher_hash.hexdigest()
    if hash != config["hash"]:
        log("checksum error")
    else:
        log("checksum success")


def list_encrypted_files(dir: str, key: str) -> None:
    """
    列举出所有加密文件
    """
    if not os.path.isdir(dir):
        log("path is not dir")
        return
    if not key:
        log("please provide key")
        return

    paths = os.listdir(dir)
    encFiles = []
    for path in paths:
        if os.path.isdir(path):
            continue
        with open(path, "rb") as file:
            try:
                # 检查标志区
                flag = file.read(len(ENC_FLAG_DATA))
                if flag != ENC_FLAG_DATA:
                    continue
                # 读取预留区
                file.read(EXTRA_DATA_LEN)
                # 读取配置
                config_size = file.read(CONFIG_SIZE_LEN)
                config_size = int(unpad_byte(config_size).decode("utf-8"), 16)
                config = file.read(config_size)
                config = simple_aes_decrypt(key, config)
                config = json.loads(config.decode())
                log(f"[{len(encFiles)+1}] {config['filename']}")
                encFiles.append(path)
            except:
                continue
    if len(encFiles):
        index = input("\nplease input index：")
        if not index:
            return
        try:
            index = int(index)
        except:
            pass
        if index > 0 and index <= len(encFiles):
            decrypt_file(encFiles[index - 1], key)
    else:
        log("no encrypted files found")


def list_and_decrypted_files(dir: str, key: str) -> None:
    """
    列举出所有加密文件并解密
    """
    if not os.path.isdir(dir):
        log("path is not dir")
        return
    if not key:
        log("please provide key")
        return
    paths = os.listdir(dir)
    encFiles = []
    for path in paths:
        if os.path.isdir(path):
            continue
        with open(path, "rb") as file:
            try:
                # 检查标志区
                flag = file.read(len(ENC_FLAG_DATA))
                if flag != ENC_FLAG_DATA:
                    continue
                # 读取预留区
                file.read(EXTRA_DATA_LEN)
                # 读取配置
                config_size = file.read(CONFIG_SIZE_LEN)
                config_size = int(unpad_byte(config_size).decode("utf-8"), 16)
                config = file.read(config_size)
                config = simple_aes_decrypt(key, config)
                config = json.loads(config.decode())
                log(f"[{len(encFiles)+1}] {config['filename']}")
                encFiles.append(path)
            except:
                continue

    for path in encFiles:
        decrypt_file(path, key)


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--encrypt", help="encrypt file", action="store_true")
    parser.add_argument("-d", "--decrypt", help="decrypt file", action="store_true")
    parser.add_argument(
        "-l", "--list", help="list all encrypted files", action="store_true"
    )
    parser.add_argument(
        "-ld",
        "--listd",
        help="list all encrypted files and decrypt all",
        action="store_true",
    )
    parser.add_argument("-k", "--key", help="security key", default="")
    parser.add_argument("-p", "--path", help="data path", default=".")
    parser.add_argument("--name", "--name", help="encrypted filename", default=None)
    return parser.parse_args()


def main():
    args = get_parser()
    mKey = args.key.strip() if args.key else ""
    mPath = args.path.strip() if args.path else "."
    mName = args.name.strip() if args.name else ""

    if args.encrypt:
        encrypt_file(mPath, mKey, mName)
    elif args.decrypt:
        decrypt_file(mPath, mKey)
    elif args.list:
        list_encrypted_files(mPath, mKey)
    elif args.listd:
        list_and_decrypted_files(mPath, mKey)
    else:
        log("please use -h to see help")


if __name__ == "__main__":
    main()
