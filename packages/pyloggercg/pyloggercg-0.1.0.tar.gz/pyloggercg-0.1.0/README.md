<h1 align='center'>PyLogger</h1>

## Description

A simple Logger module for python

---

## Installation 
```bash
pip install PyLogger
```

---

## Usage
```python
from PyLogger import Logger
logger = Logger(name="Test", log_file="test.log")
logger.debug("This is a debug message")
logger.info("App has started")
logger.warning("This is a warning")
logger.error("Something went wrong")
logger.critical("Critical failure!")
```

