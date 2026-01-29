"""
lansend 命令行接口模块

对外提供 lansend 命令，用于在局域网内共享文件。

函数:
- lansend(): Click 命令入口，提供完整参数选项
"""

import os
import webbrowser

import click

from fcbyk.cli_support.output import echo_network_urls, show_dict, copy_to_clipboard
from fcbyk.cli_support.guard import check_port
from fcbyk.utils import storage
from fcbyk.utils.network import get_private_networks
from .controller import start_web_server
from .service import LansendConfig, LansendService


def _show_lansend_config(ctx: click.Context, param, value: bool) -> None:
    if not value:
        return

    try:
        data = storage.load_section("fcbyk_config.json", "lansend", default={})
    except Exception:
        data = {}

    if not isinstance(data, dict):
        data = {}

    show_dict(ctx, param, True, "fcbyk_config.json:lansend", data)


@click.command(help="Start a local web server for sharing files over LAN")
@click.option("-p", "--port", default=80, help="Web server port (default: 80)")
@click.option("-d", "--directory", default=".", help="Directory to share (default: current directory)")
@click.option(
    "-pw",
    "--password",
    is_flag=True,
    default=False,
    help="Prompt to set upload password (default: no password, or 123456 if skipped)",
)
@click.option("-nb", "--no-browser", is_flag=True, help="Disable automatic browser opening")
@click.option("-un-d","--un-download", is_flag=True, default=False, help="Hide download buttons in directory tab")
@click.option("-un-up","--un-upload", is_flag=True, default=False, help="Disable upload functionality")
@click.option("--chat", is_flag=True, default=False, help="Enable chat functionality")
@click.option(
    "--show-config",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_show_lansend_config,
    help="Show saved config and exit",
)
@click.option("--last", is_flag=True, default=False, help="Reuse last saved config")
@click.option("--save", is_flag=True, default=False, help="Save current args to config")
def lansend(
    port: int,
    directory: str,
    password: bool = False,
    no_browser: bool = False,
    un_download: bool = False,
    un_upload: bool = False,
    chat: bool = False,
    last: bool = False,
    save: bool = False,
):
    # --last: 完全复用持久化配置（忽略其它参数）
    if last:
        try:
            cfg = storage.load_section("fcbyk_config.json", "lansend", default=None)
        except Exception:
            cfg = None

        if not isinstance(cfg, dict):
            click.echo("Error: No saved lansend config found. Use --save first.")
            return

        directory = str(cfg.get("shared_directory") or ".")
        try:
            port = int(cfg.get("port") or 80)
        except Exception:
            port = 80

        password = bool(cfg.get("password_flag") or False)
        no_browser = bool(cfg.get("no_browser") or False)
        un_download = bool(cfg.get("un_download") or False)
        un_upload = bool(cfg.get("un_upload") or False)
        chat = bool(cfg.get("chat") or False)

    if not os.path.exists(directory):
        click.echo(f"Error: Directory {directory} does not exist")
        return

    if not os.path.isdir(directory):
        click.echo(f"Error: {directory} is not a directory")
        return

    shared_directory = os.path.abspath(directory)

    config = LansendConfig(
        shared_directory=shared_directory,
        upload_password=None,
        un_download=un_download,
        un_upload=un_upload,
        chat_enabled=chat,
    )
    service = LansendService(config)
    config.upload_password = service.pick_upload_password(password, un_upload, click)
    
    click.echo()
    private_networks = get_private_networks()
    local_ip = private_networks[0]["ips"][0]

    if not check_port(port):
        return

    click.echo(f" Directory: {shared_directory}")
    if config.upload_password:
        click.echo(" Upload Password: Enabled")
    echo_network_urls(private_networks, port, include_virtual=True)
    copy_to_clipboard(f"http://{local_ip}:{port}")

    if save:
        try:
            storage.save_section(
                "fcbyk_config.json",
                "lansend",
                {
                    "shared_directory": shared_directory,
                    "port": str(port),
                    "password_flag": bool(password),
                    "no_browser": bool(no_browser),
                    "un_download": bool(un_download),
                    "un_upload": bool(un_upload),
                    "chat": bool(chat),
                },
            )
        except Exception:
            pass

    if not no_browser:
        webbrowser.open(f"http://{local_ip}:{port}")
    click.echo()
    start_web_server(port, service)
