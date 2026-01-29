"""
pick 命令行接口模块

提供随机抽奖功能，支持列表抽奖和文件抽奖两种模式。

常量:
- data_file: 数据文件路径（持久化 items）
- default_data: 默认数据结构（items 列表）

函数:
- delayed_newline_simple(): 延迟打印空行（用于改善控制台输出体验）
- pick(): Click 命令入口，处理所有参数和模式切换
"""

import click

from fcbyk.cli_support.output import show_dict
from fcbyk.cli_support.guard import load_json_object_or_exit, ensure_list_field, check_port
from fcbyk.utils import storage

from .service import PickService
from .controller import start_web_server

# items 持久化数据文件：~/.fcbyk/data/pick_data.json
data_file = storage.get_path('pick_data.json', subdir='data')

default_data = {
    'items': []
}


@click.command(name='pick', help='Randomly pick one item from the list')
@click.option(
    "--config", "-c",
    is_flag=True,
    callback=lambda ctx, param, value: show_dict(
        ctx,
        param,
        value,
        f"data file: {data_file}",
        ensure_list_field(
            load_json_object_or_exit(
                ctx,
                data_file,
                default=default_data,
                create_if_missing=True,
                label="pick data file",
            ),
            "items",
        ),
    ),
    expose_value=False,
    is_eager=True,
    help="show data and exit"
)
@click.option('--add', '-a', multiple=True, help='Add item to list (can be used multiple times)')
@click.option('--remove', '-r', multiple=True, help='Remove item from list (can be used multiple times)')
@click.option('--clear', is_flag=True, help='Clear the list')
@click.option('--list', '-l', 'show_list', is_flag=True, help='Show current list')
@click.option('--web', '-w', is_flag=True, help='Start web picker server')
@click.option('--port', '-p', default=80, show_default=True, type=int, help='Port for web mode')
@click.option('--no-browser', is_flag=True, help='Do not auto-open browser in web mode')
@click.option('--files','-f', type=click.Path(exists=True, dir_okay=True, file_okay=True, readable=True, resolve_path=True), help='Start web file picker with given file')
@click.option('--password', '-pw', is_flag=True, default=False, help='Prompt to set admin password (default: 123456 if not set)')
@click.argument('items', nargs=-1)
@click.pass_context
def pick(ctx, add, remove, clear, show_list, web, port, no_browser, files, password, items):
    data = ensure_list_field(
        load_json_object_or_exit(
            ctx,
            data_file,
            default=default_data,
            create_if_missing=True,
            label="pick data file",
        ),
        "items",
    )

    service = PickService(data_file, default_data)


    # 端口占用检测
    if files or web:
        if not check_port(port):
            return

    if show_list:
        items_list = data.get('items', [])
        if items_list:
            click.echo("Current items list:")
            for i, item in enumerate(items_list, 1):
                click.echo(f"  {i}. {item}")
        else:
            click.echo("List is empty. Please use --add to add items")
        return

    if clear:
        data['items'] = []
        storage.save_json(data_file, data)
        click.echo("List cleared")
        return

    if add:
        items_list = data.get('items', [])
        for item in add:
            if item not in items_list:
                items_list.append(item)
                click.echo(f"Added: {item}")
            else:
                click.echo(f"Item already exists: {item}")
        data['items'] = items_list
        storage.save_json(data_file, data)
        return

    if remove:
        items_list = data.get('items', [])
        for item in remove:
            if item in items_list:
                items_list.remove(item)
                click.echo(f"Removed: {item}")
            else:
                click.echo(f"Item does not exist: {item}")
        data['items'] = items_list
        storage.save_json(data_file, data)
        return

    if files:
        if password:
            admin_password = click.prompt(
                'Admin password (press Enter to use default: 123456)',
                hide_input=True,
                default='123456',
                show_default=False,
            )
            if not admin_password:
                admin_password = '123456'
        else:
            admin_password = '123456'

        start_web_server(
            port=port,
            no_browser=no_browser,
            files_root=files,
            admin_password=admin_password,
        )
        return

    if web:
        start_web_server(port, no_browser)
        return

    # 优先使用命令行参数，否则使用持久化数据文件中的列表
    if items:
        service.pick_item(list(items))
    else:
        items_list = data.get('items', [])
        if not items_list:
            click.echo("Error: No items available")
            click.echo("Usage:")
            click.echo("  1. Use --add to add items: fcbyk pick --add item1 --add item2")
            click.echo("  2. Or provide items directly: fcbyk pick item1 item2 item3")
            return
        service.pick_item(items_list)
