'''
Created on 15 nov 2019

@author: Andrea
'''

import time
import functools

def times():
  _times_dic = {
    'monotonic':time.monotonic(), 
#    'clock':time.clock(), 
    'time':time.time(), 
    'time_ns':time.time_ns(), 
    'perf_counter_ns':time.perf_counter_ns(), 
    'process_time_ns':time.process_time_ns(), 
    'thread_time_ns':time.thread_time_ns(), 
    'gmtime':time.gmtime(),
  }
  return _times_dic


__time_label_l = max(map(len, times()))  


def display_times_in(name, times=times()):
  stamps = []
  for label, data in times.items():
    stamp = f'{name} {label:{__time_label_l+1}} in: {data}'
    stamps.append(stamp)
    print(stamp)
  print('-' * max(map(len, stamps)))
  return times


def display_times_out(name, times_in, times_out=times()):
  for label, data in times_in.items():
    if isinstance(data, tuple):
      delta = type(data)([times_out[label][i] - d for i, d in enumerate(data)])
    else:
      delta = times_out[label] - data
    print(f'{name} {label:{__time_label_l}s} out: {delta}')
  return times_out


class Timers:
  
  def __init__(self, name=None, ts=times):
    self.name = name or 'Timers'
    self.ts = ts or (lambda: {'time' : time.time(),})
    
  def __call__(self):
    """ Return the current time """
    return self.ts()
  
  def __enter__(self):
    """ Set the start time """
    self.start = display_times_in(self.name, self())
    return self
  
  def __exit__(self, exc_type, exc_value, exc_traceback):
    self.end = display_times_out(self.name, self.start, self())
    print('\n')
    
  @property
  def elapsed(self):
    """ Return the current elapsed time since start
    If the `elapsed` property is called in the context manager scope,
    the elapsed time bewteen start and property access is returned.
    However, if it is accessed outside of the context manager scope,
    it returns the elapsed time bewteen entering and exiting the scope.
    The `elapsed` property can thus be accessed at different points within
    the context manager scope, to time different parts of the block.
    """
    if self.end is None:
      # if elapsed is called in the context manager scope
      return (self() - self.start) * self.factor
    else:
      # if elapsed is called out of the context manager scope
      return (self.end - self.start) * self.factor


def display_execution_times(fun, ts=None):

  @functools.wraps(fun)
  def _decorator(*args, **kwargs):
    with Timers(name=fun.__name__, ts=ts):
      return fun(*args, **kwargs)
  return _decorator


