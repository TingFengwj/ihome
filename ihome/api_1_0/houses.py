# coding:utf-
from flask import current_app, jsonify, json, g, request, session

from ihome import redis_store, constants, db
from ihome.models import Area, User, Facility, House, HouseImage
from ihome.utils.commons import login_required
from ihome.utils.image_storage import storage
from ihome.utils.response_code import RET
from . import api


@api.route("/areas")
def get_area_info():
    """获取城区信息"""
    # 先从redis中获取缓存数据
    try:
        areas_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
        areas_json = None
    if areas_json is None:
        # 查询数据库,获取城区信息
        try:
            areas_list = Area.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询城区信息异常")

        areas = []
        for area in areas_list:
            areas.append(area.to_dict())

        # 将数据在redis中保存一份
        # 1将数据转换未json
        area_json = json.dumps(areas)

        # 2将数据在redis中存储
        try:
            redis_store.setex("area_info", constants.AREA_INFO_REDIS_EXPIRES, area_json)
        except Exception as e:
            current_app.logger.error(e)
    else:
        # 表示redis中有缓存, 直接使用的是缓存数据
        current_app.logger.info("hit redis area info")
    # 从redis中去取的json数据或者从数据库中查询并转为的json数据
    # areas_json = '[{"aid":xx, "aname":xxx}, {},{}]'

    return '{"errno": 0, "errmsg": "查询城区信息成功", "data":{"areas": %s}}' % areas_json, 200, \
           {"Content-Type": "application/json"}


@api.route("/user/houses", methods=["GET"])
@login_required
def get_user_houses():
    """获取房东发布的房源信息条目"""
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
        houses = user.houses

        # houses = House.query.filter_by(user_id=user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取数据失败")

    # 将查询到的房屋信息转换为字典存放到列表中
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())
    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_list})


@api.route("/houses/info", methods=["POST"])
@login_required
def sava_house_info():
    """保存房屋的基本信息,前段发送过来的json数据"""
    # 数据参数
    house_data = request.get_json()
    if house_data is None:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    title = house_data.get("title")  # 房屋名称的标题
    price = house_data.get("price")  # 房屋价钱
    area_id = house_data.get("area_id")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房间布局(几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数
    max_days = house_data.get("max_days")  # 最大入住天数

    # 校验参数
    if not all(
            [title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="参数有误")

    # 保存信息
    user_id = g.user_id
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )
    # 处理房屋的设施信息
    facility_id_list = house_data.get("facility")
    if facility_id_list:
        # 表示用户勾选了房屋设施
        # 过滤用户传送的不合理的设施id
        # select * from facility where id in (facility_id_list)
        try:
            facility_list = Facility.query.filter(Facility.id.in_(facility_id_list)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库异常")

        # 为房屋添加设施信息
        if facility_list:
            house.facilities = facility_list

    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    # 返回
    return jsonify(errno=RET.OK, errmsg="保存成功", data={"house_id": house.id})


@api.route("/houses/image", methods=["POST"])
@login_required
def save_house_image():
    """保存房屋的图片"""
    # 获取参数 房屋的图片、房屋编号
    house_id = request.form.get("house_id")
    image_file = request.files.get("house_image")

    # 校验参数
    if not all([house_id, image_file]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if house is None:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 上传房屋图片到七牛中
    image_data = image_file.read()
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="保存房屋图片失败")

    # 保存图片信息到数据库中
    house_image = HouseImage(
        house_id=house_id,
        url=file_name
    )
    db.session.add(house_image)

    # 处理房屋基本信息中的主图片
    if not house.index_image_url:
        house.index_image_url = file_name
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存图片信息失败")

    image_url = constants.QINIU_URL_DOMAIN + file_name
    return jsonify(errno=RET.OK, errmsg="保存图片成功", data={"image_url": image_url})


@api.route("/houses/index", methods=["GET"])
def get_houses_index():
    """获取主页幻灯片展示的房屋基本信息"""
    # 从缓存中尝试获取数据
    try:
        ret = redis_store.get("home_page_data")
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("hit house index info redis")
        # 因为redi中保存的是json字符串, 所以直接进行字符串的拼接返回
        return '{"errno":0, "errmsg":"OK","data":%s}' % ret, 200, {"Content-Type": "application/json"}
    else:
        try:
            # 查询数据库, 返回房屋订单数目最多的五条数据
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据库失败")
        if not houses:
            return jsonify(errno=RET.NODATA, errmsg="查询无数据")

        houses_list = []
        for house in houses:
            # 如果房屋未设置图片, 则跳过
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict)
            # 将数据转化为json, 并保存在redis缓存中
            json_houses = json.dumps(houses_list)
            try:
                redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
            except Exception as e:
                current_app.logger.error(e)
            return '{"errno":0, "errmsg":"ok", "data":%s}' % json_houses, 200, {"Content-Type": "application/json"}


# @api.route("/houses/<int:house_id>", methods=["GET"])
# def get_house_detail(house_id):
#     """获取房屋信息"""
#     # 前段在房屋详情页面展示时, 如果浏览页面的用户不是该房屋的物主,则展示预定按钮, 否则不展示
#     # 所以需要后端返回登录用户的user_id
#     # 尝试获取用户登录的信息,若登录,则返回给前端登录用户的user_id, 否则返回user_id=-1
#     user_id = session.get("user_id", -1)
#
#     # 校验参数
#     if not house_id:
#         return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
#
#     # 先从redis宦岑中获取信息
#     try:
#         ret = redis_store.get("house_info_%s" % house_id)
#     except Exception as e:
#         current_app.logger.error(e)
#         ret = None
#     if ret:
#         current_app.logger.info("hit house info redis")
#         return '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "houses":%s}}'%(user_id, ret), 200, {"Content-Type":"application/json"}
#
#     # 查询数据库
#     try:
#         house = House.query.get(house_id)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg="查询数据库失败")
#     if not house:
#         return jsonify(errno=RET.NODATA, errmsg="没有该数据")
#
#     #将房屋对象数据转换为字典
#     try:
#         house_data = house.to_full_dict()
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DATAERR, errmsg="数据出错")
#
#     # 存入到redis中
#     json_house = json.dumps(house_data)
#     try:
#        redis_store.setex("house_info_%s"%house_id, constants.HOUSE_DETAIL_REDIS_EXPIRES_SESSION, json_house)
#     except Exception as e:
#         current_app.logger.error(e)
#     resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, json_house), 200, {"Content-Type": "application/json"}
#     return resp
@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """获取房屋详情"""
    # 前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示，
    # 所以需要后端返回登录用户的user_id
    # 尝试获取用户登录的信息，若登录，则返回给前端登录用户的user_id，否则返回user_id=-1
    user_id = session.get("user_id", "-1")

    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数确实")

    # 先从redis缓存中获取信息
    try:
        ret = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("hit house info redis")
        return '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, ret), 200, {
            "Content-Type": "application/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 将房屋对象数据转换为字典
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据出错")

    # 存入到redis中
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_house)
    except Exception as e:
        current_app.logger.error(e)

    resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, json_house), 200, {
        "Content-Type": "application/json"}
    return resp
