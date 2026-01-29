# MLCheck

**MLCheck** is an open-source Python library for pre-flight validation and reliability checks in machine learning pipelines.

It helps ML engineers detect silent failures such as:
- Data leakage
- Schema mismatches
- Shape inconsistencies
- Invalid training setups

## Why MLCheck?

Most ML failures happen **before deployment** and go unnoticed.
MLCheck acts like a **linter for ML systems**.

## Installation

```bash
pip install mlcheck
```


## Quick Example

```python
from mlcheck import check

report = check(X_train, X_test, y_train)
report.show()
```

## Project Status

🚧 Early development (v0.0.1)
APIs may change until v1.0.