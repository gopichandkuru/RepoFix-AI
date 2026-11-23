def paginate(items, page: int, page_size: int):
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be >= 1")
    start = (page - 1) * page_size
    # Bug: slices only one item instead of full page_size window
    return items[start : start + 1]
