from __future__ import annotations
import numpy as np
from .vector import Vector
class Column:
    """
    Column represents a single column of data, typically used in a tabular dataset.

    Each Column has a name and a vector of data (wrapped in a Vector object).
    Supports basic operations like length, sum, shift, division, and logarithm,
    and allows element-wise arithmetic with other Columns or scalars.
    """

    vec: 'Vector'

    def __init__(self, name, x):
        """
        Initialize a Column.

        Parameters
        ----------
        name : str
            The name of the column.
        x : list, np.ndarray, or Vector
            The data for the column.
        """
        self.vec = x if isinstance(x, Vector) else Vector(x)
        self.name = name

    def len(self):
        """
        Return the number of elements in the column.

        Returns
        -------
        int
            Length of the column vector.
        """
        return len(self.vec)

    def sum(self):
        """
        Compute the sum of all elements in the column.

        Returns
        -------
        float
            Sum of the column's elements.
        """
        return np.sum(self.vec.data)

    def shift(self, n=1):
        """
        Shift the column data downward by n positions, filling new entries with NaN.

        Parameters
        ----------
        n : int, optional
            Number of positions to shift (default is 1).

        Returns
        -------
        np.ndarray
            Shifted data as a NumPy array.
        """
        return self.vec.shift(n)

    def div(self, y) -> np.ndarray:
        """
        Divide the column element-wise by another Column or array-like object.

        Parameters
        ----------
        y : Column, Vector, or array-like
            The divisor.

        Returns
        -------
        np.ndarray
            Resulting element-wise division as a NumPy array.
        """
        if isinstance(y, Column):
            y = y.vec
        return self.vec / y

    def log(self):
        """
        Compute the natural logarithm of each element in the column.

        Returns
        -------
        np.ndarray
            Element-wise natural logarithm of the column.
        """
        return self.vec.log()

    def __truediv__(self, other) -> np.ndarray:
        """
        Enable the use of '/' operator for element-wise division.

        Parameters
        ----------
        other : Column, Vector, or array-like
            The divisor.

        Returns
        -------
        np.ndarray
            Element-wise division result.
        """
        return self.div(other)

    def to_numpy(self) -> np.ndarray:
        """Return the underlying NumPy array for this column."""
        return self.vec.data

    def __repr__(self):
        """
        Return a string representation of the column.

        Shows the first 10 elements of data and the column's name and length.

        Returns
        -------
        str
            Formatted string representation of the Column.
        """
        preview = ", ".join(map(str, self.vec[:10]))  # show first 10 items
        if len(self.vec) > 10:
            preview += ", ..."
        return f"Column(name='{self.name}', data=[{preview}], len={len(self.vec)})"
