"""
pick controller 层

负责 Flask 路由注册、请求解析、调用 service 并返回响应。

常量:
- config_file: 配置文件路径
- SERVER_SESSION_ID: 服务器会话 ID（用于区分不同服务器实例）
- default_config: 默认配置

全局变量:
- app: Flask 应用实例（SPA 模式，支持 /admin 和 /f 路由）
- files_mode_root: 文件模式根目录（None 表示列表抽奖模式）
- ADMIN_PASSWORD: 管理员密码
- service: PickService 实例

函数:
- _get_client_ip() -> str: 获取客户端 IP（优先 X-Forwarded-For）
- start_web_server(port, no_browser, files_root, admin_password): 启动抽奖 Web 服务器

路由:
- /api/info: 获取启动信息（是否文件模式）
- /api/items: 获取当前配置中的抽奖项
- /api/files: 列出文件列表并返回当前抽奖状态
- /api/files/pick: 从文件列表随机抽取一个文件（支持兑换码和 IP 两种模式）
- /api/files/result/<code>: 查询兑换码的抽奖结果（用于页面刷新后恢复）
- /api/files/download/<path:filename>: 下载指定文件（带路径安全检查）
- /api/pick: 从配置列表中随机抽取一项
- /api/admin/login: 管理员登录验证
- /api/admin/codes: 获取兑换码列表（需要管理员权限）
- /api/admin/codes/add: 新增兑换码（需要管理员权限）
"""

import os
import click
import socket
import webbrowser
import uuid
from typing import Optional
from flask import jsonify, request, send_file, url_for, Response
from fcbyk.utils import storage
from datetime import datetime
from .service import PickService
from ...web.app import create_spa

# 持久化数据文件：~/.fcbyk/data/pick_data.json
config_file = storage.get_path('pick_data.json', subdir='data')
SERVER_SESSION_ID = str(uuid.uuid4())

default_config = {
    'items': []
}

# Flask 应用（SPA 模式，支持 /admin 和 /f 路由）
app = create_spa(entry_html="pick.html", page=["/admin", "/f"])

# Web 模式状态
files_mode_root = None  # 指定目录或单文件路径（None 表示列表抽奖模式）
ADMIN_PASSWORD = None

# 服务实例
service = PickService(config_file, default_config)


def _require_admin_auth():
    if not ADMIN_PASSWORD:
        return jsonify({'error': 'admin password not set'}), 500

    password = request.headers.get('X-Admin-Password', '')
    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'unauthorized'}), 401

    return None


@app.route('/api/info')
def api_info():
    """返回启动信息接口"""
    return jsonify({
        'files_mode': files_mode_root is not None,
    })


@app.route('/api/items')
def api_items():
    """返回当前配置中的抽奖项"""
    # 配置文件格式错误时，不直接让服务崩溃，回退到空列表
    data = storage.load_json(config_file, default=default_config, create_if_missing=True, strict=False)
    if not isinstance(data, dict):
        data = default_config
    items = data.get('items', [])
    if not isinstance(items, list):
        items = []
    return jsonify({'items': items})


def _get_client_ip():
    """获取客户端 IP，优先 X-Forwarded-For（支持代理场景）"""
    xff = request.headers.get('X-Forwarded-For', '')
    if xff:
        # X-Forwarded-For 可能包含多个 IP，取第一个
        return xff.split(',')[0].strip()
    return request.remote_addr or 'unknown'


@app.route('/api/files', methods=['GET'])
def api_files():
    """列出文件列表并返回当前抽奖状态"""
    if not files_mode_root:
        return jsonify({'error': 'files mode not enabled'}), 400

    files = service.list_files(files_mode_root)
    resp = {
        'files': [{'name': f['name'], 'size': f['size']} for f in files],
    }

    resp['session_id'] = SERVER_SESSION_ID

    # 兑换码模式优先，否则使用 IP 限制模式
    if service.redeem_codes:
        total = len(service.redeem_codes)
        used = sum(1 for v in service.redeem_codes.values() if v)
        resp.update({
            'mode': 'code',
            'total_codes': total,
            'used_codes': used,
            'draw_count': used,
            'limit_per_code': 1,
        })
    else:
        client_ip = _get_client_ip()
        picked = service.ip_draw_records.get(client_ip)
        resp.update({
            'mode': 'ip',
            'draw_count': len(service.ip_draw_records),
            'ip_picked': picked,
            'limit_per_ip': 1,
        })
    return jsonify(resp)


