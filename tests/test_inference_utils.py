from model.inference import extract_clean_diff


def test_extract_clean_diff_strips_fences_and_prose():
    raw = (
        'Here is the patch:\n'
        '```diff\n'
        '--- a/shop/pricing.py\n'
        '+++ b/shop/pricing.py\n'
        '@@ -1,2 +1,2 @@\n'
        '-return price - percent\n'
        '+return price * (1 - percent / 100)\n'
        '```\n'
        'Hope this helps!'
    )
    cleaned = extract_clean_diff(raw)
    assert cleaned.startswith('--- a/shop/pricing.py')
    assert 'Hope this helps!' not in cleaned
