# -*- coding: utf-8 -*-
"""
Module framework.py
===========================================

Module for **Schema** to manage Fundamental Dimensional Units (FDUs) for Dimensional Analysis in *PyDASA*.

This module provides the Schema class which manages dimensional frameworks, FDU precedence, and regex patterns for dimensional expression validation.

Classes:
    **Schema**: Manages dimensional frameworks and FDUs, providing methods for validation,

*IMPORTANT:* Based on the theory from:

    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""

# native python modules
# dataclass imports
from __future__ import annotations
from dataclasses import dataclass, field, fields
# data type imports
from typing import List, Dict, Optional, Any, cast

# custom modules
from pydasa.validations.decorators import validate_type
from pydasa.validations.decorators import validate_emptiness
from pydasa.validations.decorators import validate_custom
from pydasa.core.basic import Foundation
from pydasa.core.setup import Frameworks
from pydasa.dimensional.fundamental import Dimension
from pydasa.validations.patterns import DFLT_POW_RE
from pydasa.core.setup import PYDASA_CFG


@dataclass
class Schema(Foundation):
    """**Schema** Manages dimensional frameworks and FDUs for *PyDASA*.

    Maintains a collection of Dimensions with their precedence, provides regex patterns for dimensional expressions, and manages the dimensional framework context.

    Args:
        Foundation: Foundation class for validation of symbols and frameworks.

    Attributes:
        _fdu_lt (List[Dimension]): List of Fundamental Dimensional Units in precedence order.
        _fdu_map (Dict[str, Dimension]): Dictionary mapping FDU symbols to Dimension objects.
        _fdu_regex (str): Regex pattern for matching dimensional expressions (e.g., 'M/L*T^-2' to 'M^1*L^-1*T^-2').
        _fdu_pow_regex (str): Regex pattern for matching dimensions with exponents. (e.g., 'M*L^-1*T^-2' to 'M^(1)*L^(-1)*T^(-2)').
        _fdu_no_pow_regex (str): Regex pattern for matching dimensions without exponents. (e.g., 'M*L*T' to 'M^(1)*L^(1)*T^(1)').
        _fdu_sym_regex (str): Regex pattern for matching FDUs in symbolic expressions. (e.g., 'M^(1)*L^(-1)*T^(-2)' to 'L**(-1)*M**(1)*T**(-2)').
    """

    # FDUs storage
    # Default Fundamental Dimensional Units (FDU) precedence list
    # FDU precedence list, linked to WKNG_FDU_PREC_LT, full object list.
    # :attr: _fdu_lt
    _fdu_lt: List[Dimension] = field(default_factory=list)
    """Internal storage for fundamental dimension objects. Always a List[Dimension] after __post_init__."""

    # Default Fundamental Dimensional Units (FDU) framework
    # FDU map, linked to WKNG_FDU_PREC_LT, symbol to Dimension object.
    # :attr: _fwk
    _fdu_map: Dict[str, Dimension] = field(default_factory=dict)
    """Dictionary mapping FDU symbols to Dimension objects in *PyDASA*. procesess (e.g., Mass [M], Length [L], Time [T]).

    Purpose:
        - Defines the default dimensional framework used in *PyDASA*.
        - Used to initialize entities without a specified framework.
        - Basis for dimensional analysis precedence list in *PyDASA*.
        - Validates parameter and variable dimensions in *PyDASA*.
        - Default is the Physical FDUs framework.
        - Can be customized for specific applications or domains.
    """

    # FDU symbol list, linked to WKNG_FDU_PREC_LT, string symbol list.
    # :attr: _fdu_symbols
    _fdu_symbols: List[str] = field(default_factory=list)
    """List of FDU symbols in the framework for the dimensional matrix (e.g., 'M*L^-1*T^-2').

    Purpose:
        - Defines the row order in the dimensional matrix.
        - Validates parameter and variable dimensions in *PyDASA*."""

    # Regex patterns
    # Default/Working FDU Pattern, WKNG_FDU_RE
    # :attr: _fdu_regex
    _fdu_regex: str = ""
    """Regex pattern for matching dimensional expressions.

    Default/Working regex pattern to match FDUs in *PyDASA* (e.g., 'M*L^-1*T^-2' to 'M^(1)*L^(-1)*T^(-2)')."""

    # FDU power regex pattern, linked to WKNG_POW_RE.
    # :attr: _fdu_pow_regex
    _fdu_pow_regex: str = DFLT_POW_RE
    """Regex pattern for matching FDUs with exponents (e.g., 'M*L^-1*T^-2' to 'M^(1)*L^(-1)*T^(-2)')"""

    # FDU no power regex pattern, linked to WKNG_NO_POW_RE.
    # :attr: _fdu_no_pow_regex
    _fdu_no_pow_regex: str = ""
    """Regex pattern for matching dimensions without exponents.

    Default/Working regex to match FDUs without exponents (e.g., 'T*D' instead of 'T^2*D^-1')."""

    # FDU symbolic regex pattern, linked to WKNG_FDU_SYM_RE.
    # :attr: _fdu_sym_regex
    _fdu_sym_regex: str = ""
    """Regex pattern for matching FDUs in symbolic expressions.

    Default/Working regex to match FDU symbols in *PyDASA* (e.g., 'T^(1)*D^(-1)' to 'D**(-1)*T**(2)')."""

    def __post_init__(self) -> None:
        """*__post_init__()* Initializes the framework and sets up regex patterns.
        """
        # Initialize base class
        super().__post_init__()

        # Initialize FDUs based on framework
        self._setup_fdus()

        # Initialize indices, map, and symbol precedence
        self._validate_fdu_precedence()
        self._update_fdu_map()
        self._update_fdu_symbols()

        # Generate regex patterns
        self._setup_regex()

    def _setup_fdus(self) -> None:
        """*_setup_fdus()* Initializes FDUs based on the selected framework.

        Creates and adds standard FDUs for the selected framework (PHYSICAL,
        COMPUTATION, SOFTWARE) or validates custom FDUs.

        Raises:
            ValueError: If framework is not supported.
            ValueError: If custom framework FDUs are not provided.
            ValueError: If custom framework FDUs are not properly formatted.
            ValueError: If custom framework FDUs contain invalid types.
        """
        # if the framework is supported (PHYSICAL, COMPUTATION, SOFTWARE), configure the default
        if self.fwk in PYDASA_CFG.get_instance().frameworks and self.fwk != Frameworks.CUSTOM.value:
            # If _fdu_lt is empty, set up default framework
            if not self._fdu_lt:
                self._fdu_lt = self._setup_default_framework()
            # If _fdu_lt is provided, just validate/convert it
            else:
                self._convert_fdu_lt()

        # if the framework is user-defined (CUSTOM), use the provided FDUs
        elif self.fwk == Frameworks.CUSTOM.value:
            if not self._fdu_lt:
                _msg = "Custom framework requires '_fdu_lt' to define FDUs"
                raise ValueError(_msg)
            # Convert provided FDUs to List[Dimension]
            self._convert_fdu_lt()

        # otherwise, raise an error
        else:
            _msg = f"Invalid Frameworks: {self.fwk}. "
            _fwk = PYDASA_CFG.get_instance().frameworks
            _msg += f"Valid options: {', '.join(_fwk)}."
            raise ValueError(_msg)

    def _convert_fdu_lt(self) -> None:
        """*_convert_fdu_lt()* Converts and validates the provided FDUs list/dict into Dimension objects.

        Raises:
            TypeError: If elements in the list are not all Dimension or dict.
            TypeError: If values in the dict are not all dict objects.
            TypeError: If _fdu_lt is not a list or dict.
        """
        # if FDUs are a list
        if isinstance(self._fdu_lt, list):
            # if FDUs are already type Dimensions
            if all(isinstance(d, Dimension) for d in self._fdu_lt):
                pass    # do nothing
            # else if FDUs are a list of dicts
            elif all(isinstance(d, dict) for d in self._fdu_lt):
                fdus = []
                # iterate over the list and create the dimensions
                for d in self._fdu_lt:
                    if isinstance(d, dict):
                        fdus.append(Dimension(**d))
                self._fdu_lt = fdus
            else:
                _msg = "All elements in '_fdu_lt' list must be either Dimension or dict"
                raise TypeError(_msg)

        # # if FDUs are a dict of dicts
        # elif isinstance(self._fdu_lt, dict):
        #     # Check if dict values are all dicts (not Dimensions in a dict)
        #     if all(isinstance(d, dict) for d in self._fdu_lt.values()):
        #         fdus = []
        #         # iterate over the dict-values and create the dimensions
        #         for idx, (sym, val) in enumerate(self._fdu_lt.items()):
        #             if isinstance(val, dict):
        #                 # Use the dict key as symbol if not in the dict
        #                 if "_sym" not in val:
        #                     val["_sym"] = sym
        #                 if "_idx" not in val:
        #                     val["_idx"] = idx
        #                 fdus.append(Dimension(**val))
        #         self._fdu_lt = fdus
        #     else:
        #         _msg = "All values in '_fdu_lt' dict must be dict objects"
        #         raise TypeError(_msg)

        # otherwise, error due to invalid type
        else:
            _msg = f"Invalid '_fdu_lt' type: {type(self._fdu_lt).__name__}."
            types_lt = [Dimension.__name__, dict.__name__, list.__name__]
            _msg += f" Supported types: {types_lt}"
            raise TypeError(_msg)

    def _setup_default_framework(self) -> List[Dimension]:
        """*_setup_default_framework()* Returns the default FDU precedence list for the specified framework.

        Returns:
            List[str]: Default FDUs precedence list based on the framework map.
        """
        # map for easy access to the FDUs
        _dflt_fwk_map = PYDASA_CFG.get_instance().SPT_FDU_FWKS
        # Tell type checker this is definitely a Dict
        _fwk_map: Dict[str, Any] = cast(Dict[str, Any], _dflt_fwk_map)
        # create the FDUs list
        ans = []
        # select FDU framework
        if self.fwk in _fwk_map:
            # Get the fdus dictionary from the framework config
            fdus_dict = _fwk_map[self.fwk].get("fdus", {})
            # Create standard FDU set
            for idx, (sym, data) in enumerate(fdus_dict.items()):
                fdu = Dimension(
                    _idx=idx,
                    _sym=sym,
                    _fwk=self._fwk,
                    _unit=data.get("unit", ""),
                    _name=data.get("name", ""),
                    description=data.get("description", ""))
                ans.append(fdu)
        return ans

    def _validate_fdu_precedence(self) -> None:
        """*_validate_fdu_precedence()* Ensures FDUs have valid and unique precedence values.

        Raises:
            ValueError: If FDU precedence values are duplicated.
        """
        # trick to do nothing if FDU set is null
        if not self._fdu_lt:
            return

        # Check for duplicate precedence values
        indices = [fdu.idx for fdu in self._fdu_lt]
        if len(indices) != len(set(indices)):
            raise ValueError("Duplicate precedence values in FDUs.")

        # Sort FDUs by idx precedence
        self._fdu_lt.sort(key=lambda fdu: fdu.idx)

    def _update_fdu_map(self) -> None:
        """*_update_fdu_map()* Updates the FDU symbol to object mapping.
        """
        self._fdu_map.clear()
        for fdu in self._fdu_lt:
            self._fdu_map[fdu.sym] = fdu

    def _update_fdu_symbols(self) -> None:
        """*_update_fdu_symbols()* Updates the list of FDU symbols in precedence order."""
        self._fdu_symbols = [fdu.sym for fdu in self._fdu_lt]

    def _setup_regex(self) -> None:
        """*_setup_regex()* Sets up regex patterns for dimensional validation. Generates regex patterns for:
            - validating dimensional expressions.
            - parsing exponents.
            - completing expressions with exponent.
            - handling symbolic expressions.
        """
        # trick to do nothing if FDU set is null
        if not self._fdu_lt:
            return None

        # Get FDU symbols in precedence order
        # fdu_symbols = [fdu.sym for fdu in self._fdu_lt]
        _fdu_str = ''.join(self.fdu_symbols)

        # NOTE: OG REGEX!
        # DFLT_FDU_RE: str = rf"^[{''.join(DFLT_FDU_PREC_LT)}](\^-?\d+)?(\*[{''.join(DFLT_FDU_PREC_LT)}](?:\^-?\d+)?)*$"
        # Generate main regex for dimensional expressions
        self._fdu_regex = rf"^[{_fdu_str}](\^-?\d+)?(\*[{_fdu_str}](?:\^-?\d+)?)*$"

        # Use default regex for exponents
        self._fdu_pow_regex = DFLT_POW_RE

        # NOTE: OG REGEX!
        # DFLT_NO_POW_RE: str = rf"[{''.join(DFLT_FDU_PREC_LT)}](?!\^)"
        # Generate regex for dimensions without exponents
        self._fdu_no_pow_regex = rf"[{_fdu_str}](?!\^)"

        # NOTE: OG REGEX!
        # DFLT_FDU_SYM_RE: str = rf"[{''.join(DFLT_FDU_PREC_LT)}]"
        # Generate regex for dimensions in symbolic expressions
        self._fdu_sym_regex = rf"[{_fdu_str}]"

    def _validate_fdu_lt(self, value: List[Dimension]) -> None:
        """*_validate_fdu_lt()* Custom validator for fdu_lt property.

        Args:
            value (List[Dimension]): List of FDUs to validate.

        Raises:
            ValueError: If list is empty or contains non-Dimension objects.
        """
        if not value:
            _msg = "FDUs list must be non-empty. "
            _msg += f"Provided: {value}"
            raise ValueError(_msg)
        if not all(isinstance(i, Dimension) for i in value):
            _msg = "FDUs list must contain only Dimension objects. "
            _msg += f"Provided: {value}"
            raise ValueError(_msg)

    # propierties getters and setters

    @property
    def fdu_lt(self) -> List[Dimension]:
        """*fdu_lt* Get the list of FDUs in precedence order.

        Returns:
            List[Dimension]: List of FDUs.
        """
        return self._fdu_lt

    @fdu_lt.setter
    @validate_type(list, allow_none=False)
    @validate_custom(lambda self, val: self._validate_fdu_lt(val))
    def fdu_lt(self, val: List[Dimension]) -> None:
        """*fdu_lt* Set the FDUs in precedence order.

        Args:
            val (List[Dimension]): List of FDUs.

        Raises:
            ValueError: If the FDUs list is empty or invalid.
        """
        self._fdu_lt = val

    @property
    def fdu_symbols(self) -> List[str]:
        """*fdu_symbols* Get the list of FDU symbols in precedence order.

        Returns:
            List[str]: List of FDU symbols.
        """
        return self._fdu_symbols.copy()

    @property
    def size(self) -> int:
        """*size* Get the number of FDUs in the framework.

        Returns:
            int: Number of FDUs.
        """
        return len(self._fdu_lt)

    @property
    def fdu_regex(self) -> str:
        """*fdu_regex* Get the FDU regex pattern.

        Returns:
            str: Regex pattern for validating dimensional expressions.
        """
        return self._fdu_regex

    @fdu_regex.setter
    @validate_type(str, allow_none=False)
    @validate_emptiness()
    def fdu_regex(self, val: str) -> None:
        """*fdu_regex* Set the FDUs regex pattern.

        Args:
            val (str): FDUs regex pattern.

        Raises:
            ValueError: If the FDUs regex pattern is empty or not a string.
        """
        self._fdu_regex = val

    @property
    def fdu_pow_regex(self) -> str:
        """*fdu_pow_regex* Get the FDU powered regex pattern.

        Returns:
            str: Regex pattern for matching dimensions with exponents.
        """
        return self._fdu_pow_regex

    @fdu_pow_regex.setter
    @validate_type(str, allow_none=False)
    @validate_emptiness()
    def fdu_pow_regex(self, val: str) -> None:
        """*fdu_pow_regex* Set the FDUs pow-regex pattern.

        Args:
            val (str): FDUs pow-regex pattern for matching dimensions with exponent.

        Raises:
            ValueError: If the FDUs pow-regex pattern is empty or not a string.
        """
        self._fdu_pow_regex = val

    @property
    def fdu_no_pow_regex(self) -> str:
        """*fdu_no_pow_regex* Get the FDU no-power regex pattern.

        Returns:
            str: Regex pattern for matching dimensions without exponents.
        """
        return self._fdu_no_pow_regex

    @fdu_no_pow_regex.setter
    @validate_type(str, allow_none=False)
    @validate_emptiness()
    def fdu_no_pow_regex(self, val: str) -> None:
        """*fdu_no_pow_regex* Set the FDUs no-pow-regex pattern.

        Args:
            val (str): FDUs no-pow-regex pattern for matching dimensions without exponent.

        Raises:
            ValueError: If the FDUs no-pow-regex pattern is empty or not a string.
        """
        self._fdu_no_pow_regex = val

    @property
    def fdu_sym_regex(self) -> str:
        """*fdu_sym_regex* Get the FDU symbol regex pattern.

        Returns:
            str: Regex pattern for matching FDUs in symbolic expressions.
        """
        return self._fdu_sym_regex

    @fdu_sym_regex.setter
    @validate_type(str, allow_none=False)
    @validate_emptiness()
    def fdu_sym_regex(self, val: str) -> None:
        """*fdu_sym_regex* Set the FDUs sym-regex pattern.

        Args:
            val (str): FDUs sym-regex pattern for matching dimensions in symbolic expressions.

        Raises:
            ValueError: If the FDUs sym-regex pattern is empty or not a string.
        """
        self._fdu_sym_regex = val

    def get_fdu(self, symbol: str) -> Optional[Dimension]:
        """*get_fdu()* Get an FDU by its symbol.

        Args:
            symbol (str): FDU symbol.

        Returns:
            Optional[Dimension]: FDU object if found, None otherwise.
        """
        return self._fdu_map.get(symbol)

    def has_fdu(self, symbol: str) -> bool:
        """*has_fdu()* Check if an FDU with the given symbol exists.

        Args:
            symbol (str): FDU symbol.

        Returns:
            bool: True if the FDU exists, False otherwise.
        """
        return symbol in self._fdu_map

    def add_fdu(self, fdu: Dimension) -> None:
        """*add_fdu()* Add an FDU to the framework.

        Args:
            fdu (Dimension): FDU to add.

        Raises:
            ValueError: If an FDU with the same symbol already exists.
            ValueError: If the FDU framework does not match the current framework.
        """
        if self.has_fdu(fdu.sym):
            raise ValueError(f"FDU with symbol '{fdu.sym}' already exists.")

        # Set framework
        if fdu.fwk != self._fwk:
            _msg = "FDU framework mismatch: "
            _msg += f"Expected '{self._fwk}', got '{fdu.fwk}'"
            raise ValueError(_msg)

        # Add FDU
        self._fdu_lt.append(fdu)

        # Update indices, map, and symbol precedence
        self._validate_fdu_precedence()
        self._update_fdu_map()
        self._update_fdu_symbols()

        # Update regex patterns
        self._setup_regex()

    def remove_fdu(self, sym: str) -> Dimension:
        """*remove_fdu()* Remove an FDU from the framework.

        Args:
            sym (str): Symbol of the FDU to remove.

        Returns:
            Dimension: removed FDU object.
        """
        if not self.has_fdu(sym):
            raise ValueError(f"FDU with symbol '{sym}' does not exist.")

        # Remove FDU
        # find index with the symbol
        if sym in self._fdu_map:
            # direct retrieve the FDU to avoid Optional return of dict.get
            fdu_obj = self._fdu_map[sym]
            # Remove by precedence index and capture the removed Dimension
            idx = fdu_obj.idx
            ans = self._fdu_lt.pop(idx)
        else:
            # Should not happen because of the earlier has_fdu check, but keep safe
            raise ValueError(f"FDU with symbol '{sym}' does not exist.")

        # Update indices, map, and symbol precedence
        self._validate_fdu_precedence()
        self._update_fdu_map()
        self._update_fdu_symbols()

        # Update regex patterns
        self._setup_regex()

        return ans

    def reset(self) -> None:

        self._fdu_lt.clear()
        self._fdu_map.clear()
        self._fdu_symbols.clear()
        self._fdu_regex = ""
        self._fdu_pow_regex = DFLT_POW_RE
        self._fdu_no_pow_regex = ""
        self._fdu_sym_regex = ""

    def to_dict(self) -> Dict[str, Any]:
        """*to_dict()* Convert framework to dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation of the framework.
        """
        result = {}

        # Get all dataclass fields
        for f in fields(self):
            attr_name = f.name
            attr_value = getattr(self, attr_name)

            # Handle Dimension list (convert each Dimension)
            if isinstance(attr_value, list) and all(isinstance(d, Dimension) for d in attr_value):
                attr_value = [d.to_dict() for d in attr_value]

            # Handle Dimension dictionary (convert each Dimension)
            if isinstance(attr_value, dict) and all(isinstance(d, Dimension) for d in attr_value.values()):
                attr_value = {k: d.to_dict() for k, d in attr_value.items()}

            # Skip None values for optional fields
            if attr_value is None:
                continue

            # Remove leading underscore from private attributes
            if attr_name.startswith("_"):
                clean_name = attr_name[1:]  # Remove first character
            else:
                clean_name = attr_name

            result[clean_name] = attr_value

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Schema:
        """*from_dict()* Create framework from dictionary representation.

        Args:
            data (Dict[str, Any]): Dictionary representation of the framework.

        Returns:
            DimScheme: New DimScheme instance.
        """
        # Get all valid field names from the dataclass
        field_names = {f.name for f in fields(cls)}

        # Map keys without underscores to keys with underscores
        mapped_data = {}

        for key, value in data.items():
            # Try the key as-is first (handles both _fwk and name)
            if key in field_names:
                mapped_data[key] = value
            # Try adding underscore prefix (handles fwk -> _fwk)
            elif f"_{key}" in field_names:
                mapped_data[f"_{key}"] = value
            # Try removing underscore prefix (handles _name -> name if needed)
            elif key.startswith("_") and key[1:] in field_names:
                mapped_data[key[1:]] = value

        # Convert Dimension list back
        if "fdu_lt" in mapped_data or "_fdu_lt" in mapped_data:
            fdu_data = mapped_data.get("fdu_lt") or mapped_data.get("_fdu_lt")
            if isinstance(fdu_data, list):
                mapped_data["_fdu_lt"] = [
                    Dimension.from_dict(d) if isinstance(d, dict) else d
                    for d in fdu_data
                ]

        # Convert Dimension map back
        if "fdu_map" in mapped_data or "_fdu_map" in mapped_data:
            map_data = mapped_data.get(
                "fdu_map") or mapped_data.get("_fdu_map")
            if isinstance(map_data, dict):
                mapped_data["_fdu_map"] = {
                    k: Dimension.from_dict(d) if isinstance(d, dict) else d
                    for k, d in map_data.items()
                }

        # Remove computed/derived fields that shouldn't be passed to constructor
        computed_fields = [
            "fdu_map", "_fdu_map",  # Reconstructed from fdu_lt
            "fdu_symbols", "_fdu_symbols",  # Reconstructed from fdu_lt
            "size"  # Computed property
        ]

        for field_name in computed_fields:
            mapped_data.pop(field_name, None)

        # Create framework instance
        framework = cls(**mapped_data)

        return framework