@app.route('/api/files/pick', methods=['POST'])
def api_files_pick():
    """从文件列表随机抽取一个文件

    - 如果配置了兑换码：每个兑换码仅能成功抽取一次
    - 否则回退到旧逻辑：每个 IP 限制一次
    """
    if not files_mode_root:
        return jsonify({'error': 'files mode not enabled'}), 400

    files = service.list_files(files_mode_root)
    if not files:
        return jsonify({'error': 'no files available'}), 400

    client_ip = _get_client_ip()

    # 兑换码模式优先
    if service.redeem_codes:
        data = request.get_json(silent=True) or {}
        code = str(data.get('code', '')).strip().upper()
        if not code:
            return jsonify({'error': '请输入兑换码'}), 400
        if code not in service.redeem_codes:
            return jsonify({'error': '兑换码无效'}), 400
        if service.redeem_codes[code]:
            return jsonify({'error': '兑换码已被使用'}), 429

        # 过滤掉当前 IP 已抽中过的文件
        used_by_ip = service.ip_file_history.get(client_ip, set())
        candidates = [f for f in files if f['name'] not in used_by_ip]
        if not candidates:
            return jsonify({'error': '本 IP 已无可抽取的文件'}), 400

        selected = service.pick_file(candidates)
        service.redeem_codes[code] = True
        # 持久化标记已用
        try:
            service.mark_redeem_code_used_in_storage(code)
        except Exception:
            pass
        service.ip_file_history.setdefault(client_ip, set()).add(selected['name'])
        used = sum(1 for v in service.redeem_codes.values() if v)
        download_url = url_for('download_file', filename=selected['name'], _external=True)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 保存兑换码的抽奖结果，用于页面刷新后恢复
        service.code_results[code] = {
            'file': {'name': selected['name'], 'size': selected['size']},
            'download_url': download_url,
            'timestamp': timestamp,
        }
        click.echo(
            "[%s] %s draw file: %s successfully, redeem code: %s used, remaining redeem codes: %s"
            % (timestamp, client_ip, selected['name'], code, (len(service.redeem_codes) - used))
        )
        return jsonify({
            'file': {'name': selected['name'], 'size': selected['size']},
            'download_url': download_url,
            'mode': 'code',
            'draw_count': used,
            'total_codes': len(service.redeem_codes),
            'used_codes': used,
            'code': code,
        })

    # IP 限制模式
    if client_ip in service.ip_draw_records:
        return jsonify({'error': 'already picked', 'picked': service.ip_draw_records[client_ip]}), 429
    used_by_ip = service.ip_file_history.get(client_ip, set())
    candidates = [f for f in files if f['name'] not in used_by_ip]
    if not candidates:
        return jsonify({'error': '本 IP 已无可抽取的文件'}), 400

    selected = service.pick_file(candidates)
    service.ip_draw_records[client_ip] = selected['name']
    service.ip_file_history.setdefault(client_ip, set()).add(selected['name'])
    download_url = url_for('download_file', filename=selected['name'], _external=True)
    return jsonify({
        'file': {'name': selected['name'], 'size': selected['size']},
        'download_url': download_url,
        'mode': 'ip',
        'draw_count': len(service.ip_draw_records),
        'ip_picked': selected['name']
    })


@app.route('/api/files/result/<code>', methods=['GET'])
def api_files_result(code):
    """查询兑换码的抽奖结果（用于页面刷新后恢复）"""
    if not files_mode_root:
        return jsonify({'error': 'files mode not enabled'}), 400
    code = str(code).strip().upper()
    if code not in service.code_results:
        return jsonify({'error': '兑换码未使用或结果不存在'}), 404
    result = service.code_results[code]
    return jsonify({
        'code': code,
        'file': result['file'],
        'download_url': result['download_url'],
        'timestamp': result['timestamp'],
    })


