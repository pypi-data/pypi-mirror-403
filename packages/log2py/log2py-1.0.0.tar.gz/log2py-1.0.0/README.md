# Simple Logging Library - log4py

![img](logo.png)

## Menual
### 1. Install
```bash
$ wget https://raw.githubusercontent.com/newkincode/log4py/main/log4py.py
```
### 2. Import
```python
from log4py import Logger
```
### 3. Use
```python
logger = Logger()
logger.info("Hello World!")
logger.save()
```
### 4. Result
```
0000-00-00 00-00-00 - INFO - Hello World!
```
