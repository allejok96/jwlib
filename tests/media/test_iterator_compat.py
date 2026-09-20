import pytest

from jwlib.media._iterator_compat import IteratorCompatibleList


def test_behaves_like_a_list():
    l = IteratorCompatibleList([1, 2, 3])
    assert list(l) == [1, 2, 3]
    assert l[0] == 1
    assert len(l) == 3


def test_next_is_deprecated():
    l = IteratorCompatibleList([1, 2, 3])
    with pytest.deprecated_call():
        assert next(l) == 1


def test_next_continues_across_calls():
    l = IteratorCompatibleList([1, 2, 3])
    with pytest.deprecated_call():
        assert next(l) == 1
    with pytest.deprecated_call():
        assert next(l) == 2
    with pytest.deprecated_call():
        assert next(l) == 3
    with pytest.deprecated_call():
        with pytest.raises(StopIteration):
            next(l)


def test_next_on_empty_list_raises_stop_iteration():
    l = IteratorCompatibleList([])
    with pytest.deprecated_call():
        with pytest.raises(StopIteration):
            next(l)
