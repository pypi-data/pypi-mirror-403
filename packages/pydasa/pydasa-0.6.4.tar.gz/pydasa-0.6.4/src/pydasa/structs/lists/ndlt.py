# -*- coding: utf-8 -*-
"""
Module ndlt.py
===========================================

Module to represent the **Node** data structure for the **Linked List** and **Doubly Linked List** in *PyDASA*.

Classes:
    **Node**: Base class for creating Single Linked List Node or **SLNode** and Double Linked List Node or **DLNode**.
    **SLNode**: Implements a single linked list node with data and next node reference.
    **DLNode**: Implements a double linked list node with data, next node, and previous node references.


*IMPORTANT:* based on the implementations proposed by the following authors/books:

    # . Algorithms, 4th Edition, Robert Sedgewick and Kevin Wayne.
    # . Data Structure and Algorithms in Python, M.T. Goodrich, R. Tamassia, M.H. Goldwasser.
"""

# native python modules
# import dataclass for defining the node class
from dataclasses import dataclass
# import modules for defining the Node type
from typing import Generic, Optional
# import inspect for getting the name of the current function
import inspect

# custom modules
# generic error handling and type checking
from pydasa.validations.error import handle_error as error
from pydasa.structs.types.generics import T
# import global variables

# checking custom modules
assert error
assert T


