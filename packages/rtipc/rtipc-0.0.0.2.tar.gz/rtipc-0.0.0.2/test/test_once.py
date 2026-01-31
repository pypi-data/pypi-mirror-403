import numpy
import ctypes
import rtipc

def test_once_1():
    rtipcObj = rtipc.RtIPC('simulator')
    rtipcGroup = rtipcObj.CreateGroup(1.0)
    receiveMemory = numpy.zeros(16, numpy.uint8)
    sendMemory = numpy.zeros(16, numpy.uint8)
    connected = ctypes.c_uint8(0)
    rtipcGroup.AddReceivePdo(b'receive', rtipc.DataType.uint8_T, receiveMemory.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)), 16, ctypes.byref(connected))
    rtipcGroup.AddSendPdo(b'send', rtipc.DataType.uint8_T, sendMemory.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)), 16)

    with rtipcObj:
        rtipcGroup.Receive()
        rtipcGroup.Send()

def test_once_2():
    # the same test as test_once_1 but to confirm that RtIPC.__exit__ cleaned up successfully
    # requires https://gitlab.com/etherlab.org/rtipc/-/merge_requests/7
    rtipcObj = rtipc.RtIPC('simulator')
    rtipcGroup = rtipcObj.CreateGroup(1.0)
    receiveMemory = numpy.zeros(16, numpy.uint8)
    sendMemory = numpy.zeros(16, numpy.uint8)
    connected = ctypes.c_uint8(0)
    rtipcGroup.AddReceivePdo(b'receive', rtipc.DataType.uint8_T, receiveMemory.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)), 16, ctypes.byref(connected))
    rtipcGroup.AddSendPdo(b'send', rtipc.DataType.uint8_T, sendMemory.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)), 16)

    with rtipcObj:
        rtipcGroup.Receive()
        rtipcGroup.Send()
