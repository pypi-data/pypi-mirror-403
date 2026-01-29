# ConstSpace 🚀

[![GitHub repo](https://img.shields.io/badge/GitHub-Repo-blue?logo=github)](https://github.com/fluffydogcatmouse/constspace)
[![PyPI version](https://img.shields.io/pypi/v/constspace.svg)](https://pypi.org/project/constspace/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ConstSpace** 是一个极致轻量化的 Python 库，用于定义**只读、不可实例化、类型安全**的常量命名空间。

它旨在解决 Python 中 `Enum` 必须使用 `.value` 的繁琐，以及普通 `Class` 容易被误修改且缺乏类型约束的痛点。

---

## 🌟 核心特性

* **零 `.value` 负担**：直接访问常量名，获取原始值，IDE 补全完美。
* **类级只读保护**：通过元类拦截，彻底封死在运行时修改或删除类属性的行为。
* **严禁实例化**：确保类仅作为命名空间使用，尝试实例化将抛出 `TypeError`。
* **统一类型归纳**：装饰器自动注入基类，支持使用 `ConstSpaceType` 对多个常量类进行统一标注和管理。
* **无感知集成**：支持属性间的直接引用，支持静态类型检查。

---

## 📦 安装

```bash
pip install constspace
```

---

## 🚀 快速上手

### 1. 定义常量空间

```python
from constspace import constspace

@constspace
class ServiceConfig:
    API_KEY = "v1_sec_123"
    TIMEOUT = 60
    # 自由引用，无需 .value，无需 self
    SIGNATURE = f"prefix_{API_KEY}_suffix" 

```

### 2. 安全保障

```python
# ✅ 正常访问
print(ServiceConfig.SIGNATURE) 

# ❌ 尝试修改类属性 -> 抛出 AttributeError
ServiceConfig.API_KEY = "new_key" 

# ❌ 尝试实例化 -> 抛出 TypeError
cfg = ServiceConfig() 

```

### 3. 类型标注与管理

```python
from typing import List
from constspace import constspace, ConstSpaceType

@constspace
class MySQL:
    PORT = 3306

@namespace
class Redis:
    PORT = 6379

# 使用 ConstSpaceType (即 Type[ConstSpace]) 统一约束
def print_port(cfg: ConstSpaceType):
    print(f"Port is: {cfg.PORT}")

configs: List[ConstSpaceType] = [MySQL, Redis]
for c in configs:
    print_port(c)

```

---

## 🧐 为什么选择 ConstSpace?

| 特性 | **ConstSpace** | **Enum** | **Dataclass (frozen)** |
| --- | --- | --- | --- |
| **访问简单** | ✅ 直接获取值 | ❌ 需 `.value` | ✅ 直接获取值 |
| **禁止实例化** | ✅ 强制拦截 | ❌ 默认允许 | ❌ 默认允许 |
| **类属性保护** | ✅ 严格只读 | ❌ 允许修改成员 | ❌ 仅保护实例变量 |
| **类型提示** | ✅ 原始类型 | ❌ 成员对象类型 | ✅ 原始类型 |

---

## 📜 开源协议

MIT License.