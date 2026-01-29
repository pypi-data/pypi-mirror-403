# ConstSpace 🚀

[![GitHub repo](https://img.shields.io/badge/GitHub-Repo-blue?logo=github)](https://github.com/fluffydogcatmouse/constspace)
[![PyPI version](https://img.shields.io/pypi/v/constspace.svg)](https://pypi.org/project/constspace/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ConstSpace** is an ultra-lightweight Python library for defining **read-only, non-instantiable, and type-safe** constant namespaces.

It is designed to eliminate the verbosity of Python's `Enum` (which requires `.value` access) and the lack of protection in plain classes.

---

## 🌟 Key Features

* **Zero `.value` Overhead**: Access constants directly. What you see is what you get, with perfect IDE autocompletion.
* **Class-Level Read-Only Protection**: Uses metaclasses to block any attempt to modify or delete class attributes at runtime.
* **Strict Non-instantiability**: Ensures classes are used purely as namespaces. Attempting to instantiate will raise a `TypeError`.
* **Unified Type Grouping**: The decorator automatically injects a base class, allowing you to use `ConstSpaceType` for clean type hinting and management.
* **Seamless Integration**: Supports direct references between attributes during definition and works perfectly with static type checkers like MyPy.

---

## 📦 Installation

```bash
pip install constspace
```

---

## 🚀 Quick Start

### 1. Define Your Constant Space

```python
from constspace import constspace

@constspace
class ServiceConfig:
    API_KEY = "v1_sec_123"
    TIMEOUT = 60
    # Reference attributes directly without .value or self
    SIGNATURE = f"prefix_{API_KEY}_suffix" 

```

### 2. Security & Constraints

```python
# ✅ Normal Access
print(ServiceConfig.SIGNATURE) 

# ❌ Modify attribute -> Raises AttributeError
ServiceConfig.API_KEY = "new_key" 

# ❌ Instantiate -> Raises TypeError
cfg = ServiceConfig() 

```

### 3. Type Hinting & Management

```python
from typing import List
from constspace import constspace, ConstSpaceType

@constspace
class MySQL:
    PORT = 3306

@constspace
class Redis:
    PORT = 6379

# Use ConstSpaceType (alias for Type[ConstSpace]) for constraints
def print_port(cfg: ConstSpaceType):
    print(f"Port is: {cfg.PORT}")

configs: List[ConstSpaceType] = [MySQL, Redis]
for c in configs:
    print_port(c)

```

---

## 🧐 Why ConstSpace?

| Feature | **ConstSpace** | **Enum** | **Dataclass (frozen)** |
| --- | --- | --- | --- |
| **Easy Access** | ✅ Direct Value | ❌ Requires `.value` | ✅ Direct Value |
| **Block Instance** | ✅ Strictly Enforced | ❌ Allowed by default | ❌ Allowed by default |
| **Class Attribute Protection** | ✅ Strictly Read-only | ❌ Allowed to modify | ❌ Only protects instances |
| **Type Integrity** | ✅ Original Types | ❌ Enum Member Type | ✅ Original Types |

---

## 📜 License

MIT License.