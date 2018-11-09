# coding=utf-8


from CCPRestSDK import REST
import ConfigParser

# 主帐号
accountSid = '8a216da86488ce480164a614c1c80e56'

# 主帐号Token
accountToken = 'eea88b3051434023af34f468842b9c6c'

# 应用Id
appId = '8a216da864a7c9e30164a7f34045003e'

# 请求地址，格式如下，不需要写http://
serverIP = 'app.cloopen.com'

# 请求端口
serverPort = '8883'

# REST版本号
softVersion = '2013-12-26'


# 发送模板短信
# @param to 手机号码
# @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
# @param $tempId 模板Id
class CCP(object):
    """发送短信工具类,单例模式"""
    def __new__(cls):
        if not hasattr(cls, "instance"):
            obj = super(CCP, cls).__new__(cls)

            obj.rest = REST(serverIP, serverPort, softVersion)
            obj.rest.setAccount(accountSid, accountToken)
            obj.rest.setAppId(appId)

            cls.instance = obj

        return cls.instance

    def send_template_sms(self, to, datas, temp_id):
        """调用云通讯的工具rest发送短信"""
        try:
            result = self.rest.sendTemplateSMS(to, datas, temp_id)
        except Exception as e:
            raise e
        status_code = result.get("statusCode")
        if status_code == "000000":
            return 0
        else:
            return -1


# sendTemplateSMS(手机号码,内容数据,模板Id)
if __name__ == '__main__':
    cpp = CCP()
    cpp.send_template_sms("13007549761", ["1234", 5], 1)
