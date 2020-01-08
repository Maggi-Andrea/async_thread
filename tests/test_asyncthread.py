'''
Created on 19 nov 2019

@author: Andrea
'''
import unittest

import asyncio

import time
from asyncthread import AsyncThread


async def task_service():
  while True:
    await asyncio.sleep(1.0)
  return True

class Test(unittest.TestCase):

  def test_AsyncThread(self):
    
    loop = asyncio.get_event_loop()
    thread = AsyncThread()
    thread.daemon = True
    thread.start()
    thread.join(1)
    
    assert thread.is_alive()
    assert thread.loop.is_running()
    assert not thread.loop.is_closed()
    
    assert loop is not thread.loop
    assert not loop.is_running()
    assert not loop.is_closed()
    
    future = thread.run_coroutine_threadsafe(task_service())
    
    time.sleep(0.1) #Give time to OS to switch to the asynch thread
    
    assert future.running()
    assert not future.done()
    
    assert thread.is_alive()
    assert thread.loop.is_running()
    assert not thread.loop.is_closed()
    
    assert loop is not thread.loop
    assert not loop.is_running()
    assert not loop.is_closed()

    thread.stop()
    
    assert future.running()
    assert not future.done()
    
    assert not thread.is_alive()
    assert not thread.loop.is_running()
    assert thread.loop.is_closed()
    
    

if __name__ == "__main__":
  #import sys;sys.argv = ['', 'Test.testName']
  unittest.main()