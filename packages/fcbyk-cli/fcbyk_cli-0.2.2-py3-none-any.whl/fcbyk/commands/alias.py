import click

from ..utils import storage

CONFIG_FILE = "fcbyk_config.json"
SECTION = "aliases"


def read_aliases() -> dict:
    """读取别名配置（统一存到 ~/.fcbyk/fcbyk_config.json 的 aliases section）"""
    aliases = storage.load_section(CONFIG_FILE, SECTION, default={})
    return aliases if isinstance(aliases, dict) else {}


def write_aliases(aliases: dict) -> None:
    """写入别名配置（只覆盖 aliases section）"""
    storage.save_section(CONFIG_FILE, SECTION, aliases)


class AliasedGroup(click.Group):
    """支持从 aliases.json 动态解析别名的 Group"""

    def get_command(self, ctx: click.Context, cmd_name: str):
        # 先走正常命令解析
        rv = super().get_command(ctx, cmd_name)
        if rv is not None:
            return rv

        # 再查别名
        aliases = read_aliases()
        actual_cmd = aliases.get(cmd_name)
        if actual_cmd:
            return super().get_command(ctx, actual_cmd)
        return None


@click.group(help="Manage command aliases")
def alias():
    """管理命令别名"""
    pass


@alias.command("add", help="Add a new alias")
@click.argument("alias_name")
@click.argument("command_name")
@click.pass_context
def add_alias(ctx: click.Context, alias_name: str, command_name: str):
    """添加一个新别名"""
    root_ctx = ctx.find_root()
    root_cmd = root_ctx.command

    # 检查 alias_name 是否是已存在的命令
    if isinstance(root_cmd, click.Group) and root_cmd.get_command(root_ctx, alias_name) is not None:
        click.echo(f"Error: '{alias_name}' is an existing command, cannot be used as an alias.", err=True)
        raise SystemExit(1)

    # 检查 command_name 是否是有效命令
    if not isinstance(root_cmd, click.Group) or root_cmd.get_command(root_ctx, command_name) is None:
        click.echo(f"Error: command '{command_name}' does not exist.", err=True)
        raise SystemExit(1)

    aliases = read_aliases()
    if alias_name in aliases:
        click.echo(f"Warning: alias '{alias_name}' already exists and points to '{aliases[alias_name]}'. Overwriting.")

    aliases[alias_name] = command_name
    write_aliases(aliases)
    click.echo(f"Alias added: {alias_name} -> {command_name}")


@alias.command("list", help="List all aliases")
def list_aliases():
    """列出所有别名"""
    aliases = read_aliases()
    if not aliases:
        click.echo("No aliases configured.")
        return

    click.echo("Aliases:")
    for alias_name, command_name in aliases.items():
        click.echo(f"  {alias_name} -> {command_name}")


@alias.command("remove", help="Remove an alias")
@click.argument("alias_name")
def remove_alias(alias_name: str):
    """移除一个别名"""
    aliases = read_aliases()
    if alias_name not in aliases:
        click.echo(f"Error: alias '{alias_name}' does not exist.", err=True)
        return

    del aliases[alias_name]
    write_aliases(aliases)
    click.echo(f"Alias removed: '{alias_name}'")
