import pytest
from lumpy_log.list1 import list1


class TestList1Basic:
    """Test basic creation and initialization of list1."""

    def test_creation_empty(self):
        """Test creating an empty list1."""
        l = list1()
        assert len(l) == 0

    def test_creation_with_items(self):
        """Test creating a list1 with initial items."""
        l = list1([10, 20, 30])
        assert len(l) == 3
        assert l.data == [10, 20, 30]

    def test_creation_from_list(self):
        """Test creating a list1 from a regular list."""
        original = [1, 2, 3, 4, 5]
        l = list1(original)
        assert len(l) == 5


class TestList1GetItem:
    """Test __getitem__ method with 1-indexed access."""

    def test_getitem_first_element(self):
        """Test accessing first element with index 1."""
        l = list1([10, 20, 30])
        assert l[1] == 10

    def test_getitem_middle_element(self):
        """Test accessing middle element with 1-indexed position."""
        l = list1([10, 20, 30, 40, 50])
        assert l[3] == 30

    def test_getitem_last_element(self):
        """Test accessing last element with 1-indexed position."""
        l = list1([10, 20, 30])
        assert l[3] == 30

    def test_getitem_negative_index(self):
        """Test accessing with negative index (last element)."""
        l = list1([10, 20, 30])
        assert l[-1] == 30

    def test_getitem_out_of_range(self):
        """Test that accessing index out of range raises IndexError."""
        l = list1([10, 20, 30])
        with pytest.raises(IndexError):
            _ = l[4]

    def test_getitem_zero_index(self):
        """Test that index 0 raises IndexError (1-indexed)."""
        l = list1([10, 20, 30])
        with pytest.raises(IndexError):
            _ = l[0]

    def test_getitem_slice(self):
        """Test slice access returns list1 with sliced items."""
        l = list1([10, 20, 30, 40, 50])
        sliced = l[1:3]
        assert isinstance(sliced, list1)
        assert sliced.data == [10, 20]


class TestList1SetItem:
    """Test __setitem__ method with 1-indexed access."""

    def test_setitem_first_element(self):
        """Test setting first element with index 1."""
        l = list1([10, 20, 30])
        l[1] = 100
        assert l.data[0] == 100

    def test_setitem_middle_element(self):
        """Test setting middle element with 1-indexed position."""
        l = list1([10, 20, 30, 40])
        l[2] = 200
        assert l.data[1] == 200

    def test_setitem_last_element(self):
        """Test setting last element with 1-indexed position."""
        l = list1([10, 20, 30])
        l[3] = 300
        assert l.data[2] == 300

    def test_setitem_negative_index(self):
        """Test setting with negative index."""
        l = list1([10, 20, 30])
        l[-1] = 300
        assert l.data[-1] == 300

    def test_setitem_slice(self):
        """Test slice assignment."""
        l = list1([10, 20, 30, 40, 50])
        l[1:3] = [100, 200]
        assert l.data == [100, 200, 30, 40, 50]


class TestList1DelItem:
    """Test __delitem__ method with 1-indexed access."""

    def test_delitem_first_element(self):
        """Test deleting first element with index 1."""
        l = list1([10, 20, 30])
        del l[1]
        assert l.data == [20, 30]

    def test_delitem_middle_element(self):
        """Test deleting middle element with 1-indexed position."""
        l = list1([10, 20, 30, 40])
        del l[2]
        assert l.data == [10, 30, 40]

    def test_delitem_last_element(self):
        """Test deleting last element with 1-indexed position."""
        l = list1([10, 20, 30])
        del l[3]
        assert l.data == [10, 20]

    def test_delitem_negative_index(self):
        """Test deleting with negative index."""
        l = list1([10, 20, 30])
        del l[-1]
        assert l.data == [10, 20]

    def test_delitem_slice(self):
        """Test deleting with slice."""
        l = list1([10, 20, 30, 40, 50])
        del l[1:3]
        assert l.data == [30, 40, 50]


class TestList1Insert:
    """Test insert method with 1-indexed position."""

    def test_insert_at_beginning(self):
        """Test inserting at position 1 (beginning)."""
        l = list1([20, 30])
        l.insert(1, 10)
        assert l.data == [10, 20, 30]

    def test_insert_in_middle(self):
        """Test inserting in the middle with 1-indexed position."""
        l = list1([10, 30, 40])
        l.insert(2, 20)
        assert l.data == [10, 20, 30, 40]

    def test_insert_at_end(self):
        """Test inserting at the end with 1-indexed position."""
        l = list1([10, 20])
        l.insert(3, 30)
        assert l.data == [10, 20, 30]

    def test_insert_negative_index(self):
        """Test inserting with negative index."""
        l = list1([10, 20, 30])
        l.insert(-1, 25)
        assert 25 in l.data


