"""
The RemotiveBroker exposes a Restbus interface for simulating CAN bus traffic.

```python
.. include:: ../_docs/snippets/restbus.py
```
"""

from remotivelabs.broker.restbus.restbus import Restbus
from remotivelabs.broker.restbus.signal_config import RestbusFrameConfig, RestbusSignalConfig

__all__ = ["Restbus", "RestbusSignalConfig", "RestbusFrameConfig"]
