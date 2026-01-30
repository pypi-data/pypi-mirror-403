# -*- coding: utf-8 -*-
"""
Module arlt.py
===========================================

Module to represent the **ArrayList** data structure in *PyDASA*. Fundamental for the rest of the Dimensional Analysis and Data Science Library.

classes:
    **ArrayList**: Implements a dynamic array data structure with customizable comparison and key functions.

*IMPORTANT:* based on the implementations proposed by the following authors/books:

    #. Algorithms, 4th Edition, Robert Sedgewick and Kevin Wayne.
    #. Data Structure and Algorithms in Python, M.T. Goodrich, R. Tamassia, M.H. Goldwasser.
"""

# native python modules
# dataclass imports
from dataclasses import dataclass, field
# data type imports
from typing import List, Optional, Callable, Generic, Iterator, Any
# code inspection imports
import inspect

# custom modules
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
class ArrayList(Generic[T]):
    """*ArrayList* implements a dynamic array data structure for PyDASA.

    Args:
        Generic (T): Generic type for a Python data structure.

    Returns:
        ArrayList: a generic data structure of type *ArrayList* or Dynamic Array with the following attributes:
            - `cmp_function`: Customizable comparison function for the elements in the *ArrayList*.
            - `_elements`: Native Python list that contains the elements of the structure.
            - `key`: Customizable key name for the elements in the *ArrayList*.
            - `_size`: Number of elements in the structure.
            - `iodata`: Customizable native Python list to initialize the structure.
    """
    # the cmp_function is used to compare elements, not defined by default
    # :attr: cmp_function
    cmp_function: Optional[Callable[[T, T], int]] = None
    """
    Customizable comparison function for *ArrayList* elements. Defaults to *dflt_cmp_function_lt()* from *PyDASA*, but can be overridden by the user.
    """

    # using default_factory to generate an empty list
    # :attr: _elements
    _elements: List[T] = field(default_factory=list)
    """
    Native Python list storing the elements of the ArrayList.
    """

    # the key is used to compare elements, not defined by default
    # :attr: key
    key: Optional[str] = DFLT_DICT_KEY
    """
    Customizable key name for identifying elements in the *ArrayList*. Defaults to *DFLT_DICT_KEY = '_id'* from *PyDASA*, but can be overridden by the user.
    """

    # by default, the list is empty
    # :attr: _size
    _size: int = 0
    """
    Size of the *ArrayList*, starting at 0 and updated with each modification.
    """

    # input elements from python list
    # :attr: iodata
    iodata: Optional[List[T]] = None
    """
    Optional Python list for loading external data intho the *ArrayList*. Defaults to *None* but can be provided during creation.
    """

    def __post_init__(self) -> None:
        """*__post_init__()* Initializes the *ArrayList* after creation by setting attributes like *cmp_function*, *key*, and *iodata*.

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
                    _msg = "iodata must be a valid iterable type, "
                    _msg += f"got {type(self.iodata)}"
                    raise TypeError(_msg)

                for elm in self.iodata:
                    self.append(elm)

            # Clear iodata after processing
            self.iodata = None

        except Exception as err:
            self._error_handler(err)

    def default_compare(self, elm1: Any, elm2: Any) -> int:
        """*default_compare()* Default comparison function for *ArrayList* elements. Compares two elements and returns:
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
        """*size()* Property to retrieve the number of elements in the *ArrayList*.

        Returns:
            int: number of elements in the *ArrayList*.
        """
        return self._size

    @property
    def empty(self) -> bool:
        """*empty()* Property to check if the *ArrayList* is empty.

        Returns:
            bool: True if the *ArrayList* is empty, False otherwise.
        """
        return self._size == 0

    def clear(self) -> None:
        """*clear()* reset the *ArrayList* by removing all elements and resetting the size to 0.

        NOTE: This method is used to empty the *ArrayList* without deleting the object itself.
        """
        self._elements.clear()
        self._size = 0

    def prepend(self, elm: T) -> None:
        """*prepend()* adds an element to the beginning of the *ArrayList*.

        Args:
            elm (T): element to be added to the beginning of the structure.
        """
        # if the element type is valid, add it to the list
        if self._validate_type(elm):
            self._elements.insert(0, elm)
            self._size += 1

    def append(self, elm: T) -> None:
        """*append()* adds an element to the end of the *ArrayList*.

        Args:
            elm (T): element to be added to the end of the structure.
        """
        # if the element type is valid, add it to the list
        if self._validate_type(elm):
            self._elements.append(elm)
            self._size += 1

    def insert(self, elm: T, pos: int) -> None:
        """*insert()* adds an element to a specific position in the *ArrayList*.

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
                raise IndexError(f"Index {pos} is out of range")
            self._elements.insert(pos, elm)
            self._size += 1
        else:
            raise IndexError("Empty data structure")

    @property
    def first(self) -> T:
        """*first* Property to read the first element of the *ArrayList*.

        Raises:
            Exception: error if the structure is empty.

        Returns:
            T: the first element of the *ArrayList*.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        return self._elements[0]

    @property
    def last(self) -> T:
        """*last* Property to read the last element of the *ArrayList*.

        Raises:
            Exception: error if the structure is empty.

        Returns:
            T: the last element of the *ArrayList*.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        return self._elements[self.size - 1]

    def get(self, pos: int) -> T:
        """*get()* reads an element from a specific position in the *ArrayList*.

        Args:
            pos (int): position of the element to be read.

        Raises:
            IndexError: error if the structure is empty.
            IndexError: error if the position is invalid.

        Returns:
            T: the element at the specified position in the *ArrayList*.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        elif pos < 0 or pos > self.size - 1:
            raise IndexError(f"Index {pos} is out of range")
        return self._elements[pos]

    def __getitem__(self, pos: int) -> T:
        """*__getitem__()* reads an element from a specific position in the *ArrayList*. Equivelent to *get()* method.

        NOTE: This method is used to access the elements of the *ArrayList* using the square brackets notation.

        Args:
            pos (int): position of the element to be read.

        Raises:
            IndexError: error if the structure is empty.
            IndexError: error if the position is invalid.

        Returns:
            T: the element at the specified position in the *ArrayList*.
        """
        return self.get(pos)

    def pop_first(self) -> T:
        """*pop_first()* removes the first element from the *ArrayList*.

        Raises:
            IndexError: error if the structure is empty.

        Returns:
            T: the first element removed from the *ArrayList*.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        elm = self._elements.pop(0)
        self._size -= 1
        return elm

    def pop_last(self) -> T:
        """*pop_last()* removes the last element from the *ArrayList*.

        Raises:
            IndexError: error if the structure is empty.

        Returns:
            T: the last element removed from the *ArrayList*.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        elm = self._elements.pop(self.size - 1)
        self._size -= 1
        return elm

    def remove(self, pos: int) -> T:
        """*remove()* removes an element from a specific position in the *ArrayList*.

        Args:
            pos (int): position of the element to be removed.

        Raises:
            IndexError: error if the structure is empty.
            IndexError: error if the position is invalid.

        Returns:
            T: the element removed from the *ArrayList*.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        elif pos < 0 or pos > self.size - 1:
            raise IndexError(f"Index {pos} is out of range")
        elm = self._elements.pop(pos)
        self._size -= 1
        return elm

    def compare(self, elem1: T, elem2: T) -> int:
        """*compare()* compares two elements using the *cmp_function* defined in the *ArrayList*.

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
        """*index_of()* searches for the first occurrence of an element in the *ArrayList*. If the element is found, it returns its index; otherwise, it returns -1.

        Args:
            elm (T): element to search for in the *ArrayList*.

        Returns:
            int: index of the element in the *ArrayList* or -1 if not found.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        _idx = -1
        found = False
        i = 0
        while not found and i < self.size:
            _telm = self._elements[i]
            # using the structure cmp function
            if self.compare(elm, _telm) == 0:
                found = True
                _idx = i
            i += 1
        return _idx

    def update(self, new_data: T, pos: int) -> None:
        """*update()* updates an element in the *ArrayList* at a specific position.

        Args:
            new_data (T): new data to be updated in the *ArrayList*.
            pos (int): position of the element to be updated.

        Raises:
            IndexError: error if the structure is empty.
            IndexError: error if the position is invalid.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        elif pos < 0 or pos > self.size - 1:
            raise IndexError(f"Index {pos} is out of range")
        # if not self._validate_type(new_data):
        elif self._validate_type(new_data):
            self._elements[pos] = new_data

    def swap(self, pos1: int, pos2: int) -> None:
        """*swap()* swaps two elements in the *ArrayList* at specified positions.

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
            raise IndexError(f"Index {pos1} is out of range")
        elif pos2 < 0 or pos2 > self.size - 1:
            raise IndexError(f"Index {pos2} is out of range")
        _temp1 = self._elements[pos1]
        _temp2 = self._elements[pos2]
        self._elements[pos2] = _temp1
        self._elements[pos1] = _temp2

    def sublist(self, start: int, end: int) -> "ArrayList[T]":
        """*sublist()* creates a new *ArrayList* containing a sublist of elements from the original *ArrayList*. The sublist is defined by the start and end indices.

        NOTE: The start index is inclusive, and the end index is inclusive.

        Args:
            start (int): start index of the sublist.
            end (int): end index of the sublist.

        Raises:
            IndexError: error if the structure is empty.
            IndexError: error if the start or end index are invalid.

        Returns:
            ArrayList[T]: a new *ArrayList* containing the sublist of elements.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        elif start < 0 or end > self.size - 1 or start > end:
            raise IndexError(f"Invalid range: between [{start}, {end}]")
        sub_lt = ArrayList(cmp_function=self.cmp_function,
                           key=self.key)
        # add the elements of the sublist to the new list
        sub_lt._elements = self._elements[start:end + 1]
        sub_lt._size = end - start + 1
        return sub_lt

    def concat(self, other: "ArrayList[T]") -> "ArrayList[T]":
        """*concat()* concatenates two *ArrayList* objects. The elements of the second list are added to the end of the first list.

        NOTE: The *cmp_function* and *key* attributes of the two lists must be the same.

        Args:
            other (ArrayList[T]): the second *ArrayList* to be concatenated.

        Raises:
            TypeError: error if the *other* argument is not an *ArrayList*.
            TypeError: error if the *key* attributes are not the same.
            TypeError: error if the *cmp_function* are not the same.

        Returns:
            ArrayList[T]: the concatenated *ArrayList* in the first list.
        """
        if not isinstance(other, ArrayList):
            _msg = f"Structure is not an ArrayList: {type(other)}"
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

        # concatenate the elements of the two lists
        self._elements = self._elements + other._elements
        # update the size of the new list
        self._size = self.size + other.size
        return self

    def clone(self) -> "ArrayList[T]":
        """*clone()* creates a new structure with the copy of the *ArrayList*. The new list is independent of the original list.

        NOTE: we named the method *clone()* instead of *copy()* to avoid confusion with the native Python *copy()* method.

        Returns:
            ArrayList[T]: a new *ArrayList* with the same elements as the original list.
        """
        # create a new list
        copy_lt = ArrayList(cmp_function=self.cmp_function,
                            key=self.key)
        # add all the elements of the current list
        for elm in self._elements:
            copy_lt.append(elm)
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
        if not self.empty:
            # raise an exception if the type is not valid
            if not isinstance(elm, type(self._elements[0])):
                _msg = f"Invalid data type: {type(elm)} "
                _msg += f"!= {type(self._elements[0])}"
                raise TypeError(_msg)
        # otherwise, the type is valid
        return True

    def __iter__(self) -> Iterator[T]:
        """*__iter__()* to iterate over the elements of the *ArrayList*. This method returns an iterator object that can be used to iterate over the elements of the list.

        NOTE: This is used to iterate over the elements of the list using a for loop.

        Returns:
            Iterator[T]: an iterator object that can be used to iterate over the elements of the list.
        """
        try:
            return iter(self._elements)
        except Exception as err:
            self._error_handler(err)
            raise  # Re-raise the exception after handling

    def __len__(self) -> int:
        """*__len__()* to get the number of elements in the *ArrayList*. This method returns the size of the list.

        Returns:
            int: the number of elements in the *ArrayList*.
        """
        return self._size

    def __str__(self) -> str:
        """*__str__()* get the string representation of the *ArrayList*. This method returns a string with the elements of the list.

        Returns:
            str: the string representation of the *ArrayList*.
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
        # Format the string representation of the ArrayList class and its attributes
        _str = f"{self.__class__.__name__}({', '.join(_attr_lt)})"
        return _str

    def __repr__(self) -> str:
        """*__repr__()* get the string representation of the *ArrayList*. This method returns a string representation.

        Returns:
            str: the string representation of the *ArrayList*.
        """
        return self.__str__()
