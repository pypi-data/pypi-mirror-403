# -*- coding: utf-8 -*-
"""
Module scht.py
===========================================

Module to represent the **SCHashTable** data structure for the **Hash Table** in *PyDASA*.

Classes:
    **Bucket**: Represents a bucket in the hash table using a single linked list.
    **SCHashTable**: Implements a hash table with separate chaining for collision resolution, supporting dynamic resizing and customizable comparison functions.

*IMPORTANT:* based on the implementations proposed by the following authors/books:

    # . Algorithms, 4th Edition, Robert Sedgewick and Kevin Wayne.
    # . Data Structure and Algorithms in Python, M.T. Goodrich, R. Tamassia, M.H. Goldwasser.
"""

# native python modules
# dataclass imports
from dataclasses import dataclass
# data type imports
from typing import List, Optional, Callable, Generic, Any
from typing import cast
# code inspection imports
import inspect
# hashing support imports
import random

# custom modules
# data structure classes imports
from pydasa.structs.tables.htme import MapEntry
from pydasa.structs.lists.arlt import ArrayList
from pydasa.structs.lists.sllt import SingleLinkedList
# hashing support imports
from pydasa.structs.tools.hashing import mad_hash
from pydasa.structs.tools.math import next_prime, previous_prime
# generic types and global variables
from pydasa.structs.types.generics import T
from pydasa.structs.types.generics import DFLT_DICT_KEY
from pydasa.structs.types.generics import VLD_IOTYPE_LT
from pydasa.structs.types.generics import DFLT_PRIME
from pydasa.structs.types.functions import dflt_cmp_function_ht
# generic error handling and type checking
from pydasa.validations.error import handle_error as error

# checking custom modules
assert MapEntry
assert ArrayList
assert SingleLinkedList
assert mad_hash
assert next_prime
assert previous_prime
assert T
assert DFLT_DICT_KEY
assert VLD_IOTYPE_LT
assert DFLT_PRIME
assert dflt_cmp_function_ht
assert error

# default load factor for separating chaining
# :data: DFLT_SC_ALPHA
DFLT_SC_ALPHA: float = 4.0
"""
Default load factor (*alpha*) for the *SCHashTable*, by default is 4.0.
"""

# :data: MAX_SC_ALPHA
MAX_SC_ALPHA: float = 8.0
"""
Maximum load factor (*alpha*) for the *SCHashTable*, by default is 8.0.
"""

# :data: MIN_SC_ALPHA
MIN_SC_ALPHA: float = 2.0
"""
Minimum load factor (*alpha*) for the *SCHashTable*, by default is 2.0.
"""


@dataclass
class Bucket(Generic[T], SingleLinkedList[MapEntry[T]]):
    """**Bucket** class to represent a bucket in the **Hash Table** with the *Separate Chaining* method. The structure is based (inherits) on a custom singly linked list (*SingleLinkedList*) for *PyDASA*.

    Args:
        SingleLinkedList (dataclass): *PyDASA* custom class for a single linked list.
        Generic (T): Generic type for a Python data structure.
    """

    def __str__(self) -> str:
        """*__str__()* function to return a string representation of the *Bucket*. It also extends the *Node* class.

        Returns:
            str: string representation of the *Bucket*.
        """
        _str = super().__str__()
        return _str

    def __repr__(self) -> str:
        """*__repr__()* function to return a string representation of the *Bucket*. It also extends the *Node* class.

        Returns:
            str: string representation of the *Bucket*.
        """
        _str = super().__repr__()
        return _str


