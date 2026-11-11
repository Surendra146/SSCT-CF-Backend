import asyncio, hashlib, unittest
from unittest.mock import patch
from app.core.passwords import hash_password, hash_password_async, verify_password, derive, UnsupportedPasswordHash

class PasswordTests(unittest.TestCase):
 def test_known_vector_and_verification(self):
  async def run():
   self.assertEqual(await derive('password','salt',600000),'669cfe52482116fda1aa2cbe409b2f56c8e4563752b7a28f6eaab614ee005178')
   encoded = await hash_password_async('fixture-only-password')
   self.assertTrue(await verify_password('fixture-only-password',encoded))
   self.assertFalse(await verify_password('wrong',encoded))
   self.assertFalse(await verify_password('wrong','pbkdf2_sha256$1$salt$'+'0'*64))
  asyncio.run(run())
 def test_legacy_scrypt_and_fail_closed_without_implementation(self):
  password, salt = 'legacy-fixture', 'legacy-salt'
  encoded = 'scrypt$'+salt+'$'+hashlib.scrypt(password.encode(),salt=salt.encode(),n=16384,r=8,p=1).hex()
  self.assertTrue(asyncio.run(verify_password(password,encoded)))
  with patch.object(hashlib,'scrypt',None):
   with self.assertRaises(UnsupportedPasswordHash):
    asyncio.run(verify_password(password,encoded))
