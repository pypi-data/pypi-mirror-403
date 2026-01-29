## fast-tavern（Python 版）

这是主项目 `fast-tavern` 的 **Python 移植版**，目标是对齐 TypeScript 实现的行为（提示词组装与多阶段调试输出）。

### 安装（开发期）

在本目录下执行：

```bash
pip install -e .[dev]
pytest
```

### 打包/发布

在本目录下执行：

```bash
pip install build twine
python -m build
twine upload dist/*
```

### 快速开始（与 TS 用法对齐）

```python
from fast_tavern import build_prompt, History

result = build_prompt(
    preset=preset,
    character=character,
    globals={"worldBooks": world_books, "regexScripts": regex_scripts},
    history=History.openai(
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
    ),
    view="model",
    macros={"user": "Bob"},
    variables={"score": 1},
    output_format="openai",
    system_role_policy="keep",
)

print(result["stages"]["tagged"]["afterPostRegex"])
print(result["stages"]["output"]["afterPostRegex"])
```

### Regex flags 说明（与 TS 的差异点）

- `findRegex` 支持 `"/pattern/flags"` 与 `"pattern"` 两种写法。
- flags 映射：`i/m/s` -> Python `re` 对应 flags；`g` 用于决定“替换一次/全部”；`u` 默认等价；`y` 不支持（若遇到会按普通正则处理）。

### 发布后安装

```bash
pip install fast-tavern
```