@dataclass
class SCHashTable(Generic[T]):

    # boolean to indicate if the hash table can be rehashed
    # :attr: rehashable
    rehashable: bool = True
    """
    Boolean to indicate if the hash table can be rehashed. By default is True.
    """

    # reserved space for the hash table
    # :attr: nentries
    nentries: int = 1
    """
    Inicial number of entries (n) for the hash table. By default is 1, but should be set according to the number of entries expected to be stored.

    NOTE: the reserved space (n) is NOT the capacity (M) of the hash table.
    """

    # starting capacity (M|m) for the hash table
    # :attr: mcapacity
    mcapacity: int = 1
    """
    The capacity (M) of the hash table. By default is 1, but should be set according to the number of entries expected to be stored.
    """

    # starting load factor (alpha) for the hash table
    # :attr: alpha
    alpha: Optional[float] = DFLT_SC_ALPHA
    """
    Load factor (*alpha*) for the hash table. By default is 4.0.

    NOTE: alpha = n/M (n: number of expected entries, M: capacity of the hash table).
    """

    # the cmp_function is used to compare emtries, not defined by default
    # :attr: cmp_function
    cmp_function: Optional[Callable[[Any, MapEntry[T]], int]] = None

    """
    Customizable comparison function for *SCHashTable* and its *MapEntry* objects. Defaults to *dflt_cmp_function_ht()* from *PyDASA*, but can be overridden by the user.
    """

    # actual place to store the entries in the hash table
    # :attr: hash_table
    hash_table: Optional[ArrayList[Bucket[T]]] = None

    """
    Index of the hash table where the *Buckets* are stored. By default is an empty *ArrayList* initialized with the configured capacity (M).
    """
    # the key is used to compare entries, not defined by default
    # :attr: key
    key: Optional[str] = DFLT_DICT_KEY
    """
    Customizable key name for identifying elements in the *SCHashTable*. Defaults to *DFLT_DICT_KEY = '_id'* from *PyDASA*, but can be overridden by the user.
    """

    # prime number (P) for the MAD compression function
    # :attr: prime
    prime: int = DFLT_PRIME
    """
    Prime number (P) for the MAD compression function. By default is 109345121, but can be overridden by the user.

    NOTE: the MAD compression function is: *h(k) = ((a*k + b) mod P) mod M*, where *a* and *b* are two random integers, *P* is a prime number and *M* is the hash table capacity.
    """

    # private scale (a) factor for the mad compression function
    # :attr: _scale
    _scale: int = 1
    """
    MAD compression function scale factor (a). By default is 1, but can be overridden by the user.
    """
    # private shift (b) factor for the mad compression function
    # :attr: _shift
    _shift: int = 0
    """
    MAD compression function shift factor (b). By default is 0, but can be overridden by the user.
    """

    # current factor (alpha) for the working hash table
    # :attr: _cur_alpha
    _cur_alpha: float = 0.0
    """
    Current load factor (*alpha*) for the hash table. By default is 0.0, and it updates with each operation that modifies the structure.
    """

    # minimum load factor (alpha) for the hash table
    # :attr: min_alpha
    min_alpha: float = MIN_SC_ALPHA
    """
    Minimum load factor (*alpha*) for the hash table. By default is 2.0. But can be overridden by the user.
    """

    # maximum load factor (alpha) for the hash table
    # :attr: max_alpha
    max_alpha: float = MAX_SC_ALPHA
    """
    Maximum load factor (*alpha*) for the hash table. By default is 8.0. But can be overridden by the user.
    """

    # actual number of used entries (n) in the hash table
    # :attr: _size
    _size: int = 0
    """
    Number of entries (*n*) in the hash table. By default is 0, but it updates with each operation that modifies the structure.
    """

    # :attr: collisions
    _collisions: int = 0
    """
    Number of collisions in the hash table. By default is 0, but it updates with each operation that modifies the structure.
    """

    # the type of the entry keys in the hash table
    # :attr: _key_type
    _key_type: Optional[type] = None
    """
    Data type for the keys of the *MapEntry* (key-value pair) that contains the hash table, by default is *None* and is configured when loading the first record.
    """

    # the type of the entry values in the hash table
    # :attr: _value_type
    _value_type: Optional[type] = None
    """
    Data type for the values of the *MapEntry* (key-value pair) that contains the hash table, by default is *None* and is configured when loading the first record.
    """

    # input elements from python list
    # :attr: iodata
    iodata: Optional[List[T]] = None
    """
    Optional Python list for loading external data intho the *SCHashTable*. Defaults to *None* but can be provided during creation.
    """

    def __post_init__(self) -> None:
        """*__post_init__()* Initializes the *SCHashTable* after creation by setting attributes like *rehashable*, *mcapacity*, *alpha*, *cmp_function*, *key*, *prime*, *scale*, *shift*, and *iodata*.
        It also sets the default values for the *min_alpha* and *max_alpha* attributes, which are used to control the load factor of the hash table.

        *NOTE:* Special method called automatically after object creation.
        """
        try:
            # Ensure alpha has a valid value
            alpha = self.alpha if self.alpha is not None else DFLT_SC_ALPHA

            # setting capacity
            self.mcapacity = next_prime(int(self.nentries / alpha))
            # setting scale and shift for MAD compression function
            self._scale = random.randint(1, self.prime - 1)
            self._shift = random.randint(0, self.prime - 1)

            # setting the compare function
            if self.cmp_function is None:
                self.cmp_function = self.default_compare

            # initializing new hash table with explicit type parameter
            self.hash_table = ArrayList[Bucket[T]](cmp_function=None,
                                                   key=self.key)

            # building buckets in the hash table
            for _ in range(self.mcapacity):
                # bucket needs cmp_function for index_of() searches
                _bucket = Bucket[T](cmp_function=self.cmp_function,
                                    key=self.key)
                # add the bucket to the hash table
                self.hash_table.append(_bucket)

            # setting the current load factor
            self._cur_alpha = self._size / self.mcapacity

            # checking the external input data type
            if self.iodata is not None and isinstance(self.iodata, VLD_IOTYPE_LT):
                for entry in self.iodata:
                    # if is a dict, use the key type
                    if isinstance(entry, dict):
                        _key = entry.get(self.key)
                        if _key is not None:
                            self.insert(_key, entry)
                    # otherwise, manage as data list
                    else:
                        self.insert(entry, entry)
            # clean input data
            self.iodata = None

        except Exception as err:
            self._error_handler(err)
            raise  # Re-raise after handling

    def default_compare(self, key1: Any, entry2: MapEntry[T]) -> int:
        """*default_compare()* Default comparison function for the *SCHashTable* and its *MapEntry* objects. Compares the key of the *MapEntry* with the provided key *key1* and reurns:
            - 0 if they are equal.
            - 1 if the *MapEntry* key is less than *key1*.
            - -1 if the *MapEntry* key is greater than *key1*.

        Args:
            key1 (Hashable): Key from the first *MapEntry* to compare.
            entry2 (MapEntry): Second *MapEntry* to compare.

        Returns:
            int: Comparison result.
        """
        try:
            # default comparison needs the key to be defined
            if self.key is None:
                raise ValueError("Key must be set before comparison")
            return dflt_cmp_function_ht(key1, entry2, self.key)
        except Exception as err:
            self._error_handler(err)
            raise   # Re-raise the exception after handling

    @property
    def size(self) -> int:
        """*size* Property to retrieve the number if entries (n) in the *SCHashTable*.
        Returns:
            int: Number of entries (n) in the *SCHashTable*.
        """
        return self._size

    @property
    def empty(self) -> bool:
        """*empty* Property to check if the *SCHashTable* has entries or not.

        Returns:
            bool: True if the *SCHashTable* is empty, False otherwise.
        """
        return self._size == 0

    @property
    def collisions(self) -> int:
        """*collisions* Property to retrieve the number of collisions in the *SCHashTable*.

        Returns:
            int: Number of collisions in the *SCHashTable*.
        """
        return self._collisions

    def clear(self) -> None:
        """*clear()* function to reset the *SCHashTable* to its initial state. It clears all the entries in the hash table and resets the size, collisions and current load factor.
        """
        # reset the size, collisions and current load factor
        self._size = 0
        self._collisions = 0
        self._cur_alpha = 0
        # clear the bukets in the hash table
        if self.hash_table is not None:
            for _bucket in self.hash_table:
                _bucket.clear()
            # clear the hash table itself
            self.hash_table.clear()

    def insert(self, key: T, value: T) -> None:
        """*insert()* adds a new entry to the *SCHashTable*. It creates a new *MapEntry* object with the key-value pair.

        Args:
            key (T): key for the entry.
            value (T): value for the entry.
        """
        # create a new entry for the hash table
        _new_entry = MapEntry(key, value)
        _idx = -1
        # cheking the type of the entry
        if self._validate_type(_new_entry):
            # get the hash key for the entry
            _hash = mad_hash(key,
                             self._scale,
                             self._shift,
                             self.prime,
                             self.mcapacity)

            if self.hash_table is not None:
                # checking the bucket
                _bucket = self.hash_table.get(_hash)
                # check if the bucket is empty
                if not _bucket.empty:
                    # Create temporary MapEntry for searching, because cmp_function needs MapEntry
                    _temp_entry = MapEntry(key, None)
                    _idx = _bucket.index_of(_temp_entry)
                # the entry is not in the bucket, add it and a collision
                # the entry is already in the bucket, update it
                if _idx > -1:
                    _bucket.update(_new_entry, _idx)
                # otherwise, is a new entry
                else:
                    if _bucket.size >= 1:
                        self._collisions += 1
                    _bucket.append(_new_entry)
                    self._size += 1
                    self._cur_alpha = self._size / self.mcapacity
                # check if the structure needs to be rehashed
                if self._cur_alpha >= self.max_alpha:
                    self.resize()

    def get_entry(self, key: T) -> Optional[MapEntry]:
        """*get_entry()* retrieves an entry from the *SCHashTable* using the provided key.

        Args:
            key (T): key for the entry.

        Raises:
            IndexError: error if the *SCHashTable* is empty.

        Returns:
            Optional[MapEntry]: *MapEntry* object with the key-value pair if found, None otherwise.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        # assume the entry is not in the structure
        entry = None
        idx = -1
        # get the hash key for the entry
        _hash = mad_hash(key,
                         self._scale,
                         self._shift,
                         self.prime,
                         self.mcapacity)

        if self.hash_table is not None:
            # checking the bucket
            _bucket = self.hash_table.get(_hash)
            # check if the bucket is empty
            if not _bucket.empty:
                # Create temporary MapEntry for searching, because cmp_function needs MapEntry
                _temp_entry = MapEntry(key, None)
                idx = _bucket.index_of(_temp_entry)
            # if the entry is in the bucket, return it
            if idx > -1:
                entry = _bucket.get(idx)

        # otherwise, return entry
        return entry

    def get_bucket(self, key: T) -> Optional[Bucket]:
        """*get_bucket()* retrieves the bucket containing the key-value pair from the *SCHashTable* using the provided key.

        Args:
            key (T): key for the entry.

        Raises:
            IndexError: error if the *SCHashTable* is empty.

        Returns:
            Optional[Bucket]: *Bucket* object containing the key-value pair if found, None otherwise.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        # assume the entry is not in the structure
        _bucket = None
        # get the hash key for the entry
        _hash = mad_hash(key,
                         self._scale,
                         self._shift,
                         self.prime,
                         self.mcapacity)

        # recover the bucket
        if self.hash_table is not None:
            _bucket = self.hash_table.get(_hash)
            # ceck if the bucket is empty
            if _bucket.empty:
                _bucket = None

        # otherwise, return the bucket
        return _bucket

    def is_present(self, key: T) -> bool:
        """*is_present()* checks if the provided key is present in the *SCHashTable*.

        Args:
            key (T): key for the entry.

        Raises:
            IndexError: error if the *SCHashTable* is empty.

        Returns:
            bool: True if the key is present in the *SCHashTable*, False otherwise.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        # assume the entry is not in the structure
        found = False
        # use the MAD compression function to get the hash key
        _hash = mad_hash(key,
                         self._scale,
                         self._shift,
                         self.prime,
                         self.mcapacity)

        if self.hash_table is not None:
            # look into the bucket
            _bucket = self.hash_table.get(_hash)
            # Create temporary MapEntry for searching
            _temp_entry = MapEntry(key, None)
            _idx = _bucket.index_of(_temp_entry)
            # if the entry is in the bucket, return True
            if _idx > -1:
                found = True

        # otherwise, return foin flag
        return found

    def delete(self, key: T) -> Optional[MapEntry]:
        """*delete()* removes an entry from the *SCHashTable* using the provided key.

        Args:
            key (T): key for the entry.

        Raises:
            IndexError: error if the *SCHashTable* is empty.

        Returns:
            Optional[MapEntry]: *MapEntry* object with the key-value pair if found, None otherwise.
        """
        if self.empty:
            raise IndexError("Empty data structure")
        # assume the entry is not in the structure
        _entry = None
        _idx = -1
        # get the hash key for the entry
        _hash = mad_hash(key,
                         self._scale,
                         self._shift,
                         self.prime,
                         self.mcapacity)

        if self.hash_table is not None:
            # checking the bucket
            _bucket = self.hash_table.get(_hash)
            # check if the bucket is not empty
            if not _bucket.empty:
                # Create temporary MapEntry for searching
                _temp_entry = MapEntry(key, None)
                _idx = _bucket.index_of(_temp_entry)
                # if the entry is in the bucket, remove it
                if _idx > -1:
                    _entry = _bucket.remove(_idx)
                    self.hash_table.update(_bucket, _hash)
                    # updating collisions
                    if _bucket.size > 1:
                        self._collisions -= 1
                    # updating size and alpha
                    self._size -= 1
                    self._cur_alpha = self._size / self.mcapacity
                # TODO old code, check if needed
                # elif _idx == -1:
                #     raise IndexError(f"Entry for Key: {key} not found")
        if self._cur_alpha < self.min_alpha:
            self.resize()
        return _entry

    def keys(self) -> SingleLinkedList[T]:
        """*keys()* returns a single linked list of keys from the *SCHashTable*.

        Returns:
            SingleLinkedList[T]: list of keys from the *SCHashTable*. e.g. [key1, key2, ...].
        """
        _keys_lt = SingleLinkedList(key=self.key)
        if self.hash_table is not None:
            for _bucket in self.hash_table:
                if not _bucket.empty:
                    for _entry in _bucket:
                        _keys_lt.append(_entry.key)
        return _keys_lt

    def values(self) -> SingleLinkedList[T]:
        """*values()* returns a single linked list of values from the *SCHashTable*.

        Returns:
            SingleLinkedList[T]: list of values from the *SCHashTable*. e.g. [value1, value2, ...].
        """
        _values_lt = SingleLinkedList(key=self.key)
        if self.hash_table is not None:
            for _bucket in self.hash_table:
                if not _bucket.empty:
                    for _entry in _bucket:
                        _values_lt.append(_entry.value)
        return _values_lt

    def entries(self) -> SingleLinkedList[T]:
        """*entries() returns a list of tuples with the key and value of each entry in the hash table.

        Returns:
            SingleLinkedList[T]: list of tuples with the key-value paor of each entry in the hash table. e.g. [(key1, value1), (key2, value2), ...].
        """
        _entries_lt = SingleLinkedList(key=self.key)
        if self.hash_table is not None:
            for _bucket in self.hash_table:
                if not _bucket.empty:
                    for _entry in _bucket:
                        _data = (_entry.key, _entry.value)
                        _entries_lt.append(_data)
        return _entries_lt

    def resize(self) -> None:
        """*resize()* rehashes the *SCHashTable* by creating a new hash table with a new capacity (M) and rehashing all the entries from the old hash table to the new one. It also updates the size, collisions and current load factor.
        """
        try:
            # check if the structure is rehashable
            if self.rehashable:
                # gettting the current capacity to avoid null errors
                new_capacity = self.mcapacity
                # find the new capacity according to limits
                # augmenting the capacity
                if self._cur_alpha >= self.max_alpha:
                    new_capacity = next_prime(self.mcapacity * 2)
                # reducing the capacity
                elif self._cur_alpha < self.min_alpha:
                    new_capacity = next_prime(self.mcapacity // 2)

                # asigning the new capacity
                self.mcapacity = new_capacity

                # reseting the size, collisions and current load factor
                self._size = 0
                self._collisions = 0
                self._cur_alpha = 0

                # creating the new hash table
                new_table = ArrayList[Bucket[T]](cmp_function=None,
                                                 key=self.key)
                # keep in memory the old hash table
                old_table = self.hash_table

                # Create the empty buckets in thenew hash table
                i = 0
                while i < self.mcapacity:
                    # bucket is a SingleLinkedList list
                    bucket = Bucket(cmp_function=self.cmp_function,
                                    key=self.key)
                    new_table.append(bucket)
                    i += 1

                # replace the old table with the new one
                self.hash_table = new_table

                if old_table is not None:
                    # iterate over the old table
                    for bucket in old_table:
                        if not bucket.empty:
                            for entry in bucket:
                                key = entry.key
                                value = entry.value
                                if None not in (key, value):
                                    self.insert(cast(T, key), cast(T, value))
        except Exception as err:
            self._error_handler(err)

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

    def _validate_type(self, entry: MapEntry) -> bool:
        """*_validate_type()* validates the type of the *MapEntry* against the expected type in the *SCHashTable*. It raises a *TypeError* if the types do not match.

        Args:
            entry (MapEntry): *MapEntry* object to validate.

        Raises:
            TypeError: error if the type of the *MapEntry* does not match the expected type in the *SCHashTable*.

        Returns:
            bool: True if the type of the *MapEntry* matches the expected type in the *SCHashTable*, False otherwise.
        """
        # TODO check usability of this function
        # if datastruct is empty, set the entry type
        key = entry.key
        value = entry.value
        if self.empty:
            self._key_type = type(key)
            self._value_type = type(value)
        # check if the new entry is the same type as the other entries
        valid = self._validate_key_type(entry)
        valid = valid and self._validate_value_type(entry)
        # otherwise, the type is valid
        return valid

    def _validate_key_type(self, entry: MapEntry) -> bool:
        """*_validate_key_type()* validates the type of the key in the *MapEntry* against the expected type in the *SCHashTable*. It raises a *TypeError* if the types do not match.

        Args:
            entry (MapEntry): *MapEntry* object to validate.

        Raises:
            TypeError: error if the type of the key in the *MapEntry* does not match the expected type in the *SCHashTable*.

        Returns:
            bool: True if the type of the key in the *MapEntry* matches the expected type in the *SCHashTable*, False otherwise.-
        """
        key = entry.key
        # if the new entry is the same type as the other entries
        if self._key_type is not type(key):
            err_msg = f"Invalid key type: {type(key)} "
            err_msg += f"for struct configured with type: {self._key_type}"
            raise TypeError(err_msg)
        # otherwise, the type is valid
        return True

    def _validate_value_type(self, entry: MapEntry) -> bool:
        """*_validate_value_type()* validates the type of the value in the *MapEntry* against the expected type in the *SCHashTable*. It raises a *TypeError* if the types do not match.

        Args:
            entry (MapEntry): *MapEntry* object to validate.

        Raises:
            TypeError: error if the type of the value in the *MapEntry* does not match the expected type in the *SCHashTable*.

        Returns:
            bool: True if the type of the value in the *MapEntry* matches the expected type in the *SCHashTable*, False otherwise.
        """
        value = entry.value
        # if the new entry is the same type as the other entries
        if self._value_type is not type(value):
            err_msg = f"Invalid value type: {type(value)} "
            err_msg += f"for struct configured with type: {self._value_type}"
            raise TypeError(err_msg)
        # otherwise, the type is valid
        return True

    def __len__(self) -> int:
        """*__len__()* function to return the number of entries (n) in the *SCHashTable*.

        Returns:
            int: Number of entries (n) in the *SCHashTable*.
        """
        return self._size

    def __str__(self) -> str:
        """*__str__()* function to return a string representation of the *SCHashTable*.

        Returns:
            str: string representation of the *SCHashTable*.
        """
        _attr_lt = []
        for attr, value in vars(self).items():
            # Skip private attributes starting with "__"
            if attr.startswith("__"):
                continue
            # Format callable attributes
            if callable(value):
                try:
                    value = f"{value.__name__}{inspect.signature(value)}"
                except ValueError:
                    value = repr(value)  # Fallback for non-standard callables
            # Format attribute name and value
            _attr_name = attr.lstrip("_")
            _attr_lt.append(f"{_attr_name}={repr(value)}")
        # Format the string representation of the ArrayList class and its attributes
        _str = f"{self.__class__.__name__}({', '.join(_attr_lt)})"
        return _str

    def __repr__(self) -> str:
        """*__repr__()* function to return a string representation of the *SCHashTable*.

        Returns:
            str: string representation of the *SCHashTable*.
        """
        return self.__str__()
