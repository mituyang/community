import os

class Config:
    # 使用 SQLite 作为数据库引擎
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/community.db'
    
    # D1 相关配置（保留但暂时不使用）
    D1_DATABASE_ID = '59c23280-ed64-4932-a259-96423d8d93f6'
    D1_API_TOKEN = os.environ.get('CF_API_TOKEN')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 添加 SQLite 多线程支持
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'check_same_thread': False  
        }
    }
    
    JWT_SECRET_KEY = 'yqw123456'  # 请更改为复杂的密钥
    
    # 邮件配置保持不变
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = '3397998891@qq.com'
    MAIL_PASSWORD = 'btcwftgikodadafb'
    MAIL_DEFAULT_SENDER = '社区论坛'

