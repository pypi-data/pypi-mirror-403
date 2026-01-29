from secrets import choice
from string import ascii_letters as letters, digits, punctuation
from hashlib import sha512 as s512, sha256 as s256

chars: tuple = (*letters, *digits, *punctuation)
def salt(length: int = 9) -> str:
    return ''.join(choice(chars) for _ in range(length))
def sha256(text: str) -> str:
    return s256(text.encode()).hexdigest()
def sha512(text: str) -> str:
    return s512(text.encode()).hexdigest()
def secure256(text: str, customSalt: str = None) -> tuple:
    gSalt: str = customSalt or salt()
    return sha256(text.encode() + gSalt), gSalt
def secure512(text: str, customSalt: str = None) -> tuple:
    gSalt: str = customSalt or salt()
    return sha512(text.encode() + gSalt), gSalt
def multi256(text: str, times: int = 3) -> str:
    return sha256(text * times)
def multi512(text: str, times: int = 3) -> str:
    return sha512(text * times)
def hashByKey(text: str, key: str) -> str:
	result = []
	for i, c in enumerate(text):
		result.append(str(ord(c) ^ ord(key[i % len(key)])))
	return ''.join(result)