class TestList1Pop:
    """Test pop method with 1-indexed access."""

    def test_pop_default(self):
        """Test pop with default argument removes last element."""
        l = list1([10, 20, 30])
        result = l.pop()
        assert result == 30
        assert l.data == [10, 20]

    def test_pop_first_element(self):
        """Test popping first element with index 1."""
        l = list1([10, 20, 30])
        result = l.pop(1)
        assert result == 10
        assert l.data == [20, 30]

    def test_pop_middle_element(self):
        """Test popping middle element with 1-indexed position."""
        l = list1([10, 20, 30, 40])
        result = l.pop(2)
        assert result == 20
        assert l.data == [10, 30, 40]

    def test_pop_last_element_explicit(self):
        """Test popping last element with explicit 1-indexed position."""
        l = list1([10, 20, 30])
        result = l.pop(3)
        assert result == 30
        assert l.data == [10, 20]

    def test_pop_negative_index(self):
        """Test popping with negative index."""
        l = list1([10, 20, 30])
        result = l.pop(-1)
        assert result == 30
        assert l.data == [10, 20]


class TestList1Index:
    """Test index method with 1-indexed return value."""

    def test_index_first_element(self):
        """Test finding index of first element returns 1."""
        l = list1([10, 20, 30])
        assert l.index(10) == 1

    def test_index_middle_element(self):
        """Test finding index of middle element returns 1-indexed position."""
        l = list1([10, 20, 30, 40])
        assert l.index(30) == 3

    def test_index_last_element(self):
        """Test finding index of last element returns 1-indexed position."""
        l = list1([10, 20, 30])
        assert l.index(30) == 3

    def test_index_not_found(self):
        """Test that index raises ValueError when item not found."""
        l = list1([10, 20, 30])
        with pytest.raises(ValueError):
            l.index(40)

    def test_index_with_start_argument(self):
        """Test index method with start position."""
        l = list1([10, 20, 10, 40])
        # Finding 10 starting from position 2 (0-indexed internally becomes 1-indexed)
        result = l.index(10, 2)
        assert result >= 1


class TestList1InheritedMethods:
    """Test that inherited methods from UserList still work correctly."""

    def test_append(self):
        """Test append adds to the end."""
        l = list1([10, 20])
        l.append(30)
        assert l[3] == 30

    def test_extend(self):
        """Test extend adds multiple items."""
        l = list1([10, 20])
        l.extend([30, 40])
        assert len(l) == 4
        assert l[3] == 30

    def test_remove(self):
        """Test remove deletes first occurrence."""
        l = list1([10, 20, 30, 20])
        l.remove(20)
        assert l.data == [10, 30, 20]

    def test_clear(self):
        """Test clear removes all elements."""
        l = list1([10, 20, 30])
        l.clear()
        assert len(l) == 0

    def test_count(self):
        """Test count returns correct count."""
        l = list1([10, 20, 10, 30, 10])
        assert l.count(10) == 3

    def test_len(self):
        """Test len returns correct length."""
        l = list1([10, 20, 30, 40])
        assert len(l) == 4

    def test_iter(self):
        """Test iteration works correctly."""
        l = list1([10, 20, 30])
        items = list(l)
        assert items == [10, 20, 30]


class TestList1EdgeCases:
    """Test edge cases and special scenarios."""

    def test_single_element_list(self):
        """Test operations on single element list."""
        l = list1([42])
        assert l[1] == 42
        l[1] = 100
        assert l[1] == 100

    def test_large_list(self):
        """Test with a larger list."""
        l = list1(range(1, 101))
        assert l[1] == 1
        assert l[50] == 50
        assert l[100] == 100

    def test_mixed_types(self):
        """Test with mixed data types."""
        l = list1([1, "two", 3.0, None, []])
        assert l[1] == 1
        assert l[2] == "two"
        assert l[3] == 3.0
        assert l[4] is None
        assert l[5] == []

    def test_nested_list1(self):
        """Test with nested list1 objects."""
        inner = list1([1, 2, 3])
        outer = list1([inner, "other"])
        assert outer[1] is inner
        assert outer[1][1] == 1

    def test_copy_operation(self):
        """Test that copy returns a list1."""
        l = list1([10, 20, 30])
        l_copy = l.copy()
        assert isinstance(l_copy, list1)
        assert l_copy == [10, 20, 30]

    def test_repr(self):
        """Test string representation."""
        l = list1([10, 20, 30])
        repr_str = repr(l)
        assert "10" in repr_str
        assert "20" in repr_str
        assert "30" in repr_str
