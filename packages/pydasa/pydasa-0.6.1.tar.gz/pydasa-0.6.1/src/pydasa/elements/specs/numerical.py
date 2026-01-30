# -*- coding: utf-8 -*-
"""
Module numerical.py
===========================================

Numerical perspective for variable representation.

This module defines the NumericalSpecs class representing the computational
value ranges and discretization properties of a variable.

Classes:
    **BoundsSpecs**: Value bounds in original units
    **StandardizedSpecs**: Standardized value specifications with discretization
    **NumericalSpecs**: Numerical variable specifications (combines BoundsSpecs and StandardizedSpecs)

*IMPORTANT:* Based on the theory from:

    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""
# native python modules
# dataclass imports
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# third-party numerical imports
import numpy as np
from numpy.typing import NDArray

# custom modules
from pydasa.validations.decorators import validate_type
from pydasa.validations.decorators import validate_range


@dataclass
class BoundsSpecs:
    """Value bounds in original units: min, max, mean, deviation, setpoint.

    This class represents the value ranges and statistical measures
    in the original (non-standardized) units of a variable.

    Attributes:
        _setpoint (Optional[float]): Specific value/point in original units.
        _min (Optional[float]): Minimum value in original units.
        _max (Optional[float]): Maximum value in original units.
        _mean (Optional[float]): Mean value in original units.
        _median (Optional[float]): Median value in original units.
        _dev (Optional[float]): Standard deviation in original units.
    """

    # Value ranges (original units)
    # :attr: _setpoint
    _setpoint: Optional[float] = None
    """Specific value in original units."""

    # :attr: _min
    _min: Optional[float] = None
    """Minimum value in original units."""

    # :attr: _max
    _max: Optional[float] = None
    """Maximum value in original units."""

    # :attr: _mean
    _mean: Optional[float] = None
    """Mean value in original units."""

    # :attr: _median
    _median: Optional[float] = None
    """Median value in original units."""

    # :attr: _dev
    _dev: Optional[float] = None
    """Standard deviation in original units."""

    @property
    def setpoint(self) -> Optional[float]:
        """*setpoint* Get specific value/point system for original units.

        Returns:
            Optional[str]: Specific value/point system for original units.
        """
        return self._setpoint

    @setpoint.setter
    @validate_type(int, float, allow_none=False, allow_nan=True)
    def setpoint(self, val: Optional[float]) -> None:
        """*setpoint* Sets specific value/point system for original units.

        Args:
            val (Optional[float]): Specific value/point system for original units.

        Raises:
            ValueError: If value not a valid number.
        """
        self._setpoint = val

    @property
    def min(self) -> Optional[float]:
        """*min* Get minimum range value.

        Returns:
            Optional[float]: Minimum range value.
        """
        return self._min

    @min.setter
    @validate_type(int, float, allow_none=False, allow_nan=True)
    @validate_range(max_attr="_max")
    def min(self, val: Optional[float]) -> None:
        """*min* Sets minimum range value.

        Args:
            val (Optional[float]): Minimum range value.

        Raises:
            ValueError: If value not a valid number.
            ValueError: If value is greater than max.
        """
        self._min = val

    @property
    def max(self) -> Optional[float]:
        """*max* Get the maximum range value.

        Returns:
            Optional[float]: Maximum range value.
        """
        return self._max

    @max.setter
    @validate_type(int, float, allow_none=False, allow_nan=True)
    @validate_range(min_attr="_min")
    def max(self, val: Optional[float]) -> None:
        """*max* Sets the maximum range value.

        Args:
            val (Optional[float]): Maximum range value.

        Raises:
            ValueError: If value is not a valid number.
            ValueError: If value is less than min.
        """
        self._max = val

    @property
    def mean(self) -> Optional[float]:
        """*mean* Get the Variable average value.

        Returns:
            Optional[float]: Variable average value.
        """
        return self._mean

    @mean.setter
    @validate_type(int, float, allow_none=False, allow_nan=True)
    @validate_range(min_attr="_min", max_attr="_max")
    def mean(self, val: Optional[float]) -> None:
        """*mean* Sets the Variable mean value.

        Args:
            val (Optional[float]): Variable mean value.

        Raises:
            ValueError: If value not a valid number.
            ValueError: If value is outside min-max range.
        """
        self._mean = val

    @property
    def median(self) -> Optional[float]:
        """*median* Get the median value.

        Returns:
            Optional[float]: Median value.
        """
        return self._median

    @median.setter
    @validate_type(int, float, allow_none=False, allow_nan=True)
    @validate_range(min_attr="_min", max_attr="_max")
    def median(self, val: Optional[float]) -> None:
        """*median* Sets the median value.

        Args:
            val (Optional[float]): Median value.

        Raises:
            ValueError: If value not a valid number.
            ValueError: If value is outside min-max range.
        """
        self._median = val

    @property
    def dev(self) -> Optional[float]:
        """*dev* Get the Variable standardized deviation.

        Returns:
            Optional[float]: Variable standardized deviation.
        """
        return self._dev

    @dev.setter
    @validate_type(int, float, allow_none=False, allow_nan=True)
    @validate_range(min_value=0, min_inclusive=True)
    def dev(self, val: Optional[float]) -> None:
        """*dev* Sets the Variable standardized deviation.

        Args:
            val (Optional[float]): Variable standardized deviation.
        Raises:
            ValueError: If value not a valid number.
            ValueError: If value is negative.
        """
        # if val is not None and not isinstance(val, (int, float)):
        #     raise ValueError("Standard deviation must be a number.")

        self._dev = val

    def clear(self) -> None:
        """*clear()* Reset bounds attributes to default values.

        Resets all value ranges in original units.
        """
        self._setpoint = None
        self._min = None
        self._max = None
        self._mean = None
        self._median = None
        self._dev = None


@dataclass
class StandardizedSpecs:
    """Standardized value specifications: ranges, statistics, and discretization.

    This class represents value ranges and statistical measures in standardized units,
    plus discretization properties for numerical analysis (step size, range array).

    Attributes:
        _std_setpoint (Optional[float]): Specific value/point in standardized units.
        _std_min (Optional[float]): Minimum value in standardized units.
        _std_max (Optional[float]): Maximum value in standardized units.
        _std_mean (Optional[float]): Mean value in standardized units.
        _std_median (Optional[float]): Median value in standardized units.
        _std_dev (Optional[float]): Standard deviation in standardized units.
    """

    # Value ranges (standardized units)
    # :attr: _std_setpoint
    _std_setpoint: Optional[float] = None
    """Specific value/point system for standardized units."""

    # :attr: _std_min
    _std_min: Optional[float] = None
    """Minimum value in standardized units."""

    # :attr: _std_max
    _std_max: Optional[float] = None
    """Maximum value in standardized units."""

    # :attr: _std_mean
    _std_mean: Optional[float] = None
    """Mean value in standardized units."""

    # :attr: _std_median
    _std_median: Optional[float] = None
    """Median value in standardized units."""

    # :attr: _std_dev
    _std_dev: Optional[float] = None
    """Standard deviation in standardized units."""

    @property
    def std_setpoint(self) -> Optional[float]:
        """*std_setpoint* Get specific value/point system for standardized units.

        Returns:
            Optional[str]: Specific value/point system for standardized units.
        """
        return self._std_setpoint

    @std_setpoint.setter
    @validate_type(int, float, allow_none=False)
    def std_setpoint(self, val: Optional[float]) -> None:
        """*std_setpoint* Sets specific value/point system for standardized units.

        Args:
            val (Optional[float]): Specific value/point system for standardized units.
        Raises:
            ValueError: If value not a valid number.
        """
        self._std_setpoint = val

    @property
    def std_min(self) -> Optional[float]:
        """*std_min* Get the standardized minimum range value.

        Returns:
            Optional[float]: standardized minimum range value.
        """
        return self._std_min

    @std_min.setter
    @validate_type(int, float, allow_none=False)
    @validate_range(max_attr="_std_max")
    def std_min(self, val: Optional[float]) -> None:
        """*std_min* Sets the standardized minimum range value.

        Args:
            val (Optional[float]): standardized minimum range value.

        Raises:
            ValueError: If value not a valid number.
            ValueError: If value is greater than std_max.
        """
        self._std_min = val

    @property
    def std_max(self) -> Optional[float]:
        """*std_max* Get the standardized maximum range value.

        Returns:
            Optional[float]: standardized maximum range value.
        """
        return self._std_max

    @std_max.setter
    @validate_type(int, float, allow_none=False)
    @validate_range(min_attr="_std_min")
    def std_max(self, val: Optional[float]) -> None:
        """*std_max* Sets the standardized maximum range value.

        Raises:
            ValueError: If value is not a valid number.
            ValueError: If value is less than std_min.
        """
        self._std_max = val

    @property
    def std_mean(self) -> Optional[float]:
        """*std_mean* Get standardized mean value.

        Returns:
            Optional[float]: standardized mean.
        """
        return self._std_mean

    @std_mean.setter
    @validate_type(int, float, allow_none=False)
    @validate_range(min_attr="_std_min", max_attr="_std_max")
    def std_mean(self, val: Optional[float]) -> None:
        """*std_mean* Sets the standardized mean value.

        Args:
            val (Optional[float]): standardized mean value.

        Raises:
            ValueError: If value is not a valid number.
            ValueError: If value is outside std_min-std_max range.
        """
        self._std_mean = val

    @property
    def std_median(self) -> Optional[float]:
        """*std_median* Get standardized median value.

        Returns:
            Optional[float]: Standardized median.
        """
        return self._std_median

    @std_median.setter
    @validate_type(int, float, allow_none=False)
    @validate_range(min_attr="_std_min", max_attr="_std_max")
    def std_median(self, val: Optional[float]) -> None:
        """*std_median* Sets the standardized median value.

        Args:
            val (Optional[float]): Standardized median value.

        Raises:
            ValueError: If value is not a valid number.
            ValueError: If value is outside std_min-std_max range.
        """
        self._std_median = val

    @property
    def std_dev(self) -> Optional[float]:
        """*std_dev* Get standardized standardized deviation.

        Returns:
            Optional[float]: Standardized standardized deviation.
        """
        return self._std_dev

    @std_dev.setter
    @validate_type(int, float, allow_none=False)
    @validate_range(min_value=0, min_inclusive=True)
    def std_dev(self, val: Optional[float]) -> None:
        """*std_dev* Sets the standardized standardized deviation.

        Args:
            val (Optional[float]): Standardized standardized deviation.

        Raises:
            ValueError: If value is not a valid number.
            ValueError: If value is negative.
        """
        self._std_dev = val

    def clear(self) -> None:
        """*clear()* Reset standardized attributes to default values.

        Resets all value ranges in standardized units.
        """
        self._std_setpoint = None
        self._std_min = None
        self._std_max = None
        self._std_mean = None
        self._std_median = None
        self._std_dev = None


@dataclass
class NumericalSpecs(BoundsSpecs, StandardizedSpecs):
    """Numerical perspective: computational value ranges. Answers the question: "What VALUES can this variable take?"

    This perspective combines:
        - BoundsSpecs: Value ranges in original units (min, max, mean, deviation, setpoint)
        - StandardizedSpecs: Value ranges in standardized units
        - Discretization properties (step, range array)

    This perspective focuses on:
        - Concrete bounds (minimum, maximum)
        - Central tendency (mean value)
        - Variation (standard deviation)
        - Discretization for simulations (step size, range arrays)
        - Unit conversions (original <-> standardized)
        - Variable dependencies (calculated variables)

    Attributes:
        # From BoundsSpecs (original units):
            _setpoint (Optional[float]): Specific value/point in original units.
            _min (Optional[float]): Minimum value in original units.
            _max (Optional[float]): Maximum value in original units.
            _mean (Optional[float]): Mean value in original units.
            _median (Optional[float]): Median value in original units.
            _dev (Optional[float]): Standard deviation in original units.
        # From StandardizedSpecs (standardized units):
            _std_setpoint (Optional[float]): Specific value/point in standardized units.
            _std_min (Optional[float]): Minimum value in standardized units.
            _std_max (Optional[float]): Maximum value in standardized units.
            _std_mean (Optional[float]): Mean value in standardized units.
            _std_median (Optional[float]): Median value in standardized units.
            _std_dev (Optional[float]): Standard deviation in standardized units.
        # Discretization properties:
            _step (Optional[float]): Step size for simulations.
            _data (NDArray[np.float64]): Range for numerical analysis in standardized units.
    """

    # :attr: _step
    _step: Optional[float] = 1e-3
    """Step size for simulations."""

    # :attr: _data
    _data: NDArray[np.float64] = field(
        default_factory=lambda: np.array([], dtype=np.float64)
    )
    """Data range array for analysis."""

    @property
    def step(self) -> Optional[float]:
        """*step* Get standardized step size.

        Returns:
            Optional[float]: Step size (always standardized).
        """
        return self._step

    @step.setter
    @validate_type(int, float, allow_none=False)
    @validate_range(min_value=0,
                    min_inclusive=False,
                    min_attr="_std_min",
                    max_attr="_std_max")
    def step(self, val: Optional[float]) -> None:
        """*step* Set standardized step size.

        Args:
            val (Optional[float]): Step size (always standardized).
        """
        self._step = val

    @property
    def data(self) -> NDArray[np.float64]:
        """*data* Get standardized data array.

        Returns:
            NDArray[np.float64]: Data array for range (always standardized).
        """
        return self._data

    @data.setter
    @validate_type(list, np.ndarray, allow_none=False)
    def data(self, val: NDArray[np.float64]) -> None:
        """*data* Set standardized data array.

        Args:
            val (NDArray[np.float64]): Data array for range (always standardized).

        Raises:
            ValueError: If value is not a numpy array or list.
        """
        # always store as numpy array
        if isinstance(val, list):
            val = np.array(val, dtype=np.float64)
        self._data = val

    def generate_data(self) -> None:
        """*generate_data()* Generate standardized data array from min, max, using step value.

        Raises:
            ValueError: If needed values are missing.
        """
        # Type narrow using local variables
        std_min = self._std_min
        std_max = self._std_max
        step = self._step

        if std_min is not None and std_max is not None and step is not None:
            self._data = np.arange(std_min, std_max, step)
        else:
            _msg = "Cannot generate data array. Needed values are missing: "
            _msg += f"std_min={std_min}, std_max={std_max}, step={step}."
            raise ValueError(_msg)

    def clear(self) -> None:
        """*clear()* Reset numerical attributes to default values.

        Resets all value ranges, discretization, and step size by calling parent clear() methods.
        """
        BoundsSpecs.clear(self)
        StandardizedSpecs.clear(self)
        self._step = None
        self._data = np.array([])
