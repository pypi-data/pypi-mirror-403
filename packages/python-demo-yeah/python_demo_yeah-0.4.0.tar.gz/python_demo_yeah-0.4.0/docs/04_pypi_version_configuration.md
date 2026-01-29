# PyPI 版本号配置说明

## 📦 版本号来源

PyPI 上的版本号 `pip install debug-helpers==0.4.0` 主要来自 **`pyproject.toml`** 文件。

---

## 🔍 版本号配置位置

### 1. 主要配置：`pyproject.toml` ⭐

**位置**: `pyproject.toml`

```toml
[project]
name = "debug-helpers"
version = "0.4.0"  # ← 这是 PyPI 版本号的来源！
```

**作用**:
- ✅ **这是 PyPI 上显示的版本号**
- ✅ 构建分发包时，`build` 工具会读取这个版本号
- ✅ 生成的 `.whl` 和 `.tar.gz` 文件名包含这个版本号
- ✅ `pip install debug-helpers==0.4.0` 中的 `0.4.0` 来自这里

**验证**:
```bash
# 查看配置的版本号
grep "version = " pyproject.toml
# 输出: version = "0.4.0"

# 构建后查看文件名
python -m build
ls dist/
# 输出:
# debug_helpers-0.4.0-py3-none-any.whl
# debug_helpers-0.4.0.tar.gz
#                    ↑
#              版本号在这里
```

### 2. 运行时版本：`src/debug_helpers/__init__.py`

**位置**: `src/debug_helpers/__init__.py`

```python
__version__ = "0.4.0"  # ← 这是代码中使用的版本号
```

**作用**:
- ✅ 代码运行时可以通过 `from debug_helpers import __version__` 获取
- ✅ 用于在代码中显示版本信息
- ✅ **不影响 PyPI 上的版本号**

**验证**:
```python
from debug_helpers import __version__
print(__version__)  # 输出: 0.4.0
```

---

## 🔄 版本号同步

### 为什么需要两个地方？

| 位置 | 用途 | 是否必须 |
|------|------|----------|
| `pyproject.toml` | PyPI 版本号、构建包名 | ✅ **必须** |
| `__init__.py` | 代码中获取版本号 | ⚠️ 推荐（保持同步） |

### 最佳实践

**保持两个地方版本号一致**：

```bash
# 更新版本号的脚本
#!/bin/bash
VERSION="0.4.0"

# 1. 更新 pyproject.toml
sed -i '' "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml

# 2. 更新 __init__.py
sed -i '' "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" src/debug_helpers/__init__.py

# 3. 验证
echo "pyproject.toml:"
grep "version = " pyproject.toml
echo ""
echo "__init__.py:"
grep "__version__" src/debug_helpers/__init__.py
```

---

## 📊 版本号流转过程

```
1. 开发者更新版本号
   ↓
   pyproject.toml: version = "0.4.0"
   src/debug_helpers/__init__.py: __version__ = "0.4.0"
   ↓
2. 构建分发包
   python -m build
   ↓
   读取 pyproject.toml 中的 version
   ↓
3. 生成分发包
   dist/debug_helpers-0.4.0-py3-none-any.whl
   dist/debug_helpers-0.4.0.tar.gz
   ↓
4. 上传到 PyPI
   twine upload dist/*
   ↓
5. PyPI 显示版本号
   https://pypi.org/project/debug-helpers/0.4.0/
   ↓
6. 用户安装
   pip install debug-helpers==0.4.0
   ↓
   从 PyPI 下载 debug_helpers-0.4.0-*.whl
   ↓
7. 安装后使用
   from debug_helpers import __version__
   print(__version__)  # 输出: 0.4.0
```

---

## 🔍 详细说明

### `pyproject.toml` 中的版本号

```toml
[project]
name = "debug-helpers"
version = "0.4.0"  # ← PyPI 版本号来源
```

**构建工具如何读取**:

使用 `hatchling` 构建后端时：

```bash
python -m build
```

构建过程：
1. 读取 `pyproject.toml`
2. 提取 `[project].version`
3. 生成分发包文件名：`{name}-{version}-{tag}.{ext}`
4. 在分发包的元数据中记录版本号

**验证分发包版本**:
```bash
# 构建
python -m build

# 检查分发包元数据
python -m twine check dist/*.whl
# 输出会显示: Checking dist/debug_helpers-0.4.0-py3-none-any.whl: PASSED

# 查看分发包信息
python -m zipfile -l dist/debug_helpers-0.4.0-py3-none-any.whl | grep METADATA
# 解压后查看 METADATA 文件，会看到: Version: 0.4.0
```

### `__init__.py` 中的版本号

```python
__version__ = "0.4.0"
```

**用途**:
- 代码中动态获取版本号
- 显示版本信息
- 调试和日志

**使用示例**:
```python
# 在代码中使用
from debug_helpers import __version__

def show_version():
    print(f"debug-helpers version: {__version__}")

# 在命令行工具中使用
import sys
if "--version" in sys.argv:
    print(__version__)
    sys.exit(0)
```

