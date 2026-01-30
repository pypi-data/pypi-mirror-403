from collections import UserList


class list1(UserList):
    """A 1-indexed list class that inherits from UserList.
    
    This class overrides all methods that involve indices to convert between
    1-indexed (user-facing) and 0-indexed (internal) representations.
    - Methods that accept an index parameter subtract 1 before processing
    - Methods that return an index add 1 before returning
    """

    def _convert_index_input(self, index):
        """Convert 1-indexed input to 0-indexed for internal use."""
        if index is None:
            return None
        if index < 0:
            return index
        if index == 0:
            raise IndexError("Indexing starts at 1")
        return index - 1

    def _convert_index_output(self, index):
        """Convert 0-indexed internal index to 1-indexed for output."""
        # No conversion for negative indices as they refer to positions from the end
        return index + 1

    def __getitem__(self, key):
        """Get item by 1-indexed position."""
        if isinstance(key, slice):
            # Convert slice bounds from 1-indexed to 0-indexed
            start = self._convert_index_input(key.start)
            stop = self._convert_index_input(key.stop)
            step = key.step
            converted_slice = slice(start, stop, step)
            return self.__class__(super().__getitem__(converted_slice))
        else:
            # Convert 1-indexed to 0-indexed
            return super().__getitem__(self._convert_index_input(key))

    def __setitem__(self, key, value):
        """Set item by 1-indexed position."""
        if isinstance(key, slice):
            # Convert slice bounds from 1-indexed to 0-indexed
            start = self._convert_index_input(key.start)
            stop = self._convert_index_input(key.stop)
            step = key.step
            converted_slice = slice(start, stop, step)
            super().__setitem__(converted_slice, value)
        else:
            # Convert 1-indexed to 0-indexed
            super().__setitem__(self._convert_index_input(key), value)

    def __delitem__(self, key):
        """Delete item by 1-indexed position."""
        if isinstance(key, slice):
            # Convert slice bounds from 1-indexed to 0-indexed
            start = self._convert_index_input(key.start)
            stop = self._convert_index_input(key.stop)
            step = key.step
            converted_slice = slice(start, stop, step)
            super().__delitem__(converted_slice)
        else:
            # Convert 1-indexed to 0-indexed
            super().__delitem__(self._convert_index_input(key))

    def insert(self, index, item):
        """Insert item at 1-indexed position."""
        super().insert(self._convert_index_input(index), item)

    def pop(self, index=-1):
        """Remove and return item at 1-indexed position.
        
        If index is -1 (default), removes the last item.
        Otherwise, index should be 1-indexed.
        """
        if index == -1:
            return super().pop(index)
        else:
            return super().pop(self._convert_index_input(index))

    def index(self, item, *args):
        """Return 1-indexed position of item.
        
        Additional arguments are forwarded to the parent class.
        """
        # Get 0-indexed result from parent
        result = super().index(item, *args)
        # Convert to 1-indexed
        return self._convert_index_output(result)

    def __iter__(self):
        """Iterate over items using the underlying data directly.
        
        This bypasses the __getitem__ method to avoid 1-indexed conversion
        which would break iteration (since it starts at index 0).
        """
        return iter(self.data)
