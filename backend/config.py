import os
class Config:
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:yqw123456@localhost/community?charset=utf8mb4'
    SQLALCHEMY_DATABASE_URI = 'd1://59c23280-ed64-4932-a259-96423d8d93f6/community'
    D1_API_TOKEN = os.environ.get('CF_API_TOKEN')  # 这里使用 CF_API_TOKEN

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 添加SQLite多线程支持
    # SQLALCHEMY_ENGINE_OPTIONS = {
    #     'connect_args': {
    #         'check_same_thread': False  # 允许多线程访问SQLite
    #     }
    # }
    JWT_SECRET_KEY = 'yqw123456'  # 请更改为复杂的密钥 

    
    # 添加邮件配置
    MAIL_SERVER = 'smtp.qq.com'  # 如果使用QQ邮箱
    MAIL_PORT = 465  # QQ邮箱的SSL端口号
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False  # 确保TLS关闭
    MAIL_USERNAME = '3397998891@qq.com'  # 发件人邮箱
    MAIL_PASSWORD = 'btcwftgikodadafb'  # 邮箱授权码，不是邮箱密码
    MAIL_DEFAULT_SENDER = '社区论坛'  # 添加默认发件人

