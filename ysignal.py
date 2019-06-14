'''
Created on 28 Jan 2013

@author: Dave Wilson
'''


import inspect
import weakref


class Ysignal(object):

    '''WeakRef Signal/Slots'''

    def __init__(self):
        '''Initialise attributes to store observers'''
        self._functions = weakref.WeakSet()
        self._methods = weakref.WeakKeyDictionary()

    def emit_slot(self, slot, *args, **kwargs):
        '''emit a signal to the passed in slot only'''
        slot(*args, **kwargs)

    def emit(self, *args, **kwargs):
        '''emit a signal to all slots'''
        self._emit_functions(*args, **kwargs)
        self._emit_methods(*args, **kwargs)

    def _emit_functions(self, *args, **kwargs):
        '''Emits a signal to any Function slots'''
        for func in tuple(self._functions):
            func(*args, **kwargs)

    def _emit_methods(self, *args, **kwargs):
        '''Emits a signal to any Method slots'''
        for obj, funcs in self._methods.items():
            for func in tuple(funcs):
                method = getattr(obj, func.__name__)
                method(*args, **kwargs)

    def bind(self, slot):
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
        if inspect.ismethod(slot):
            self._unbind_method(slot)
        else:
            self._unbind_function(slot)

    def _unbind_function(self, slot):
        '''Remove a Function slot'''
        try:
            self._functions.remove(slot)
        except (ValueError, KeyError):
            pass

    def _unbind_method(self, slot):
        '''Remove a Method slot'''
        try:
            self._methods[slot.__self__].remove(slot.__func__)
        except (ValueError, KeyError):
            pass

    def unbind_all(self):
        '''Remove all slots'''
        self._functions.clear()
        self._methods.clear()
