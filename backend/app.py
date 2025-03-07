from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token
from flask_mail import Mail, Message
from models import User, Post, PostView, PostLike, PostComment, PostShare, Follow, CommentLike, CommentShare, CommentReply, Notification
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
from datetime import datetime, timedelta
import redis
import traceback
import pytz
from flask_migrate import Migrate
from redis import Redis
from sqlalchemy import func, distinct, text
from pytz import timezone
from sqlalchemy import or_
import jwt as pyjwt  # 重命名为pyjwt以避免冲突
from flask_socketio import SocketIO, emit
from fakeredis import FakeStrictRedis
from sqlalchemy import event  
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import os
import requests


app = Flask(__name__)
app.config.from_object(Config)

# CORS配置
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://www.searchsomething.top",
            "https://api.searchsomething.top",
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# 初始化扩展
jwt = JWTManager(app)
mail = Mail(app)

# Redis连接
try:
    redis_client = FakeStrictRedis(decode_responses=True)
    print("✓ Redis/缓存服务初始化成功")
except Exception as e:
    print(f"✗ 缓存服务初始化失败: {str(e)}")
    redis_client = None

# JWT配置
app.config['JWT_SECRET_KEY'] = 'yqw123456'  # 修改为你的密钥
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)  # token有效期1天/30天
app.config['JWT_ERROR_MESSAGE_KEY'] = 'message'  # 错误消息的键名
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

# 设置中国时区
CHINA_TZ = pytz.timezone('Asia/Shanghai')
# 添加一个格式化时间的辅助函数
def format_datetime(dt):
    if isinstance(dt, str):
        return dt
    # 确保时间是UTC+8
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    china_time = dt.astimezone(CHINA_TZ)
    return china_time.strftime('%Y-%m-%d %H:%M:%S')

# JWT错误处理
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': '认证已过期',
        'message': 'Token has expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'error': '无效的认证信息',
        'message': str(error)
    }), 401

@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({
        'error': '缺少认证信息',
        'message': str(error)
    }), 401

