from typing import Generic, TypeVar

T = TypeVar('T')

"""
Here is our own implementation of queue. The reason is that built-in List type is overloaded and is not good for
frequent deletes and updates. Regular Python Queue and Deque do not have method to access head and tail in constant
time w/o deleting those elements.
"""


class ListNode(Generic[T]):

    def __init__(self, val: T):
        self.__val = val
        # noinspection PyTypeChecker
        self.__next: ListNode[T] = None
        # noinspection PyTypeChecker
        self.__prev: ListNode[T] = None

    @property
    def val(self) -> T:
        return self.__val

    @val.setter
    def val(self, v: T):
        self.__val: T = v

    @property
    def next(self) -> 'ListNode[T]':
        return self.__next

    @next.setter
    def next(self, n: 'ListNode[T]'):
        self.__next: ListNode[T] = n

    @property
    def prev(self) -> 'ListNode[T]':
        return self.__prev

    @prev.setter
    def prev(self, n: 'ListNode[T]'):
        self.__prev: ListNode[T] = n


class Queue(Generic[T]):

    def __init__(self):
        self.__size: int = 0
        # noinspection PyTypeChecker
        self.__head: ListNode[T] = None
        # noinspection PyTypeChecker
        self.__tail: ListNode[T] = None

    @property
    def size(self) -> int:
        """
        :return: queue size
        """
        return self.__size

    def append(self, el: T):
        """
             Add element to the end of the queue
        """
        node_el = ListNode(el)
        if self.size == 0:
            self.__head = node_el
            self.__tail = node_el
        else:
            node_el.next = self.__tail
            self.__tail.prev = node_el
            self.__tail = node_el
        self.__size += 1

    def poll(self) -> T:
        """
            Remove and return a head of the queue
        """
        if self.size > 0:
            el = self.__head
            self.__head = self.__head.prev
            self.__size -= 1
            v = el.val
            del el
            return v
        return None

    def head(self) -> T:
        """
            Return but not remove a head of the queue
        """
        return self.__head.val if self.size > 0 else None

    def tail(self) -> T:
        """
            Return but not remove a tail of the queue
        """
        return self.__tail.val if self.size > 0 else None

    def pop(self) -> T:
        """
            Return and remove a tail of the queue
        """
        if self.size > 0:
            el = self.__tail
            self.__tail = self.__tail.next
            self.__size -= 1
            v = el.val
            del el
            return v
        return None
