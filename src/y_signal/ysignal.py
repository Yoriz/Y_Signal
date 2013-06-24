'''
Created on 28 Jan 2013

@author: Dave Wilson
'''

from weakref import WeakSet, WeakKeyDictionary
import inspect
from Queue import Queue, Empty
from threading import Thread, Lock


class _ThreadWorker(object):
    def __init__(self, func, *args, **kwargs):
        self.class_ = func
        self.args = args
        self.kwargs = kwargs


class QThread(Thread):
    '''
    A thread that that picks off and calls items from the passed in queue until
    there are no items left
    '''
    def __init__(self, queue, lock):
        '''

        :param queue: An instance of a QueuedThread
        :param lock: The thread lock to use with this thread
        '''
        Thread.__init__(self)
        self.daemon = False
        self.queue = queue
        self.lock = lock
        self.start()

    def run(self):
        self.queue.threadRunning = True
        while not self.queue.empty():
            with self.lock:
                try:
                    item = self.queue.get_nowait()
                    item.class_(*item.args, **item.kwargs)
                    self.queue.task_done()
                except Empty:
                    pass
        self.queue.threadRunning = False


class QueuedThread(Queue):
    def __init__(self):
        Queue.__init__(self)
        self.threadRunning = False

    def createThread(self):
        self.thread = QThread(self, Lock())

    def submit(self, func, *args, **kwargs):
        self.put(_ThreadWorker(func, *args, **kwargs))
        if not self.threadRunning:
            self.createThread()

    def waitThreadNotRunning(self):
        self.join()


queuedThread = QueuedThread()


class Ysignal(object):
    '''WeakRef Signal/Slots that uses a single threaded pool if required'''
    def __init__(self, useThread=True):
        '''Initialise attributes to store observers'''
        self._functions = WeakSet()
        self._methods = WeakKeyDictionary()
        self.useThread = useThread
        self.queuedThread = queuedThread

    def slotCheck(self, future):
        '''Raises an exception if an error occurred during the future call'''
        future.result()

    def waitInQueue(self):
        '''Wait in queue for signals to complete'''
        self.queuedThread.waitThreadNotRunning()

    def shutDownQueue(self):
        self.queuedThread.shutdown()

#     def waitTillQueueEmpty(self):
#         '''Wait till the queue is empty (not reliable!)'''
#         while not self.queuedThread._work_queue.empty():
#             print 'Waiting in waitTillEndQueue'
#             self.waitInQueue()
#         self.waitInQueue()

    def emitSlot(self, slot, *args, **kwargs):
        '''emit a signal to the passed in slot only'''
        if self.useThread:
            self.queuedThread.submit(slot, *args, **kwargs)

        else:
            slot(*args, **kwargs)

    def emit(self, *args, **kwargs):
        '''emit a signal to all slots'''
        if self.useThread:
            self.queuedThread.submit(self._emitCall, *args, **kwargs)

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
            self.queuedThread.submit(self._bindCall, slot)

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
            self.queuedThread.submit(self._unbindCall, slot)

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
            self.queuedThread.submit(self._unbindAllCall)

        else:
            self._unbindAllCall()

    def _unbindAllCall(self):
        '''Remove all slots'''
        self._functions.clear()
        self._methods.clear()
