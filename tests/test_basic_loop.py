'''
Created on 12 nov 2019

@author: Andrea
'''
#import unittest

import unittest

import asyncio

import concurrent.futures

from tests.threads import trace_thread_name

class Test(unittest.TestCase):

  def setUp(self):
    try:
      loop = asyncio.get_event_loop()
    except RuntimeError:
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
    else:
      if loop.is_running():
        loop.call_soon_threadsafe(loop.stop)
        while loop.is_running(): ...
      assert not loop.is_running()
      
      if not loop.is_closed():
        loop.close()
      
      assert loop.is_closed()
      asyncio.set_event_loop(asyncio.new_event_loop())

  def tearDown(self):
    pass

  def test_get_event_loop(self):
    loop = asyncio.get_event_loop()
    assert loop is not None, f'syncio.get_event_loop() is None!'
    assert not loop.is_running()
    assert not loop.is_closed()

  def test_set_event_loop(self):
    loop = asyncio.get_event_loop()
    assert not loop.is_running()
    assert not loop.is_closed()
    
    asyncio.set_event_loop(None)
    assert not loop.is_running()
    assert not loop.is_closed()
  
    with self.assertRaises(RuntimeError):
      asyncio.get_event_loop()
    
    assert not loop.is_running()
    assert not loop.is_closed()
  
    asyncio.set_event_loop(loop)
    assert not loop.is_running()
    assert not loop.is_closed()
    
    assert loop is asyncio.get_event_loop()
  
  def test_get_running_loop(self):
    with self.assertRaises(RuntimeError):
      asyncio.get_running_loop()
      
  async def _async_assert_get_event_loop(self, main_loop):
    event_loop = asyncio.get_event_loop()
    assert event_loop is not main_loop, \
           f'asyncio.run(main) did not set a new event loop'
   
    assert event_loop.is_running()
    assert not event_loop.is_closed()

    assert not main_loop.is_running()
    assert not main_loop.is_closed()
    return event_loop
  
  async def _async_assert_get_running_loop(self, main_loop):
    event_loop = await self._async_assert_get_event_loop(main_loop)
    running_loop = asyncio.get_running_loop()
    assert running_loop is event_loop, \
           f'running loop is not current event loop!'
    assert running_loop is not main_loop, \
           f'asyncio.run(main) did not set a new event loop'
   
    assert running_loop.is_running()
    assert not running_loop.is_closed()

    assert not main_loop.is_running()
    assert not main_loop.is_closed()
    return running_loop
  
  async def _async_assert_set_event_loop(self, main_loop):
    event_loop = await self._async_assert_get_event_loop(main_loop)
    running_loop = await self._async_assert_get_running_loop(main_loop)
    
    assert event_loop is running_loop
    assert event_loop is not main_loop

    asyncio.set_event_loop(main_loop)
    
    post_event_loop = await self._async_assert_get_event_loop(main_loop)
    post_running_loop = await self._async_assert_get_running_loop(main_loop)
    
    assert post_event_loop is post_running_loop
    assert post_event_loop is not main_loop
    assert post_event_loop is event_loop

  def test_asyncio_run_and_get_event_loop(self):
    """
      asyncio.run(main) create and set a new event loop to run command
    """
    loop = asyncio.get_event_loop()
    event_loop = asyncio.run(self._async_assert_get_event_loop(loop))
    
    assert event_loop is not loop
    
  def test_asyncio_run_and_set_evnet_loop(self):
    """
      What happen when I have a running loop and change the current loop?
      
      asyncio will ignore this change, 
    """
    loop = asyncio.get_event_loop()
    asyncio.run(self._async_assert_set_event_loop(loop))
    
    with self.assertRaises(RuntimeError):
      asyncio.get_event_loop()
      
  def test_asyncio_run_and_get_running_loop(self):
    """
    asyncio.run(main) always create a new event loop, set it as actual, run the
    coro and then close the loop and set the actual loop with None
    """
    loop = asyncio.get_event_loop()
    
    runned_loop = asyncio.run(self._async_assert_get_running_loop(loop))
    
    assert not runned_loop.is_running()
    assert runned_loop.is_closed(), 'asyncio.run'
    
    assert runned_loop is not loop

    assert not loop.is_running()
    assert not loop.is_closed(), 'asyncio.run(main) closed the outside loop'
    
    with self.assertRaises(RuntimeError):
      asyncio.get_event_loop()
      assert False, "asyncio.run(main) did not clear the current loop"
    
    asyncio.set_event_loop(loop)
    self.assertIs(loop, asyncio.get_event_loop())
    asyncio.set_event_loop(None)
    self.assertEqual(False, loop.is_running())
    self.assertEqual(False, loop.is_closed())
    """
      loop.close() closed because garbage collector call the del function
      rising exception
    """
    loop.close()
    
  def asyncio_run_coroutine_threadsafete_do_not_start_main_loop(self):
    
    async def service():
      while True:
        asyncio.sleep(1.0)
    
    loop = asyncio.get_event_loop()
    
    srv = service.MyService()
    
    fut = asyncio.run_coroutine_threadsafe(
      srv.start(), loop
    )
    
    with self.assertRaises(concurrent.futures.TimeoutError) as cm:
      fut.result(timeout=1.0)
    print(cm.exception)

    assert not loop.is_running()
    assert not loop.is_closed()
    
  def test_thread_get_event_loop(self):
    """
      Into a new thread at first there is no loop set into asyncio
    """
    loop = asyncio.get_event_loop()
    assert not loop.is_running()
    assert not loop.is_closed()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
      future_loop = executor.submit(asyncio.get_event_loop)
      with self.assertRaises(RuntimeError):
        future_loop.result()
    
    assert not loop.is_running()
    assert not loop.is_closed()
  
  @trace_thread_name
  def test_thread_set_event_loop(self):
    """
      Setting into a thread the same main event loop do not change the current
      loop into the Main thread 
    """
    loop = asyncio.get_event_loop()
    assert not loop.is_running()
    assert not loop.is_closed()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
      future = executor.submit(trace_thread_name(asyncio.set_event_loop), loop)
      assert future.result() is None
      
      future = executor.submit(trace_thread_name(asyncio.get_event_loop))
      future.result()
        
    assert not loop.is_running()
    assert not loop.is_closed()
    assert loop is asyncio.get_event_loop()
    

if __name__ == "__main__":
  # import sys;sys.argv = ['', 'Test.test_loop']
  unittest.main()
