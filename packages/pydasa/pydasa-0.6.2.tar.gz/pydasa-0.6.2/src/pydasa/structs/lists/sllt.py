# -*- coding: utf-8 -*-
"""
Module sllt.py
===========================================

Module for the custom **SingleLinkedList** data structure in *PyDASA*. Essential for Dimensional Analysis and Data Science operations.

Classes:
    **SingleLinkedList**: Implements a single linked list with methods for insertion, deletion, and traversal.

*IMPORTANT:* based on the implementations proposed by the following authors/books:

    #. Algorithms, 4th Edition, Robert Sedgewick and Kevin Wayne.
    #. Data Structure and Algorithms in Python, M.T. Goodrich, R. Tamassia, M.H. Goldwasser.
"""

# native python modules
# dataclass imports
from dataclasses import dataclass
# data type imports
from typing import List, Optional, Callable, Generic, Iterator, Any
# code inspection imports
import inspect

# custom modules
# linked list node implementation
from pydasa.structs.lists.ndlt import SLNode

# generic types and global variables
from pydasa.structs.types.generics import T
from pydasa.structs.types.generics import DFLT_DICT_KEY
from pydasa.structs.types.generics import VLD_IOTYPE_LT
from pydasa.structs.types.functions import dflt_cmp_function_lt
# generic error handling and type checking
from pydasa.validations.error import handle_error as error

# checking custom modules
assert T
assert DFLT_DICT_KEY
assert VLD_IOTYPE_LT
assert dflt_cmp_function_lt
assert error


