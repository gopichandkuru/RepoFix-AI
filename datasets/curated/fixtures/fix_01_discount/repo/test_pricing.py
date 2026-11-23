from shop.pricing import apply_discount


def test_apply_twenty_percent_discount():
    assert apply_discount(200.0, 20.0) == 160.0
