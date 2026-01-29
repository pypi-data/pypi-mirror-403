"""fcbyk 通用数据 / 文件工具
================================

提供一组与 *业务无关* 的文件/数据持久化工具，统一路径规则：
    所有 CLI 相关文件（配置、缓存、日志、数据）统一放在
        ~/.fcbyk/

设计目标：
1. **简单易用**：子命令只关心读/写 JSON 或文本，不再重复做路径拼接。
2. **无业务逻辑**：不做 default 补齐、不做 CLI 参数合并，那些交给调用者。
3. **容错安全**：自动创建目录，写文件采用临时文件+原子替换，尽量避免损坏。
4. **可扩展**：未来可加 YAML / Pickle / SQLite 等读写函数。

注意：
- 通用层默认不会“吞掉”用户数据错误。
- 对于 JSON 解析失败（格式错误），默认会抛出异常，让调用方决定如何处理。

使用范例::

    from fcbyk.utils import storage

    # 获取统一路径
    path = storage.get_path("lottery.json")

    # 读写 JSON
    lottery = storage.load_json(path, default=list())
    lottery.append({"user": "xxx", "time": 123})
    storage.save_json(path, lottery)

    # 操作统一文件的某个 section
    aliases = storage.load_section("fcbyk_config.json", "aliases", default={})
    aliases["ppt"] = "slide"
    storage.save_section("fcbyk_config.json", "aliases", aliases)

"""

import json
import os
import tempfile
from typing import Any, Dict, Optional, TypeVar

# ----------------------------------------
# 基础路径工具
# ----------------------------------------

_DEFAULT_APP_NAME = "fcbyk"


def _ensure_dir(path: str) -> None:
    """确保 `path` 所在目录存在"""
    os.makedirs(os.path.dirname(path), exist_ok=True)


def get_path(filename: str, *, app_name: str = _DEFAULT_APP_NAME, subdir: Optional[str] = None) -> str:
    """返回位于 `~/.{app_name}/[subdir]/filename` 的绝对路径。

    - 若 `subdir` 提供则追加一级子目录（会自动创建）。
    - **不会**创建文件，只返回路径。
    """
    base = os.path.join(os.path.expanduser("~"), f".{app_name}")
    if subdir:
        base = os.path.join(base, subdir)
    return os.path.join(base, filename)


# ----------------------------------------
# JSON 操作
# ----------------------------------------

T = TypeVar("T")


def load_json(
    path: str,
    *,
    default: Optional[T] = None,
    create_if_missing: bool = False,
    strict: bool = True,
) -> T:
    """读取 JSON 文件为 Python 对象。

    参数:
        path:
            文件路径。
        default:
            文件不存在时返回的默认值（默认 None）。
        create_if_missing:
            当文件不存在且 default 不为 None 时，是否立即写入 default。
        strict:
            是否严格解析：
            - True（默认）：JSON 格式错误会抛出异常（推荐，避免悄悄吞掉数据问题）。
            - False：JSON 格式错误时返回 default。

    返回:
        解析得到的数据（或 default）。
    """
    _ensure_dir(path)

    if not os.path.exists(path):
        if create_if_missing and default is not None:
            save_json(path, default)
        return default  # type: ignore[return-value]

    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)  # type: ignore[return-value]
        except Exception:
            if strict:
                raise
            return default  # type: ignore[return-value]


def save_json(path: str, data: Any, *, indent: int = 2, ensure_ascii: bool = False, atomic: bool = True) -> None:
    """保存 Python 对象到 JSON 文件。

    参数说明：
        indent:
            JSON 输出缩进空格数。
            - indent=2：更易读（默认）。
            - indent=None：更紧凑（更小体积，但可读性差）。

        ensure_ascii:
            是否强制把非 ASCII 字符（如中文）转义成 ``\u4e2d\u6587`` 形式。
            - False（默认）：中文会直接写入文件，便于阅读。
            - True：全部转义成 ASCII，兼容极少数只接受 ASCII 的场景。

        atomic:
            是否使用“原子写入”。
            - True（默认）：先写到同目录的临时文件，再用 ``os.replace`` 一次性替换目标文件。
              好处：进程中途崩溃/断电时，更不容易留下半截文件导致 JSON 损坏。
            - False：直接打开目标文件写入（速度略快，但更容易产生损坏文件）。
    """
    _ensure_dir(path)

    if atomic:
        dir_name = os.path.dirname(path)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_name, encoding="utf-8") as tf:
            json.dump(data, tf, indent=indent, ensure_ascii=ensure_ascii)
            temp_name = tf.name
        os.replace(temp_name, path)
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)


# ----------------------------------------
# JSON section 操作（一个文件多 section）
# ----------------------------------------

def load_section(filename: str, section: str, *, default: Optional[T] = None, app_name: str = _DEFAULT_APP_NAME) -> T:
    """读取、补齐并返回 ~/.{app_name}/filename 的 JSON 文件中的某个顶层 section。

    行为:
    - 如果 section 不存在，则使用 default 创建并写回文件。
    - 如果 section 已存在且是 dict，则用 default 中的字段补齐缺失项，并写回文件。
    - 如果 JSON 文件格式错误：抛出异常（保持 strict）。
    """
    path = get_path(filename, app_name=app_name)
    root = load_json(path, default={}, create_if_missing=True, strict=True)
    assert isinstance(root, dict), "Root of JSON must be an object for section operations"

    section_data = root.get(section)
    updated = False

    # Section 不存在，用 default 创建
    if section_data is None:
        if default is not None:
            root[section] = default
            updated = True
            section_data = default
    # Section 存在，且 default 和 section 都是 dict，则补齐
    elif isinstance(section_data, dict) and isinstance(default, dict):
        for k, v in default.items():
            if k not in section_data:
                section_data[k] = v
                updated = True

    if updated:
        save_json(path, root)

    return section_data if section_data is not None else default  # type: ignore[return-value]


def save_section(filename: str, section: str, data: Any, *, app_name: str = _DEFAULT_APP_NAME) -> None:
    """写入/覆盖 ~/.{app_name}/filename 中的某个 section (顶层 key)。"""
    path = get_path(filename, app_name=app_name)
    root = load_json(path, default={}, create_if_missing=True, strict=True)
    assert isinstance(root, dict), "Root of JSON must be object"
    root[section] = data
    save_json(path, root)


# ----------------------------------------
# 文本文件工具 (简单场景)
# ----------------------------------------

def read_text(path: str, *, default: Optional[str] = None) -> Optional[str]:
    _ensure_dir(path)
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return default


def write_text(path: str, content: str, *, atomic: bool = True) -> None:
    _ensure_dir(path)
    if atomic:
        dir_name = os.path.dirname(path)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_name, encoding="utf-8") as tf:
            tf.write(content)
            temp_name = tf.name
        os.replace(temp_name, path)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
