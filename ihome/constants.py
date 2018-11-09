#coding:utf-8

IMAGE_CODE_REDIS_EXPIRES = 120 #图片验证码redis存储有效期, 单位秒

SMS_CODE_REDIS_EXPIRES = 300 # 短信验证码redis有效期,单位秒

QINIU_URL_DOMAIN = "http://o91qujnqh.bkt.clouddn.com/" # 七牛的访问域名

LOGIN_ERROR_MAX_NUM = 5 # 登录的最大错误次数

LOGIN_ERROR_FORBID_TIME = 600 # 登录错误封ip的时间, 单位:秒

AREA_INFO_REDIS_EXPIRES = 3600 # 城区信息在redis缓存时间 单位:秒

HOME_PAGE_MAX_HOUSES = 5  # 首页显示的最多的五条数据

HOME_PAGE_DATA_REDIS_EXPIRES = 7200 # 首页房屋书库的redis缓存时间, 单位:秒

HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 30 # 房屋详情显示的评论最大数

HOUSE_DETAIL_REDIS_EXPIRES_SESSION = 7200 # 详情页面的数据redis缓存时间,时间秒

HOUSE_DETAIL_REDIS_EXPIRE_SECOND = 7200 # 详情页面的数据redis缓存时间,时间秒