@dataclass
class SingleLinkedList(Generic[T]):
    """**SingleLinkedList** implements a single linked list data structure for PyDASA.

    Args:
        Generic (T): Generic type for a Python data structure.

    Returns:
        SingleLinkedList: a generic single linked list data structure with the following attributes:
            - **cmp_function**: function to compare elements in the list.
            - **key**: key to identify the elements in the list.
            - **first**: reference to the first node of the list.
            - **last**: reference to the last node of the list.
            - **_size**: size of the list.
    """

    # the cmp_function is used to compare elements, not defined by default
    # :attr: cmp_function
    cmp_function: Optional[Callable[[T, T], int]] = None
    """
    Customizable comparison function for *SingleLinkedList* elements. Defaults to *dflt_cmp_function_lt()* from *PyDASA*, but can be overridden by the user.
    """

    # reference to the first node of the list
    # :attr: _first
    _first: Optional[SLNode[T]] = None
    """
    Reference to the first node of the *SingleLinkedList*.
    """

    # reference to the last node of the list
    # :attr: _last
    _last: Optional[SLNode[T]] = None
    """
    Reference to the last node of the *SingleLinkedList*.
    """

    # the key is used to compare elements, not defined by default
    # :attr: key
    key: Optional[str] = DFLT_DICT_KEY
    """
    Customizable key name for identifying elements in the *SingleLinkedList*. Defaults to *DFLT_DICT_KEY = '_id'* from *PyDASA*, but can be overridden by the user.
    """

    # by default, the list is empty
    # :attr: _size
    _size: int = 0
    """
    Size of the *SingleLinkedList*, starting at 0 and updated with each modification.
    """

    # input elements from python list
    # :attr: iodata
    iodata: Optional[List[T]] = None
    """
    Optional Python list for loading external data intho the *SingleLinkedList*. Defaults to *None* but can be provided during creation.
    """

    def __post_init__(self) -> None:
        """*__post_init__()* Initializes the *SingleLinkedList* after creation by setting attributes like *cmp_function*, *key*, *first*, *last*, and *iodata*.

        *NOTE:* Special method called automatically after object creation.
        """
        try:
            # if the key is not defined, use the default
            if self.key is None:
                self.key = DFLT_DICT_KEY

            # if the compare function is not defined, use the default
            if self.cmp_function is None:
                self.cmp_function = self.default_compare

            # if elements are provided, add them to the ArrayList
            if self.iodata is not None:
                if not isinstance(self.iodata, VLD_IOTYPE_LT):
                    raise TypeError(f"iodata must be a valid iterable type, got {type(self.iodata)}")

                for elm in self.iodata:
                    self.append(elm)

            # Clear iodata after processing
            self.iodata = None

        except Exception as err:
            self._error_handler(err)

    def default_compare(self, elm1: Any, elm2: Any) -> int:
        """*default_compare()* Default comparison function for *SingleLinkedList* elements. Compares two elements and returns:
            - 0 if they are equal,
            - 1 if the first is greater,
            - -1 if the first is smaller.

        Args:
            elm1 (Any): First element to compare.
            elm2 (Any): Second element to compare.

        Returns:
            int: Comparison result.
        """
        try:
            # default comparison needs the key to be defined
            if self.key is None:
                raise ValueError("Key must be set before comparison")
            return dflt_cmp_function_lt(elm1, elm2, self.key)
        except Exception as err:
            self._error_handler(err)
            raise   # Re-raise the exception after handling

    @property
    def size(self) -> int:
        """*size()* Property to retrieve the number of elements in the *SingleLinkedList*.

        Returns:
            int: number of elements in the *SingleLinkedList*.
        """
        return self._size

    @property
    def empty(self) -> bool:
        """*empty()* Property to check if the *SingleLinkedList* is empty.

        Returns:
            bool: True if the *SingleLinkedList* is empty, False otherwise.
        """
        return self._size == 0

    def clear(self) -> None:
        """*clear()* clears the *SingleLinkedList* by removing all elements and resetting the size to 0.

        NOTE: This method is used to empty the *SingleLinkedList* without deleting the object itself.
        """
        self._first = None
        self._last = None
        self._size = 0

    def prepend(self, elm: T) -> None:
        """*prepend()* adds an element to the beginning of the *SingleLinkedList*.

        Args:
            elm (T): element to be added to the beginning of the structure.
        """
        # if the element type is valid, add it to the list
        if self._validate_type(elm):
            # create a new node
            _new = SLNode(elm)
            _new.next = self._first
            self._first = _new
            if self.size == 0:
                self._last = self._first
            self._size += 1

    def append(self, elm: T) -> None:
        """*append()* adds an element to the end of the *SingleLinkedList*.

        Args:
            elm (T): element to be added to the end of the structure.
        """
        # if the element type is valid, add it to the list
        if self._validate_type(elm):
            # create a new node
            _new = SLNode(elm)
            if self._last is None:
                self._first = _new
            else:
                self._last.next = _new
            self._last = _new
            self._size += 1

    def insert(self, elm: T, pos: int) -> None:
        """*insert()* adds an element to the *SingleLinkedList* at a specific position.

        Args:
            elm (T): element to be added to the structure.
            pos (int): position where the element will be added.

        Raises:
            IndexError: error if the structure is empty.
            IndexError: error if the position is invalid.
            TypeError: error if the element type is invalid.
        """
        if not self.empty and self._validate_type(elm):
            if pos < 0 or pos > self.size:
                raise IndexError("Position is out of range")

            # create a new node
            _new = SLNode(elm)

            # if the position is the first, add it to the first
            if pos == 0:
                _new.next = self._first
                self._first = _new
                if self._last is None:  # Empty list case
                    self._last = _new

            # if the position is the last (append), add it to the end
            elif pos == self.size:
                if self._last is not None:
                    self._last.next = _new
                self._last = _new

            # otherwise, insert in the middle
            else:
                i = 0
                _cur = self._first
                _prev: Optional[SLNode[T]] = None
                while i < pos and _cur is not None:
                    _prev = _cur
                    _cur = _cur.next
                    i += 1
                if _prev is not None:
                    _new.next = _cur
                    _prev.next = _new
            # increment the size
            self._size += 1
        else:
            raise IndexError("Empty data structure")

    @property
    def first(self) -> T:
        """*first* Property to read the first element of the *SingleLinkedList*.

        Raises:
            IndexError: error if the structure is empty.

        Returns:
            T: the first element of the *SingleLinkedList*.
        """
        if self.empty or self._first is None:
            raise IndexError("Empty data structure")
        return self._first.data

    @property
    def last(self) -> T:
        """*last* Property to read the last element of the *SingleLinkedList*.

        Raises:
            Exception: error if the structure is empty.

        Returns:
             T: the last element of the *SingleLinkedList*.
        """
        if self.empty or self._last is None:
            raise IndexError("Empty data structure")
        return self._last.data

    def get(self, pos: int) -> T:
        """*get()* retrieves an element from the *SingleLinkedList* at a specific position.

        Args:
            pos (int): position of the element to be retrieved.

        Raises:
            IndexError: error if the structure is empty.
            IndexError: error if the position is invalid.

        Returns:
            T: the element at the specified position in the *SingleLinkedList*.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        if pos < 0 or pos > self.size - 1:
            raise IndexError(f"Index {pos} is out of range")

        # current node starting at the first node
        _cur = self._first
        i = 0
        # iterate to the desired position
        while i != pos and _cur is not None:
            _cur = _cur.next
            i += 1

        if _cur is None:
            raise IndexError(f"Corrupted list structure at position {pos}")

        return _cur.data

    def __getitem__(self, pos: int) -> Optional[T]:
        """*__getitem__()* retrieves an element from the *SingleLinkedList* at a specific position.

        NOTE: This method is used to access the elements of the *SingleLinkedList* using the square brackets notation.

        Args:
            pos (int): position of the element to be retrieved.

        Raises:
            IndexError: error if the structure is empty.
            IndexError: error if the position is invalid.

        Returns:
            Optional[T]: the element at the specified position in the *SingleLinkedList*.
        """
        return self.get(pos)

    def pop_first(self) -> T:
        """*pop_first()* removes the first element from the *SingleLinkedList*.

        Raises:
            IndexError: error if the structure is empty.

        Returns:
            T: the first element of the *SingleLinkedList*.
        """
        # check if the list is empty
        if self.empty or self._first is None:
            raise IndexError("Empty data structure")

        # save the data before removing the node
        _data = self._first.data

        # move first pointer to the next node
        self._first = self._first.next
        self._size -= 1

        # if the list is now empty, set last to None
        if self._first is None:
            self._last = None

        return _data

    def pop_last(self) -> T:
        """*pop_last()* removes the last element from the *SingleLinkedList*.

        Raises:
            IndexError: error if the structure is empty.

        Returns:
            T: the last element of the *SingleLinkedList*.
        """
        # Check if the list is empty
        if self.empty or self._last is None:
            raise IndexError("Empty data structure")

        # Save the data before removing the node
        _data = self._last.data

        # if the list has only one element, set the first and last to None
        if self._first == self._last:
            self._first = None
            self._last = None

        # otherwise, remove the last element
        else:
            _cur = self._first
            # traverse the list to find the second-to-last element
            while _cur is not None and _cur.next != self._last:
                _cur = _cur.next

            # Ensure we found the second-to-last node
            if _cur is None:
                raise IndexError("Corrupted list structure")

            # rearrange the last element
            self._last = _cur
            self._last.next = None

        self._size -= 1
        return _data

    def remove(self, pos: int) -> T:
        """*remove()* removes an element from the *SingleLinkedList* at a specific position.

        Args:
            pos (int): position of the element to be removed.

        Raises:
            IndexError: error if the structure is empty.
            IndexError: error if the position is invalid.

        Returns:
            T: the element removed from the *SingleLinkedList*.
        """
        # check if the list is empty
        if self.empty or self._first is None:
            raise IndexError("Empty data structure")
        # check if the position is valid
        if pos < 0 or pos > self.size - 1:
            raise IndexError(f"Index {pos} is out of range")

        # if removing the first element
        if pos == 0:
            _data = self._first.data
            self._first = self._first.next
            # if list is now empty, update last
            if self._first is None:
                self._last = None
        # if removing from middle or end
        else:
            _cur = self._first
            _prev = self._first
            i = 0
            # traverse to the position
            while i != pos and _cur is not None:
                _prev = _cur
                _cur = _cur.next
                i += 1

            # Check if we found the node
            if _cur is None:
                raise IndexError(f"Corrupted list structure at position {pos}")

            _data = _cur.data
            _prev.next = _cur.next

            # if removing the last element, update last pointer
            if _cur == self._last:
                self._last = _prev

        self._size -= 1
        return _data

    def compare(self, elem1: T, elem2: T) -> int:
        """*compare()* compares two elements using the comparison function defined in the *SingleLinkedList*.

        Args:
            elem1 (T): first element to compare.
            elem2 (T): second element to compare.

        Raises:
            TypeError: error if the *cmp_function* is not defined.

        Returns:
            int: -1 if elem1 < elem2, 0 if elem1 == elem2, 1 if elem1 > elem2.
        """
        if self.cmp_function is None:
            # raise an exception if the cmp function is not defined
            raise TypeError("Undefined compare function!!!")
        # use the structure cmp function
        return self.cmp_function(elem1, elem2)

    def index_of(self, elm: T) -> int:
        """*index_of()* searches for the first occurrence of an element in the *SingleLinkedList*. If the element is found, it returns its index; otherwise, it returns -1.

        Args:
            elm (T): element to search for in the *SingleLinkedList*.

        Returns:
            int: index of the element in the *SingleLinkedList* or -1 if not found.
        """
        if self.empty:
            raise IndexError("Empty data structure")

        _idx = -1
        _node = self._first
        found = False
        i = 0

        # iterate through the list to find the element
        while not found and _node is not None and i < self.size:
            # using the structure cmp function
            if self.compare(elm, _node.data) == 0:
                found = True
                _idx = i
            else:
                _node = _node.next
                i += 1

        return _idx

    def update(self, new_data: T, pos: int) -> None:
        """*update()* updates an element in the *SingleLinkedList* at a specific position.

        Args:
            new_data (T): new data to be updated in the structure.
            pos (int): position of the element to be updated.

        Raises:
            IndexError: error if the structure is empty.
            IndexError: error if the position is invalid.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        elif pos < 0 or pos > self.size - 1:
            raise IndexError(f"Index {pos} is out of range")
        # if the element type is valid, update the element
        elif self._validate_type(new_data):
            _cur = self._first
            i = 0
            while i != pos and _cur is not None:
                _cur = _cur.next
                i += 1

            if _cur is None:
                raise IndexError(f"Corrupted list structure at position {pos}")

            _cur.data = new_data

    def swap(self, pos1: int, pos2: int) -> None:
        """*swap()* swaps two elements in the *SingleLinkedList* at specific positions.


        Args:
            pos1 (int): position of the first element to swap.
            pos2 (int): position of the second element to swap.

        Raises:
            IndexError: error if the structure is empty.
            IndexError: error if the first position is invalid.
            IndexError: error if the second position is invalid.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        elif pos1 < 0 or pos1 > self.size - 1:
            raise IndexError("Index", pos1, "is out of range")
        elif pos2 < 0 or pos2 > self.size - 1:
            raise IndexError("Index", pos2, "is out of range")
        info_pos1 = self.get(pos1)
        info_pos2 = self.get(pos2)
        self.update(info_pos2, pos1)
        self.update(info_pos1, pos2)

    def sublist(self, start: int, end: int) -> "SingleLinkedList[T]":
        """*sublist()* creates a new *SingleLinkedList* containing a sublist of elements from the original *SingleLinkedList*. The sublist is defined by the start and end indices.

        NOTE: The start index is inclusive, and the end index is inclusive.

        Args:
            start (int): start index of the sublist.
            end (int): end index of the sublist.

        Raises:
            IndexError: error if the structure is empty.
            IndexError: error if the start or end index are invalid.

        Returns:
            SingleLinkedList[T]: a new *SingleLinkedList* containing the sublist of elements.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        elif start < 0 or end > self.size - 1 or start > end:
            raise IndexError(f"Invalid range: between [{start}, {end}]")

        sub_lt = SingleLinkedList(cmp_function=self.cmp_function,
                                  key=self.key)
        i = 0
        _cur = self._first

        while i != end + 1 and _cur is not None:
            if i >= start:
                sub_lt.append(_cur.data)
            _cur = _cur.next
            i += 1
        return sub_lt

    def concat(self, other: "SingleLinkedList[T]") -> "SingleLinkedList[T]":
        """*concat()* concatenates two *SingleLinkedList* objects. The elements of the second list are added to the end of the first list.

        NOTE: The *cmp_function* and *key* attributes of the two lists must be the same.

        Args:
            other (SingleLinkedList[T]): the second *SingleLinkedList* to be concatenated.

        Raises:
            TypeError: error if the *other* argument is not an *SingleLinkedList*.
            TypeError: error if the *key* attributes are not the same.
            TypeError: error if the *cmp_function* are not the same.

        Returns:
            SingleLinkedList[T]: the concatenated *SingleLinkedList* in the first list.
        """
        if not isinstance(other, SingleLinkedList):
            _msg = f"Structure is not an SingleLinkedList: {type(other)}"
            raise TypeError(_msg)
        if self.key != other.key:
            raise TypeError(f"Invalid key: {self.key} != {other.key}")
        # checking functional code of the cmp function
        if self.cmp_function is not None and other.cmp_function is not None:
            code1 = self.cmp_function.__code__.co_code
            code2 = other.cmp_function.__code__.co_code
            if code1 != code2:
                _msg = f"Invalid compare function: {self.cmp_function}"
                _msg += f" != {other.cmp_function}"
                raise TypeError(_msg)

        # Handle empty lists
        if other.empty:
            return self  # Nothing to concatenate

        # If self is empty, just copy other's strucure
        if self.empty:
            self._first = other._first
            self._last = other._last

        # concatenate the two lists
        elif self._last is not None:
            self._last.next = other._first
            self._last = other._last

        # update the size
        self._size = self.size + other.size
        return self

    def clone(self) -> "SingleLinkedList[T]":
        """*clone()* creates a copy of the *SingleLinkedList*. The new list is independent of the original list.

        NOTE: The elements of the new list are the same as the original list, but they are not references to the same objects.

        Returns:
            SingleLinkedList[T]: a new *SingleLinkedList* with the same elements as the original list.
        """
        # create new list
        copy_lt = SingleLinkedList(cmp_function=self.cmp_function,
                                   key=self.key)
        # get the first node of the original list
        _cur = self._first
        # traverse the list and add the elements to the new list
        while _cur is not None:
            copy_lt.append(_cur.data)
            _cur = _cur.next
        return copy_lt

    def _error_handler(self, err: Exception) -> None:
        """*_error_handler()* to process the context (package/class), function name (method), and the error (exception) that was raised to format a detailed error message and traceback.

        Args:
            err (Exception): Python raised exception.
        """
        _context = self.__class__.__name__
        _function_name = "unknown"
        frame = inspect.currentframe()
        if frame is not None:
            if frame.f_back is not None:
                _function_name = frame.f_back.f_code.co_name
        else:
            _function_name = "unknown"
        error(_context, _function_name, err)

    def _validate_type(self, elm: T) -> bool:
        """*_validate_type()* checks if the type of the element is valid. If the structure is empty, the type is valid. If the structure is not empty, the type must be the same as the first element in the list.
        This is used to check the type of the element before adding it to the list.

        Args:
            elm (T): element to be added to the structure.

        Raises:
            TypeError: error if the type of the element is not valid.

        Returns:
            bool: True if the type is valid, False otherwise.
        """
        # if the structure is not empty, check the first element type
        if not self.empty and self._first is not None:
            # raise an exception if the type is not valid at the first element
            if not isinstance(elm, type(self._first.data)):
                _msg = f"Invalid data type: {type(elm)} "
                _msg += f"!= {type(self._first.data)}"
                raise TypeError(_msg)
        # otherwise, any type is valid
        return True

    def __iter__(self) -> Iterator[T]:
        """*__iter__()* to iterate over the elements of the *SingleLinkedList*. This method returns an iterator object that can be used to iterate over the elements of the list.

        NOTE: This is used to iterate over the nodes of the list using a for loop.

        Returns:
            Iterator[T]: an iterator object that can be used to iterate over the nodes of the list.
        """
        try:
            # TODO do I need the try/except block?
            _cur = self._first
            while _cur is not None:
                yield _cur.data
                _cur = _cur.next
        except Exception as err:
            self._error_handler(err)

    def __len__(self) -> int:
        """*__len__()* to get the number of elements in the *SingleLinkedList*. This method returns the size of the list.

        Returns:
            int: the number of elements in the *SingleLinkedList*.
        """
        return self._size

    def __str__(self) -> str:
        """*__str__()* to get the string representation of the *SingleLinkedList*. This method returns a string with the elements of the list separated by commas.

        Returns:
            str: string representation of the *SingleLinkedList*.
        """
        _attr_lt = []
        for attr, value in vars(self).items():
            # Skip private attributes starting with "__"
            if attr.startswith("__"):
                continue
            # Format callable attributes
            if callable(value):
                value = f"{value.__name__}{inspect.signature(value)}"
            # Format attribute name and value
            _attr_name = attr.lstrip("_")
            _attr_lt.append(f"{_attr_name}={repr(value)}")
        # format the string with the SingleLinkedList class name and the attributes
        _str = f"{self.__class__.__name__}({', '.join(_attr_lt)})"
        return _str

    def __repr__(self) -> str:
        """*__repr__()* get the string representation of the *SingleLinkedList*. This method returns a string representation,

        Returns:
            str: string representation of the *SingleLinkedList*.
        """
        return self.__str__()
