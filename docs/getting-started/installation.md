# Installation

networkconfparse requires **Python 3.11 or newer** and has **no runtime
dependencies**.

## With uv

```bash
uv add networkconfparse
```

## With pip

```bash
pip install networkconfparse
```

## Verify the installation

```python
import networkconfparse

config = networkconfparse.parse("hostname r1\n")
print([line.text for line in config])
# ['hostname r1']
```
