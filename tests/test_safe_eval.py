from chatbot import safe_eval_math, fallback_response


def test_safe_eval_simple():
    assert safe_eval_math('2+3*4') == 14


def test_safe_eval_pow_and_mod():
    assert safe_eval_math('2**3 + 5%3') == 8 + 2


def test_fallback_contains_input():
    out = fallback_response('?´ê±´ ?ŒìŠ¤?¸ì…?ˆë‹¤')
    assert '?ŒìŠ¤?? in out or '?…ë ¥?˜ì‹  ?´ìš©' in out
