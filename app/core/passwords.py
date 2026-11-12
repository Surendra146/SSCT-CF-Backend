"""Portable hashing with async Web Crypto on Python Workers."""
import hashlib
import hmac
import secrets
import sys

ITERATIONS = 100000
DUMMY_HASH = 'pbkdf2_sha256$100000$00000000000000000000000000000000$' + '0' * 64

class UnsupportedPasswordHash(RuntimeError):
    pass

def hash_password(password):
    """Native helper for tests and offline administrator hash generation."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), ITERATIONS).hex()
    return f'pbkdf2_sha256${ITERATIONS}${salt}${digest}'

async def derive(password, salt, iterations):
    if sys.platform != 'emscripten':
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations).hex()
    from js import crypto, Uint8Array, Object
    from pyodide.ffi import to_js
    key = await crypto.subtle.importKey('raw', to_js(password.encode()), 'PBKDF2', False, to_js(['deriveBits']))
    options = to_js({'name':'PBKDF2', 'salt':to_js(salt.encode()), 'iterations':iterations, 'hash':'SHA-256'}, dict_converter=Object.fromEntries)
    bits = await crypto.subtle.deriveBits(options, key, 256)
    return Uint8Array.new(bits).to_py().tobytes().hex()

async def hash_password_async(password):
    salt = secrets.token_hex(16)
    digest = await derive(password, salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt}${digest}'

async def verify_password(password, encoded):
    try:
        parts = encoded.split('$')
        if parts[0] == 'pbkdf2_sha256' and len(parts) == 4:
            _, iterations, salt, expected = parts
            iterations = int(iterations)
            if not 100000 <= iterations <= 2000000 or not 1 <= len(salt) <= 128 or len(expected) != 64:
                return False
            if sys.platform == 'emscripten' and iterations > 100000:
                raise UnsupportedPasswordHash(
                    'Password hash requires migration to a Cloudflare-compatible format.'
                )
            actual = await derive(password, salt, iterations)
        elif parts[0] == 'scrypt' and len(parts) == 3:
            _, salt, expected = parts
            implementation = getattr(hashlib, 'scrypt', None)
            if not callable(implementation):
                raise UnsupportedPasswordHash('Legacy password requires an approved reset before use on this runtime.')
            actual = implementation(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
        else:
            return False
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, AttributeError):
        return False
