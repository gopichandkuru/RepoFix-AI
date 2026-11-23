from api.pager import paginate


def test_page_two_returns_expected_slice():
    items = list(range(1, 11))
    assert paginate(items, page=2, page_size=3) == [4, 5, 6]
