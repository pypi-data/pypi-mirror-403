from collections import deque
from typing import override, Iterator, TypeVar

GenericType = TypeVar('GenericType')
Numeric = int | float

class queue[GenericType]:
    """ Wrapper for deque to provide FIFO queue functionality """
    def __init__(self) -> None:
        self.data:deque[GenericType] = deque()  # internal deque storage

    @override
    def __repr__(self) -> str:
        """ string representation of queue as sequence of elements """
        return str(list(self.data))
    

    def __iter__(self) -> Iterator[GenericType]:
        """ Iterator over queue elements, allows in checks and looping """
        return iter(self.data)


    def push(self, x:GenericType) -> None:
        """ Appends an item to the end of the queue 
        
        :param x: item to append
        """
        self.data.append(x)


    def pop(self) -> GenericType:
        """ Pops first element """
        return self.data.popleft()



class stack[GenericType](queue):
    """ Wrapper for deque to provide LIFO stack functionality """
    @override
    def pop(self) -> GenericType:
        """ Pops last element """
        return self.data.pop()
    

def manhattan(a: tuple[Numeric, Numeric], b:tuple[Numeric, Numeric]) -> Numeric:
    """ Basic Manhattan distance calculation between two (x,y) points """
    ax, ay = a  # (x, y)
    bx, by = b  # (x, y)
    return abs(bx-ax) + abs(by-ay)