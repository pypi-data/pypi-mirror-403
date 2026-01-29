#!/usr/bin/env python3
import click,random

from fcbyk import commands
from fcbyk.commands.alias import AliasedGroup
from fcbyk.cli_support import (
    version_callback, 
    print_aliases, 
    add_gui_options, 
    banner
)


@click.group(
    cls=AliasedGroup,
    context_settings=dict(
        help_option_names=['-h', '--help']
    ),
    invoke_without_command=True
)
@click.option(
    '--version', '-v', 
    is_flag=True, 
    callback=version_callback, 
    expose_value=False, 
    is_eager=True, 
    help='Show version and exit.'
)
@add_gui_options
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        banner_text = random.choice(banner)
        
        click.secho(banner_text, fg="white", dim=True)
        click.echo(ctx.get_help())      # 帮助信息
        print_aliases()                 # 打印别名，如果有


# 注册子命令
for cmd_name in commands.__all__:
    cli.add_command(getattr(commands, cmd_name))


if __name__ == "__main__":
    cli()
