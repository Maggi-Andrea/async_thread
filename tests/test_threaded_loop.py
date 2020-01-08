'''
Created on 19 nov 2019

@author: Andrea
'''
import unittest

import asyncio

import time
import threading
import concurrent.futures

from asyncthread.asyncthread import _cancel_all_tasks
from tests.timers import display_execution_times

class Test(unittest.TestCase):

  def test_loop_run_forever(self):
    """
    Stop the event loop using a call_soon_threadsafe with loop.stop, thus the
    loop wake up to process this very task, and then stop itself because the
    loop instead of going waiting for other task, respond to the stop request,
    stop running the loop
    """
    loop = asyncio.new_event_loop()
    assert not loop.is_running()
    assert not loop.is_closed()

    main_loop = asyncio.get_event_loop()
    assert main_loop is not loop
    assert not main_loop.is_running()
    assert not main_loop.is_closed()
    
    thread = threading.Thread(target=loop.run_forever)
    thread.daemon = True
    thread.start()
    thread.join(1)
    
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    loop.call_soon_threadsafe(loop.stop)
    
    thread.join()
    assert not thread.is_alive()
    assert not loop.is_running()
    assert not loop.is_closed()
    
    loop.close()
    assert loop.is_closed()
    assert loop is not main_loop
    
  @display_execution_times  
  def test_stop_loop_from_other_thread(self):
    """
    To stop the loop, calling loop.stop() from the MainThread do not stop
    immediately the loop because the loop is waiting for new coroutine and is
    not able to detect the stop signal until the loop is waked up. Indeed when
    the MainThread request the loop to execute with loop.call_soon_threadsafe(),
    the loop wake up, run the newly added callback and the, due to the previous
    call to loop.stop(), stop itself. As soon as the loop stops, the Thread
    return from the loop.run_forever() call continuing its execution to death.
    This is indeed checked with thread.is_alive() call, returning False now.
    Note that if we try to execute a dummy callback without using the
    threadsafe method, the loop is not waked up.
    """
    loop = asyncio.new_event_loop()
    
    assert not loop.is_running()
    assert not loop.is_closed()
    
    thread = threading.Thread(target=loop.run_forever)
    thread.daemon = True
    thread.start()
    thread.join(1)

    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    loop.stop()
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    thread.join(1)
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    # This call of the dummy callback do not wake up the loop, because
    # loop.call_soon() must not be used outside the loop thread!
    loop.call_soon(lambda:print('Dummy call_soon'))
    thread.join(1)
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    # This call of the dummy callback do wake up the loop, because 
    # loop.call_soon_threadsafe() is to be used outside the loop thread.
    loop.call_soon_threadsafe(lambda:print('Dummy call_soon_threadsafe'))
    thread.join()
    assert not thread.is_alive()
    assert not loop.is_running()
    assert not loop.is_closed()
    
    loop.close()
    assert not loop.is_running()
    assert loop.is_closed()
    
  def test_use_MainThread_loop(self):
    """
    The loop collected from the MainThread with asyncio.get_event_loop() is 
    run into a new Thread with the loop.run_forever() method.
    Into the MainThread this very loop is still returned with the
    asyncio.get_event_loop() and introspecting it within the MainThread
    with loop.is_running() return True but calling asyncio.get_running_loop()
    into the MainThread continue to raise a RuntimeError.
    """
    loop = asyncio.get_event_loop()
    
    assert not loop.is_running()
    assert not loop.is_closed()
    
    thread = threading.Thread(target=loop.run_forever)
    thread.daemon = True
    thread.start()
    thread.join(1)

    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    # On this main thread there is no loop running
    with self.assertRaises(RuntimeError):
      asyncio.get_running_loop()
    
    # But still the current loop is the in thread running loop
    assert loop is asyncio.get_event_loop()

    loop.call_soon_threadsafe(loop.stop)
    thread.join()
    assert not thread.is_alive()
    assert not loop.is_running()
    assert not loop.is_closed()
    assert loop is asyncio.get_event_loop()
    
    loop.close()
    assert not loop.is_running()
    assert loop.is_closed()
    assert loop is asyncio.get_event_loop()
  
  def test_run_coroutine_threadsafe(self):
    """
    With the async loop running into a thread we try to interact with it using
    the asyncio.run_coroutine_threadsafe() to set executing both awaitable
    function and normal function.
    Awaitable function can be passed as they are, normal function can be
    scheduled only after having this function wrapped into a coroutine with
    asyncio.coroutine() method/decorator.
    Using the asyncio.run_coroutine_threadsafe() allows to have the caller
    waiting for the result via the concurrent.futures.Future(). This future
    is used with an hidden callback, created by run_coroutine_threadsafe().
    It is this very callback that get scheduled with a call to
    loop.call_soon_threadsafe(callback).
    """
    loop = asyncio.new_event_loop()
    assert not loop.is_running()
    assert not loop.is_closed()
    
    thread = threading.Thread(target=loop.run_forever)
    thread.daemon = True
    thread.start()
    thread.join(0.1)
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    fut = asyncio.run_coroutine_threadsafe(
      asyncio.coroutine(asyncio.get_running_loop)(), loop
    )
    assert loop is fut.result()

    async def async_get_running_loop():
      return asyncio.get_running_loop()
    
    fut = asyncio.run_coroutine_threadsafe(
      async_get_running_loop(), loop
    )
    assert loop is fut.result()

  def test_run_coroutine_threadsafe_handling_exception(self):
    """
    """
    loop = asyncio.new_event_loop()
    assert not loop.is_running()
    assert not loop.is_closed()
    
    thread = threading.Thread(target=loop.run_forever)
    thread.daemon = True
    thread.start()
    thread.join(0.1)
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    def raise_RuntimeError():
      raise RuntimeError('What do you do?')
    
    fut = asyncio.run_coroutine_threadsafe(
      asyncio.coroutine(raise_RuntimeError)(), loop
    )
    with self.assertRaises(RuntimeError) as cm:
      fut.result()
    assert str(cm.exception) == 'What do you do?'

    async def async_raise_RuntimeError():
      raise_RuntimeError()
    
    fut = asyncio.run_coroutine_threadsafe(
      async_raise_RuntimeError(), loop
    )
    
    with self.assertRaises(RuntimeError) as cm:
      fut.result()
    assert str(cm.exception) == 'What do you do?'
    
  @staticmethod  
  async def async_ticker_callback(callback_stop_event):
      counter = 0
      print(f'async_ticker_callback started.')
      while not callback_stop_event.is_set():
        try:
          await asyncio.sleep(1)
        except asyncio.CancelledError:
          print(f'async_ticker_callback cancelled: {counter}.')
          raise
        else:
          counter += 1
        print(f'async_ticker_callback tick: {counter}.')
      print(f'async_ticker_callback completed with {counter}.')
      return counter
  
  @staticmethod  
  def ticker_callback(callback_stop_event):
    counter = 0
    print(f'ticker_callback started.')
    while not callback_stop_event.wait(1.0):
      counter += 1
      print(f'ticker_callback tick: {counter}.')
    print(f'ticker_callback completed with {counter}.')
    return counter
    
  def test_run_coroutine_threadsafe_loop_stop_while_async_function_running(self):
    """
    loop.close stop immediately the loop, thus the running coroutine scheduled
    with run_coroutine_threadsafe remain on the pending task
    """
    loop = asyncio.new_event_loop()
    
    thread = threading.Thread(target=loop.run_forever)
    thread.daemon = True
    thread.start()
    thread.join(0.1)
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    asyc_ticker_callback_stop = asyncio.Event(loop=loop)
    
    print(f"run_coroutine_threadsafe")
    fut = asyncio.run_coroutine_threadsafe(
      self.async_ticker_callback(asyc_ticker_callback_stop), loop
    )
    
    print(f"let coroutine run")
    thread.join(2.0)
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    print(f"call_soon_threadsafe(loop.stop)")
    loop.call_soon_threadsafe(loop.stop)
    thread.join(0.1)
    assert not thread.is_alive()
    assert not loop.is_running()
    assert not loop.is_closed()
    
    print(f"loop closed but our task is still there!")
    assert len(asyncio.all_tasks(loop)) == 1
    assert not fut.cancelled()
    assert not fut.done()

    print(f"So _cancel_all_tasks!")    
    _cancel_all_tasks(loop)
    assert len(asyncio.all_tasks(loop)) == 0
    assert fut.cancelled()
    assert fut.done()
    with self.assertRaises(concurrent.futures.CancelledError) as cm:
      fut.result()
    print(f"Indeed fut.result() raise: {type(cm.exception)}")    
    
    loop.close()
    assert not loop.is_running()
    assert loop.is_closed()
  
    
  def test_run_coroutine_threadsafe_cancel_async_function_but_loop_stop(self):
    """
    loop.close stop immediately the loop, thus the running coroutine scheduled
    with run_coroutine_threadsafe and cancel requested could not be have been
    either received or processed py the loop 
    """
    loop = asyncio.new_event_loop()
    
    thread = threading.Thread(target=loop.run_forever)
    thread.daemon = True
    thread.start()
    thread.join(0.1)
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    asyc_ticker_callback_stop = asyncio.Event(loop=loop)
    
    print(f"run_coroutine_threadsafe")
    fut = asyncio.run_coroutine_threadsafe(
      self.async_ticker_callback(asyc_ticker_callback_stop), loop
    )
    
    print(f"let coroutine run")
    thread.join(1.5)
    
    print(f"fut.cancel() and call_soon_threadsafe(loop.stop)")
    assert fut.cancel()
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    with self.assertRaises(concurrent.futures.CancelledError) as cm:
      fut.result()
    print(f'fut.result() exception is: {type(cm.exception)}.')

    loop.call_soon_threadsafe(loop.stop)
    thread.join(0.1)
    assert not thread.is_alive()
    assert not loop.is_running()
    assert not loop.is_closed()
    
    all_task = asyncio.all_tasks(loop)
    
    if all_task:
      print("Our task has not been removed jet!")
      _cancel_all_tasks(loop)

    
    assert not loop.is_closed()
    
    loop.close()
    assert not loop.is_running()
    assert loop.is_closed()
    
  def test_run_coroutine_threadsafe_function_wrapped_in_coroutine(self):
    """
    Running a blocking callback hidden into a coroutine does affect the loop
    anyway, any operation is lock until the blocking code ends!
    """
    loop = asyncio.new_event_loop()
    assert not loop.is_running()
    assert not loop.is_closed()
    
    thread = threading.Thread(target=loop.run_forever)
    thread.daemon = True
    thread.start()
    thread.join(0.1)
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    ticker_callback_stop = threading.Event()
    
    print(f"run_coroutine_threadsafe")
    fut = asyncio.run_coroutine_threadsafe(
      asyncio.coroutine(self.ticker_callback)(ticker_callback_stop), loop
    )
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    assert not fut.done()
    
    print(f"loop.call_soon_threadsafe(loop.stop)")
    loop.call_soon_threadsafe(loop.stop)
    
    print(f"let callback run")
    thread.join(1.5)
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    assert not fut.done()
    
    print(f"ticker_callback_stop.set()")
    ticker_callback_stop.set()
    
    thread.join(0.1)
    assert not thread.is_alive()
    assert not loop.is_running()
    assert not loop.is_closed()
    
    pending_tasks = asyncio.all_tasks(loop)
    assert not pending_tasks
    
    loop.close()
    assert not loop.is_running()
    assert loop.is_closed()
    
  def test_run_in_executor(self):
    loop = asyncio.new_event_loop()
    assert not loop.is_running()
    assert not loop.is_closed()
    
    thread = threading.Thread(target=loop.run_forever)
    thread.daemon = True
    thread.start()
    thread.join(0.1)
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    ticker_callback_stop = threading.Event()
    
    print(f"run_coroutine_threadsafe")
    fut = loop.run_in_executor(None, self.ticker_callback, ticker_callback_stop)
    assert not fut.done()
    assert not fut.cancelled()

    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    asyc_ticker_callback_stop = asyncio.Event(loop=loop)
    
    async_fut = asyncio.run_coroutine_threadsafe(
      self.async_ticker_callback(asyc_ticker_callback_stop), loop
    )
    assert not async_fut.done()
    assert not async_fut.cancelled()
    
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    
    print(f"let callbacks run")
    thread.join(5)
    assert thread.is_alive()
    assert loop.is_running()
    assert not loop.is_closed()
    assert not fut.done()
    
    assert fut.cancel()
    print(f"let fut.cancel() work")
    thread.join(5)
    
    assert async_fut.cancel()
    print(f"let async_fut.cancel() work")
    thread.join(5)
    
    print(f"ticker_callback_stop.set()")
    ticker_callback_stop.set()
    
    print(f"loop.call_soon_threadsafe(loop.stop)")
    loop.call_soon_threadsafe(loop.stop)
    
    thread.join(0.1)
    assert not thread.is_alive()
    assert not loop.is_running()
    assert not loop.is_closed()
    
    pending_tasks = asyncio.all_tasks(loop)
    assert not pending_tasks
    
    loop.close()
    assert not loop.is_running()
    assert loop.is_closed()
    
  
if __name__ == "__main__":
  #import sys;sys.argv = ['', 'Test.testName']
  unittest.main()