@app.route('/api/files/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """下载指定文件，受限于文件模式根目录（带路径安全检查）"""
    if not files_mode_root:
        return jsonify({'error': 'files mode not enabled'}), 400

    if os.path.isfile(files_mode_root):
        if filename != os.path.basename(files_mode_root):
            return jsonify({'error': 'file not found'}), 404
        return send_file(files_mode_root, as_attachment=True, download_name=filename)

    # 防止路径穿越攻击
    safe_root = os.path.abspath(files_mode_root)
    target_path = os.path.abspath(os.path.join(safe_root, filename))
    if not target_path.startswith(safe_root + os.sep) and target_path != safe_root:
        return jsonify({'error': 'invalid path'}), 400
    if not os.path.isfile(target_path):
        return jsonify({'error': 'file not found'}), 404
    return send_file(target_path, as_attachment=True, download_name=os.path.basename(target_path))


@app.route('/api/pick', methods=['POST'])
def api_pick_item():
    """从配置列表中随机抽取一项"""
    data = storage.load_json(config_file, default=default_config, create_if_missing=True, strict=False)
    if not isinstance(data, dict):
        data = default_config
    items = data.get('items', [])
    if not isinstance(items, list) or not items:
        return jsonify({'error': 'no items available'}), 400
    selected = service.pick_random_item(items)
    return jsonify({'item': selected, 'items': items})


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    if not ADMIN_PASSWORD:
        return jsonify({'error': 'admin password not set'}), 500

    data = request.get_json(silent=True) or {}
    password = str(data.get('password', ''))

    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'invalid password'}), 401

    return jsonify({'success': True})


@app.route('/api/admin/codes', methods=['GET'])
def admin_codes():
    auth = _require_admin_auth()
    if auth is not None:
        return auth

    codes_list = [{'code': code, 'used': used} for code, used in service.redeem_codes.items()]
    total = len(codes_list)
    used = sum(1 for c in codes_list if c['used'])
    left = total - used

    return jsonify({
        'codes': codes_list,
        'total_codes': total,   # 总数
        'used_codes': used,     # 已用
        'left_codes': left      # 剩余
    })


@app.route('/api/admin/codes/add', methods=['POST'])
def admin_codes_add():
    """新增兑换码"""
    auth = _require_admin_auth()
    if auth is not None:
        return auth

    data = request.get_json(silent=True) or {}
    code = str(data.get('code', '')).strip().upper()

    if not code:
        return jsonify({'error': '兑换码不能为空'}), 400

    if not all(c.isalnum() for c in code):
        return jsonify({'error': '兑换码只能包含字母和数字'}), 400

    if code in service.redeem_codes:
        return jsonify({'error': '兑换码已存在'}), 400

    # 内存态是本次 server 运行的权威来源；持久化仅用于 files 模式下的跨次启动恢复。
    # 因此：内存中不存在时应允许新增成功；即便持久化层提示已存在，也不应让 API 失败。
    service.redeem_codes[code] = False
    try:
        service.add_redeem_code_to_storage(code)
    except Exception:
        # 持久化失败不影响管理员在当前会话内添加兑换码
        pass
    click.echo("[%s] Admin added new redeem code: %s" % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), code))

    return jsonify({
        'success': True,
        'code': code,
        'message': '成功新增兑换码: %s' % code
    })


@app.route('/api/admin/codes/gen', methods=['POST'])
def admin_codes_gen():
    """批量生成兑换码（单次最多 100）。"""
    auth = _require_admin_auth()
    if auth is not None:
        return auth

    data = request.get_json(silent=True) or {}
    count = data.get('count', None)

    try:
        n = int(count)
    except Exception:
        return jsonify({'error': 'count must be int'}), 400

    if n <= 0:
        return jsonify({'error': 'count must be > 0'}), 400

    if n > 100:
        return jsonify({'error': 'count max is 100'}), 400

    new_codes = []
    try:
        new_codes = service.generate_and_add_redeem_codes_to_storage(n)
    except Exception as e:
        return jsonify({'error': 'failed to generate codes: %s' % e}), 500

    click.echo(
        "[%s] Admin generated redeem codes: requested=%d generated=%d"
        % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), n, len(new_codes))
    )

    return jsonify({
        'success': True,
        'requested': n,
        'generated_count': len(new_codes),
        'generated': new_codes,
    })


@app.route('/api/admin/codes/<code>', methods=['DELETE'])
def admin_codes_delete(code):
    """删除单个兑换码。"""
    auth = _require_admin_auth()
    if auth is not None:
        return auth

    code = str(code or '').strip().upper()
    if not code:
        return jsonify({'error': 'invalid code'}), 400

    if code not in service.redeem_codes:
        # 内存里都没有，直接视为不存在
        return jsonify({'error': 'code not found'}), 404

    was_used = bool(service.redeem_codes.get(code))

    # 先删内存
    try:
        del service.redeem_codes[code]
    except Exception:
        pass

    # 再删持久化
    try:
        service.delete_redeem_code_from_storage(code)
    except Exception:
        pass

    # 同时清理结果缓存（避免前端还能查到旧结果）
    try:
        if code in service.code_results:
            del service.code_results[code]
    except Exception:
        pass

    click.echo("[%s] Admin deleted redeem code: %s" % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), code))

    return jsonify({'success': True, 'code': code, 'was_used': was_used})


