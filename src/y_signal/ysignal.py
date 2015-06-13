'''
Created on 28 Jan 2013

@author: Dave Wilson
'''

import Queue as queue
import collections
import inspect
import threading
import weakref

worker = collections.namedtuple('Worker', 'func args kwargs')


class QThread(threading.Thread):
    '''
    A thread that picks off and calls items from the passed in queue until
    there are no items left
    '''
    def __init__(self, queued_thread):
        threading.Thread.__init__(self)
        self.daemon = False
        self.queue = queued_thread
        self.start()

    def run(self):
        self.queue.threadRunning = True
        while not self.queue.empty():
            try:
                item = self.queue.get_nowait()
                item.func(*item.args, **item.kwargs)
                self.queue.task_done()
            except queue.Empty:
                pass
        self.queue.threadRunning = False


class QueuedThread(queue.Queue):
    def __init__(self):
        queue.Queue.__init__(self)
        self.threadRunning = False

    def submit(self, func, *args, **kwargs):
        self.put(worker(func, args, kwargs))
        if not self.threadRunning:
            QThread(self)

    def waitThreadNotRunning(self):
        self.join()


class Ysignal(object):
    '''WeakRef Signal/Slots that uses a queued thread if required'''
    def __init__(self, queued_thread=None):
        '''Initialise attributes to store observers'''
        self._functions = weakref.WeakSet()
        self._methods = weakref.WeakKeyDictionary()
        self.queued_thread = queued_thread

    def wait_in_queue(self):
        '''Wait in queue for signals to complete'''
        self.queued_thread.waitThreadNotRunning()

    def emit_slot(self, slot, *args, **kwargs):
        '''emit a signal to the passed in slot only'''
        if self.queued_thread:
            self.queued_thread.submit(slot, *args, **kwargs)

        else:
            slot(*args, **kwargs)

    def emit(self, *args, **kwargs):
        '''emit a signal to all slots'''
        if self.queued_thread:
            self.queued_thread.submit(self._emit_call, *args, **kwargs)

        else:
            self._emit_call(*args, **kwargs)

    def _emit_call(self, *args, **kwargs):
        '''Emit a signal to all slots'''
        self._emit_functions(*args, **kwargs)
        self._emitMethods(*args, **kwargs)

    def _emit_functions(self, *args, **kwargs):
        '''Emits a signal to any Function slots'''
        for func in tuple(self._functions):
            func(*args, **kwargs)

    def _emitMethods(self, *args, **kwargs):
        '''Emits a signal to any Method slots'''
        for obj, funcs in self._methods.items():
            for func in tuple(funcs):
                method = getattr(obj, func.func_name)
                method(*args, **kwargs)

    def bind(self, slot):
        '''Add a slot to the list of listeners'''
        if self.queued_thread:
            self.queued_thread.submit(self._bind_call, slot)

        else:
            self._bind_call(slot)

    def _bind_call(self, slot):
        '''Add a slot to the list of listeners'''
        if inspect.ismethod(slot):
            self._bind_method(slot)
        else:
            self._bind_function(slot)

    def _bind_function(self, slot):
        '''Add a Function slot'''
        self._functions.add(slot)

    def _bind_method(self, slot):
        '''Add a Method slot'''
        try:
            self._methods[slot.__self__].add(slot.__func__)
        except KeyError:
            self._methods[slot.__self__] = set()
            self._bind_method(slot)

    def unbind(self, slot):
        '''Remove slot from the list of listeners'''
        if self.queued_thread:
            self.queued_thread.submit(self._unbind_call, slot)

        else:
            self._unbind_call(slot)

    def _unbind_call(self, slot):
        '''Remove slot from the list of listeners'''
        if inspect.ismethod(slot):
            self._unbind_method(slot)
        else:
            self._unbind_function(slot)

    def _unbind_function(self, slot):
        '''Remove a Function slot'''
        try:
            self._functions.remove(slot)
        except ValueError:
            pass

    def _unbind_method(self, slot):
        '''Remove a Method slot'''
        try:
            self._methods[slot.__self__].remove(slot.__func__)
        except (ValueError, KeyError):
            pass

    def unbind_all(self):
        '''Remove all slots'''
        if self.queued_thread:
            self.queued_thread.submit(self._unbind_all_call)

        else:
            self._unbind_all_call()

    def _unbind_all_call(self):
        '''Remove all slots'''
        self._functions.clear()
        self._methods.clear()
