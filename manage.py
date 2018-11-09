# coding:utf-8
from flask_migrate import Migrate, MigrateCommand
from  flask_script import Manager
from ihome import create_app, db

# 创建管理工具对象
app = create_app('develop')

# 创建管理工具对象
manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)


# 为flask补充csrf防护机制
"""test"""



if __name__ == '__main__':
    app.run()
