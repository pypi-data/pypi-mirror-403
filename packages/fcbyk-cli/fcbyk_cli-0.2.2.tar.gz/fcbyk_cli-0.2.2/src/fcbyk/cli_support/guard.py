"""
CLI guard / 验证工具
"""

import json, click
from typing import Any, Dict, Optional
from fcbyk.utils import storage, network


def check_port(port: int, host: str = "0.0.0.0", output_prefix: str = " ", silent: bool = False) -> bool:
    try:
        network.ensure_port_available(port=port, host=host)
    except OSError as e:
        if not silent:
            click.echo(
                f"{output_prefix}Error: Port {port} is already in use (or you don't have permission). "
                f"{output_prefix}Please choose another port (e.g. --port {int(port) + 1})."
            )
            click.echo(f"{output_prefix}Details: {e}\n")
        return False
    return True


def load_json_object_or_exit(
    ctx: click.Context,
    path: str,
    *,
    default: Optional[Dict[str, Any]] = None,
    create_if_missing: bool = True,
    label: str = "data file",
) -> Dict[str, Any]:
    """读取一个 JSON 文件并确保顶层为 object(dict)，失败则友好提示并退出。"""
    try:
        data = storage.load_json(
            path,
            default=default,
            create_if_missing=create_if_missing,
            strict=True,
        )
    except json.JSONDecodeError as e:
        click.secho(f"Error: {label} is not valid JSON.", fg="red", err=True)
        click.secho(f"File: {path}", fg="red", err=True)
        click.secho(f"Details: {e}", fg="red", err=True)
        ctx.exit(1)
    except Exception as e:
        click.secho(f"Error: failed to read {label}.", fg="red", err=True)
        click.secho(f"File: {path}", fg="red", err=True)
        click.secho(f"Details: {e}", fg="red", err=True)
        ctx.exit(1)

    if data is None:
        # 只有 default=None 且文件不存在时才可能发生
        click.secho(f"Error: {label} does not exist.", fg="red", err=True)
        click.secho(f"File: {path}", fg="red", err=True)
        ctx.exit(1)

    if not isinstance(data, dict):
        click.secho(f"Error: invalid {label} format. Expected a JSON object.", fg="red", err=True)
        click.secho(f"File: {path}", fg="red", err=True)
        ctx.exit(1)

    return data


def ensure_list_field(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    """确保 data[key] 是 list。

    - 如果 key 不存在，或对应值不是 list，则会设置为空列表 []。
    - 仅修改内存对象，不做写回；是否持久化由调用方决定。

    用途：
        pick 这类数据文件允许用户手改，为避免手改造成字段缺失/类型错误导致命令报错，
        可以在读取后做轻量自愈（不覆盖整个文件）。
    """
    if key not in data or not isinstance(data.get(key), list):
        data[key] = []
    return data
