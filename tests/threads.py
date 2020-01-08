'''
Created on 15 nov 2019

@author: Andrea
'''
import threading
import functools 

def trace_thread_name(fun):
  @functools.wraps(fun)
  def _decorated(*args, **kwargs):
    print(f"Running '{fun.__name__}' on '{threading.current_thread().name}'.")
    return fun(*args, **kwargs)
  return _decorated