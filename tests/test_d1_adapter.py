import unittest, asyncio
from types import SimpleNamespace
from app.core import db

class D1AdapterTests(unittest.TestCase):
    def test_awaited_bindings_and_conversion(self):
        class Proxy:
            def __init__(self,value):self.value=value
            def to_py(self):return self.value
        class Statement:
            def bind(self,*values):self.values=values;return self
            async def all(self):return Proxy({'results':[{'id':1}]})
            async def run(self):return Proxy({'meta':{'last_row_id':7}})
        statement=Statement()
        env=SimpleNamespace(DB=SimpleNamespace(prepare=lambda sql:statement))
        async def run():
            token=db.worker_env.set(env)
            try:
                self.assertEqual(await db.rows('SELECT ?', (True,)),[{'id':1}])
                self.assertEqual(statement.values,(1,))
                self.assertEqual(await db.execute('INSERT ?', ('value',)),7)
            finally:db.worker_env.reset(token)
        asyncio.run(run())

if __name__=='__main__':unittest.main()
