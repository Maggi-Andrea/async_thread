'''
Created on 11 dic 2019

@author: Andrea
'''

from .asyncthread import AsyncThread

class AsyncThreadTestCaseMixin:
  
  def setUp(self):
    super().setUp()
    self.asyncio = AsyncThread()
    self.asyncio.start()
    self.asyncio.join(0.1)
    
  def tearDown(self):
    super().tearDown()
    self.asyncio.stop()
    self.asyncio = None
    
  @property
  def loop(self):
    return self.asyncio.loop
  
  def run_coro(self, coro):
    return self.asyncio.run_coroutine_threadsafe(coro)
  
  def run_call(self, call, *args):
    return self.asyncio.run_callback_threadsafe(call, *args)
