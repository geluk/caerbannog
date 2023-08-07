import base64
import re
from typing import Any, Dict, Tuple

from Cryptodome import Random
from Cryptodome.Cipher import AES
from Cryptodome.Protocol import KDF

SCRYPT_SALT_SIZE = 32

AES_KEY_SIZE = 32
AES_NONCE_SIZE = 16
AES_TAG_SIZE = 16

SCRYPT_N = 2**20
SCRYPT_R = 8
SCRYPT_P = 1

HEADER = "caerbannog"
VERSION = "1"

SECRET_MARKER = f"${HEADER}$"

_cached_keys: Dict[str, bytes] = {}


def encrypt(plaintext: bytes, password: str, pretty=True) -> str:
    """
    Encrypt the given plaintext bytes to a Caerbannog-formatted secret string.
    """
    salt, key = _derive_key(password)
    nonce, tag, ciphertext = _encrypt(key, plaintext)

    message = f"{salt}${_encode(nonce)}${_encode(tag)}${_encode(ciphertext)}"

    if pretty:
        chopped_message = "\n".join(re.findall(r".{1,80}", message))
        secret = f"{SECRET_MARKER}{VERSION}$\n{chopped_message}"
    else:
        secret = f"{SECRET_MARKER}{VERSION}${message}"

    return secret


def decrypt(secret: str, password: str) -> bytes:
    """
    Decrypt a Caerbannog-formatted secret string to retrieve the original
    plaintext bytes.
    """
    trimmed_secret = re.sub(r"\s", "", secret)
    sections = trimmed_secret.split("$")
    if len(sections) != 7:
        raise Exception("Unknown secret format")

    [_, header, version, salt, nonce, tag, ciphertext] = sections
    if header != HEADER:
        raise Exception("Unknown secret format")
    if version != VERSION:
        raise Exception(f"Unknown secret format version: '{version}'")

    nonce = _decode(nonce)
    tag = _decode(tag)
    ciphertext = _decode(ciphertext)

    key = _lookup_key(salt, password)
    plaintext = _decrypt(key, nonce, tag, ciphertext)

    return plaintext


def _lookup_key(salt: str, password: str) -> bytes:
    key = _cached_keys.get(password)
    if key is None:
        key = _rederive_key(salt, password)

    return key


def _derive_key(password: str) -> Tuple[str, bytes]:
    salt = _encode(Random.get_random_bytes(SCRYPT_SALT_SIZE))
    key: Any = KDF.scrypt(password, salt, AES_KEY_SIZE, SCRYPT_N, SCRYPT_R, SCRYPT_P)

    return (salt, key)


def _rederive_key(salt: str, password: str) -> bytes:
    key: Any = KDF.scrypt(password, salt, AES_KEY_SIZE, SCRYPT_N, SCRYPT_R, SCRYPT_P)

    return key


def _encrypt(key: bytes, plaintext: bytes) -> Tuple[bytes, bytes, bytes]:
    aes = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = aes.encrypt_and_digest(plaintext)

    return aes.nonce, tag, ciphertext


def _decrypt(key: bytes, nonce: bytes, tag: bytes, ciphertext: bytes) -> bytes:
    aes = AES.new(key, AES.MODE_GCM, nonce=nonce)

    return aes.decrypt_and_verify(ciphertext, tag)


def _encode(bytes: bytes) -> str:
    return base64.b64encode(bytes).decode("ascii")


def _decode(text: str) -> bytes:
    return base64.b64decode(text)
