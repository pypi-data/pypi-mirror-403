"""
slide 控制器层
处理 Flask 路由、WebSocket 事件和 HTTP 请求/响应
"""
import os
from functools import wraps
from flask import request, session
from flask_socketio import SocketIO, disconnect

from fcbyk.web.app import create_spa
from fcbyk.web.R import R
from .service import SlideService


def create_slide_app(service: SlideService):
    """
    创建 slide Flask 应用
    
    Args:
        service: SlideService 实例
        
    Returns:
        (Flask应用, SocketIO实例)
    """
    app = create_spa("slide.html")
    app.secret_key = os.urandom(24)
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    app.slide_service = service
    register_routes(app, service)
    register_socketio_events(socketio, service)
    return app, socketio


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return R.error("Unauthorized", 401)
        return f(*args, **kwargs)
    return decorated_function


def require_socketio_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return
        return f(*args, **kwargs)
    return decorated_function


def register_routes(app, service: SlideService):
    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        password = data.get('password', '')
        if service.verify_password(password):
            session['authenticated'] = True
            return R.success({"authenticated": True}, "Login successful")
        else:
            return R.error("Invalid password", 401)
    
    @app.route('/api/check_auth', methods=['GET'])
    def check_auth():
        authenticated = bool(session.get('authenticated'))
        return R.success({"authenticated": authenticated})
    
    @app.route('/api/logout', methods=['POST'])
    def logout():
        session.clear()
        return R.success(message="Logged out")
    
    @app.route('/api/next', methods=['POST'])
    @require_auth
    def next_slide():
        success, error = service.next_slide()
        if success:
            return R.success({"action": "next"})
        else:
            return R.error(error or "next failed", 500)
    
    @app.route('/api/prev', methods=['POST'])
    @require_auth
    def prev_slide():
        success, error = service.prev_slide()
        if success:
            return R.success({"action": "prev"})
        else:
            return R.error(error or "prev failed", 500)
    
    @app.route('/api/home', methods=['POST'])
    @require_auth
    def home_slide():
        success, error = service.home_slide()
        if success:
            return R.success({"action": "home"})
        else:
            return R.error(error or "home failed", 500)
    
    @app.route('/api/end', methods=['POST'])
    @require_auth
    def end_slide():
        success, error = service.end_slide()
        if success:
            return R.success({"action": "end"})
        else:
            return R.error(error or "end failed", 500)
    
    @app.route('/api/mouse/move', methods=['POST'])
    @require_auth
    def mouse_move():
        data = request.get_json()
        dx = data.get('dx', 0)
        dy = data.get('dy', 0)
        success, error = service.move_mouse(dx, dy)
        if success:
            return R.success({"action": "move"})
        else:
            return R.error(error or "move failed", 500)
    
    @app.route('/api/mouse/click', methods=['POST'])
    @require_auth
    def mouse_click():
        success, error = service.click_mouse()
        if success:
            return R.success({"action": "click"})
        else:
            return R.error(error or "click failed", 500)
    
    @app.route('/api/mouse/down', methods=['POST'])
    @require_auth
    def mouse_down():
        success, error = service.mouse_down()
        if success:
            return R.success({"action": "down"})
        else:
            return R.error(error or "down failed", 500)
    
    @app.route('/api/mouse/up', methods=['POST'])
    @require_auth
    def mouse_up():
        success, error = service.mouse_up()
        if success:
            return R.success({"action": "up"})
        else:
            return R.error(error or "up failed", 500)
    
    @app.route('/api/mouse/rightclick', methods=['POST'])
    @require_auth
    def mouse_rightclick():
        success, error = service.right_click_mouse()
        if success:
            return R.success({"action": "rightclick"})
        else:
            return R.error(error or "rightclick failed", 500)
    
    @app.route('/api/mouse/scroll', methods=['POST'])
    @require_auth
    def mouse_scroll():
        data = request.get_json()
        dx = data.get('dx', 0)
        dy = data.get('dy', 0)
        success, error = service.scroll_mouse(dx, dy)
        if success:
            return R.success({"action": "scroll"})
        else:
            return R.error(error or "scroll failed", 500)


def register_socketio_events(socketio: SocketIO, service: SlideService):
    @socketio.on('connect')
    def handle_connect():
        if not session.get('authenticated'):
            disconnect()
            return False
    
    @socketio.on('mouse_move')
    @require_socketio_auth
    def handle_mouse_move(data):
        dx = data.get('dx', 0)
        dy = data.get('dy', 0)
        service.move_mouse(dx, dy)
    
    @socketio.on('mouse_click')
    @require_socketio_auth
    def handle_mouse_click():
        service.click_mouse()
    
    @socketio.on('mouse_down')
    @require_socketio_auth
    def handle_mouse_down():
        service.mouse_down()
    
    @socketio.on('mouse_up')
    @require_socketio_auth
    def handle_mouse_up():
        service.mouse_up()
    
    @socketio.on('mouse_rightclick')
    @require_socketio_auth
    def handle_mouse_rightclick():
        service.right_click_mouse()
    
    @socketio.on('mouse_scroll')
    @require_socketio_auth
    def handle_mouse_scroll(data):
        dx = data.get('dx', 0)
        dy = data.get('dy', 0)
        service.scroll_mouse(dx, dy)
    
    @socketio.on('ping_server')
    @require_socketio_auth
    def handle_ping_server():
        return 'pong'