def generate_verification_code():
    """生成6位数字验证码"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code):
    """发送验证码邮件"""
    try:
        subject = '社区论坛 - 验证码'
        body = f'''
        您好！
        您的验证码是：{code}
        该验证码将在5分钟内有效。
        如果这不是您本人的操作，请忽略此邮件。
        
        此致
        社区论坛团队
        '''.encode('utf-8')
        
        msg = Message(
            subject=subject,
            sender=('社区论坛', app.config['MAIL_USERNAME']),
            recipients=[email],
            body=body
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"邮件发送失败：{str(e)}")
        return False

# 用户相关路由
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        verification_code = data.get('verificationCode')
        
        # 数据验证
        if not all([username, email, password, verification_code]):
            return jsonify({'error': '所有字段都是必填的'}), 400
            
        # 验证码验证
        stored_code = redis_client.get(f'verification:register:{email}')
        if not stored_code or stored_code != verification_code:
            return jsonify({'error': '验证码错误或已过期'}), 400
            
        # 检查用户名和邮箱是否已存在
        if User.get_by_username(username):
            return jsonify({'error': '用户名已存在'}), 400
            
        if User.get_by_email(email):
            return jsonify({'error': '邮箱已被注册'}), 400
            
        # 创建用户
        hashed_password = generate_password_hash(password)
        user_id = User.create(username, hashed_password, email)
        
        if user_id:
            # 删除验证码
            redis_client.delete(f'verification:register:{email}')
            
            # 创建token
            access_token = create_access_token(identity=str(user_id))
            
            return jsonify({
                'message': '注册成功',
                'token': access_token,
                'user': {
                    'id': user_id,
                    'username': username,
                    'email': email
                }
            }), 201
        
        return jsonify({'error': '注册失败'}), 500
        
    except Exception as e:
        print(f"注册失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '注册失败'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.get_by_username(username)
        if user and check_password_hash(user['password'], password):
            access_token = create_access_token(identity=str(user['id']))
            return jsonify({
                'token': access_token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email']
                }
            }), 200
            
        return jsonify({'error': '用户名或密码错误'}), 401
        
    except Exception as e:
        print(f"登录失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '登录失败'}), 500

@app.route('/api/send-verification-code', methods=['POST'])
def send_verification_code():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': '请提供邮箱地址'}), 400
            
        # 生成验证码
        code = generate_verification_code()
        
        # 发送验证码
        if send_verification_email(email, code):
            # 存储验证码，5分钟有效期
            redis_client.setex(f'verification:register:{email}', 300, code)
            return jsonify({'message': '验证码已发送'}), 200
        
        return jsonify({'error': '验证码发送失败'}), 500
        
    except Exception as e:
        print(f"发送验证码失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '发送验证码失败'}), 500

# 帖子相关路由
@app.route('/api/posts', methods=['GET'])
def get_posts():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        sort_by = request.args.get('sort_by', 'latest')
        
        posts = Post.get_all(page, per_page, sort_by)
        return jsonify({'posts': posts}), 200
        
    except Exception as e:
        print(f"获取帖子失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取帖子失败'}), 500

@app.route('/api/posts', methods=['POST'])
@jwt_required()
def create_post():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        title = data.get('title')
        content = data.get('content')
        
        if not all([title, content]):
            return jsonify({'error': '标题和内容不能为空'}), 400
            
        post_id = Post.create(title, content, user_id)
        if post_id:
            return jsonify({
                'message': '发帖成功',
                'post_id': post_id
            }), 201
            
        return jsonify({'error': '发帖失败'}), 500
        
    except Exception as e:
        print(f"发帖失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '发帖失败'}), 500

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        post = Post.get_by_id(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404
            
        return jsonify({'post': post}), 200
        
    except Exception as e:
        print(f"获取帖子详情失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取帖子详情失败'}), 500

# 评论相关路由
@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        comments = PostComment.get_by_post(post_id, page, per_page)
        return jsonify({'comments': comments}), 200
        
    except Exception as e:
        print(f"获取评论失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取评论失败'}), 500

@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(post_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({'error': '评论内容不能为空'}), 400
            
        comment_id = PostComment.create(post_id, user_id, content)
        if comment_id:
            # 创建通知
            post = Post.get_by_id(post_id)
            if post and post[0]['user_id'] != user_id:
                Notification.create(
                    recipient_id=post[0]['user_id'],
                    sender_id=user_id,
                    type='comment',
                    content=content,
                    post_id=post_id
                )
            
            return jsonify({
                'message': '评论成功',
                'comment_id': comment_id
            }), 201
            
        return jsonify({'error': '评论失败'}), 500
        
    except Exception as e:
        print(f"评论失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '评论失败'}), 500

# 点赞相关路由
@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@jwt_required()
def like_post(post_id):
    try:
        user_id = get_jwt_identity()
        
        result = PostLike.create(post_id, user_id)
        if result:
            # 创建通知
            post = Post.get_by_id(post_id)
            if post and post[0]['user_id'] != user_id:
                Notification.create(
                    recipient_id=post[0]['user_id'],
                    sender_id=user_id,
                    type='like',
                    post_id=post_id
                )
            
            return jsonify({'message': '点赞成功'}), 200
            
        return jsonify({'error': '点赞失败'}), 500
        
    except Exception as e:
        print(f"点赞失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '点赞失败'}), 500

@app.route('/api/posts/<int:post_id>/like', methods=['DELETE'])
@jwt_required()
def unlike_post(post_id):
    try:
        user_id = get_jwt_identity()
        
        result = PostLike.delete(post_id, user_id)
        if result:
            return jsonify({'message': '取消点赞成功'}), 200
            
        return jsonify({'error': '取消点赞失败'}), 500
        
    except Exception as e:
        print(f"取消点赞失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '取消点赞失败'}), 500

# 通知相关路由
@app.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        notifications = Notification.get_user_notifications(user_id, page, per_page)
        return jsonify({'notifications': notifications}), 200
        
    except Exception as e:
        print(f"获取通知失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取通知失败'}), 500

@app.route('/api/notifications/unread-count', methods=['GET'])
@jwt_required()
def get_unread_notifications_count():
    try:
        user_id = get_jwt_identity()
        count = Notification.get_unread_count(user_id)
        return jsonify({'count': count}), 200
        
    except Exception as e:
        print(f"获取未读通知数量失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取未读通知数量失败'}), 500

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_as_read(notification_id):
    try:
        result = Notification.mark_as_read(notification_id)
        if result:
            return jsonify({'message': '标记已读成功'}), 200
            
        return jsonify({'error': '标记已读失败'}), 500
        
    except Exception as e:
        print(f"标记通知已读失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '标记通知已读失败'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

