@dataclass
class Node(Generic[T]):
    """**Node** base class for creating Single Linked List Node or **SLNode** and Double Linked List Node or **DLNode**. Fundamental for the **Linked List** and **Doubly Linked List** data structures.

    Args:
        Generic (T): Generic type for a Python data structure.

    Returns:
        Node: A node object with the following attributes:
            - `_data`: The data stored in the node.
    """
    # optional information of any type
    # :attr: _data
    _data: Optional[T] = None
    """
    data stored in the node. By default, it is set to None.
    """

    def _error_handler(self, err: Exception) -> None:
        """*_error_handler()* function that handles the errors that can occur in the *Node*.

        if an error occurs in *SingleLinkedList*, it formats the error according to the context (package/module/class), the function (method) that generated it, and sends it to the upper component in the *DataStruct* hierarchy to handle it as the user considers appropriate.

        Args:
            err (Exception): Exception that occurred in the *Node*.
        """
        # TODO check utility of this error handling
        _context = self.__class__.__name__
        _function_name = "unknown"
        frame = inspect.currentframe()
        if frame is not None:
            if frame.f_back is not None:
                _function_name = frame.f_back.f_code.co_name
        else:
            _function_name = "unknown"
        error(_context, _function_name, err)

    def _validate_type(self, elm: Optional[T]) -> bool:
        """*_validate_type()* function that checks if the type of the element is the same as the type of the *Node*.

        Args:
            elm (Optional[T]): element to be processed in the *Node*.
            - *T*: Type of the element to be processed in the *Node*.

        Raises:
            TypeError: error if the type of the element to be added is not the same as the type of the elements already contained in the *Node*.

        Returns:
            bool: True if the type of the element is the same as the type of the *Node*. False otherwise.
        """
        _result: bool = True
        if elm is not None and self._data is not None and not isinstance(elm, type(self._data)):
            _msg = f"Invalid data type: {type(elm)} "
            _msg += f"Node configured with {type(self._data)}"
            raise TypeError(_msg)
        return _result

    @property
    def data(self) -> T:    # Optional[T]:
        """*data* Property to read the data in the *Node*. Acts as a getter (*get()*) for the *_data* attribute.

        Returns:
            T: data stored in the *Node*.
        """
        # return self._data
        if self._data is None:
            raise ValueError("Node data has not been initialized")
        return self._data

    @data.setter
    def data(self, data: T) -> None:
        """*data* Property to write the data in the *Node*. Acts as a setter (*set()*) for the *_data* attribute.

        Args:
            data (T): data to be set in the *Node*.
        """
        if self._data is not None:
            self._validate_type(data)
        self._data = data

    def __str__(self) -> str:
        """*__str__()* function to return a string representation of the *Node*. It also extendes for the *SLNode* and *DLNode* classes.

        Returns:
            str: string representation of the *Node*.
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
        # Format the string representation of Node class
        _str = f"{self.__class__.__name__}({', '.join(_attr_lt)})"
        return _str

    def __repr__(self) -> str:
        """*__repr__()* function to return a string representation of the *Node*. It also extendes for the *SLNode* and *DLNode* classes.

        Returns:
            str: string representation of the *Node*.
        """
        return self.__str__()


@dataclass
class SLNode(Node[T]):
    """**SLNode** class for creating a Single Linked List Node. Inherits from the **Node** class. Fundamental for the **Linked List** data structure.

    Args:
        Node (dataclass): **Node** base class for creating single and double linked nodes.
        Generic (T): Generic type for a Python data structure.

    Returns:
        SLNode: A single linked node object with the following attributes:
            - `_data`: The data stored in the node.
            - `_next`: The next node of the same type.
    """
    # optional reference to the next node of the same type
    # :attr: _next
    _next: Optional["SLNode[T]"] = None
    """
    next node of the same type. By default, it is set to None.
    """

    @property
    def next(self) -> Optional["SLNode[T]"]:
        """"*next()* Property to read the next node in the list. Acts as a getter (*get()*) for the *_next* attribute.

        Returns:
            Optional["SLNode[T]"]: reference to the next node of the list. If there is no next node, it returns None.
        """
        return self._next

    @next.setter
    def next(self, node: Optional["SLNode[T]"]) -> None:
        """*next()* Property to write the next node in the list. Acts as a setter (*set()*) for the *_next* attribute.

        Args:
            node (Optional["SLNode[T]"]): reference to the next node of the list.
        """
        if node is not None:
            self._validate_type(node.data)
        self._next = node

    def __str__(self) -> str:
        """*__str__()* function to return a string representation of the *SLNode*. It also extends the *Node* class.

        Returns:
            str: string representation of the *SLNode*.
        """
        _str = super().__str__()
        return _str

    def __repr__(self) -> str:
        """*__repr__()* function to return a string representation of the *SLNode*. It also extends the *Node* class.

        Returns:
            str: string representation of the *SLNode*.
        """
        _str = super().__repr__()
        return _str


@dataclass
class DLNode(SLNode[T]):
    """**DLNode** class for creating a Double Linked List Node. Inherits from the **SLNode** class. Fundamental for the **Doubly Linked List** data structure.

    Args:
        SLNode (dataclass): **SLNode** class for creating a single linked list node.
        Generic (T): Generic type for a Python data structure.

    Returns:
        DLNode: A double linked node object with the following attributes:
            - `_data`: The data stored in the node.
            - `_next`: The next node of the same type.
            - `_prev`: The previous node of the same type.
    """
    # optional reference to the previous node of the same type
    # :attr: _prev
    _prev: Optional["DLNode[T]"] = None

    @property
    def prev(self) -> Optional["DLNode[T]"]:
        """*prev()* Property to read the previous node in the list. Acts as a getter (*get()*) for the *_prev* attribute.

        Returns:
            node (Optional["DLNode[T]"]): reference to the previous node of the list.
        """
        return self._prev

    @prev.setter
    def prev(self, node: Optional["DLNode[T]"]) -> None:
        """*prev()* Property to write the previous node in the list. Acts as a setter (*set()*) for the *_prev* attribute.

        Args:
            node (Optional["DLNode[T]"]): reference to the previous node of the list.
        """
        if node is not None:
            self._validate_type(node.data)
        self._prev = node

    def __str__(self) -> str:
        """*__str__()* function to return a string representation of the *DLNode*. It also extends the *Node* class.

        Returns:
            str: string representation of the *DLNode*.
        """
        _str = super().__str__()
        return _str

    def __repr__(self) -> str:
        """*__repr__()* function to return a string representation of the *DLNode*. It also extends the *Node* class.

        Returns:
            str: string representation of the *DLNode*.
        """
        _str = super().__repr__()
        return _str
