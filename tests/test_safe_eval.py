from chatbot import safe_eval_math, fallback_response


def test_safe_eval_simple():
    assert safe_eval_math('2+3*4') == 14


def test_safe_eval_pow_and_mod():
    assert safe_eval_math('2**3 + 5%3') == 8 + 2


def test_fallback_contains_input():
    out = fallback_response('이건 테스트입니다')
    assert '테스트' in out or '입력하신 내용' in out
