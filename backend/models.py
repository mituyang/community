from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from pytz import timezone
from sqlalchemy import CheckConstraint, Text
import traceback
import pytz
import requests
from flask import current_app


CHINA_TZ = timezone('Asia/Shanghai')
from datetime import datetime
import pytz
import requests
from flask import current_app
import traceback

CHINA_TZ = pytz.timezone('Asia/Shanghai')

class D1Database:
    @staticmethod
    def execute(query, params=None):
        try:
            headers = {
                'Authorization': f'Bearer {current_app.config["D1_API_TOKEN"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'sql': query,
                'params': params or []
            }
            
            response = requests.post(
                current_app.config['D1_BASE_URL'],
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                return response.json()['result']
            else:
                print(f"D1 query failed: {response.text}")
                return None
        except Exception as e:
            print(f"D1 query error: {str(e)}")
            traceback.print_exc()
            return None

class User:
    @staticmethod
    def get_by_id(user_id):
        return D1Database.execute(
            "SELECT * FROM users WHERE id = ?",
            [user_id]
        )

    @staticmethod
    def get_by_username(username):
        return D1Database.execute(
            "SELECT * FROM users WHERE username = ?",
            [username]
        )

    @staticmethod
    def create(username, password, email, **kwargs):
        return D1Database.execute(
            """
            INSERT INTO users (username, password, email, nickname, avatar, gender, 
                             birthday, location, website, bio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            [username, password, email, kwargs.get('nickname'), kwargs.get('avatar'),
             kwargs.get('gender', 'secret'), kwargs.get('birthday'), kwargs.get('location'),
             kwargs.get('website'), kwargs.get('bio')]
        )

    @staticmethod
    def is_following(follower_id, following_id):
        result = D1Database.execute(
            "SELECT 1 FROM follows WHERE follower_id = ? AND following_id = ?",
            [follower_id, following_id]
        )
        return bool(result)

    @staticmethod
    def follow(follower_id, following_id):
        if follower_id != following_id:
            return D1Database.execute(
                "INSERT INTO follows (follower_id, following_id) VALUES (?, ?)",
                [follower_id, following_id]
            )
        return None

    @staticmethod
    def unfollow(follower_id, following_id):
        return D1Database.execute(
            "DELETE FROM follows WHERE follower_id = ? AND following_id = ?",
            [follower_id, following_id]
        )

    @staticmethod
    def get_followers_count(user_id):
        result = D1Database.execute(
            "SELECT COUNT(*) as count FROM follows WHERE following_id = ?",
            [user_id]
        )
        return result[0]['count'] if result else 0

    @staticmethod
    def get_following_count(user_id):
        result = D1Database.execute(
            "SELECT COUNT(*) as count FROM follows WHERE follower_id = ?",
            [user_id]
        )
        return result[0]['count'] if result else 0

class Post:
    @staticmethod
    def create(title, content, user_id):
        return D1Database.execute(
            "INSERT INTO posts (title, content, user_id) VALUES (?, ?, ?) RETURNING id",
            [title, content, user_id]
        )

    @staticmethod
    def get_by_id(post_id):
        return D1Database.execute(
            """
            SELECT p.*, u.username as author_name 
            FROM posts p 
            JOIN users u ON p.user_id = u.id 
            WHERE p.id = ?
            """,
            [post_id]
        )

    @staticmethod
    def get_all(page=1, per_page=10):
        offset = (page - 1) * per_page
        return D1Database.execute(
            """
            SELECT p.*, u.username as author_name,
                   (SELECT COUNT(*) FROM post_likes WHERE post_id = p.id) as likes_count,
                   (SELECT COUNT(*) FROM post_comments WHERE post_id = p.id) as comments_count
            FROM posts p 
            JOIN users u ON p.user_id = u.id 
            ORDER BY p.created_at DESC 
            LIMIT ? OFFSET ?
            """,
            [per_page, offset]
        )

    @staticmethod
    def get_total_views(post_id):
        result = D1Database.execute(
            "SELECT view_count FROM post_views WHERE post_id = ?",
            [post_id]
        )
        return result[0]['view_count'] if result else 0

class PostView:
    @staticmethod
    def record_view(post_id, author_id, user_id):
        return D1Database.execute(
            """
            INSERT INTO post_views (post_id, author_id, user_id, view_count, last_viewed_at)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT (post_id) DO UPDATE 
            SET view_count = view_count + 1,
                last_viewed_at = CURRENT_TIMESTAMP
            """,
            [post_id, author_id, user_id]
        )

class PostLike:
    @staticmethod
    def create(post_id, user_id):
        return D1Database.execute(
            "INSERT INTO post_likes (post_id, user_id) VALUES (?, ?)",
            [post_id, user_id]
        )

    @staticmethod
    def delete(post_id, user_id):
        return D1Database.execute(
            "DELETE FROM post_likes WHERE post_id = ? AND user_id = ?",
            [post_id, user_id]
        )

    @staticmethod
    def exists(post_id, user_id):
        result = D1Database.execute(
            "SELECT 1 FROM post_likes WHERE post_id = ? AND user_id = ?",
            [post_id, user_id]
        )
        return bool(result)

class PostComment:
    @staticmethod
    def create(post_id, user_id, content):
        return D1Database.execute(
            """
            INSERT INTO post_comments (post_id, user_id, content)
            VALUES (?, ?, ?)
            RETURNING id
            """,
            [post_id, user_id, content]
        )

    @staticmethod
    def get_by_post(post_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        return D1Database.execute(
            """
            SELECT c.*, u.username,
                   (SELECT COUNT(*) FROM comment_likes WHERE comment_id = c.id) as likes_count,
                   (SELECT COUNT(*) FROM comment_replies WHERE parent_comment_id = c.id) as replies_count
            FROM post_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at DESC
            LIMIT ? OFFSET ?
            """,
            [post_id, per_page, offset]
        )

class CommentLike:
    @staticmethod
    def create(comment_id, user_id):
        return D1Database.execute(
            "INSERT INTO comment_likes (comment_id, user_id) VALUES (?, ?)",
            [comment_id, user_id]
        )

    @staticmethod
    def delete(comment_id, user_id):
        return D1Database.execute(
            "DELETE FROM comment_likes WHERE comment_id = ? AND user_id = ?",
            [comment_id, user_id]
        )

class CommentReply:
    @staticmethod
    def create(parent_comment_id, user_id, content):
        return D1Database.execute(
            """
            INSERT INTO comment_replies (parent_comment_id, user_id, content)
            VALUES (?, ?, ?)
            RETURNING id
            """,
            [parent_comment_id, user_id, content]
        )

    @staticmethod
    def get_by_comment(comment_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        return D1Database.execute(
            """
            SELECT r.*, u.username
            FROM comment_replies r
            JOIN users u ON r.user_id = u.id
            WHERE r.parent_comment_id = ?
            ORDER BY r.created_at ASC
            LIMIT ? OFFSET ?
            """,
            [comment_id, per_page, offset]
        )

class Notification:
    @staticmethod
    def create(recipient_id, sender_id, type, content=None, post_id=None, comment_id=None):
        # 检查是否是自己的操作
        if recipient_id == sender_id:
            return None

        # 检查是否是自己的内容
        if post_id:
            post = Post.get_by_id(post_id)
            if post and post[0]['user_id'] == sender_id:
                return None

        return D1Database.execute(
            """
            INSERT INTO notifications 
            (recipient_id, sender_id, type, content, post_id, comment_id, is_read)
            VALUES (?, ?, ?, ?, ?, ?, false)
            RETURNING id
            """,
            [recipient_id, sender_id, type, content, post_id, comment_id]
        )

    @staticmethod
    def get_unread_count(user_id):
        result = D1Database.execute(
            "SELECT COUNT(*) as count FROM notifications WHERE recipient_id = ? AND is_read = false",
            [user_id]
        )
        return result[0]['count'] if result else 0

    @staticmethod
    def mark_as_read(notification_id):
        return D1Database.execute(
            "UPDATE notifications SET is_read = true WHERE id = ?",
            [notification_id]
        )

    @staticmethod
    def get_user_notifications(user_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        return D1Database.execute(
            """
            SELECT n.*, u.username as sender_name
            FROM notifications n
            JOIN users u ON n.sender_id = u.id
            WHERE n.recipient_id = ?
            ORDER BY n.created_at DESC
            LIMIT ? OFFSET ?
            """,
            [user_id, per_page, offset]
        )
