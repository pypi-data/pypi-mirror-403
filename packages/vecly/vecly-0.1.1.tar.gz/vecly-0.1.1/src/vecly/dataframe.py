from __future__ import annotations

import numpy as np

from .column import Column


class DataFrame:
    """
    DataFrame: a simple tabular data structure.

    Maintains a list of Column objects in self.cols. Supports basic operations
    like length, adding columns, appending columns, and printing a formatted preview.
    """

    def __init__(self, cols):
        """
        Initialize the DataFrame.

        Parameters
        ----------
        cols : list
            A list of Column objects to initialize the DataFrame.
        """
        self.cols = cols

    def __len__(self):
        """
        Return the number of rows in the DataFrame.

        Returns
        -------
        int
            Number of rows. Assumes all columns have the same length.
        """
        return self.cols[0].len()

    def append(self, col):
        """
        Append a Column object to the DataFrame.

        Parameters
        ----------
        col : Column
            The Column object to append.
        """
        for i, c in enumerate(self.cols):
          if col.name == c.name:
            self.cols[i] = col
            return
        self.cols.append(col)

    def add_col(self, name, col):
        """
        Create a Column from name and data, and append it to the DataFrame.

        Parameters
        ----------
        name : str
            Name of the new column.
        col : list or np.ndarray
            Data for the new column.
        """
        self.cols.append(Column(name, col))

    def __getitem__(self, keys):
            """
            Select columns by name.

            Parameters
            ----------
            keys : str or list of str
                Column name(s) to select.

            Returns
            -------
            np.ndarray
                2D array with shape (n_rows, n_selected_columns)
            """
            if isinstance(keys, str):
                # Single column -> return 1D array
                for col in self.cols:
                    if col.name == keys:
                        return col.vec.data
                raise KeyError(f"Column '{keys}' not found.")
            elif isinstance(keys, list):
                # Multiple columns -> return 2D row-major array
                selected_cols = []
                for key in keys:
                    for col in self.cols:
                        if col.name == key:
                            selected_cols.append(col.vec)
                            break
                    else:
                        raise KeyError(f"Column '{key}' not found.")
                # Stack columns and transpose so rows are observations
                return np.column_stack(selected_cols)
            else:
                raise TypeError("Key must be a string or list of strings.")

    def __repr__(self):
        """
        Return a string representation of the DataFrame.

        Displays the first 10 rows of the DataFrame as a formatted table
        with column headers. If the DataFrame has more than 10 rows,
        adds "..." at the end to indicate more data.

        Returns
        -------
        str
            Formatted string table of the DataFrame preview.
        """
        col_names = [col.name for col in self.cols]

        # Determine width for each column (max of header or any value)
        col_widths = []
        preview_rows = min(len(self), 10)
        for col in self.cols:
            data_preview = [str(x) for x in col.vec[:preview_rows]]
            max_data_width = max(len(x) for x in data_preview) if data_preview else 0
            width = max(len(col.name), max_data_width)
            col_widths.append(width)

        # Format header row
        header = " | ".join(
            name.ljust(width) for name, width in zip(col_names, col_widths)
        )

        # Separator (column-aligned)
        separator = "-+-".join("-" * width for width in col_widths)

        # Format data rows
        rows = []
        for i in range(preview_rows):
            row = " | ".join(
                str(col.vec[i]).ljust(width) for col, width in zip(self.cols, col_widths)
            )
            rows.append(row)

        table = "\n".join([header, separator] + rows)
        if len(self) > 10:
            table += "\n..."
        return table