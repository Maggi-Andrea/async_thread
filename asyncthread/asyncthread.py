"""Main module."""
'''
Created on 14 nov 2019

@author: Andrea
'''
import asyncio
import threading
import itertools
from asyncio.events import AbstractEventLoop
import concurrent.futures
import logging

from typing import ( #pylint: disable=unused-import
  Any, #@UnusedImport
  Coroutine, #@UnusedImport
  Callable,
  TypeVar, #@UnusedImport
  Awaitable, #@UnusedImport
)

_LOGGER = logging.getLogger(__name__)

counter = itertools.count().__next__
counter()

def _set_concurrent_future_state(dest, source):
  """Copy state from a future to a dest.futures.Future."""
  assert source.done()
  if source.cancelled():
    dest.cancel()
  if not dest.set_running_or_notify_cancel():
    return
  exception = source.exception()
  if exception is not None:
    dest.set_exception(exception)
  else:
    result = source.result()
    dest.set_result(result)


def _copy_future_state(source, dest):
  """Internal helper to copy state from another Future.

  The other Future may be a concurrent.futures.Future.
  """
  assert source.done()
  if dest.cancelled():
    return
  assert not dest.done()
  if source.cancelled():
    dest.cancel()
  else:
    exception = source.exception()
    if exception is not None:
      dest.set_exception(exception)
    else:
      result = source.result()
      dest.set_result(result)

def _chain_future(source, destination):
  """Chain two futures so that when one completes, so does the other.

  The result (or exception) of source will be copied to destination.
  If destination is cancelled, source gets cancelled too.
  Compatible with both asyncio.Future and concurrent.futures.Future.
  """
  _get_loop = asyncio.futures._get_loop #pylint: disable=protected-access
  isfuture = asyncio.isfuture
  
  if not isfuture(source) and not isinstance(source,
                                            concurrent.futures.Future):
    raise TypeError('A future is required for source argument')
  if not isfuture(destination) and not isinstance(destination,
                                            concurrent.futures.Future):
    raise TypeError('A future is required for destination argument')
  source_loop = _get_loop(source) if isfuture(source) else None
  dest_loop = _get_loop(destination) if isfuture(destination) else None

  def _set_state(future, other):
    if isfuture(future):
      _copy_future_state(other, future)
    else:
      _copy_future_state(other, future)
#        _set_concurrent_future_state(future, other)

  def _call_check_cancel(destination):
    if destination.cancelled():
      if source_loop is None or source_loop is dest_loop:
        source.cancel()
      else:
        source_loop.call_soon_threadsafe(source.cancel)

  def _call_set_state(source):
    if (destination.cancelled() and
        dest_loop is not None and dest_loop.is_closed()):
      return
    if dest_loop is None or dest_loop is source_loop:
      _set_state(destination, source)
    else:
      dest_loop.call_soon_threadsafe(_set_state, destination, source)

  destination.add_done_callback(_call_check_cancel)
  source.add_done_callback(_call_set_state)

def run_coroutine_threadsafe(
    coro,
    loop: AbstractEventLoop,
)-> concurrent.futures.Future:
  """Submit a coroutine object to a given event loop.

  Return a concurrent.futures.Future to access the result.
  """
  if not asyncio.coroutines.iscoroutine(coro):
    raise TypeError('A coroutine object is required')
  future = concurrent.futures.Future()
  def callback():
    try:
      if future.set_running_or_notify_cancel():
        _chain_future(asyncio.tasks.ensure_future(coro, loop=loop), future)
    except Exception as exc:
      future.set_exception(exc)
      raise
  loop.call_soon_threadsafe(callback)
  return future

def run_callback_threadsafe(
  loop: AbstractEventLoop,
  callback: Callable,
  *args: Any
) -> concurrent.futures.Future:
  """Submit a callback object to a given event loop.

  Return a concurrent.futures.Future to access the result.
  """
  ident = loop.__dict__.get("_thread_ident")
  if ident is not None and ident == threading.get_ident():
    raise RuntimeError("Cannot be called from within the event loop")

  future: concurrent.futures.Future = concurrent.futures.Future()

  def run_callback() -> None:
    """Run callback and store result."""
    try:
      if future.set_running_or_notify_cancel():
        future.set_result(callback(*args))
    except Exception as exc:  # pylint: disable=broad-except
      future.set_exception(exc)

  loop.call_soon_threadsafe(run_callback)
  return future

def _cancel_all_tasks(loop):
  to_cancel = asyncio.all_tasks(loop)
  if not to_cancel:
    return
  for task in to_cancel:
    task.cancel()
  loop.run_until_complete(
    asyncio.gather(*to_cancel, loop=loop, return_exceptions=True)
  )
  for task in to_cancel:
    if task.cancelled():
      continue
    if task.exception() is not None:
      loop.call_exception_handler({
        'message': 'unhandled exception during asyncio.run() shutdown',
        'exception': task.exception(),
        'task': task,
      })

class AsyncThread(threading.Thread):
      
  def __init__(self, *, loop=None, debug=False):
    super().__init__(
      name=f'AsyncThread-{counter()}',
      daemon=True)
    ...
    self.debug = debug
    self.loop = loop
    self._started = threading.Event()
    
  def run(self):
    self.loop = loop = self.loop or asyncio.new_event_loop()
    try:
      asyncio.set_event_loop(loop)
      loop.set_debug(self.debug)
      loop.run_forever()
    finally:
      try:
        self._cancel_all_tasks()
        self.loop.run_until_complete(loop.shutdown_asyncgens())
      finally:
        asyncio.set_event_loop(None)
        loop.close()
  
  def stop(self, timeout=None):
    loop = self.loop
    assert loop
    loop.call_soon_threadsafe(loop.stop)
    if timeout is False:
      return
    self.join(timeout)
      
  def run_callback_threadsafe(self, callback, *args):
    return run_callback_threadsafe(self.loop, callback, *args)
      
  def run_coroutine_threadsafe(self, coro):
    return run_coroutine_threadsafe(coro, self.loop)
    return asyncio.run_coroutine_threadsafe(coro, loop=self.loop)
  
  def wait_for_threadsafe(self, coro, timeout=None):
    coro = asyncio.wait_for(coro, timeout, loop=self.loop)
    return run_coroutine_threadsafe(coro, self.loop).result()
  
  def _cancel_all_tasks(self):
    _cancel_all_tasks(self.loop)
    
  def shield(self, coro):
    return asyncio.shield(coro, loop=self.loop)
