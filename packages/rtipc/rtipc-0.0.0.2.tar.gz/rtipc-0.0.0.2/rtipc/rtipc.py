# rtipc.py - a binding for https://gitlab.com/etherlab.org/rtipc

import ctypes

from stat import S_IRUSR
from stat import S_IWUSR
from os import environ
from os.path import join
from six import ensure_binary

try:
    from enum import IntEnum
except ImportError:
    from aenum import IntEnum

# libc

class IPC(IntEnum):
    RMID = 0
    SET = 1
    STAT = 2
    INFO = 3

libc = ctypes.CDLL('libc.so.6', use_errno=True)

def _RemoveShm(path):
    shmkey = libc.ftok(ensure_binary(path), 1)
    if shmkey == -1:
        return  # path not available, not interested
    shmid = libc.shmget(shmkey, 0, S_IRUSR | S_IWUSR)
    if shmid == -1:
        return  # shm already removed
    assert 0 == libc.shmctl(shmid, IPC.RMID, None)
    semid = libc.semget(shmkey, 0, S_IRUSR | S_IWUSR)
    if semid == -1:
        return  # sem already removed
    assert 0 == libc.semctl(semid, 0, IPC.RMID)

def RemoveShm(ecName):
    ecHomeDir = environ.get('FAKE_EC_HOMEDIR', '/tmp/FakeEtherCAT')
    _RemoveShm(join(ecHomeDir, ecName+'.conf'))

# librtipc

class Direction(IntEnum):
    # ec_direction_t
    Invalid = 0
    Output = 1
    Input = 2

class DataType(IntEnum):
    # rtipc_datatype_t
    double_T = 1
    single_T = 2
    uint8_T = 3
    sint8_T = 4
    uint16_T = 5
    sint16_T = 6
    uint32_T = 7
    sint32_T = 8
    uint64_T = 9
    sint64_T = 10
    boolean_T = 11

try:
    librtipc = ctypes.CDLL('librtipc.so')
except OSError:
    raise ImportError('librtipc.so cannot be loaded, cannot import rtipc binding')

librtipc.rtipc_create.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
librtipc.rtipc_create.restype = ctypes.c_void_p  # rtipc*

librtipc.rtipc_create_group.argtypes = [ctypes.c_void_p, ctypes.c_double]  # rtipc*
librtipc.rtipc_create_group.restype = ctypes.c_void_p  # rtipc_group*

librtipc.rtipc_txpdo.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_int]  # rtipc_group*
librtipc.rtipc_txpdo.restype = ctypes.c_void_p  # txpdo*

librtipc.rtipc_set_txpdo_addr.argtypes = [ctypes.c_void_p, ctypes.c_void_p]  # txpdo*

librtipc.rtipc_rxpdo.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]  # rtipc_group*
librtipc.rtipc_rxpdo.restype = ctypes.c_void_p  # rxpdo*

librtipc.rtipc_set_rxpdo_addr.argtypes = [ctypes.c_void_p, ctypes.c_void_p]  # rxpdo*

librtipc.rtipc_prepare.argtypes = [ctypes.c_void_p]  # rtipc*

librtipc.rtipc_tx.argtypes = [ctypes.c_void_p]  # rtipc_group*

librtipc.rtipc_rx.argtypes = [ctypes.c_void_p]  # rtipc_group*

librtipc.rtipc_exit.argtypes = [ctypes.c_void_p]  # rtipc*

class RtIPCGroup(object):

    def __init__(self, rtipcGroup):
        self.__rtipcGroup = rtipcGroup

    def Receive(self):
        librtipc.rtipc_rx(self.__rtipcGroup)

    def Send(self):
        librtipc.rtipc_tx(self.__rtipcGroup)

    def AddReceivePdo(self, name, datatype, addr, count, connected):
        return librtipc.rtipc_rxpdo(self.__rtipcGroup, name, datatype, addr, count, connected)

    def SetReceivePdoAddr(self, rxpdo, addr):
        librtipc.rtipc_set_rxpdo_addr(rxpdo, addr)
    
    def AddSendPdo(self, name, datatype, addr, count):
        return librtipc.rtipc_txpdo(self.__rtipcGroup, name, datatype, addr, count)

    def SetSendPdoAddr(self, txpdo, addr):
        librtipc.rtipc_set_txpdo_addr(txpdo, addr)

class RtIPC(object):

    def __init__(self, ecName='simulator'):
        # FAKE_EC_NAME does not need to be on environ, as the name must be distinct and Python simulator's name would be different.
        self.__ecHomeDir = environ.get('FAKE_EC_HOMEDIR', '/tmp/FakeEtherCAT')
        self.__ecName = ecName

        self.__rtipc = librtipc.rtipc_create(ensure_binary(ecName), ensure_binary(self.__ecHomeDir))
        self.__isRunning = False

    def GetEcHomeDir(self):
        return self.__ecHomeDir

    def GetEcName(self):
        return self.__ecName

    def Start(self):
        if not self.__isRunning:
            assert 0 == librtipc.rtipc_prepare(self.__rtipc)
            self.__isRunning = True
        return self

    def __enter__(self):
        return self.Start()

    def Stop(self):
        if self.__isRunning:
            librtipc.rtipc_exit(self.__rtipc)
            self.__isRunning = False
    
    def __exit__(self, exception_type, exception_value, traceback):
        self.Stop()

    def Wait(self):
        pass

    def CreateGroup(self, sampleTime):
        return RtIPCGroup(librtipc.rtipc_create_group(self.__rtipc, sampleTime))
