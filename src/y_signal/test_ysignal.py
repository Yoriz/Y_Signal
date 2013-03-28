'''
Created on 27 Mar 2013

@author: Dave Wilson
'''

from y_signal.ysignal import Ysignal
import time
import unittest


class TestYsignal(unittest.TestCase):

    def setUp(self):
        self.signal = Ysignal(False)
        self.attr1 = None
        self.attr2 = None
        self.attr3 = 0

    def tearDown(self):
        pass

    def setAttr1(self, value):
        self.attr1 = value

    def methodForTest(self):
        pass

    def methodAdd(self):
        time.sleep(0.25)
        self.attr3 += 1

    def methodRaise(self):
        raise ValueError('Raised ValueError')

    def testConnectFunction(self):
        def testFunction():
            pass
        func = testFunction
        self.signal.bind(func)
        self.signal.waitInQueue()
        self.assertSetEqual(set((func,)), self.signal._functions)

    def testConnectMethod(self):
        self.signal.bind(self.setAttr1)
        self.signal.waitInQueue()
        self.assertIn(self, self.signal._methods)
        funcs = self.signal._methods.get(self, set())
        self.assertIn(self.setAttr1.__func__, funcs)

    def testEmitFunction(self):
        value = 'EmitFunction'

        def testFunction(value):
            self.attr1 = value
        self.signal.bind(testFunction)
        self.signal.emit(value=value)
        self.signal.waitInQueue()
        self.assertEqual(self.attr1, value)

    def testEmitMethod(self):
        value = 'EmitMethod'
        self.signal.bind(self.setAttr1)
        self.signal.emit(value=value)
        self.signal.waitInQueue()
        self.assertEqual(self.attr1, value)

    def testEmitFunctionAndMethod(self):
        value = 'EmitBothTypes'

        def testFunction(value):
            self.attr2 = value
        self.signal.bind(testFunction)
        self.signal.bind(self.setAttr1)
        self.signal.emit(value=value)
        self.signal.waitInQueue()
        self.assertEqual(self.attr1, value)
        self.assertEqual(self.attr2, value)

    def testEmitSlotFunction(self):
        value = 'EmitSlotFunction'

        def testFunction(value):
            self.attr1 = value

        self.signal.emitSlot(testFunction, value=value)
        self.signal.waitInQueue()
        self.assertEqual(self.attr1, value)

    def testEmitSlotMethod(self):
        value = 'EmitMethod'
        self.signal.emitSlot(self.setAttr1, value=value)
        self.signal.waitInQueue()
        self.assertEqual(self.attr1, value)

    def testWaitInQueue(self):
        self.signal.emitSlot(self.methodAdd)
        self.signal.waitInQueue()
        self.assertEqual(self.attr3, 1)

    def testRaiseError(self):
        if self.signal.useThread:
            self.signal.slotCheck = lambda future: True
            future = self.signal.emitSlot(self.methodRaise)
            self.signal.waitInQueue()
            self.assertRaises(ValueError, future.result)

    def testDisconnectSlotFunction(self):
        def testFunction():
            pass

        def testFunction2():
            pass

        func = testFunction
        func2 = testFunction2
        self.signal.bind(func)
        self.signal.bind(func2)
        self.signal.waitInQueue()
        self.assertSetEqual(set((func, func2)), self.signal._functions)
        self.signal.unbind(func2)
        self.signal.waitInQueue()
        self.assertSetEqual(set((func,)), self.signal._functions)

    def testDisconnectSlotMethod(self):
        self.signal.bind(self.setAttr1)
        self.signal.bind(self.methodForTest)
        self.signal.waitInQueue()
        self.assertIn(self, self.signal._methods)
        funcs = self.signal._methods.get(self, [])
        self.assertSetEqual(set((self.setAttr1.__func__,
                                self.methodForTest.__func__)), funcs)
        self.signal.unbind(self.methodForTest)
        self.signal.waitInQueue()
        funcs = self.signal._methods.get(self, set())
        self.assertSetEqual(set((self.setAttr1.__func__,)), funcs)

    def testDisconnectAll(self):
        def testFunction():
            pass

        def testFunction2():
            pass

        func = testFunction
        func2 = testFunction2
        self.signal.bind(func)
        self.signal.bind(func2)
        self.signal.bind(self.setAttr1)
        self.signal.bind(self.methodForTest)
        self.signal.unbindAll()
        self.signal.waitInQueue()
        self.assertSetEqual(set(), self.signal._functions)
        funcs = self.signal._methods.get(self, set())
        self.assertSetEqual(set(), funcs)


if __name__ == '__main__':
    unittest.main()
