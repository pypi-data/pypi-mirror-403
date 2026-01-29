import os
import logging
from flask import Flask, send_from_directory, make_response


# 禁用 Flask 的日志
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def create_spa(
    entry_html: str,
    root: str = "dist",
    page=None,
    cli_data=None,
) -> Flask:
    """
    Args:
        entry_html: SPA 入口文件，如 slide.html
        root: 静态文件根目录，默认 dist
        page: 前端路由列表
        cli_data: 附加到 app 的 CLI 数据
    Returns:
        Flask: 已配置的 Flask 应用实例
    """
    app = Flask(
        __name__,
        static_folder=f"{root}/assets",
        static_url_path="/assets"
    )

    dist_root = os.path.join(app.root_path, root)

    # SPA 入口
    @app.route("/")
    def index():
        response = make_response(send_from_directory(dist_root, entry_html))
        # 禁用缓存，防止切换应用时显示旧的 HTML
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # 前端路由列表 - 统一返回入口主页
    if page:
        for url in page:
            def view(entry_html=entry_html, dist_root=dist_root):
                response = make_response(send_from_directory(dist_root, entry_html))
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                return response

            # 保证每个路由的 endpoint 唯一
            endpoint = f"page_{url.strip('/').replace('/', '_') or 'root'}"
            app.add_url_rule(url, endpoint, view)

    if cli_data:
        app.cli_data = cli_data

    return app