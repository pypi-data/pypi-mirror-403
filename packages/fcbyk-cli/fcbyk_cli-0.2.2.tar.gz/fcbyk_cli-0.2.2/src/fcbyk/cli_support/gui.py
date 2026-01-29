"""GUI 相关功能支持"""
import click


HAS_GUI = False
show_gui = None
kill_gui = None

try:
    from fcbyk.gui.app import HAS_GUI, show_gui, kill_gui
except ImportError:
    HAS_GUI = False
    show_gui = None
    kill_gui = None


def launch_gui_callback(ctx, param, value):
    """启动 GUI 窗口"""
    if not value or ctx.resilient_parsing:
        return
    
    if not HAS_GUI:
        click.echo("Error: GUI feature is not installed.", err=True)
        click.echo("Please install GUI dependencies using:", err=True)
        click.echo("  pip install fcbyk-cli[gui]", err=True)
        click.echo("or", err=True)
        click.echo("  pip install PySide6", err=True)
        click.echo("For Python 3.6, you may need to install Qt5 bindings:", err=True)
        click.echo("  pip install PyQt5", err=True)
        ctx.exit(1)

    try:
        result = show_gui()
        if result == "activated":
            click.echo("GUI is already running, activated and brought to front.")
        else:
            click.echo("GUI is starting in a separate process...")
    except Exception as e:
        click.echo("Error starting GUI: {}".format(e), err=True)
        click.echo("If dependencies are installed but errors persist, try reinstalling:", err=True)
        click.echo("  pip install --force-reinstall fcbyk-cli[gui]", err=True)
        ctx.exit(1)

    ctx.exit()


def kill_gui_callback(ctx, param, value):
    """退出 GUI 进程（如果正在运行）"""
    if not value or ctx.resilient_parsing:
        return

    if not HAS_GUI:
        click.echo("Error: GUI feature is not installed.", err=True)
        click.echo("Please install GUI dependencies using:", err=True)
        click.echo("  pip install fcbyk-cli[gui]", err=True)
        ctx.exit(1)

    try:
        result = kill_gui(force=True)
        if result == "terminated":
            click.echo("GUI is unresponsive; process was force terminated.")
        elif result == "requested":
            click.echo("Quit request sent to GUI.")
        elif result == "not_running":
            click.echo("No running GUI instance found.")
        else:
            click.echo("Failed to quit GUI (cannot connect to singleton channel and no PID file found).", err=True)
            ctx.exit(1)
    except Exception as e:
        click.echo("Error quitting GUI: {}".format(e), err=True)
        click.echo("If the issue persists, try reinstalling GUI dependencies:", err=True)
        click.echo("  pip install --force-reinstall fcbyk-cli[gui]", err=True)
        ctx.exit(1)

    ctx.exit()


def add_gui_options(func):
    """动态注册 GUI 相关的 click 选项"""
    if HAS_GUI:
        func = click.option(
            '--kill-gui',
            is_flag=True,
            callback=kill_gui_callback,
            expose_value=False,
            is_eager=True,
            help='Kill/quit GUI process.'
        )(func)
        
        func = click.option(
            '--gui',
            is_flag=True,
            callback=launch_gui_callback,
            expose_value=False,
            is_eager=True,
            help='Launch GUI window.'
        )(func)
    return func