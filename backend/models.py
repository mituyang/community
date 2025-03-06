from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from pytz import timezone
from sqlalchemy import CheckConstraint
import traceback

db = SQLAlchemy()

CHINA_TZ = timezone('Asia/Shanghai')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True)
    nickname = db.Column(db.String(80))
    avatar = db.Column(db.String(255))
    gender = db.Column(db.Enum('male', 'female', 'secret'), default='secret')
    birthday = db.Column(db.Date)
    location = db.Column(db.String(100))
    website = db.Column(db.String(255))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 添加与帖子的关系
    posts = db.relationship('Post', backref='author', lazy=True)
    
    # 添加关注功能的帮助方法
    def is_following(self, user):
        """检查当前用户是否关注了指定用户"""
        if user.id is None:
            return False
        return Follow.query.filter_by(
            follower_id=self.id,
            following_id=user.id
        ).first() is not None
    
    def follow(self, user):
        """关注指定用户"""
        if not self.is_following(user) and self.id != user.id:
            f = Follow(follower_id=self.id, following_id=user.id)
            db.session.add(f)
            return True
        return False
    
    def unfollow(self, user):
        """取消关注指定用户"""
        f = Follow.query.filter_by(
            follower_id=self.id,
            following_id=user.id
        ).first()
        if f:
            db.session.delete(f)
            return True
        return False
    
    def get_followers_count(self):
        """获取关注者数量"""
        return Follow.query.filter_by(following_id=self.id).count()
    
    def get_following_count(self):
        """获取关注数量"""
        return Follow.query.filter_by(follower_id=self.id).count()

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 获取总浏览量的方法
    def get_total_views(self):
        view = PostView.query.filter_by(post_id=self.id).first()
        return view.view_count if view else 0

# 添加关注关系模型
class Follow(db.Model):
    __tablename__ = 'follows'
    
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('follower_id', 'following_id', name='unique_follow'),
    )
    
    # 关系
    follower = db.relationship('User', foreign_keys=[follower_id], backref=db.backref('followings', lazy='dynamic'))
    following = db.relationship('User', foreign_keys=[following_id], backref=db.backref('followers', lazy='dynamic'))

class PostView(db.Model):
    __tablename__ = 'post_view'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), unique=True, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    view_count = db.Column(db.Integer, default=0)
    last_viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 修改关联关系，使用不同的名称
    post = db.relationship('Post', backref=db.backref('view_record', uselist=False))
    author = db.relationship('User', foreign_keys=[author_id], backref='authored_views')
    viewer = db.relationship('User', foreign_keys=[user_id], backref='viewed_posts')

class PostLike(db.Model):
    __tablename__ = 'post_like'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(CHINA_TZ))
    
    __table_args__ = (
        db.UniqueConstraint('post_id', 'user_id', name='unique_post_user_like'),
    )

class PostComment(db.Model):
    __tablename__ = 'post_comment'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(CHINA_TZ))
    
    user = db.relationship('User', backref='comments')

class PostShare(db.Model):
    __tablename__ = 'post_share'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(CHINA_TZ))

class CommentLike(db.Model):
    __tablename__ = 'comment_like'
    
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('post_comment.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(CHINA_TZ))
    
    # 添加关系
    comment = db.relationship('PostComment', backref=db.backref('likes', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('comment_likes', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('comment_id', 'user_id', name='uk_comment_like'),
    )

class CommentShare(db.Model):
    __tablename__ = 'comment_share'
    
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('post_comment.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(CHINA_TZ))
    
    # 添加关系
    comment = db.relationship('PostComment', backref=db.backref('shares', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('comment_shares', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('comment_id', 'user_id', name='uk_comment_share'),
    )

class CommentReply(db.Model):
    __tablename__ = 'comment_reply'
    
    id = db.Column(db.Integer, primary_key=True)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('post_comment.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(CHINA_TZ))
    
    # 添加关系
    parent_comment = db.relationship('PostComment', backref=db.backref('replies', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('comment_replies', lazy='dynamic'))

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    comment_id = db.Column(db.Integer, db.ForeignKey('post_comment.id'))
    content = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(CHINA_TZ))
    
    # 添加数据库级别的约束
    __table_args__ = (
        db.CheckConstraint('recipient_id <> sender_id', name='check_no_self_notification'),
    )
    
    # 关系
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_notifications')
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_notifications')
    post = db.relationship('Post', backref='notifications')
    comment = db.relationship('PostComment', backref='notifications')

    @classmethod
    def create_notification(cls, recipient_id, sender_id, type, content=None, post_id=None, comment_id=None):
        """
        创建一个新的通知
        """
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
            
            notification = cls(
                recipient_id=recipient_id,
                sender_id=sender_id,
                type=type,
                content=content,
                post_id=post_id,
                comment_id=comment_id,
                is_read=False
            )
            db.session.add(notification)
            db.session.commit()
            return notification
            
        except Exception as e:
            db.session.rollback()
            print(f"创建通知失败: {str(e)}")
            traceback.print_exc()
            return None

