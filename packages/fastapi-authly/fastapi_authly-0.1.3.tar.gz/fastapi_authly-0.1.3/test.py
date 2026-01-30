
"""
题 1（入门）
给定 nums = [1, 2, 3, 4, 5]，用 map 得到每个元素的平方，输出为列表。

"""
numbers = [1,2,3,4,5,6,7,8,9]
content = map(lambda x: x**2, numbers)
print(list(content))


"""
给定 words = [" Alice ", "BOB", "cHaRlIe "]
用 map 把每个元素转换成：去掉两端空格 + 全部小写。
"""

a = 'Word'
words = [" Alice ", "BOB", "cHaRlIe "]

new_words = map(lambda x: x.strip().lower(), words)

print(list(new_words))

"""
### 题 3（类型转换 + 容错）
给定 `raw = ["1", "2", "x", "3", ""]`  
实现一个转换函数：能转成 int 的转 int，不能转的返回 `None`。  
用 `map` 得到结果列表。
"""

raw = ["1", "2", "x", "3", ""]

def change(x):
    try:
        return int(x)
    except ValueError:
        return None

content = map(change, raw)

print(list(content))


"""
### 题 4（多个 iterable）
给定：

```python
a = [1, 2, 3, 4]
b = [10, 20, 30]
```

用 `map` 生成 `a[i] + b[i]` 的列表，并解释为什么结果长度是多少。
"""

a = [1, 2, 3, 4]
b = [10, 20, 30]

def _add(x,y):
    print(x,y)

content = map(lambda x,y:x+y, a, b)

print(list(content))
# 长度为最短的那个可迭代对象的长度，因为灰爆出stop什么来着


"""
### 题 5（嵌套数据处理）
给定：

```python
records = [
    {"name": "alice", "score": "98"},
    {"name": "bob", "score": "87"},
    {"name": "cathy", "score": "100"},
]
```

用 `map` 输出一个列表：每个元素是 `(NAME_UPPER, score_int)`。
"""

records = [
    {"name": "alice", "score": "98"},
    {"name": "bob", "score": "87"},
    {"name": "cathy", "score": "100"},
]

content = map(lambda x: (x["name"].upper(), x["score"]), records)

print(list(content))


"""
### 题 6（惰性验证题）
写一段最短代码证明：`map` 不会立刻执行函数，而是在迭代时执行。  
要求：必须能从输出看出来“什么时候调用”。
"""

numbers = [1,2,3,4,5,6,7,8,9]

content = map(lambda x: print(f"当前{x}"), numbers)

print(next(content))


"""
### 题 7（组合题：map + filter）
给定 `nums = list(range(-5, 6))`  
用 **filter 先筛掉负数**，再用 **map 转平方**，输出列表。  
（要求用函数式写法，不用列表推导式。）
"""
nums = list(range(-5, 6))

filtered = filter(lambda x: x > 0, nums)

new_nums = map(lambda x: x**2, filtered)
print(list(new_nums))

"""
### 题 8（进阶：并行处理 + 缺失值）
给定：

```python
names = ["alice", "bob", "cathy", "dan"]
scores = ["100", "", "87", "x"]
```

目标输出一个列表：`["Alice:100", "Bob:NA", "Cathy:87", "Dan:NA"]`  
规则：分数能转 int 就用该数字，否则用 `"NA"`。  
要求：用 `map`，并尽量把逻辑放进一个清晰的转换函数里。

"""
names = ["alice", "bob", "cathy", "dan"]
scores = ["100", "", "87", "x"]

def chang(name,score):
    try:
        score = int(score)
        return f"{name}:{score}"
    except ValueError:
        return f"{name}:NA"

content = map(chang, names, scores)

print(list(content))

print(callable(chang))

"""
### 题 9（较难：实现你自己的 map）
实现一个函数 `my_map(func, iterable)`，返回一个**生成器**，行为尽量像 `map`（惰性、一次产出一个）。  
然后用它跑一下题 1 的例子验证。
"""

from typing import Callable

def my_map(func: Callable, iterable):
    if not callable(func):
        raise "func 应该是一个函数"

    # todo 应该增加iterable 的判断，判断他是一个可迭代的对象

    # todo 应该增加可是传递多个可迭代对象，但是我不知道怎么做
    for item in iterable:
        yield func(item)

numbers = [1,2,3,4,5,6,7,8,9]

content = my_map(lambda x: x**2, numbers)

print(next(content))

print(list(content))


print(map.__doc__)