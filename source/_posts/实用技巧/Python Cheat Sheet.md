---
title: Python Cheat Sheet
tags:
  - cheatsheet
categories:
  - 实用技巧
date: 2023-07-17 20:17:25
---
#cheatsheet 

## 实现自定义的With
+ 实现 `__enter__` 和 `__exit__`
```python
class Sample:
	def __enter__(self):
		print("in enter")
		return "Foo"

	def __exit__(self, type, value, trace):
		print("in exit")


with Sample() as sample:
	print("get_sample() as {}".format(sample))

# 输出
# in enter
# get_sample() as Foo
# in exit
```
+ 使用ContextManager
```python
from contextlib import contextmanager


class Sample:
	@contextmanager
	def foo(self):
		try:
			print('do something')
			yield 'foo' # 可选
 		finally:
	 		print('do other thing')

sample = Smaple()
with sample.foo() as sf:
	print(sf)

# do something
# foo
# do other thing
```

