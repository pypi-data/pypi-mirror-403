from secrets import choice as _choice, randint as _randint, random as _random
from secrets import token_hex as _tkhex
import random as _rand
from string import ascii_letters as letters, digits, punctuation
from hashlib import sha512 as s512, sha256 as s256

chars: tuple = (*letters, *digits, *punctuation)
def salt(length: int = 9) -> str:
    return ''.join(_choice(chars) for _ in range(length))
def sha256(text: str) -> str:
    return s256(text.encode()).hexdigest()
def sha512(text: str) -> str:
    return s512(text.encode()).hexdigest()
def secure256(text: str, customSalt: str = None) -> tuple:
    gSalt: str = customSalt or salt()
    return sha256(text + gSalt), gSalt
def secure512(text: str, customSalt: str = None) -> tuple:
    gSalt: str = customSalt or salt()
    return sha512(text + gSalt), gSalt
def multi256(text: str, times: int = 3) -> str:
    return sha256(text * times)
def multi512(text: str, times: int = 3) -> str:
    return sha512(text * times)
def hashByKey(text: str, key: str, delim: str = '') -> str:
	result = []
	for i, c in enumerate(text):
		result.append(str(ord(c) ^ ord(key[i % len(key)])))
	return delim.join(result)
def randint(min: int, max: int):
    return _choice([_randint(min, max) for _ in range(20)])
def choice(seq: list):
    return _choice([_choice(seq) for _ in range(20)])
def random():
    return _choice([_random() for _ in range(20)])
def token_hex(nbytes):
    return _choice([_tkhex(nbytes) for _ in range(20)])
def safe_func(func, *args, **kwargs):
    return _choice([func(*args, **kwargs) for _ in range(20)])
def shuffle(seq: list):
    def _temp():
        temp = list(seq)
        _rand.shuffle(temp)
        return temp
    return _choice([_temp() for _ in range(20)])
