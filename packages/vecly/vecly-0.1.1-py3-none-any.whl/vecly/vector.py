from __future__ import annotations
import numpy as np
class Vector:
    """
    A lightweight vector wrapper around NumPy arrays, providing
    elementwise arithmetic operations, statistics, and operator overloads.

    Parameters
    ----------
    data : array_like
        Input data to initialize the vector. Can be a list, tuple, or NumPy array.

    Attributes
    ----------
    data : np.ndarray
        The underlying NumPy array storing the vector elements.

    Examples
    --------
    >>> v = Vector([1, 2, 3])
    >>> v + 2
    Vector([3 4 5])
    >>> v * v
    Vector([1 4 9])
    >>> v.mean()
    2.0
    """


    def __init__(self, data) -> None:
        """Initialize the vector with the given data."""
        self.data = np.array(data)

    def __array__(self, dtype=None):
        """
        NumPy interop hook.

        This allows `np.asarray(Vector(...))`, NumPy ufuncs (e.g. `np.log(v)`),
        and functions like `np.column_stack([v1, v2])` to work naturally.
        """
        if dtype is None:
            return self.data
        return self.data.astype(dtype, copy=False)

    def to_numpy(self) -> np.ndarray:
        """Return the underlying NumPy array."""
        return self.data

    def log(self) -> "Vector":
        """Elementwise natural log."""
        with np.errstate(divide="ignore", invalid="ignore"):
            return Vector(np.log(self.data))

    def shift(self, n: int = 1, *, fill_value=np.nan) -> "Vector":
        """
        Shift values downward by n, filling the first n with fill_value.

        Notes
        -----
        - Only supports non-negative n.
        - If fill_value is NaN, the result will be float dtype.
        """
        if n < 0:
            raise ValueError("shift() only supports non-negative n.")
        if n == 0:
            return Vector(self.data.copy())
        fill_is_nan = isinstance(fill_value, float) and np.isnan(fill_value)
        if n >= len(self.data):
            return Vector(np.full(len(self.data), fill_value, dtype=float if fill_is_nan else None))
        tail = self.data[:-n]
        if fill_is_nan:
            tail = tail.astype(float, copy=False)
        head = np.full(n, fill_value, dtype=float if fill_is_nan else None)
        return Vector(np.concatenate([head, tail]))

    # ---------------------------------------------------------------------
    # Basic arithmetic methods
    # ---------------------------------------------------------------------
    def add(self, y) -> np.ndarray:
        """
        Add a scalar or array-like object to the vector.

        Parameters
        ----------
        y : array_like or scalar
            The value(s) to add.

        Returns
        -------
        np.ndarray
            Elementwise sum.
        """
        return self.data + y

    def sub(self, y) -> np.ndarray:
        """Subtract a scalar or array-like object from the vector."""
        return self.data - y

    def mul(self, y) -> np.ndarray:
        """Multiply the vector elementwise by a scalar or array-like object."""
        return self.data * y

    def div(self, y) -> np.ndarray:
        """Divide the vector elementwise by a scalar or array-like object."""
        return self.data / y

    # ---------------------------------------------------------------------
    # Statistical methods
    # ---------------------------------------------------------------------
    def sum(self):
        """
        Return the sum of all elements in the vector.

        Returns
        -------
        float
            The sum of all vector elements.
        """
        return np.sum(self.data)

    def mean(self):
        """
        Return the mean (average) of the vector elements.

        Returns
        -------
        float
            The mean of the vector elements.
        """
        return np.mean(self.data)

    def var(self) -> np.ndarray:
        """
        Return the variance of the vector elements.

        Returns
        -------
        float
            The variance of the vector elements.
        """
        mu = self.mean()
        return np.mean((self.data - mu) ** 2)

    def std(self):
        """
        Return the standard deviation of the vector elements.

        Returns
        -------
        float
            The standard deviation of the vector elements.
        """
        return np.sqrt(self.var())

    def len(self):
        """
        Return the number of elements in the vector.

        Returns
        -------
        int
            Number of elements.
        """
        return len(self.data)

    # ---------------------------------------------------------------------
    # Operator overloads
    # ---------------------------------------------------------------------
    def __add__(self, other):
        """Implements self + other (elementwise addition)."""
        return Vector(self.data + self._to_array(other))

    def __sub__(self, other):
        """Implements self - other (elementwise subtraction)."""
        return Vector(self.data - self._to_array(other))

    def __mul__(self, other):
        """Implements self * other (elementwise multiplication)."""
        return Vector(self.data * self._to_array(other))

    def __truediv__(self, other):
        """Implements self / other (elementwise division)."""
        return Vector(self.data / self._to_array(other))

    def __radd__(self, other):
        """Implements other + self."""
        return self.__add__(other)

    def __rsub__(self, other):
        """Implements other - self."""
        return Vector(self._to_array(other) - self.data)

    def __rmul__(self, other):
        """Implements other * self."""
        return self.__mul__(other)

    def __rtruediv__(self, other):
        """Implements other / self."""
        return Vector(self._to_array(other) / self.data)

    def __pow__(self, power):
        """
        Implements self ** power (elementwise exponentiation).

        Parameters
        ----------
        power : float or int
            Exponent to which each element is raised.

        Returns
        -------
        Vector
            New vector with each element raised to the given power.
        """
        return Vector(self.data ** power)

    # ---------------------------------------------------------------------
    # Accessors
    # ---------------------------------------------------------------------
    def __getitem__(self, index):
        """
        Allow element or slice access via v[index].

        Parameters
        ----------
        index : int or slice
            Index or slice object.

        Returns
        -------
        scalar or Vector
            A single element (if int index) or a new Vector (if slice).
        """
        result = self.data[index]
        if isinstance(result, np.ndarray):
            return Vector(result)
        return result

    def __len__(self):
        """Return the number of elements in the vector (for len(v))."""
        return len(self.data)

    # ---------------------------------------------------------------------
    # Internal helpers and representation
    # ---------------------------------------------------------------------
    def _to_array(self, x):
        """
        Convert input to a NumPy array for arithmetic operations.

        Parameters
        ----------
        x : scalar, array_like, or Vector
            Input to convert.

        Returns
        -------
        np.ndarray
            NumPy array representation.
        """
        if isinstance(x, Vector):
            return x.data
        return np.array(x)

    def __repr__(self):
        """Return a string representation of the Vector."""
        return f"Vector({self.data})"