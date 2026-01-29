"""示例测试"""

from example_package import hello, add

def test_hello() -> None:
    """测试 hello 函数"""
    assert hello("World") == "Hello, World!"
    assert hello("Python") == "Hello, Python!"

def test_add() -> None:
    """测试 add 函数"""
    assert add(1, 2) == 3
    assert add(0, 0) == 0
    assert add(-1, 1) == 0
