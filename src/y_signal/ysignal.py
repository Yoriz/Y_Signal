'''
Created on 28 Jan 2013

@author: Dave Wilson
'''

from concurrent.futures import ThreadPoolExecutor, wait
from concurrent.futures._base import Future
from weakref import WeakSet, WeakKeyDictionary
import inspect


class ThreadLessExecutor(object):
    '''Creates a threadless executor'''
    def __init__(self):

        class WorkQueue(object):
            def empty(self):
                return True
        self._work_queue = WorkQueue()

    def submit(self, slot, *args, **kwargs):
        future = Future()
        try:
            slot(*args, **kwargs)
            future.set_result('')
        except Exception as exception:
            future.set_exception(exception)

        return future


class Ysignal(object):
    '''WeakRef Threaded Queued Signal/Slots'''
    def __init__(self, thread=True):
        '''Initialise attributes to store observers'''
        self._functions = WeakSet()
        self._methods = WeakKeyDictionary()
        if thread:
            self.signalExe = ThreadPoolExecutor(max_workers=1)
        else:
            self.signalExe = ThreadLessExecutor()

    def slotCheck(self, future):
        '''Raises an exception if an error occurred during the future call'''
        future.result()

    def waitInQueue(self):
        '''Wait in queue for signals to complete'''
        future = self.signalExe.submit(lambda: object)
        wait((future,))

    def shutDownQueue(self):
        self.signalExe.shutdown()

    def waitTillQueueEmpty(self):
        '''Wait till the queue is empty (not reliable!)'''
        while not self.signalExe._work_queue.empty():
            print 'Waiting in waitTillEndQueue'
            self.waitInQueue()
        self.waitInQueue()

    def emitSlot(self, slot, *args, **kwargs):
        '''Add a specified slot only signal to the queue'''
        future = self.signalExe.submit(slot, *args, **kwargs)
        future.add_done_callback(self.slotCheck)
        return future

    def emit(self, *args, **kwargs):
        '''Add a emit signal all slots to the queue'''
        future = self.signalExe.submit(self._emitCall, *args, **kwargs)
        future.add_done_callback(self.slotCheck)
        return future

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
        for obj, funcs in self._methods.iteritems():
            for func in funcs:
                method = getattr(obj, func.func_name)
                method(*args, **kwargs)

    def bind(self, slot):
        '''Add a slot to the queue'''
        future = self.signalExe.submit(self._bindCall, slot)
        future.add_done_callback(self.slotCheck)
        return future

    def _bindCall(self, slot):
        '''Add a slot'''
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
        '''Add a Remove slot to the queue'''
        future = self.signalExe.submit(self._unbindCall, slot)
        future.add_done_callback(self.slotCheck)
        return future

    def _unbindCall(self, slot):
        '''Remove a slot'''
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
        '''Add remove all slots to the queue'''
        future = self.signalExe.submit(self._unbindAllCall)
        future.add_done_callback(self.slotCheck)
        return future

    def _unbindAllCall(self):
        '''unbind all slots'''
        self._functions.clear()
        self._methods.clear()
