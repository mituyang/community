from flask import Flask, request, jsonify, current_app
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token
from flask_mail import Mail, Message
from models import db, User, Post, PostView, PostLike, PostComment, PostShare, Follow, CommentLike, CommentShare, CommentReply, Notification
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

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://www.searchsomething.top",
            "https://api.searchsomething.top",
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Content-Type", 
            "Authorization",
            "authorization",  # 添加小写的 authorization
            "Access-Control-Allow-Headers",
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods"
        ],
        "expose_headers": ["Authorization"],
        "supports_credentials": True
    }
})

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# 初始化Mail
mail = Mail()
mail.init_app(app)

# Redis连接
try:
        # 在生产环境中使用其他缓存解决方案
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
    print("Token expired")  # 调试日志
    return jsonify({
        'error': '认证已过期',
        'message': 'Token has expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print("Invalid token:", error)  # 调试日志
    return jsonify({
        'error': '无效的认证信息',
        'message': str(error)
    }), 401

@jwt.unauthorized_loader
def unauthorized_callback(error):
    print("Unauthorized:", error)  # 调试日志
    return jsonify({
        'error': '缺少认证信息',
        'message': str(error)
    }), 401

def generate_verification_code():
    """生成6位数字验证码"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code, is_register=False):
    """发送验证码邮件"""
    try:
        with app.app_context():
            print(f"尝试发送邮件到 {email}，验证码：{code}")
            
            subject = '社区论坛 - 验证码'
            body = f'''
            您好！

            您的验证码是：{code}

            该验证码将在5分钟内有效，请尽快完成操作。

            如果这不是您本人的操作，请忽略此邮件。

            此致
            社区论坛团队
            '''.encode('utf-8')
            
            html = f'''
            <p>您好！</p>
            <p>您的验证码是：<strong>{code}</strong></p>
            <p>该验证码将在5分钟内有效，请尽快完成操作。</p>
            <p>如果这不是您本人的操作，请忽略此邮件。</p>
            <p>此致<br>社区论坛团队</p>
            '''

            msg = Message(
                subject=subject,
                sender=('社区论坛', app.config['MAIL_USERNAME']),
                recipients=[email],
                body=body,
                html=html
            )
            
            print("准备发送邮件...")
            mail.send(msg)
            print("邮件发送成功")
            return True
            
    except Exception as e:
        print(f"邮件发送失败，错误：{str(e)}")
        traceback.print_exc()
        return False

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
            
        # 验证用户名长度
        if len(username) < 3 or len(username) > 20:
            return jsonify({'error': '用户名长度必须在3-20个字符之间'}), 400
            
        # 验证密码长度
        if len(password) < 6:
            return jsonify({'error': '密码长度不能少于6个字符'}), 400
            
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'error': '该用户名已被使用'}), 400
            
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify({'error': '该邮箱已被注册'}), 400
            
        # 验证验证码
        verification_key = f'verification:register:{email}'
        stored_code = redis_client.get(verification_key)
        
        # 调试信息
        print(f"验证码检查 - Email: {email}")
        print(f"存储的验证码: {stored_code}")
        print(f"提交的验证码: {verification_code}")
        
        if not stored_code:
            return jsonify({'error': '验证码已过期'}), 400
            
        # 移除 decode() 调用，直接比较字符串
        if stored_code != verification_code:
            return jsonify({'error': '验证码错误'}), 400
            
        # 创建新用户
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            created_at=datetime.now(CHINA_TZ)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # 删除已使用的验证码
        redis_client.delete(verification_key)
        
        return jsonify({
            'message': '注册成功',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email
            }
        }), 201
        
    except Exception as e:
        print(f"注册失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': '注册失败'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')

        # 查询用户（支持用户名或邮箱登录）
        user = User.query.filter(
            or_(
                User.username == username_or_email,
                User.email == username_or_email
            )
        ).first()
        
        if user and check_password_hash(user.password, password):
            # 将用户ID转换为字符串
            access_token = create_access_token(identity=str(user.id))
            return jsonify({
                'token': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username
                }
            }), 200
            
        return jsonify({'error': '用户名/邮箱或密码错误'}), 401
        
    except Exception as e:
        print(f"登录失败: {str(e)}")
        return jsonify({'error': '登录失败，请稍后重试'}), 500

@app.route('/api/send-verification-code', methods=['POST'])
def send_verification_code():
    """重置密码的验证码发送"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': '请提供邮箱地址'}), 400

        # 检查邮箱是否存在
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': '该邮箱未注册'}), 404
        
        # 生成验证码
        code = generate_verification_code()
        print(f"生成的验证码: {code} 用于邮箱: {email}")  # 调试信息
        
        # 发送验证码邮件
        if not send_verification_email(email, code):
            return jsonify({'error': '验证码发送失败，请稍后重试'}), 500
        
        # 将验证码存储到Redis，设置5分钟过期
        redis_client.setex(f'reset_code:{email}', 300, code)
        print(f"验证码已存储到Redis, key: reset_code:{email}")  # 调试信息
        
        return jsonify({'message': '验证码已发送到您的邮箱'}), 200
        
    except Exception as e:
        print(f"处理验证码请求时出错：{str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/api/send-register-code', methods=['POST'])
def send_register_code():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': '邮箱不能为空'}), 400
            
        # 检查邮箱是否已被注册
        if User.query.filter_by(email=email).first():
            return jsonify({'error': '该邮箱已被注册'}), 400
            
        # 生成验证码
        code = generate_verification_code()
        
        # 存储验证码到 Redis，设置5分钟过期
        verification_key = f'verification:register:{email}'
        redis_client.setex(verification_key, 300, code)
        
        # 发送验证码邮件
        if not send_verification_email(email, code):
            return jsonify({'error': '验证码发送失败'}), 500
            
        # 调试信息
        print(f"发送注册验证码 - Email: {email}, Code: {code}, Key: {verification_key}")
        
        return jsonify({'message': '验证码已发送'}), 200
            
    except Exception as e:
        print(f"发送验证码失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '发送验证码失败'}), 500

@app.route('/api/verify-code', methods=['POST'])
def verify_code():
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')
        
        print(f"验证请求 - 邮箱: {email}, 验证码: {code}")  # 调试信息
        
        if not email or not code:
            return jsonify({'error': '邮箱和验证码不能为空'}), 400
            
        # 获取存储的验证码
        stored_code = redis_client.get(f'reset_code:{email}')
        print(f"存储的验证码: {stored_code}")  # 调试信息
        
        if not stored_code:
            return jsonify({'error': '验证码已过期'}), 400
            
        stored_code = stored_code.decode()
        print(f"比较验证码 - 输入: {code}, 存储: {stored_code}")  # 调试信息
        
        if code != stored_code:
            return jsonify({'error': '验证码错误'}), 400
            
        # 验证成功后不要立即删除验证码，而是延长其有效期
        redis_client.expire(f'reset_code:{email}', 300)  # 延长5分钟
        
        return jsonify({'message': '验证成功'}), 200
        
    except Exception as e:
        print(f"验证码验证失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '验证失败'}), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('verificationCode')
        new_password = data.get('newPassword')
        
        print(f"重置密码请求 - 邮箱: {email}, 验证码: {code}")  # 调试信息
        
        if not all([email, code, new_password]):
            return jsonify({'error': '请提供所有必要信息'}), 400
        
        # 验证验证码
        stored_code = redis_client.get(f'reset_code:{email}')
        print(f"存储的验证码: {stored_code}")  # 调试信息
        
        if not stored_code:
            return jsonify({'error': '验证码已过期'}), 400
            
        stored_code = stored_code.decode()
        print(f"比较验证码 - 输入: {code}, 存储: {stored_code}")  # 调试信息
        
        if code != stored_code:
            return jsonify({'error': '验证码错误'}), 400
        
        # 更新密码
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        user.password = generate_password_hash(new_password)
        db.session.commit()
        
        # 密码重置成功后再删除验证码
        redis_client.delete(f'reset_code:{email}')
        
        return jsonify({'message': '密码重置成功'}), 200
        
    except Exception as e:
        print(f"重置密码失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/api/check-username', methods=['POST'])
def check_username():
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'error': '请输入用户名'}), 400
            
        # 检查用户名是否已存在
        user = User.query.filter_by(username=username).first()
        if user:
            return jsonify({'error': '该用户名已被注册'}), 400
            
        return jsonify({'message': '用户名可用'}), 200
        
    except Exception as e:
        print(f"检查用户名失败: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

# 获取帖子列表
@app.route('/api/posts', methods=['GET', 'POST'])
@jwt_required(optional=True)
def handle_posts():
    if request.method == 'GET':
        try:
            current_user_id = get_jwt_identity()
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('page_size', 10, type=int)
            sort_by = request.args.get('sort_by', 'latest')
            
            # 使用子查询获取统计数据
            posts_query = db.session.query(
                Post,
                User.username.label('author'),
                db.session.query(func.count(PostLike.id))
                    .filter(PostLike.post_id == Post.id)
                    .label('like_count'),
                db.session.query(func.count(PostComment.id))
                    .filter(PostComment.post_id == Post.id)
                    .label('comment_count'),
                db.session.query(func.count(PostShare.id))
                    .filter(PostShare.post_id == Post.id)
                    .label('share_count'),
                db.session.query(func.coalesce(func.sum(PostView.view_count), 0))
                    .filter(PostView.post_id == Post.id)
                    .label('view_count')
            ).join(
                User, Post.user_id == User.id
            )
            
            # 根据排序参数决定排序方式
            if sort_by == 'hot':
                posts_query = posts_query.order_by(
                    text('view_count DESC'),
                    Post.created_at.desc()
                )
            else:  # 默认按最新排序
                posts_query = posts_query.order_by(Post.created_at.desc())
            
            # 添加调试日志
            print(f"SQL Query: {posts_query}")
            
            pagination = posts_query.paginate(page=page, per_page=per_page)
            
            posts_data = []
            for item in pagination.items:
                post_data = {
                    'id': item.Post.id,
                    'title': item.Post.title,
                    'content': item.Post.content,
                    'author': item.author,
                    'user_id': item.Post.user_id,
                    'created_at': item.Post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'like_count': int(item.like_count),
                    'comment_count': int(item.comment_count),
                    'share_count': int(item.share_count),
                    'view_count': int(item.view_count)
                }
                
                if current_user_id:
                    post_data.update({
                        'isLiked': db.session.query(PostLike).filter_by(
                            post_id=item.Post.id,
                            user_id=current_user_id
                        ).first() is not None,
                        'isCommented': db.session.query(PostComment).filter_by(
                            post_id=item.Post.id,
                            user_id=current_user_id
                        ).first() is not None,
                        'isShared': db.session.query(PostShare).filter_by(
                            post_id=item.Post.id,
                            user_id=current_user_id
                        ).first() is not None
                    })
                
                posts_data.append(post_data)
            
            # 添加调试日志
            print(f"返回帖子数量: {len(posts_data)}")
            print(f"第一篇帖子: {posts_data[0] if posts_data else None}")
            
            return jsonify({
                'posts': posts_data,
                'total': pagination.total
            }), 200
            
        except Exception as e:
            print(f"获取帖子列表失败: {str(e)}")
            traceback.print_exc()
            return jsonify({'error': '获取帖子列表失败'}), 500
            
    elif request.method == 'POST':
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            if not data or 'title' not in data or 'content' not in data:
                return jsonify({'error': '标题和内容不能为空'}), 400
                
            title = data['title'].strip()
            content = data['content'].strip()
            
            if len(title) < 2 or len(title) > 100:
                return jsonify({'error': '标题长度必须在2-100个字符之间'}), 400
            if len(content) < 2 or len(content) > 1000:
                return jsonify({'error': '内容长度必须在2-1000个字符之间'}), 400
            
            # 使用北京时间创建帖子
            beijing_tz = pytz.timezone('Asia/Shanghai')
            current_time = datetime.now(beijing_tz)
            
            new_post = Post(
                title=title,
                content=content,
                user_id=current_user_id,
                created_at=current_time
            )
            
            db.session.add(new_post)
            db.session.commit()
            
            # 获取用户信息
            user = User.query.get(current_user_id)
            
            # 返回完整的帖子信息
            return jsonify({
                'id': new_post.id,
                'title': new_post.title,
                'content': new_post.content,
                'user_id': current_user_id,
                'author': user.username,
                'created_at': new_post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'like_count': 0,
                'comment_count': 0,
                'share_count': 0,
                'view_count': 0,
                'isLiked': False,
                'isCommented': False,
                'isShared': False
            }), 201
            
        except Exception as e:
            print(f"发布帖子失败: {str(e)}")
            traceback.print_exc()
            db.session.rollback()
            return jsonify({'error': '发布失败'}), 500

@app.route('/api/community-stats', methods=['GET'])
def get_community_stats():
    try:
        # 获取用户总数
        user_count = User.query.count()
        # 获取帖子总数
        post_count = Post.query.count()
        
        print(f"社区统计 - 用户数: {user_count}, 帖子数: {post_count}")  # 添加调试日志
        
        return jsonify({
            'userCount': user_count,
            'postCount': post_count
        }), 200
        
    except Exception as e:
        print(f"获取社区统计信息失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取统计信息失败'}), 500

# 测试认证路由
@app.route('/api/test-auth', methods=['GET'])
@jwt_required()
def test_auth():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户不存在'
            }), 404
            
        return jsonify({
            'status': 'success',
            'message': '认证成功',
            'user': {
                'id': user.id,
                'username': user.username
            }
        }), 200
    except Exception as e:
        print(f"认证测试失败: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': '认证失败'
        }), 500

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        # 查询帖子
        post = Post.query.get(post_id)
        
        if not post:
            return jsonify({'error': '帖子不存在'}), 404
            
        # 获取作者信息
        author = User.query.get(post.user_id)
        
        if not author:
            return jsonify({'error': '作者信息不存在'}), 404
            
        # 检查当前用户是否已登录
        current_user_id = None
        is_liked = False
        is_shared = False
        
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                # 使用pyjwt库而不是Flask-JWT-Extended的jwt对象
                payload = pyjwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                current_user_id = payload['sub']
                
                # 输出详细信息用于调试
                print(f"成功解析token - 用户ID: {current_user_id}")
                
                # 检查是否点赞
                like = PostLike.query.filter_by(
                    user_id=current_user_id,
                    post_id=post_id
                ).first()
                is_liked = like is not None
                
                # 检查是否转发
                share = PostShare.query.filter_by(
                    user_id=current_user_id,
                    post_id=post_id
                ).first()
                is_shared = share is not None
                
                print(f"用户{current_user_id}获取帖子{post_id}：点赞状态={is_liked}，转发状态={is_shared}")
                
            except Exception as e:
                print(f"Token解析失败: {str(e)}")
                traceback.print_exc()
        else:
            print("请求中没有Authorization头或格式不正确")
        
        # 获取统计数据
        view_count = db.session.query(func.count(distinct(PostView.id))).filter(PostView.post_id == post_id).scalar() or 0
        like_count = db.session.query(func.count(distinct(PostLike.id))).filter(PostLike.post_id == post_id).scalar() or 0
        comment_count = db.session.query(func.count(distinct(PostComment.id))).filter(PostComment.post_id == post_id).scalar() or 0
        share_count = db.session.query(func.count(distinct(PostShare.id))).filter(PostShare.post_id == post_id).scalar() or 0
        
        # 构建帖子数据
        post_data = {
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'share_count': share_count,
            'author': {
                'id': author.id,
                'username': author.username,
                'avatar': author.avatar if hasattr(author, 'avatar') else None
            },
            'isLiked': is_liked,
            'isShared': is_shared
        }
        
        print(f"返回前的数据验证: isLiked={post_data['isLiked']}, isShared={post_data['isShared']}")
        return jsonify(post_data), 200
        
    except Exception as e:
        print(f"获取帖子详情失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取帖子详情失败: ' + str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get_or_404(current_user_id)
        
        # 格式化生日日期
        birthday = user.birthday.strftime('%Y-%m-%d') if user.birthday else None
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'nickname': user.nickname,
                'avatar': user.avatar,
                'gender': user.gender,
                'birthday': birthday,
                'location': user.location,
                'website': user.website,
                'bio': user.bio,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200
        
    except Exception as e:
        print(f"获取用户信息失败: {str(e)}")
        return jsonify({'error': '获取用户信息失败'}), 500

@app.route('/api/user/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get_or_404(current_user_id)
        data = request.get_json()

        # 需要验证码的字段
        if data.get('username') != user.username or data.get('email') != user.email:
            verification_code = data.get('verificationCode')
            new_email_code = data.get('newEmailCode')
            
            # 验证当前邮箱验证码
            current_email_key = f'verification:current_email:{current_user_id}:{user.email}'
            stored_code = redis_client.get(current_email_key)
            
            if not stored_code or stored_code.decode() != verification_code:
                return jsonify({'error': '验证码无效或已过期'}), 400

            # 验证用户名
            if data.get('username') != user.username:
                existing_user = User.query.filter_by(username=data['username']).first()
                if existing_user:
                    return jsonify({'error': '该用户名已被使用'}), 400

            # 验证新邮箱
            if data.get('email') and data['email'] != user.email:
                existing_user = User.query.filter_by(email=data['email']).first()
                if existing_user:
                    return jsonify({'error': '该邮箱已被使用'}), 400

                new_email_key = f'verification:new_email:{current_user_id}:{data["email"]}'
                new_email_stored_code = redis_client.get(new_email_key)
                
                if not new_email_stored_code or new_email_stored_code.decode() != new_email_code:
                    return jsonify({'error': '新邮箱验证码无效或已过期'}), 400

        # 更新用户信息
        update_fields = [
            'username', 'email', 'nickname', 'avatar', 'gender',
            'birthday', 'location', 'website', 'bio'
        ]
        
        for field in update_fields:
            if field in data:
                # 特殊处理生日字段
                # if field == 'birthday' and data[field]:
                #     setattr(user, field, datetime.strptime(data[field], '%Y-%m-%d').date())
                if field == 'birthday' and data[field]:
                    try:
                        date_obj = datetime.strptime(data[field], '%Y-%m-%d').date()
                        setattr(user, field, date_obj)
                    except ValueError as e:
                        return jsonify({'error': '日期格式无效'}), 400
                else:
                    setattr(user, field, data[field])

        db.session.commit()

        # 删除已使用的验证码
        if data.get('username') != user.username or data.get('email') != user.email:
            redis_client.delete(current_email_key)
            if data.get('email') != user.email:
                redis_client.delete(f'verification:new_email:{current_user_id}:{data["email"]}')

        return jsonify({
            'message': '更新成功',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'nickname': user.nickname,
                'avatar': user.avatar,
                'gender': user.gender,
                'birthday': user.birthday.strftime('%Y-%m-%d') if user.birthday else None,
                'location': user.location,
                'website': user.website,
                'bio': user.bio,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200

    except Exception as e:
        print(f"更新用户信息失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '更新用户信息失败'}), 500

@app.route('/api/send-verification', methods=['POST'])
@jwt_required()
def send_verification():
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        email = data.get('email')
        code_type = data.get('type', 'current_email')
        
        if not email:
            return jsonify({'error': '邮箱不能为空'}), 400
            
        # 生成验证码
        code = generate_verification_code()
        
        # 存储验证码
        key = f'verification:{code_type}:{current_user_id}:{email}'
        redis_client.setex(key, 300, code)
        
        # 发送验证码邮件
        if not send_verification_email(email, code):
            return jsonify({'error': '验证码发送失败'}), 500
            
        # 调试信息
        print(f"发送验证码 - Email: {email}, Code: {code}, Key: {key}")
        
        return jsonify({'message': '验证码已发送'}), 200        
    except Exception as e:
        print(f"发送验证码失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '发送验证码失败'}), 500

@app.route('/api/users/posts', methods=['GET'])
@jwt_required()
def get_my_posts():
    try:
        current_user_id = int(get_jwt_identity())
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('page_size', 10, type=int)
        
        # 获取用户的帖子，按创建时间倒序排列
        posts_query = Post.query.filter_by(user_id=current_user_id)\
            .order_by(Post.created_at.desc())
            
        # 分页
        pagination = posts_query.paginate(page=page, per_page=per_page)
        
        # 获取每个帖子的浏览次数
        posts_data = []
        for post in pagination.items:
            view_count = PostView.query\
                .filter_by(post_id=post.id)\
                .with_entities(func.sum(PostView.view_count))\
                .scalar() or 0
                
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'view_count': int(view_count)
            })
        
        return jsonify({
            'posts': posts_data,
            'total': pagination.total,
            'page': page,
            'page_size': per_page
        }), 200
        
    except Exception as e:
        print(f"获取用户帖子失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取帖子失败'}), 500

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    try:
        current_user_id = int(get_jwt_identity())
        post = Post.query.get_or_404(post_id)
        
        # 验证帖子所有权
        if post.user_id != current_user_id:
            return jsonify({'error': '没有权限修改此帖子'}), 403
            
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        
        # 验证数据
        if not title or not content:
            return jsonify({'error': '标题和内容不能为空'}), 400
        if len(title) < 2 or len(title) > 100:
            return jsonify({'error': '标题长度必须在2-100字之间'}), 400
        if len(content) > 2000:
            return jsonify({'error': '内容长度不能超过2000字'}), 400
            
        # 使用事务上下文管理器
        with db.session.begin_nested():
            post.title = title
            post.content = content
        db.session.commit()
        
        return jsonify({
            'message': '更新成功',
            'post': {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"更新帖子失败: {str(e)}")
        return jsonify({'error': '更新帖子失败'}), 500

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    try:
        current_user_id = get_jwt_identity()
        
        # 检查帖子是否存在
        post = Post.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404
            
        # 检查是否是帖子的作者
        if str(post.user_id) != str(current_user_id):
            print(f"权限错误: 用户 {current_user_id} 尝试删除用户 {post.user_id} 的帖子")
            return jsonify({'error': '只能删除自己的帖子'}), 403
            
        try:
            # 开始事务
            # 1. 删除相关的点赞记录
            likes_deleted = PostLike.query.filter_by(post_id=post_id).delete()
            print(f"删除点赞记录 {likes_deleted} 条")
            
            # 2. 删除相关的评论记录
            comments_deleted = PostComment.query.filter_by(post_id=post_id).delete()
            print(f"删除评论记录 {comments_deleted} 条")
            
            # 3. 删除相关的分享记录
            shares_deleted = PostShare.query.filter_by(post_id=post_id).delete()
            print(f"删除分享记录 {shares_deleted} 条")
            
            # 4. 删除相关的浏览记录
            views_deleted = PostView.query.filter_by(post_id=post_id).delete()
            print(f"删除浏览记录 {views_deleted} 条")
            
            # 5. 最后删除帖子
            db.session.delete(post)
            print(f"删除帖子 ID: {post_id}")
            
            # 提交事务
            db.session.commit()
            print(f"帖子 {post_id} 删除成功，事务已提交")
            
            return jsonify({'message': '帖子删除成功'}), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"删除操作事务失败，已回滚: {str(e)}")
            raise e
        
    except Exception as e:
        print(f"删除帖子失败: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'error': '删除帖子失败: ' + str(e)}), 500

# 帖子点赞
@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@jwt_required()
def like_post(post_id):
    try:
        current_user_id = get_jwt_identity()
        post = db.session.get(Post, post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404
            
        existing_like = PostLike.query.filter_by(
            user_id=current_user_id,
            post_id=post_id
        ).first()
        
        is_now_liked = False
        
        if existing_like:
            db.session.delete(existing_like)
            is_now_liked = False
        else:
            # 添加点赞
            new_like = PostLike(
                user_id=current_user_id,
                post_id=post_id,
                created_at=datetime.now(CHINA_TZ)
            )
            db.session.add(new_like)
            is_now_liked = True
            print(f"当前用户ID (current_user_id): {current_user_id}")
            print(f"帖子作者ID (post.user_id): {post.user_id}")
            # 创建通知
            if int(current_user_id) == int(post.user_id):
                print("跳过通知：用户正在点赞自己的帖子")
                # 不创建通知
            else:
                print("创建通知：用户正在点赞他人的帖子")
                Notification.create_notification(
                    recipient_id=post.user_id,
                    sender_id=current_user_id,
                    type='like',
                    post_id=post_id,
                    content=f"点赞了你的帖子 '{post.title}'"
                )
        
        db.session.commit()
        likes_count = PostLike.query.filter_by(post_id=post_id).count()
        
        return jsonify({
            'message': '点赞操作成功',
            'likes_count': likes_count,
            'isLiked': is_now_liked
        }), 200
            
    except Exception as e:
        db.session.rollback()
        print(f"点赞操作失败: {str(e)}")
        return jsonify({'error': '操作失败'}), 500

# 帖子评论
@app.route('/api/posts/<int:post_id>/comment', methods=['POST'])
@jwt_required()
def create_comment(post_id):
    try:
        current_user_id = get_jwt_identity()
        post = db.session.get(Post, post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404
            
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': '评论内容不能为空'}), 400
            
        comment = PostComment(
            post_id=post_id,
            user_id=current_user_id,
            content=content,
            created_at=datetime.now(CHINA_TZ)
        )
        db.session.add(comment)

                # 输出用户ID信息
        print(f"当前用户ID (current_user_id): {current_user_id}")
        print(f"帖子作者ID (post.user_id): {post.user_id}")
        
        # 创建通知 - 如果评论者不是帖子作者，则发送通知
        if int(current_user_id) == int(post.user_id):  # 确保类型一致
            print("跳过通知：用户正在评论自己的帖子")
            # 不创建通知
        else:
            print("创建通知：用户正在评论他人的帖子")
            Notification.create_notification(
                recipient_id=post.user_id,  # 帖子作者
                sender_id=current_user_id,   # 评论者
                type='comment',
                post_id=post_id,
                comment_id=comment.id,
                content=f"评论了你的帖子 '{post.title}'"
            )
        
        db.session.commit()
        
        # 返回评论信息
        return jsonify({
            'message': '评论成功',
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': current_user_id,
                'username': db.session.get(User, current_user_id).username,
                'post_id': post_id,
                'likes_count': 0,
                'shares_count': 0,
                'replies_count': 0
            }
        }), 201
            
    except Exception as e:
        db.session.rollback()
        print(f"评论失败: {str(e)}")
        return jsonify({'error': '评论失败'}), 500

# 获取评论列表
@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        # 检查当前用户是否已登录
        current_user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                payload = pyjwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                current_user_id = payload['sub']
            except Exception as e:
                print(f"Token解析失败: {str(e)}")
        
        # 获取评论和作者信息
        comments_query = db.session.query(
            PostComment, User.username.label('author_name'), User.id.label('author_id'), User.avatar.label('author_avatar')
        ).join(
            User, PostComment.user_id == User.id
        ).filter(
            PostComment.post_id == post_id
        ).order_by(
            PostComment.created_at.desc()
        )
        
        # 分页
        paginated_comments = comments_query.paginate(page=page, per_page=page_size)
        total_comments = paginated_comments.total
        
        # 格式化评论数据
        comments_data = []
        for item in paginated_comments.items:
            comment = item.PostComment
            
            # 获取点赞和转发数
            like_count = CommentLike.query.filter_by(comment_id=comment.id).count()
            share_count = CommentShare.query.filter_by(comment_id=comment.id).count()
            reply_count = CommentReply.query.filter_by(parent_comment_id=comment.id).count()
            
            # 检查当前用户是否点赞、转发
            is_liked = False
            is_shared = False
            if current_user_id:
                is_liked = CommentLike.query.filter_by(
                    comment_id=comment.id, 
                    user_id=current_user_id
                ).first() is not None
                
                is_shared = CommentShare.query.filter_by(
                    comment_id=comment.id,
                    user_id=current_user_id
                ).first() is not None
            
            comments_data.append({
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': comment.user_id,
                'author_id': item.author_id,
                'author_name': item.author_name,
                'author_avatar': item.author_avatar,
                'like_count': like_count,
                'share_count': share_count,
                'reply_count': reply_count,
                'isLiked': is_liked,
                'isShared': is_shared
            })
        
        return jsonify({
            'comments': comments_data,
            'total': total_comments,
            'page': page,
            'page_size': page_size,
            'has_more': page < paginated_comments.pages
        }), 200
        
    except Exception as e:
        print(f"获取评论失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取评论失败'}), 500
    

# 转发接口
@app.route('/api/posts/<int:post_id>/share', methods=['POST'])
@jwt_required()
def share_post(post_id):
    try:
        current_user_id = get_jwt_identity()
        post = db.session.get(Post, post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404
            
        existing_share = PostShare.query.filter_by(
            user_id=current_user_id,
            post_id=post_id
        ).first()
        
        is_now_shared = False
        
        if existing_share:
            db.session.delete(existing_share)
            is_now_shared = False
        else:
            new_share = PostShare(
                user_id=current_user_id,
                post_id=post_id,
                created_at=datetime.now(CHINA_TZ)
            )
            db.session.add(new_share)
            is_now_shared = True
            
            print(f"当前用户ID (current_user_id): {current_user_id}")
            print(f"帖子作者ID (post.user_id): {post.user_id}")
            # 创建通知
            if int(current_user_id) == int(post.user_id):
                print("跳过通知：用户正在转发自己的帖子")
                # 不创建通知
            else:
                print("创建通知：用户正在转发他人的帖子")
                Notification.create_notification(
                    recipient_id=post.user_id,
                    sender_id=current_user_id,
                    type='share',
                    post_id=post_id,
                    content=f"转发了你的帖子 '{post.title}'"
                )
        
        db.session.commit()
        shares_count = PostShare.query.filter_by(post_id=post_id).count()
        
        return jsonify({
            'message': '转发操作成功',
            'shares_count': shares_count,
            'isShared': is_now_shared
        }), 200
            
    except Exception as e:
        db.session.rollback()
        print(f"转发操作失败: {str(e)}")
        return jsonify({'error': '操作失败'}), 500

# 评论点赞
@app.route('/api/comments/<int:comment_id>/like', methods=['POST'])
@jwt_required()
def like_comment(comment_id):
    try:
        current_user_id = get_jwt_identity()
        comment = db.session.get(PostComment, comment_id)
        if not comment:
            return jsonify({'error': '评论不存在'}), 404
            
        # 输出用户ID信息
        print(f"当前用户ID (current_user_id): {current_user_id}")
        print(f"评论作者ID (comment.user_id): {comment.user_id}")
        
        existing_like = CommentLike.query.filter_by(
            user_id=current_user_id,
            comment_id=comment_id
        ).first()
        
        is_now_liked = False
        
        if existing_like:
            db.session.delete(existing_like)
            is_now_liked = False
        else:
            new_like = CommentLike(
                user_id=current_user_id,
                comment_id=comment_id,
                created_at=datetime.now(CHINA_TZ)
            )
            db.session.add(new_like)
            is_now_liked = True
            
            # 创建通知
            if int(current_user_id) == int(comment.user_id):
                print("跳过通知：用户正在点赞自己的评论")
            else:
                print("创建通知：用户正在点赞他人的评论")
                Notification.create_notification(
                    recipient_id=comment.user_id,
                    sender_id=current_user_id,
                    type='like',
                    post_id=comment.post_id,
                    comment_id=comment_id,
                    content=f"点赞了你的评论 '{comment.content}'"
                )
        
        db.session.commit()
        likes_count = CommentLike.query.filter_by(comment_id=comment_id).count()
        
        return jsonify({
            'message': '点赞操作成功',
            'likes_count': likes_count,
            'isLiked': is_now_liked
        }), 200
            
    except Exception as e:
        db.session.rollback()
        print(f"点赞评论失败: {str(e)}")
        return jsonify({'error': '操作失败'}), 500

# 评论转发
@app.route('/api/comments/<int:comment_id>/share', methods=['POST'])
@jwt_required()
def share_comment(comment_id):
    try:
        current_user_id = get_jwt_identity()
        comment = db.session.get(PostComment, comment_id)
        if not comment:
            return jsonify({'error': '评论不存在'}), 404
            
        # 输出用户ID信息
        print(f"当前用户ID (current_user_id): {current_user_id}")
        print(f"评论作者ID (comment.user_id): {comment.user_id}")
        
        existing_share = CommentShare.query.filter_by(
            user_id=current_user_id,
            comment_id=comment_id
        ).first()
        
        is_now_shared = False
        
        if existing_share:
            db.session.delete(existing_share)
            is_now_shared = False
        else:
            new_share = CommentShare(
                user_id=current_user_id,
                comment_id=comment_id,
                created_at=datetime.now(CHINA_TZ)
            )
            db.session.add(new_share)
            is_now_shared = True
            
            # 创建通知
            if int(current_user_id) == int(comment.user_id):
                print("跳过通知：用户正在转发自己的评论")
            else:
                print("创建通知：用户正在转发他人的评论")
                Notification.create_notification(
                    recipient_id=comment.user_id,
                    sender_id=current_user_id,
                    type='share',
                    post_id=comment.post_id,
                    comment_id=comment_id,
                    content=f"转发了你的评论 '{comment.content}'"
                )
        
        db.session.commit()
        shares_count = CommentShare.query.filter_by(comment_id=comment_id).count()
        
        return jsonify({
            'message': '转发操作成功',
            'shares_count': shares_count,
            'isShared': is_now_shared
        }), 200
            
    except Exception as e:
        db.session.rollback()
        print(f"转发评论失败: {str(e)}")
        return jsonify({'error': '操作失败'}), 500

# 评论回复
@app.route('/api/comments/<int:comment_id>/reply', methods=['POST'])
@jwt_required()
def reply_comment(comment_id):
    try:
        current_user_id = get_jwt_identity()
        comment = db.session.get(PostComment, comment_id)
        if not comment:
            return jsonify({'error': '评论不存在'}), 404
            
        # 输出用户ID信息
        print(f"当前用户ID (current_user_id): {current_user_id}")
        print(f"评论作者ID (comment.user_id): {comment.user_id}")
        
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': '回复内容不能为空'}), 400
            
        reply = CommentReply(
            parent_comment_id=comment_id,
            user_id=current_user_id,
            content=content,
            created_at=datetime.now(CHINA_TZ)
        )
        db.session.add(reply)
        
        # 创建通知
        if int(current_user_id) == int(comment.user_id):
            print("跳过通知：用户正在回复自己的评论")
        else:
            print("创建通知：用户正在回复他人的评论")
            Notification.create_notification(
                recipient_id=comment.user_id,
                sender_id=current_user_id,
                type='reply',
                post_id=comment.post_id,
                comment_id=comment_id,
                content=f"回复了你的评论 '{comment.content}'"  # 使用原评论的内容
            )
    
        db.session.commit()
        
        return jsonify({
            'message': '回复成功',
            'reply': {
                'id': reply.id,
                'content': reply.content,
                'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': current_user_id,
                'username': db.session.get(User, current_user_id).username
            }
        }), 201
            
    except Exception as e:
        db.session.rollback()
        print(f"回复评论失败: {str(e)}")
        return jsonify({'error': '回复失败'}), 500

@app.route('/api/posts/<int:post_id>/view', methods=['POST'])
@jwt_required()
def handle_post_view(post_id):
    try:
        current_user_id = int(get_jwt_identity())
        current_time = datetime.utcnow() + timedelta(hours=8)
        
        # 使用 Redis 检查是否在短时间内已经更新过浏览量
        view_key = f'post_view:{post_id}:{current_user_id}'
        if redis_client.get(view_key):
            # 如果已经更新过，直接返回当前浏览量
            post_view = PostView.query.filter_by(post_id=post_id).first()
            print(f"已经更新过浏览量，当前浏览量: {post_view.view_count if post_view else 0}")
            return jsonify({
                'view_count': post_view.view_count if post_view else 0,
                'message': '已经更新过浏览量'
            }), 200
            
        # 设置 Redis 标记，30秒内不再更新浏览量
        redis_client.setex(view_key, 30, '1')
        
        # 检查用户对该帖子的浏览次数
        user_view_count_key = f'user_view_count:{post_id}:{current_user_id}'
        user_view_count = int(redis_client.get(user_view_count_key) or 0)
        
        print(f"用户 {current_user_id} 对帖子 {post_id} 的浏览次数: {user_view_count}")
        
        # 如果已经达到5次，直接返回当前浏览量
        if user_view_count >= 5:
            post_view = PostView.query.filter_by(post_id=post_id).first()
            print(f"达到最大浏览次数，当前浏览量: {post_view.view_count if post_view else 0}")
            return jsonify({
                'view_count': post_view.view_count if post_view else 0,
                'message': '已达到最大浏览次数'
            }), 200
        
        try:
            # 获取帖子信息
            post = Post.query.get_or_404(post_id)
                
            # 使用行锁查询记录
            post_view = PostView.query.filter_by(post_id=post_id)\
                .with_for_update().first()
            
            if post_view:
                # 更新浏览量和最后浏览时间
                post_view.view_count += 1
                post_view.last_viewed_at = current_time
                # 将帖子作者ID存储在user_id和author_id字段中
                post_view.user_id = post.user_id
                post_view.author_id = post.user_id  # 确保author_id不为空
            else:
                # 如果记录不存在，创建新记录
                post_view = PostView(
                    post_id=post_id,
                    user_id=post.user_id,  # 将帖子作者ID存储在user_id字段中
                    author_id=post.user_id,  # 同时将作者ID存储在author_id字段
                    view_count=1,
                    last_viewed_at=current_time
                )
                db.session.add(post_view)
            
            # 增加用户浏览次数并设置过期时间（30天）
            redis_client.incr(user_view_count_key)
            if user_view_count == 0:  # 第一次浏览时设置过期时间
                redis_client.expire(user_view_count_key, 30*24*60*60)  # 30天
            
            db.session.commit()
            
            # 获取更新后的用户浏览次数
            updated_user_view_count = int(redis_client.get(user_view_count_key) or 0)
            
            print(f"帖子 {post_id} 的总浏览量更新为: {post_view.view_count}")
            print(f"用户 {current_user_id} 对帖子 {post_id} 的浏览次数更新为: {updated_user_view_count}")
            print(f"帖子作者ID (存储在user_id和author_id字段): {post_view.user_id}")
            print(f"最后浏览时间(UTC+8): {current_time}")
            
            return jsonify({
                'view_count': post_view.view_count,
                'user_view_count': updated_user_view_count,
                'message': '浏览量更新成功'
            }), 200
            
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        print(f"更新浏览量失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '更新浏览量失败'}), 500

# 搜索帖子API
@app.route('/api/search/posts', methods=['GET'])
def search_posts():
    try:
        # 获取查询参数
        query = request.args.get('q', '')
        sort = request.args.get('sort', 'latest')  # 默认按最新排序
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        if not query:
            return jsonify({'error': '搜索关键词不能为空'}), 400
            
        # 构建查询
        search_query = f"%{query}%"
        base_query = Post.query.filter(
            or_(
                Post.title.like(search_query),
                Post.content.like(search_query)
            )
        )
        
        # 根据排序方式获取帖子
        if sort == 'hot':
            # 热门排序：根据点赞数、评论数、分享数、浏览量等综合排序
            posts_query = base_query.outerjoin(PostLike, Post.id == PostLike.post_id)\
                .outerjoin(PostComment, Post.id == PostComment.post_id)\
                .outerjoin(PostShare, Post.id == PostShare.post_id)\
                .outerjoin(PostView, Post.id == PostView.post_id)\
                .group_by(Post.id)\
                .order_by(
                    func.count(PostLike.id).desc(),
                    func.count(PostComment.id).desc(),
                    func.count(PostShare.id).desc(),
                    func.coalesce(func.max(PostView.view_count), 0).desc(),
                    Post.created_at.desc()
                )
        else:  # latest
            # 最新排序
            posts_query = base_query.order_by(Post.created_at.desc())
            
        # 分页
        pagination = posts_query.paginate(page=page, per_page=per_page, error_out=False)
        posts = pagination.items
        
        # 获取当前用户的点赞、分享状态
        current_user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                payload = pyjwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                current_user_id = payload['sub']
            except:
                pass
                
        # 格式化返回结果
        posts_data = []
        for post in posts:
            # 获取作者信息
            user = User.query.get(post.user_id)
            
            # 获取点赞数、评论数、分享数、浏览量
            like_count = PostLike.query.filter_by(post_id=post.id).count()
            comment_count = PostComment.query.filter_by(post_id=post.id).count()
            share_count = PostShare.query.filter_by(post_id=post.id).count()
            
            # 获取浏览量
            view_record = PostView.query.filter_by(post_id=post.id).first()
            view_count = view_record.view_count if view_record else 0
            
            # 检查当前用户是否点赞、分享
            is_liked = False
            is_shared = False
            if current_user_id:
                is_liked = PostLike.query.filter_by(post_id=post.id, user_id=current_user_id).first() is not None
                is_shared = PostShare.query.filter_by(post_id=post.id, user_id=current_user_id).first() is not None
                
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'avatar': user.avatar
                },
                'like_count': like_count,
                'comment_count': comment_count,
                'share_count': share_count,
                'view_count': view_count,
                'isLiked': is_liked,
                'isShared': is_shared
            })
            
        return jsonify({
            'posts': posts_data,
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'has_more': page < pagination.pages
        }), 200
        
    except Exception as e:
        print(f"搜索帖子失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '搜索帖子失败'}), 500

# 搜索用户API
@app.route('/api/search/users', methods=['GET'])
def search_users():
    try:
        # 获取查询参数
        query = request.args.get('q', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        if not query:
            return jsonify({'error': '搜索关键词不能为空'}), 400
            
        # 构建查询
        search_query = f"%{query}%"
        users_query = User.query.filter(
            or_(
                User.username.like(search_query),
                User.email.like(search_query),
                User.bio.like(search_query)
            )
        ).order_by(User.username)
            
        # 分页
        pagination = users_query.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items
        
        # 格式化返回结果
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'avatar': user.avatar,
                'bio': user.bio
            })
            
        return jsonify({
            'users': users_data,
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'has_more': page < pagination.pages
        }), 200
        
    except Exception as e:
        print(f"搜索用户失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '搜索用户失败'}), 500

# 获取用户信息API
@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        # 查询用户基本信息
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
            
        # 检查是否为已登录用户，确定是否已关注该用户
        current_user_id = None
        is_following = False
        
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                payload = pyjwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                current_user_id = int(payload['sub'])
                
                # 检查是否关注
                if current_user_id != user_id:  # 不检查自己关注自己
                    follow = Follow.query.filter_by(
                        follower_id=current_user_id, 
                        following_id=user_id
                    ).first()
                    is_following = follow is not None
            except:
                pass
                
        # 获取统计数据
        post_count = Post.query.filter_by(user_id=user_id).count()
        follower_count = Follow.query.filter_by(following_id=user_id).count()
        following_count = Follow.query.filter_by(follower_id=user_id).count()
        
        # 构建用户数据
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'nickname': user.nickname,
            'avatar': user.avatar,
            'bio': user.bio,
            'gender': user.gender,
            'birthday': user.birthday.isoformat() if user.birthday else None,
            'location': user.location,
            'website': user.website,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'post_count': post_count,
            'follower_count': follower_count,
            'following_count': following_count
        }
        
        return jsonify({
            'user': user_data,
            'is_following': is_following,
            'is_self': current_user_id == user_id
        }), 200
        
    except Exception as e:
        print(f"获取用户信息失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取用户信息失败'}), 500

# 获取用户帖子API
@app.route('/api/users/<int:user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 获取用户帖子
        posts_query = db.session.query(
            Post, User.username.label('author_name'), User.avatar.label('author_avatar')
        ).join(
            User, Post.user_id == User.id
        ).filter(
            Post.user_id == user_id
        ).order_by(
            Post.created_at.desc()
        )
        
        # 分页
        paginated_posts = posts_query.paginate(page=page, per_page=per_page)
        total_posts = paginated_posts.total
        
        # 检查当前用户是否已登录
        current_user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                payload = pyjwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                current_user_id = payload['sub']
            except Exception as e:
                print(f"Token解析失败: {str(e)}")
        
        # 格式化帖子数据
        posts_data = []
        for item in paginated_posts.items:
            post = item.Post
            
            # 获取点赞、评论、分享、浏览数
            like_count = PostLike.query.filter_by(post_id=post.id).count()
            comment_count = PostComment.query.filter_by(post_id=post.id).count()
            share_count = PostShare.query.filter_by(post_id=post.id).count()
            
            # 获取浏览量
            view_record = PostView.query.filter_by(post_id=post.id).first()
            view_count = view_record.view_count if view_record else 0
            
            # 检查当前用户是否点赞、分享
            is_liked = False
            is_shared = False
            if current_user_id:
                is_liked = PostLike.query.filter_by(
                    post_id=post.id, 
                    user_id=current_user_id
                ).first() is not None
                
                is_shared = PostShare.query.filter_by(
                    post_id=post.id,
                    user_id=current_user_id
                ).first() is not None
            
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S') if post.created_at else None,
                'user_id': post.user_id,
                'author_name': item.author_name,
                'author_avatar': item.author_avatar,
                'like_count': like_count,
                'comment_count': comment_count,
                'share_count': share_count,
                'view_count': view_count,
                'isLiked': is_liked,
                'isShared': is_shared
            })
        
        return jsonify({
            'posts': posts_data,
            'total': total_posts,
            'page': page,
            'per_page': per_page,
            'has_more': page < paginated_posts.pages
        }), 200
        
    except Exception as e:
        print(f"获取用户帖子失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取帖子列表失败'}), 500

# 获取用户的评论列表
@app.route('/api/users/<int:user_id>/comments', methods=['GET'])
@jwt_required(optional=True)
def get_user_comments(user_id):
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 获取用户评论
        comments_query = PostComment.query\
            .filter_by(user_id=user_id)\
            .order_by(PostComment.created_at.desc())
            
        # 分页
        pagination = comments_query.paginate(page=page, per_page=per_page)
        
        # 格式化评论数据
        comments_data = []
        for comment in pagination.items:
            # 获取评论所属的帖子信息
            post = db.session.get(Post, comment.post_id)
            if not post:
                continue
                
            # 获取点赞和回复数量
            likes_count = CommentLike.query.filter_by(comment_id=comment.id).count()
            replies_count = CommentReply.query.filter_by(parent_comment_id=comment.id).count()
            
            # 检查当前用户是否点赞
            is_liked = False
            if current_user_id:
                is_liked = CommentLike.query.filter_by(
                    comment_id=comment.id,
                    user_id=current_user_id
                ).first() is not None
            
            comments_data.append({
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'post': {
                    'id': post.id,
                    'title': post.title
                },
                'likes_count': likes_count,
                'replies_count': replies_count,
                'is_liked': is_liked
            })
        
        return jsonify({
            'comments': comments_data,
            'total': pagination.total,
            'has_more': page < pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        print(f"获取用户评论失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取评论失败'}), 500

# 获取用户的点赞列表
@app.route('/api/users/<int:user_id>/likes', methods=['GET'])
@jwt_required(optional=True)
def get_user_likes(user_id):
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 获取用户点赞的帖子
        post_likes_query = PostLike.query\
            .filter_by(user_id=user_id)\
            .order_by(PostLike.created_at.desc())
            
        # 分页
        pagination = post_likes_query.paginate(page=page, per_page=per_page)
        
        # 格式化点赞数据
        likes_data = []
        for like in pagination.items:
            post = db.session.get(Post, like.post_id)
            if not post:
                continue
                
            likes_data.append({
                'id': like.id,
                'created_at': like.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'post': {
                    'id': post.id,
                    'title': post.title,
                    'author': {
                        'id': post.user_id,
                        'username': db.session.get(User, post.user_id).username
                    }
                }
            })
        
        return jsonify({
            'likes': likes_data,
            'total': pagination.total,
            'has_more': page < pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        print(f"获取用户点赞列表失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取点赞列表失败'}), 500

# 获取用户的转发列表
@app.route('/api/users/<int:user_id>/shares', methods=['GET'])
@jwt_required(optional=True)
def get_user_shares(user_id):
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 获取用户转发的帖子
        shares_query = PostShare.query\
            .filter_by(user_id=user_id)\
            .order_by(PostShare.created_at.desc())
            
        # 分页
        pagination = shares_query.paginate(page=page, per_page=per_page)
        
        # 格式化转发数据
        shares_data = []
        for share in pagination.items:
            post = db.session.get(Post, share.post_id)
            if not post:
                continue
                
            shares_data.append({
                'id': share.id,
                'created_at': share.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'post': {
                    'id': post.id,
                    'title': post.title,
                    'author': {
                        'id': post.user_id,
                        'username': db.session.get(User, post.user_id).username
                    }
                }
            })
        
        return jsonify({
            'shares': shares_data,
            'total': pagination.total,
            'has_more': page < pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        print(f"获取用户转发列表失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取转发列表失败'}), 500
    
# 关注用户API
@app.route('/api/users/<int:user_id>/follow', methods=['POST'])
@jwt_required()
def follow_user(user_id):
    try:
        current_user_id = get_jwt_identity()
        
        # 不能关注自己
        if int(current_user_id) == user_id:
            return jsonify({'error': '不能关注自己'}), 400
            
        # 检查要关注的用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
            
        # 检查是否已经关注
        existing_follow = Follow.query.filter_by(
            follower_id=current_user_id,
            following_id=user_id
        ).first()
        
        if existing_follow:
            return jsonify({'message': '已经关注了该用户'}), 200
            
        # 创建新的关注关系
        new_follow = Follow(
            follower_id=current_user_id,
            following_id=user_id,
            created_at=datetime.now(CHINA_TZ)
        )
        db.session.add(new_follow)
        
        # 创建关注通知
        current_user = db.session.get(User, current_user_id)
        Notification.create_notification(
            recipient_id=user_id,  # 被关注的用户
            sender_id=current_user_id,  # 关注者
            type='follow',
            content=f"{current_user.username} 关注了你"
        )
        
        db.session.commit()
        
        # 获取最新的粉丝数
        follower_count = Follow.query.filter_by(following_id=user_id).count()
        
        return jsonify({
            'message': '关注成功',
            'follower_count': follower_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"关注用户失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '关注用户失败'}), 500

# 取消关注用户API
@app.route('/api/users/<int:user_id>/unfollow', methods=['POST'])
@jwt_required()
def unfollow_user(user_id):
    try:
        current_user_id = get_jwt_identity()
        
        # 检查要取消关注的用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
            
        # 删除关注关系
        follow = Follow.query.filter_by(
            follower_id=current_user_id,
            following_id=user_id
        ).first()
        
        if not follow:
            return jsonify({'message': '未关注该用户'}), 200
            
        db.session.delete(follow)
        db.session.commit()
        
        # 获取最新的粉丝数
        follower_count = Follow.query.filter_by(following_id=user_id).count()
        
        return jsonify({
            'message': '取消关注成功',
            'follower_count': follower_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"取消关注用户失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '取消关注用户失败'}), 500
    


# 获取通知列表
@app.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        # 获取分页的通知列表
        notifications = Notification.query\
            .filter_by(recipient_id=current_user_id)\
            .order_by(Notification.created_at.desc())\
            .paginate(page=page, per_page=page_size)
            
        # 获取未读消息数量
        unread_count = Notification.query\
            .filter_by(recipient_id=current_user_id, is_read=False)\
            .count()
            
        notifications_data = []
        for notification in notifications.items:
            notifications_data.append({
                'id': notification.id,
                'type': notification.type,
                'content': notification.content,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'sender': {
                    'id': notification.sender.id,
                    'username': notification.sender.username
                },
                'post_id': notification.post_id,
                'comment_id': notification.comment_id
            })
            
        return jsonify({
            'notifications': notifications_data,
            'has_more': page < notifications.pages,
            'unread_count': unread_count  # 添加未读消息数量
        }), 200
        
    except Exception as e:
        print(f"获取通知失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取通知失败'}), 500

# 获取未读通知数量
@app.route('/api/notifications/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    try:
        current_user_id = get_jwt_identity()
        count = Notification.query\
            .filter_by(recipient_id=current_user_id, is_read=False)\
            .count()
            
        return jsonify({'count': count}), 200
        
    except Exception as e:
        print(f"获取未读通知数量失败: {str(e)}")
        return jsonify({'error': '获取未读通知数量失败'}), 500

# 标记通知为已读
@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    try:
        current_user_id = get_jwt_identity()
        notification = Notification.query\
            .filter_by(id=notification_id, recipient_id=current_user_id)\
            .first_or_404()
            
        notification.is_read = True
        db.session.commit()
        
        # 获取最新的未读消息数量
        unread_count = Notification.query\
            .filter_by(recipient_id=current_user_id, is_read=False)\
            .count()
        
        return jsonify({
            'message': '已标记为已读',
            'unread_count': unread_count  # 返回最新的未读数量
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"标记通知已读失败: {str(e)}")
        return jsonify({'error': '标记已读失败'}), 500

# 标记所有通知为已读
@app.route('/api/notifications/read-all', methods=['POST'])
@jwt_required()
def mark_all_notifications_read():
    try:
        current_user_id = get_jwt_identity()
        Notification.query\
            .filter_by(recipient_id=current_user_id, is_read=False)\
            .update({'is_read': True})
            
        db.session.commit()
        
        return jsonify({
            'message': '所有通知已标记为已读',
            'unread_count': 0  # 全部已读，未读数量为0
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"标记所有通知已读失败: {str(e)}")
        return jsonify({'error': '标记所有已读失败'}), 500

# 获取评论的回复列表
@app.route('/api/comments/<int:comment_id>/replies', methods=['GET'])
@jwt_required(optional=True)  # 允许未登录用户查看回复
def get_comment_replies(comment_id):
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 5, type=int)
        
        # 检查评论是否存在
        comment = db.session.get(PostComment, comment_id)
        if not comment:
            return jsonify({'error': '评论不存在'}), 404
            
        # 获取回复列表
        replies_query = CommentReply.query.filter_by(parent_comment_id=comment_id)\
            .order_by(CommentReply.created_at.asc())
            
        # 分页
        paginated_replies = replies_query.paginate(page=page, per_page=page_size)
        
        # 格式化回复数据
        replies_data = []
        for reply in paginated_replies.items:
            reply_user = db.session.get(User, reply.user_id)
            replies_data.append({
                'id': reply.id,
                'content': reply.content,
                'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': reply.user_id,
                'username': reply_user.username if reply_user else '[已删除]',
                'is_author': current_user_id == reply.user_id if current_user_id else False
            })
            
        return jsonify({
            'replies': replies_data,
            'total': paginated_replies.total,
            'has_more': paginated_replies.has_next,
            'current_page': page
        }), 200
        
    except Exception as e:
        print(f"获取评论回复失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '获取回复失败'}), 500

# 获取当前用户的评论列表
@app.route('/api/users/comments', methods=['GET'])
@jwt_required()
def get_my_comments():
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        comments_query = PostComment.query\
            .filter_by(user_id=current_user_id)\
            .order_by(PostComment.created_at.desc())
            
        pagination = comments_query.paginate(page=page, per_page=per_page)
        
        comments_data = []
        for comment in pagination.items:
            post = db.session.get(Post, comment.post_id)
            if not post:
                continue
            
            post_author = db.session.get(User, post.user_id)
            comments_data.append({
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'post_title': post.title,
                'post_id': post.id,
                'post_author': post_author.username  # 添加帖子作者用户名
            })
        
        return jsonify({
            'comments': comments_data,
            'has_more': pagination.has_next,
            'total': pagination.total
        }), 200
        
    except Exception as e:
        print(f"获取评论失败: {str(e)}")
        return jsonify({'error': '获取评论失败'}), 500

# 获取当前用户的点赞列表
@app.route('/api/users/likes', methods=['GET'])
@jwt_required()
def get_my_likes():
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        likes_query = PostLike.query\
            .filter_by(user_id=current_user_id)\
            .order_by(PostLike.created_at.desc())
            
        pagination = likes_query.paginate(page=page, per_page=per_page)
        
        likes_data = []
        for like in pagination.items:
            post = db.session.get(Post, like.post_id)
            if not post:
                continue
            
            post_author = db.session.get(User, post.user_id)
            likes_data.append({
                'id': like.id,
                'created_at': like.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'post_title': post.title,
                'post_id': post.id,
                'post_author': post_author.username  # 添加帖子作者用户名
            })
        
        return jsonify({
            'likes': likes_data,
            'has_more': pagination.has_next,
            'total': pagination.total
        }), 200
        
    except Exception as e:
        print(f"获取点赞列表失败: {str(e)}")
        return jsonify({'error': '获取点赞列表失败'}), 500

# 获取当前用户的转发列表
@app.route('/api/users/shares', methods=['GET'])
@jwt_required()
def get_my_shares():
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        shares_query = PostShare.query\
            .filter_by(user_id=current_user_id)\
            .order_by(PostShare.created_at.desc())
            
        pagination = shares_query.paginate(page=page, per_page=per_page)
        
        shares_data = []
        for share in pagination.items:
            post = db.session.get(Post, share.post_id)
            if not post:
                continue
            
            post_author = db.session.get(User, post.user_id)
            shares_data.append({
                'id': share.id,
                'created_at': share.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'post_title': post.title,
                'post_id': post.id,
                'post_author': post_author.username  # 添加帖子作者用户名
            })
        
        return jsonify({
            'shares': shares_data,
            'has_more': pagination.has_next,
            'total': pagination.total
        }), 200
        
    except Exception as e:
        print(f"获取转发列表失败: {str(e)}")
        return jsonify({'error': '获取转发列表失败'}), 500

# 初始化 SocketIO
socketio = SocketIO(app, 
    cors_allowed_origins=[
        "https://www.searchsomething.top",
        "https://api.searchsomething.top"
    ],  
    async_mode='threading',  # 使用线程模式
    logger=True,  # 启用日志
    engineio_logger=True  # 启用 Engine.IO 日志
)

# 存储用户连接
user_connections = {}

@socketio.on('connect')
def handle_connect():
    try:
        # 从请求头获取 token
        auth = request.args.get('auth')
        if not auth:
            print("No auth provided")
            return False
        
        # 移除 "Bearer " 前缀
        token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else auth
        
        # 解析 token 获取用户 ID
        try:
            decoded_token = decode_token(token)
            current_user_id = decoded_token['sub']
            
            # 存储用户连接
            user_connections[current_user_id] = request.sid
            print(f"User {current_user_id} connected with sid {request.sid}")
            return True
            
        except Exception as e:
            print(f"Token decode error: {str(e)}")
            traceback.print_exc()  # 添加堆栈跟踪
            return False
            
    except Exception as e:
        print(f"Connection error: {str(e)}")
        traceback.print_exc()  # 添加堆栈跟踪
        return False

@socketio.on('disconnect')
def handle_disconnect():
    try:
        token = request.args.get('token')
        if token:
            decoded_token = decode_token(token)
            current_user_id = decoded_token['sub']
            if current_user_id in user_connections:
                user_connections.pop(current_user_id)
                print(f"User {current_user_id} disconnected")
    except Exception as e:
        print(f"Disconnect error: {str(e)}")

# 在创建新通知时发送 WebSocket 消息
def send_notification(recipient_id, notification_data):
    if recipient_id in user_connections:
        socket_id = user_connections[recipient_id]
        emit('new_notification', notification_data, room=socket_id)

# 修改创建通知的函数
def create_notification(recipient_id, sender_id, notification_type, post_id=None, comment_id=None, content=None):
    try:
        # 如果是自己的操作，不创建通知
        if recipient_id == sender_id:
            print(f"跳过自己给自己的通知: user_id={recipient_id}")
            return None
            
        # 如果是对自己内容的操作，不创建通知
        if post_id:
            post = Post.query.get(post_id)
            if post and post.user_id == sender_id:
                print(f"跳过自己操作自己帖子的通知: user_id={sender_id}, post_id={post_id}")
                return None
                
        if comment_id:
            comment = PostComment.query.get(comment_id)
            if comment and comment.user_id == sender_id:
                print(f"跳过自己操作自己评论的通知: user_id={sender_id}, comment_id={comment_id}")
                return None
        
        notification = Notification(
            recipient_id=recipient_id,
            sender_id=sender_id,
            type=notification_type,
            post_id=post_id,
            comment_id=comment_id,
            content=content,
            is_read=False,
            created_at=datetime.now(CHINA_TZ)
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # 获取未读消息数量
        unread_count = Notification.query\
            .filter_by(recipient_id=recipient_id, is_read=False)\
            .count()
        
        # 如果用户在线，发送实时通知
        if recipient_id in user_connections:
            notification_data = {
                'id': notification.id,
                'type': notification_type,
                'content': content,
                'unread_count': unread_count,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'sender': {
                    'id': notification.sender.id,
                    'username': notification.sender.username
                },
                'post_id': post_id,
                'comment_id': comment_id,
                'is_read': False
            }
            socketio.emit('new_notification', notification_data, room=user_connections[recipient_id])
            print(f"Sent notification to user {recipient_id}")
        
        return notification
        
    except Exception as e:
        db.session.rollback()
        print(f"创建通知失败: {str(e)}")
        traceback.print_exc()
        return None

# 修改错误处理
@app.errorhandler(SQLAlchemyError)
def handle_db_error(error):
    db.session.rollback()
    print(f"数据库错误: {str(error)}")
    return jsonify({'error': '数据库操作失败'}), 500

@app.errorhandler(IntegrityError)
def handle_integrity_error(error):
    db.session.rollback()
    print(f"数据完整性错误: {str(error)}")
    return jsonify({'error': '数据冲突'}), 409

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get('PORT', 5000))
        # 生产环境
    app.run(host='0.0.0.0', port=port)

