@app.route('/api/admin/codes/clear', methods=['POST'])
def admin_codes_clear():
    """清空所有兑换码。"""
    auth = _require_admin_auth()
    if auth is not None:
        return auth

    data = request.get_json(silent=True) or {}
    confirm = bool(data.get('confirm'))
    if not confirm:
        return jsonify({'error': 'confirm required'}), 400

    before = len(service.redeem_codes)

    # 清内存
    service.redeem_codes = {}
    service.code_results = {}

    # 清持久化
    try:
        service.clear_redeem_codes_in_storage()
    except Exception:
        pass

    click.echo("[%s] Admin cleared redeem codes: %d" % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), before))

    return jsonify({'success': True, 'cleared': before})


@app.route('/api/admin/codes/<code>/reset', methods=['POST'])
def admin_codes_reset(code):
    """将单个兑换码重置为未使用。"""
    auth = _require_admin_auth()
    if auth is not None:
        return auth

    code = str(code or '').strip().upper()
    if not code:
        return jsonify({'error': 'invalid code'}), 400

    if code not in service.redeem_codes:
        return jsonify({'error': 'code not found'}), 404

    # 内存重置
    service.redeem_codes[code] = False

    # 持久化重置
    ok = None
    try:
        ok = service.reset_redeem_code_unused_in_storage(code)
    except Exception:
        ok = None

    # 清理结果缓存：reset 后不应再能查询到上一次抽奖结果
    try:
        if code in service.code_results:
            del service.code_results[code]
    except Exception:
        pass

    click.echo("[%s] Admin reset redeem code to unused: %s" % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), code))

    return jsonify({'success': True, 'code': code, 'storage_reset': bool(ok)})


@app.route('/api/admin/codes/export', methods=['GET'])
def admin_codes_export():
    """导出兑换码。

    Query:
        - only_unused=1: 仅导出未使用兑换码
        - format=text: 返回纯文本，每行一个兑换码

    默认返回 JSON（兼容旧调用方）。
    """
    auth = _require_admin_auth()
    if auth is not None:
        return auth

    only_unused = str(request.args.get('only_unused', '')).strip() == '1'
    fmt = str(request.args.get('format', '')).strip().lower()

    try:
        exported = service.export_redeem_codes_from_storage(only_unused=only_unused)
    except Exception as e:
        return jsonify({'error': 'export failed: %s' % e}), 500

    # 纯文本导出：每行一个 code
    if fmt == 'text':
        lines = []
        for item in exported:
            c = item.get('code')
            if c:
                lines.append(str(c))
        text = "\n".join(lines)
        return Response(text, mimetype='text/plain; charset=utf-8')

    total = len(exported)
    used = sum(1 for c in exported if c.get('used'))

    return jsonify({
        'codes': exported,
        'total_codes': total,
        'used_codes': used,
        'left_codes': total - used,
    })


def start_web_server(
    port: int,
    no_browser: bool,
    files_root: Optional[str] = None,
    admin_password: Optional[str] = None,
) -> None:
    """启动抽奖 Web 服务器"""
    global files_mode_root, ADMIN_PASSWORD
    ADMIN_PASSWORD = admin_password
    files_mode_root = os.path.abspath(files_root) if files_root else None

    service.reset_state()

    # files 模式下使用持久化兑换码
    if files_mode_root:
        service.redeem_codes = service.load_redeem_codes_from_storage()
        # 初始化体验：如果兑换码为空，则自动生成 5 个（避免用户进入页面后无法使用兑换码模式）
        if not service.redeem_codes:
            try:
                new_codes = service.generate_and_add_redeem_codes_to_storage(5)
                if new_codes:
                    click.echo(" Auto-generated %d redeem codes: %s" % (len(new_codes), ", ".join(new_codes)))
            except Exception:
                pass

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    url_local = f"http://127.0.0.1:{port}"
    url_network = f"http://{local_ip}:{port}"
    click.echo()
    click.echo(f" Local URL: {url_local}")
    click.echo(f" Network URL: {url_network}")
    click.echo(f" Admin URL: {url_network}/admin")
    if files_mode_root:
        click.echo(f" Files root: {files_mode_root}")
    if not no_browser:
        try:
            webbrowser.open(url_network)
            click.echo(" Attempted to open picker page in browser (network URL)")
        except Exception:
            click.echo(" Note: Could not auto-open browser, please visit the URL above")
    click.echo()
    from waitress import serve
    serve(app, host='0.0.0.0', port=port)
