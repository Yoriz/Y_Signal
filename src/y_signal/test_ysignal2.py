'''
Created on 27 Mar 2013

@author: Dave Wilson
'''

import y_signal.ysignal2 as ysignal
import time
import unittest


class TestYsignal(unittest.TestCase):

    def setUp(self):
        self.signal = ysignal.Ysignal()
        self.attr1 = None
        self.attr2 = None
        self.attr3 = 0

    def tearDown(self):
        pass

    def set_attr1(self, value):
        self.attr1 = value

    def method_for_test(self):
        pass

    def test_connect_function(self):
        def test_function():
            pass
        func = test_function
        self.signal.bind(func)
        self.assertSetEqual(set((func,)), self.signal._functions)

    def test_connect_method(self):
        self.signal.bind(self.set_attr1)
        self.assertIn(self, self.signal._methods)
        funcs = self.signal._methods.get(self, set())
        self.assertIn(self.set_attr1.__func__, funcs)

    def test_emit_function(self):
        value = 'EmitFunction'

        def test_function(value):
            self.attr1 = value

        self.signal.bind(test_function)
        self.signal.emit(value=value)
        self.assertEqual(self.attr1, value)

    def test_emit_method(self):
        value = 'EmitMethod'
        self.signal.bind(self.set_attr1)
        self.signal.emit(value=value)
        self.assertEqual(self.attr1, value)

    def test_emit_function_and_method(self):
        value = 'EmitBothTypes'

        def test_function(value):
            self.attr2 = value

        self.signal.bind(test_function)
        self.signal.bind(self.set_attr1)
        self.signal.emit(value=value)
        self.assertEqual(self.attr1, value)
        self.assertEqual(self.attr2, value)

    def test_emit_slot_function(self):
        value = 'EmitSlotFunction'

        def test_function(value):
            self.attr1 = value

        self.signal.emit_slot(test_function, value=value)
        self.assertEqual(self.attr1, value)

    def test_emit_slot_method(self):
        value = 'EmitMethod'
        self.signal.emit_slot(self.set_attr1, value=value)
        self.assertEqual(self.attr1, value)

    def test_disconnect_slot_function(self):
        def test_function():
            pass

        def test_function2():
            pass

        func = test_function
        func2 = test_function2
        self.signal.bind(func)
        self.signal.bind(func2)
        self.assertSetEqual(set((func, func2)), self.signal._functions)
        self.signal.unbind(func2)
        self.assertSetEqual(set((func,)), self.signal._functions)

    def test_disconnect_slot_method(self):
        self.signal.bind(self.set_attr1)
        self.signal.bind(self.method_for_test)
        self.assertIn(self, self.signal._methods)
        funcs = self.signal._methods.get(self, [])
        self.assertSetEqual(set((self.set_attr1.__func__,
                                self.method_for_test.__func__)), funcs)
        self.signal.unbind(self.method_for_test)

        funcs = self.signal._methods.get(self, set())
        self.assertSetEqual(set((self.set_attr1.__func__,)), funcs)

    def test_disconnect_all(self):
        def test_function():
            pass

        def test_function2():
            pass

        func = test_function
        func2 = test_function2
        self.signal.bind(func)
        self.signal.bind(func2)
        self.signal.bind(self.set_attr1)
        self.signal.bind(self.method_for_test)
        self.signal.unbind_all()
        self.assertSetEqual(set(), self.signal._functions)
        funcs = self.signal._methods.get(self, set())
        self.assertSetEqual(set(), funcs)


if __name__ == '__main__':
    unittest.main()
