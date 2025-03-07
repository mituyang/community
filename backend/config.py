import os

# 获取当前文件所在目录的绝对路径（backend 目录）
basedir = os.path.abspath(os.path.dirname(__file__))
# 创建 backend/instance 目录的路径
# instance_path = os.path.join(basedir, 'instance')

# # 确保 backend/instance 目录存在
# os.makedirs(instance_path, exist_ok=True)

class Config:
    # D1 配置
    D1_DATABASE_ID = '59c23280-ed64-4932-a259-96423d8d93f6'
    D1_API_TOKEN = os.environ.get('CF_API_TOKEN')
    D1_BASE_URL = f'https://api.cloudflare.com/client/v4/accounts/{D1_DATABASE_ID}/d1/query'
    
    # JWT配置
    JWT_SECRET_KEY = 'yqw123456'
    JWT_ACCESS_TOKEN_EXPIRES = 30 * 24 * 60 * 60  # 30天过期
    JWT_ERROR_MESSAGE_KEY = 'message'
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # 邮件配置
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = '3397998891@qq.com'
    MAIL_PASSWORD = 'btcwftgikodadafb'
    MAIL_DEFAULT_SENDER = '社区论坛'

