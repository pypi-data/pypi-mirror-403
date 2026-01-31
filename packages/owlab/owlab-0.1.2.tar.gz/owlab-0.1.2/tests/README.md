# 测试说明

## 运行测试

### 使用 pytest

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_config.py

# 运行特定测试类
pytest tests/test_config.py::TestConfig

# 运行特定测试方法
pytest tests/test_config.py::TestConfig::test_default_config

# 显示详细输出
pytest -v

# 显示覆盖率报告
pytest --cov=owlab --cov-report=html
```

### 使用 Makefile

```bash
# 运行测试
make test

# 运行代码检查
make lint

# 自动修复代码格式
make lint-fix
```

## 测试覆盖的模块

### 核心模块
- `test_config.py`: 配置管理测试
- `test_logger.py`: 日志管理测试

### 工具模块
- `test_schema_validator.py`: Schema 验证测试
- `test_formatter.py`: 数据格式化测试
- `test_retry.py`: 重试机制测试

### 存储模块
- `test_local_storage.py`: 本地存储测试

## 测试结构

所有测试都遵循以下结构：

1. **测试类**: 每个模块对应一个测试类，命名格式为 `Test<ModuleName>`
2. **测试方法**: 每个测试方法以 `test_` 开头
3. **Fixtures**: 公共 fixtures 定义在 `conftest.py` 中

## 编写新测试

1. 在 `tests/` 目录下创建新的测试文件，命名格式为 `test_<module_name>.py`
2. 导入必要的模块和 pytest
3. 创建测试类和方法
4. 使用 fixtures 来设置测试数据

示例：

```python
"""Tests for my_module."""

import pytest
from owlab.my_module import MyClass

class TestMyClass:
    """Tests for MyClass."""
    
    def test_my_method(self):
        """Test my_method."""
        obj = MyClass()
        result = obj.my_method()
        assert result == expected_value
```
