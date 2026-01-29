import click
import random
import time
from typing import Any, Dict, List


def colored_key_value(key: str, value: Any, key_color: str = 'cyan', value_color: str = 'yellow') -> str:
    """
    返回格式化后的彩色 key:value 字符串。

    Args:
        key (str): 字段名
        value (Any): 字段值
        key_color (str): key 的颜色
        value_color (str): value 的颜色

    Returns:
        str: 彩色格式化字符串
    """
    return f"{click.style(str(key), fg=key_color)}: {click.style(str(value), fg=value_color)}"


def show_dict(
    ctx: click.Context,
    param: Any,
    value: bool,
    title: str,
    data: Dict[str, Any]
) -> None:
    """直接显示一个 dict，并退出 CLI（彩色高亮）。

    用途：
        当配置不再是“单独一个 json 文件”时（例如统一配置文件的某个 section），
        调用方可以先自行拿到 dict，再交给该函数统一打印。

    输出格式：
        <title>: <...>   （key 青色，value 黄色）
        key: value

    Args:
        ctx: click 上下文对象
        param: click 参数对象（占位，保持与 click callback 签名一致）
        value: 是否触发显示
        title: 标题（例如 "config file"、"section"、"ai config"）
        data: 要显示的字典
    """
    if not value:
        return

    click.echo(colored_key_value(title, ""))
    for k, v in data.items():
        click.echo(colored_key_value(k, v))

    ctx.exit()


def echo_network_urls(networks: list, port: int, include_virtual: bool = False):
    """
    打印可访问的本地和局域网 URL，支持彩色高亮。

    Args:
        networks (list[dict]): get_private_networks() 返回的网卡信息列表
        port (int): 端口号
        include_virtual (bool): 是否显示虚拟网卡（如 VMware、Docker）

    输出示例：
        Local: http://localhost:5173
        Local: http://127.0.0.1:5173
        [Ethernet] Network URL: http://192.168.0.101:5173
    """
    # 本地访问地址
    for host in ["localhost", "127.0.0.1"]:
        click.echo(colored_key_value(" Local", f"http://{host}:{port}", key_color=None, value_color="cyan"))

    # 局域网访问
    for net in networks:
        if net['virtual'] and not include_virtual:
            continue  # 跳过虚拟网卡

        for ip in net["ips"]:
            # 排除回环地址，避免与前面的本地地址重复
            if ip == "127.0.0.1":
                continue
            click.echo(colored_key_value(f" [{net['iface']}] Network URL:", f"http://{ip}:{port}", key_color=None, value_color="cyan"))

def copy_to_clipboard(text: str, label: str = "URL", output_prefix: str = " ", silent: bool = False):
    """
    将文本复制到剪贴板，并根据结果打印 Click 提示。
    
    text: 要复制的内容
    label: 内容的名称，用于提示语（如 "URL", "Password" 等）
    output_prefix: 输出前缀（默认空格）
    silent: 是否静默执行（不打印提示）
    """
    import pyperclip
    import click
    
    try:
        pyperclip.copy(text)
        if not silent:
            click.echo(f"{output_prefix}{label} has been copied to clipboard")
    except Exception:
        if not silent:
            click.echo(f"{output_prefix}Warning: Could not copy {label} to clipboard")


def show_spinning_animation(
    items: List[str],
    iterations: int,
    delay: float,
    prefix: str = "Current pointer: ",
    max_length: int = 0
) -> None:
    """显示旋转/抽奖动画的一帧。
    
    Args:
        items: 候选项目列表
        iterations: 动画帧数
        delay: 每帧之间的延迟（秒）
        prefix: 显示前缀
        max_length: 最大显示长度（用于清除整行），如果为0则自动计算
    """
    if not items:
        return

    if max_length <= 0:
        max_length = max(len(f"{prefix}{item}") for item in items)

    for _ in range(iterations):
        current = random.choice(items)
        display_text = f"{prefix}{current}"
        padding = " " * max(0, max_length - len(display_text))
        click.echo(f"\r{display_text}{padding}", nl=False)
        time.sleep(delay)

