import os

# 获取当前文件所在目录的绝对路径（backend 目录）
basedir = os.path.abspath(os.path.dirname(__file__))
# 创建 backend/instance 目录的路径
instance_path = os.path.join(basedir, 'instance')

# 确保 backend/instance 目录存在
os.makedirs(instance_path, exist_ok=True)

class Config:
    # 移除 SQLite 配置，改用 D1 配置
    DATABASE_URL = os.environ.get('DATABASE_URL', 'https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}')
    D1_DATABASE_ID = '59c23280-ed64-4932-a259-96423d8d93f6'
    D1_API_TOKEN = os.environ.get('CF_API_TOKEN')
    
    # 保持其他配置不变
    JWT_SECRET_KEY = 'yqw123456'
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = '3397998891@qq.com'
    MAIL_PASSWORD = 'btcwftgikodadafb'
    MAIL_DEFAULT_SENDER = '社区论坛'

