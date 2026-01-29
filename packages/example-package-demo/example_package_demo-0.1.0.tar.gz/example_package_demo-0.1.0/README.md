# Example Package

一个简单的 Python 包示例，用于演示如何发布到 PyPI。

## 安装

```bash
pip install example-package-demo
```

## 使用方法

```python
from example_package import hello, add

# 使用 hello 函数
print(hello("World"))
# 输出: Hello, World!

# 使用 add 函数
result = add(1, 2)
print(result)
# 输出: 3
```

## 运行示例

```bash
python -m example_package.main
```

## 运行测试

```bash
pytest tests/
```

## 许可证

MIT License
