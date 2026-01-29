# debug-tools

一个简单的 Python 调试工具包。

## 功能特性

- ✅ `hello(name)` - 返回问候语
- ✅ `add(a, b)` - 两数相加
- ✅ `print_dict(data, level)` - 格式化打印字典，支持日志分级

## 安装

```bash
pip install debug-tools
```

## 使用示例

```python
from debug_tools import hello, add, print_dict

# 基本功能
print(hello("World"))  # Hello, World!
print(add(1, 2))       # 3

# 打印字典
data = {
    "name": "Alice",
    "age": 30,
    "hobbies": ["reading", "coding"]
}
print_dict(data)
```

输出：
```json
{
  "name": "Alice",
  "age": 30,
  "hobbies": [
    "reading",
    "coding"
  ]
}
```

### 日志分级

`print_dict` 支持不同的日志级别：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from debug_tools import print_dict

print_dict({"info": "data"}, level="info")
print_dict({"warning": "msg"}, level="warning")
print_dict({"error": "msg"}, level="error")
```

## 本地开发

```bash
# 克隆项目
git clone <repository>
cd debug_tools

# 开发模式安装
pip install -e .

# 运行示例
python examples/test.py

# 运行测试
pytest tests/
```

## 项目结构

```
debug_tools/
├── src/
│   └── debug_tools/        # 源代码
│       ├── __init__.py
│       ├── main.py
│       └── print.py
├── tests/                  # 单元测试
├── examples/               # 使用示例
├── docs/                   # 文档
├── scripts/                # 发布脚本
└── pyproject.toml          # 项目配置
```

## 文档

- [发布指南](docs/01_release.md)
- [本地开发](docs/02_local_development.md)
- [包名与模块名](docs/03_package_vs_module_name.md)

## 要求

- Python >= 3.9

## 许可证

MIT License