---

## ⚠️ 常见问题

### Q1: 如果两个版本号不一致会怎样？

**情况 A**: `pyproject.toml` 是 `0.4.0`，`__init__.py` 是 `0.3.0`

```
结果:
✅ PyPI 上显示: 0.4.0
✅ pip install debug-helpers==0.4.0 正常
❌ 但代码中 __version__ 显示: 0.3.0（不一致）
```

**情况 B**: `pyproject.toml` 是 `0.3.0`，`__init__.py` 是 `0.4.0`

```
结果:
❌ PyPI 上显示: 0.3.0（旧版本）
❌ pip install debug-helpers==0.4.0 会失败（找不到）
✅ 但代码中 __version__ 显示: 0.4.0（不一致）
```

**建议**: 总是保持两个版本号一致！

### Q2: 可以只更新一个地方吗？

**只更新 `pyproject.toml`**:
- ✅ PyPI 版本号会更新
- ❌ 代码中 `__version__` 还是旧版本
- ⚠️ 不推荐

**只更新 `__init__.py`**:
- ❌ PyPI 版本号不会更新
- ✅ 代码中 `__version__` 会更新
- ❌ 完全错误！

**正确做法**: 两个地方都要更新！

### Q3: 如何自动同步版本号？

**方法 1: 使用脚本**

创建 `scripts/update_version.sh`:
```bash
#!/bin/bash
VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./scripts/update_version.sh 0.4.0"
    exit 1
fi

# 更新 pyproject.toml
sed -i '' "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml

# 更新 __init__.py
sed -i '' "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" src/debug_helpers/__init__.py

echo "✅ 版本号已更新为: $VERSION"
echo ""
echo "验证:"
grep "version = " pyproject.toml
grep "__version__" src/debug_helpers/__init__.py
```

**方法 2: 使用 Python 脚本**

创建 `scripts/update_version.py`:
```python
#!/usr/bin/env python3
import sys
import re

def update_version(version):
    # 更新 pyproject.toml
    with open('pyproject.toml', 'r') as f:
        content = f.read()
    content = re.sub(r'version = ".*"', f'version = "{version}"', content)
    with open('pyproject.toml', 'w') as f:
        f.write(content)
    
    # 更新 __init__.py
    with open('src/debug_helpers/__init__.py', 'r') as f:
        content = f.read()
    content = re.sub(r'__version__ = ".*"', f'__version__ = "{version}"', content)
    with open('src/debug_helpers/__init__.py', 'w') as f:
        f.write(content)
    
    print(f"✅ 版本号已更新为: {version}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python scripts/update_version.py 0.4.0")
        sys.exit(1)
    update_version(sys.argv[1])
```

**方法 3: 使用 Makefile**

在 `Makefile` 中添加：
```makefile
VERSION ?= 0.4.0

update-version:
	@echo "更新版本号为: $(VERSION)"
	@sed -i '' 's/version = ".*"/version = "$(VERSION)"/' pyproject.toml
	@sed -i '' 's/__version__ = ".*"/__version__ = "$(VERSION)"/' src/debug_helpers/__init__.py
	@echo "✅ 完成"
	@echo ""
	@echo "验证:"
	@grep "version = " pyproject.toml
	@grep "__version__" src/debug_helpers/__init__.py

.PHONY: update-version
```

使用：
```bash
make update-version VERSION=0.4.1
```

---

## 📋 版本号更新检查清单

发布新版本前，确保：

```
☐ pyproject.toml 中的 version 已更新
☐ src/debug_helpers/__init__.py 中的 __version__ 已更新
☐ 两个版本号完全一致
☐ CHANGELOG.md 已更新
☐ 已提交所有更改
☐ 已创建并推送 tag
```

---

## 🎯 总结

### 核心要点

1. **PyPI 版本号来源**: `pyproject.toml` 中的 `version` 字段
2. **代码版本号**: `__init__.py` 中的 `__version__` 变量
3. **最佳实践**: 保持两个版本号一致
4. **更新方式**: 手动更新或使用脚本自动化

### 快速参考

| 位置 | 文件 | 字段 | 用途 |
|------|------|------|------|
| **PyPI 版本** | `pyproject.toml` | `version = "0.4.0"` | ⭐ 决定 PyPI 上的版本号 |
| **代码版本** | `src/debug_helpers/__init__.py` | `__version__ = "0.4.0"` | 代码中获取版本号 |

### 验证命令

```bash
# 检查 pyproject.toml
grep "version = " pyproject.toml

# 检查 __init__.py
grep "__version__" src/debug_helpers/__init__.py

# 构建后验证
python -m build
ls dist/ | grep "0.4.0"
```

---

**记住**: `pip install debug-helpers==0.4.0` 中的 `0.4.0` 来自 `pyproject.toml`！📦
