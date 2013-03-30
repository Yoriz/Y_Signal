'''
Created on 28 Jan 2013

@author: Dave Wilson
'''

from concurrent.futures import ThreadPoolExecutor, wait
from weakref import WeakSet, WeakKeyDictionary
import inspect


THREAD_POOL_EXECUTOR = ThreadPoolExecutor(max_workers=2)


class Ysignal(object):
    '''WeakRef Signal/Slots that uses a single threaded pool if required'''
    def __init__(self, useThread=True):
        '''Initialise attributes to store observers'''
        self._functions = WeakSet()
        self._methods = WeakKeyDictionary()
        self.useThread = useThread
        self.threadPoolExe = THREAD_POOL_EXECUTOR

    def slotCheck(self, future):
        '''Raises an exception if an error occurred during the future call'''
        future.result()

    def waitInQueue(self):
        '''Wait in queue for signals to complete'''
        future = self.threadPoolExe.submit(lambda: object)
        wait((future,))

    def shutDownQueue(self):
        self.threadPoolExe.shutdown()

    def waitTillQueueEmpty(self):
        '''Wait till the queue is empty (not reliable!)'''
        while not self.threadPoolExe._work_queue.empty():
            print 'Waiting in waitTillEndQueue'
            self.waitInQueue()
        self.waitInQueue()

    def emitSlot(self, slot, *args, **kwargs):
        '''emit a signal to the passed in slot only'''
        if self.useThread:
            future = self.threadPoolExe.submit(slot, *args, **kwargs)
            future.add_done_callback(self.slotCheck)
            return future
        else:
            slot(*args, **kwargs)

    def emit(self, *args, **kwargs):
        '''emit a signal to all slots'''
        if self.useThread:
            future = self.threadPoolExe.submit(self._emitCall, *args, **kwargs)
            future.add_done_callback(self.slotCheck)
            return future
        else:
            self._emitCall(*args, **kwargs)

    def _emitCall(self, *args, **kwargs):
        '''Emit a signal to all slots'''
        self._emitFunctions(*args, **kwargs)
        self._emitMethods(*args, **kwargs)

    def _emitFunctions(self, *args, **kwargs):
        '''Emits a signal to any Function slots'''
        for func in self._functions:
            func(*args, **kwargs)

    def _emitMethods(self, *args, **kwargs):
        '''Emits a signal to any Method slots'''
        for obj, funcs in self._methods.items():
            for func in funcs:
                method = getattr(obj, func.func_name)
                method(*args, **kwargs)

    def bind(self, slot):
        '''Add a slot to the list of listeners'''
        if self.useThread:
            future = self.threadPoolExe.submit(self._bindCall, slot)
            future.add_done_callback(self.slotCheck)
            return future
        else:
            self._bindCall(slot)

    def _bindCall(self, slot):
        '''Add a slot to the list of listeners'''
        if inspect.ismethod(slot):
            self._bindMethod(slot)
        else:
            self._bindFunction(slot)

    def _bindFunction(self, slot):
        '''Add a Function slot'''
        self._functions.add(slot)

    def _bindMethod(self, slot):
        '''Add a Method slot'''
        try:
            self._methods[slot.__self__].add(slot.__func__)
        except KeyError:
            self._methods[slot.__self__] = set()
            self._bindMethod(slot)

    def unbind(self, slot):
        '''Remove slot from the list of listeners'''
        if self.useThread:
            future = self.threadPoolExe.submit(self._unbindCall, slot)
            future.add_done_callback(self.slotCheck)
            return future
        else:
            self._unbindCall(slot)

    def _unbindCall(self, slot):
        '''Remove slot from the list of listeners'''
        if inspect.ismethod(slot):
            self._unbindMethod(slot)
        else:
            self._unbindFunction(slot)

    def _unbindFunction(self, slot):
        '''Remove a Function slot'''
        try:
            self._functions.remove(slot)
        except ValueError:
            pass

    def _unbindMethod(self, slot):
        '''Remove a Method slot'''
        try:
            self._methods[slot.__self__].remove(slot.__func__)
        except (ValueError, KeyError):
            pass

    def unbindAll(self):
        '''Remove all slots'''
        if self.useThread:
            future = self.threadPoolExe.submit(self._unbindAllCall)
            future.add_done_callback(self.slotCheck)
            return future
        else:
            self._unbindAllCall()

    def _unbindAllCall(self):
        '''Remove all slots'''
        self._functions.clear()
        self._methods.clear()
