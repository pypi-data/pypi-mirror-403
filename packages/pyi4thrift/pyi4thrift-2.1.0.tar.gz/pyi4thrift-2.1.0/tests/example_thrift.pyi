# coding:utf-8
from typing import Set, List, Dict
from .a import a.a_thrift as a.a
from thriftpy2.thrift import TException
from enum import Enum

A = '1'
B = 1
C = []
D = [1, 2]
E = {}
F = 1.1

# noinspection PyPep8Naming, PyShadowingNames
class ExampleEnum(Enum):
    A = 0
    B = 1
    C = 2

# noinspection PyPep8Naming, PyShadowingNames
class ErrCode(Enum):
    ERR_SUCCESS = 0
    ERR_REQ_PARAM_INVALID = 4000
    ERR_UNKNOWN = 5000
    ERR_SYSTEM_INNER_EXCEPTION = 5001
    ERR_LIMIT_EXCEEDED = 5002

# noinspection PyPep8Naming, PyShadowingNames
class Example(object):
    A: Dict[Dict[a.a.A,a.a.A],a.a.A]
    B: int
    C: int
    D: int
    E: bool
    F: int
    G: float
    H: str
    I: a.a.A
    J: Dict[a.a.A,Dict[a.a.A,a.a.A]]
    K: Dict[a.a.A,a.a.A]
    L: Dict[str,bool]
    M: Dict[str,List[Dict[str,a.a.A]]]
    N: List[a.a.A]
    O: List[str]
    P: Set[int]
    Q: List[Dict[str,a.a.A]]
    R: bytes

    def __init__(self,
                 A: Dict[Dict[a.a.A,a.a.A],a.a.A] = None,
                 B: int = None,
                 C: int = None,
                 D: int = None,
                 E: bool = True,
                 F: int = None,
                 G: float = 0.1,
                 H: str = 'hello',
                 I: a.a.A = None,
                 J: Dict[a.a.A,Dict[a.a.A,a.a.A]] = None,
                 K: Dict[a.a.A,a.a.A] = None,
                 L: Dict[str,bool] = {},
                 M: Dict[str,List[Dict[str,a.a.A]]] = None,
                 N: List[a.a.A] = None,
                 O: List[str] = None,
                 P: Set[int] = None,
                 Q: List[Dict[str,a.a.A]] = None,
                 R: bytes = None) -> None:
        ...

# noinspection PyPep8Naming, PyShadowingNames
class ExampleUnion(object):
    A: int

    def __init__(self,
                 A: int = 1) -> None:
        ...

# noinspection PyPep8Naming, PyShadowingNames
class ByteException(TException):
    ErrorCode: int

    def __init__(self,
                 ErrorCode: int = 0) -> None:
        ...

# noinspection PyPep8Naming, PyShadowingNames
class ExampleService(object):
    def Get(self, rq: a.a.A = None, xx: int = None) -> Example:
        ...

    def Pull(self, name: str = '', xxx: Dict[str,str] = None) -> int:
        ...

    def Test(self, ) -> None:
        ...
