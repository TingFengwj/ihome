# coding:utf-8
from logging.handlers import RotatingFileHandler
# 注册转换器
from utils.commons import RegexConverter

import redis
import logging
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import csrf, CSRFProtect
from config import config_dict, Config

# 创建redis链接对象
redis_store = None

#构造数据库对象
db = SQLAlchemy()
csrf = CSRFProtect()

logging.basicConfig(level=logging.DEBUG)  # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日记录器
logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    # 创建Flask应用对象
    app = Flask(__name__)
    conf = config_dict[config_name]

    # 设置flask的配置信息
    app.config.from_object(config_dict[config_name])

    # 初始化数据库
    db.init_app(app)

    # 初始化redis
    global redis_store
    redis_store = redis.StrictRedis(host=conf.REDIS_HOST, port=conf.REDIS_PORT)

    #初始化csrf防护机制
    csrf.init_app(app)
    # 将Flask里的session数据保存在redis中
    Session(app)

    #向app中添加自定义的路由转换器
    app.url_map.converters["re"] = RegexConverter

    #注册蓝图 其中，api_1_0放在这里的导入是将其延迟了
    from ihome import api_1_0
    app.register_blueprint(api_1_0.api, url_prefix='/api/v1_0')

    #提供html静态文件的蓝图
    import web_html
    app.register_blueprint(web_html.html)

    return app
