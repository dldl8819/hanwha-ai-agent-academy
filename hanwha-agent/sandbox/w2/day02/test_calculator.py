from calculator import add, substract

def test_add():
    result = add(10, 20)
    # 검사 명렁어
    assert result == 30 

def test_substract():
    result = substract(10, 3)
    assert result == 5