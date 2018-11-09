# coding:utf-8
from functools import wraps


def login_required(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        """装饰器哈哈哈"""
        pass
    return wrapper


@login_required
def logout():
    """登出"""
    pass

if __name__ == '__main__':
    print (logout.__name__)
    print (logout.__doc__)