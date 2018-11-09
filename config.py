# coding:utf-8

import redis
class Config(object):
    SECRET_KEY = 'KAJDFA2894592805%^$%#%$#(*)((*'
    DEBUG = True

    # 数据库配置信息
    SQLALCHEMY_DATABASE_URI = 'mysql://root:heima931008@127.0.0.1:3306/ihome_python02'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    SESSION_TYPE = 'redis'
    SESSION_USE_SINGER = True # 让cookie中的session_id被加密签名处理
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    PERMANENT_SESSION_LIFETIME =86400


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_dict= {
    'develop': DevelopmentConfig,
    'product': ProductionConfig,
}