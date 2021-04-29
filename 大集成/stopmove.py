import math
import matplotlib.pyplot as plt
from shapely.geometry import MultiPoint, Polygon
import os
import json
from datetime import datetime
import time
# 计算两点的距离，单位为m
'''
lat1 纬度
lon1 经度
lat2 纬度
lon2 经度
return 距离
'''


def getDistance(lon1, lat1, lon2, lat2):
    radLat1 = lat1 * math.pi / 180.0  # 角度转换为弧度
    radLat2 = lat2 * math.pi / 180.0
    a = radLat1 - radLat2  # 两点纬度之差
    b = (lon1 - lon2) * math.pi / 180.0  # 两点经度之差
    # 计算两点距离的公式
    s = 2 * math.asin(
        math.sqrt(math.pow(math.sin(a / 2), 2) + math.cos(radLat1) * math.cos(radLat2) * math.pow(math.sin(b / 2), 2)))
    # 弧长乘地球半径，半径为米
    s = s * 6378137.0
    # 精确距离的数值，可有可无,返回四舍五入的浮点数
    s = round(s * 10000) / 10000
    return s


# 计算速度，单位为m/s
'''
lat1 纬度
lon1 经度
lat2 纬度
lon2 经度
t1 时间戳
t2 时间戳
return 速度
'''


def getSpeed(lon1, lat1, lon2, lat2, t):
    d = getDistance(lon1, lat1, lon2, lat2)
    s = d / float(t)
    return round(s, 2)


# 计算方向角，单位为°
'''
lat1 纬度
lon1 经度
lat2 纬度
lon2 经度
return 方位角
'''


def getAngle(lon1, lat1, lon2, lat2):
    lat1_rad = lat1 * math.pi / 180
    lon1_rad = lon1 * math.pi / 180
    lat2_rad = lat2 * math.pi / 180
    lon2_rad = lon2 * math.pi / 180
    y = math.sin(lon2_rad - lon1_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
        math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad)
    bearing = math.atan2(y, x)
    bearing = 180 * bearing / math.pi
    bearing = float((bearing + 360.0) % 360.0)
    return round(bearing, 2)



def geo_to_miller(lon,lat):
    '''
    :param lon: 经度
    :param lat: 纬度
    :return: 米勒投影转换结果---米
    '''
    L = 6381372 * math.pi * 2
    W = L
    H = L / 2
    mill = 2.3
    x = lon * math.pi / 180
    y = lat * math.pi / 180
    y = 1.25 * math.log(abs(math.tan(0.25 * math.pi + 0.4 * y)))
    x = (W / 2) + (W / (2 * math.pi)) * x
    y = ( H / 2 ) - ( H / ( 2 * mill ) ) * y
    result = [x,y]
    return result



# 计算两点时间间隔位于领域内的部分
# 计算逗留时间，需要计算相邻两点之间位于领域内的部分，然后按比例计算逗留时间
'''
data 数据列表
x1 索引
x2 索引
x 点x的索引
r 邻域半径
return 时间
'''
# x是目标点
def calculateinsidetime(data, x1, x2, x, r):
    d1 = getDistance(data[x1][2], data[x1][1], data[x][2], data[x][1])  # x1到中心点的距离
    d2 = getDistance(data[x2][2], data[x2][1], data[x][2], data[x][1])  # x2到中心点的距离
    c = getDistance(data[x1][2], data[x1][1], data[x2][2], data[x2][1]) # x1和x2的距离
    # 如果两个点都位于领域之内，逗留时间就是两点之间的时间差
    if d1 <= r and d2 <= r:
        return math.fabs(data[x1][3] - data[x2][3])  # 返回时间差
    # 如果两个点都不在领域之中
    # 先判断轨迹是否与领域相交，计算相邻两点的直线方程，然后计算目标点与直线之间的距离，若小于半径则相交
    # 勾股定理：求出弦长，最后用领域内的距离做比求出逗留时间
    elif d1 > r and d2 > r:
        if data[x1][2] == data[x2][2] and data[x1][1] == data[x2][1]:
            return math.fabs(data[x1][3] - data[x2][3])
        # 设 O(x0，y0) a(x1,y1)  b(x2,y2)
        # 直线的一般公式： Ax + By +C = 0
        # A = y1 - y2
        # B = x2 - x1
        # C = x1*y2 - x2y1
        # 点到直线的距离：|A*x0 + B*y0 +C| / sqrt(A*A + B*B)
        # 余弦定理求角oab，角oba
        # y--0,x--1 <<--->> list(miller.from_latlon(lat, lon))
        tran1 = geo_to_miller(data[x1][2],data[x1][1])
        a1 = tran1[0]
        b1 = tran1[1]
        tran2 = geo_to_miller(data[x2][2],data[x2][1])
        a2 = tran2[0]
        b2 = tran2[1]
        A = b1 - b2
        B = a2 - a1
        C = a1 * b2 - a2 * b1
        u = abs(A * data[x][2] + B * data[x][1] + C)
        d = float(math.sqrt(A * A + B * B))
        dist = u/d
        if dist < r:
            print('cunzai')
            u1 = d1 * d1 + c * c - d2 * d2
            down1 = float(2 * d1 * c)
            CosA = u1 / down1
            u2 = d2 * d2 + c * c - d1 * d1
            down2 = float(2 * d2 * c)
            CosB = u2 / down2
            if CosA > 0 and CosB > 0:
                dist1 = 2 * math.sqrt(r * r - dist * dist)
                return dist1 / c * math.fabs(data[x1][3] - data[x2][3])
        else:
            return 0.0
    # 一个点在领域之内另一点在领域之外
    elif (d1 < r and d2 > r) or (d1 > r and d2 < r):
        # 使d2>d1若j点不在领域内，而j+1点在领域内，交换长度，长的是d2
        if d2 < d1:
            temp = d1
            d1 = d2
            d2 = temp
        # j点在领域内而j+1点不在领域内
        a = d1
        b = d2
        d = ((a * a + c * c - b * b) / c + math.sqrt((a * a + c * c - b * b) / c * (a * a + c * c - b * b) / c + 4 * r * r - 4 * a * a)) / 2.0
        return d / c * math.fabs(data[x1][3] - data[x2][3])

# def calculateinsidetime(data,x1,x2,x,r):
#     d1=getDistance(data[x1][2],data[x1][1],data[x][2],data[x][1]) # x1到中心点的距离
#     d2=getDistance(data[x2][2],data[x2][1],data[x][2],data[x][1]) # x2到中心点的距离
#     # print(d1,d2)
#     # 如果两个点都位于领域之内，逗留时间就是两点之间的时间差
#     if d1 <= r and d2 <= r:
#         return math.fabs(data[x1][3] - data[x2][3])
#     if d1 > r and d2 > r:
#         return 0.0
#     if d2 < d1:
#         temp = d1
#         d1 = d2
#         d2 = temp
#     a = d1
#     b = d2
#     c = getDistance(data[x1][2], data[x1][1], data[x2][2], data[x2][1])
#     d = ((a * a + c * c - b * b) / c + math.sqrt((a * a + c * c - b * b) / c * (a * a + c * c - b * b) / c + 4 * r * r - 4 * a * a)) / 2.0
#     return d / c * math.fabs(data[x1][3] - data[x2][3])
# 计算停留指数，使用高斯核函数计算，r = 30m
# GPS的误差在15米左右，设定领域的范围在30米到90米之间

'''
data 数据列表
r 邻域半径
'''
'''
停留指数是对每一个轨迹点进行计算，在空间上设定一个领域，领域内包含一系列的点，而停留指数的计算需要累积每一个领域点的时空贡献。
而时空贡献的本质就是带空间权重的逗留时间。
第三步
'''


def calculateindex(data, r):
    if r > 0:  # 健壮性
        data = [i for i in data if len(i)==6]
        # data = [i for i in data if len(i)==]
        for i in range(len(data)):
            i2, i3, i4, i5 = 0.0, 0.0, 0.0, 0.0
            # 往后算
            for j in range(i, len(data) - 1, 1):
                # print(i,j)
                # 对每一点计算领域内点的时空贡献
                # print(j)
                # print(data[j])
                i1 = calculateinsidetime(data, j, j + 1, i, r)
                # i1为停留时间
                i2 += data[j][5] * i1
                # 索引5--速度乘时间，停留的距离，累加
                i3 += getDistance(data[j][2], data[j][1], data[j + 1][2], data[j + 1][1])
                i4 = getDistance(data[i][2], data[i][1], data[j + 1][2], data[j + 1][1])
                if i1 > 0.0:
                    if i3 != 0:
                        i5 += i2 / i3 * math.exp(-i4 * i4 / 2.0 / r / r) * i1
                    if i3 == 0:
                        i5 += math.exp(-i4 * i4 / 2.0 / r / r) * i1

            i3 = 0.0
            i2 = 0.0
            # 往前算
            for j in range(i, 0, -1):
                i1 = calculateinsidetime(data, j, j - 1, i, r)
                i2 += data[j - 1][5] * i1
                i3 += getDistance(data[j][2], data[j][1], data[j - 1][2], data[j - 1][1])
                i4 = getDistance(data[i][2], data[i][1], data[j - 1][2], data[j - 1][1])
                if i1 > 0.0:
                    if i3 != 0:
                        i5 += i2 / i3 * math.exp(-i4 * i4 / 2.0 / r / r) * i1
                    if i3 == 0:
                        i5 += math.exp(-i4 * i4 / 2.0 / r / r) * i1
            data[i].append(i5)

# 数据列表增加一列tag，根据停留指数阈值判断停留，标识停留
'''
data 数据列表
thre 停留指数阈值
'''


def indexdata(data, thre):
    ty = 0
    # print(len(data[1]))
    data = [i for i in data if len(i) == 7]
    if data[0][6] < thre:
        data[0].append(0)
    else:
        data[0].append(1)
        ty += 1
    for j in range(1, len(data)):
        if data[j][6] < thre:
            data[j].append(0)  # 小于停留指数标记为0，无状态，标数字的是停留
        # 停留的段递增标号
        elif data[j][6] >= thre and data[j - 1][7] == 0:
            ty += 1
            data[j].append(ty)
        elif data[j][6] >= thre and data[j - 1][7] != 0:
            data[j].append(ty)


# 去除停留时间小的停留段，10s
'''
data 数据列表
maxmov 阈值
'''


def delete(data, maxmov):
    # end,star = -1,-1
    # if data[0][7] != 0:
    # 	star = 0

    # 对第0个点进行判断，如果是停留点，那么就找到了停留段的起点了，此时将star标记为0
    # print(len(data[1]))
    data = [i for i in data if len(i) == 8]
    if data[0][7] != 0:
        star = 0
    # 若起始点并非停留点，star标记为-1
    else:
        star = -1
    end = -1
    # 刚开始的时候，end，star的初始值都为-1，若找到起始点和末尾点，则赋值为1
    ty = 1
    # 循环以遍历，从第一个点开始，到最后一个点，涉及前后相邻两个点的操作，故遍历尾点的索引为len(data)-1
    # 涉及到前后相邻两个点之间的操作。所以对于整个数据来讲，首尾的数据都先提前空出来，先做出判断
    for i in range(1, len(data) - 1):
        if data[i][7] != 0 and data[i - 1][7] == 0:  # 寻找停留段的起点【第i点为停留点，而前一个点为非停留点，此时第i个点就是停留段的起点】，找到之后star初始化为i
            star = i
        if data[i][7] != 0 and data[i + 1][7] == 0:  # 寻找停留段的终点【第i点为停留点，而第i+1点为非停留点，，此时第i点就是停留段的终点】，找到之后end初始化为i+1【为什么是i+1点】
            end = i + 1
            if end > star:  # 保证健壮性
                t = data[end][3] - data[star][3]  # 计算停留段的时间间隔
                if t < maxmov:  # 时间间隔小于阈值
                    ty = data[star][7]  # 该停留段的标识号提出来
                    for k in range(star, end):  # 将停留段中所有点的标识改为非停留
                        data[k][7] = 0
                else:
                    for m in range(star, end):  # 时间间隔大于阈值，将该段所有点的标识改为统一标识，标识是从1开始的，每多一段停留标识就自增1
                        data[m][7] = ty
                    ty += 1  # 每次标识完成，要自增1，处于大循环体内，小循环外
    if data[len(data) - 1][7] != 0:  # 如果数据的最后一个点是停留点
        end = len(data)  # end赋值
        for n in range(star, end):  # 从最近的star开始一直到最后一个点，状态标识改变【存疑：若最近的一段停留时间间隔太小被处理为非停留，是否会因此再次被改为停留】
            data[n][7] = ty


# 合并相邻时间间隔小于30s的停留段，30s
# 潜在停留段的合并
'''
data 数据列表
minmov 阈值
'''


def combine(data, minmov):
    j = 0
    # print(len(data[1]))
    data = [i for i in data if len(i) == 8]
    while data[j][7] == 0 or data[j + 1][7] != 0:  # 循环结束的条件就是：a非 & b非
        if j == len(data)-2 and data[j+1][7] == 1:
            print("该轨迹全部为停留")
            return
        if j == len(data) - 1:
            print("该轨迹无停留")
            break
        j += 1  # j记录了第一个停留段结束的位置
        # print('j',j-1,data[j-1][7])
    ty = 1  # 初始化star以及end的值
    star = -1
    end = -1
    for i in range(j, len(data) - 1):  # 从第一个停留段结束位置开始到最后一个点
        # 上一个停留段结束的位置
        if data[i][7] == 0 and data[i - 1][7] != 0:  # 找到前一个停留结束的位置，得到索引值赋值star
            star = i
        # 下一个停留段开始的位置
        if data[i][7] == 0 and data[i + 1][7] != 0:  # 找到下一个停留段开始的位置，得到索引值赋值end
            end = i + 1
            if end > star:  # 健壮性
                t = data[end][3] - data[star][3]  # 求得两个停留段之间的时间间隔
                y = end
                if t < minmov:  # 若时间间隔小于阈值
                    while data[y][7] != 0:  # 将后一段的停留标识改为前一段的标识，实现了合并
                        data[y][7] = ty
                        y += 1
                        if y == len(data):
                            break
                else:  # 若停留时间间隔大于阈值，标识号后移一位，重新标号
                    ty += 1
                    while data[y][7] != 0:  # 对于停留段重新标号
                        data[y][7] = ty
                        y += 1
                        if y == len(data):  # 健壮性
                            break


# 生成凸包
'''
lon_ 停留段经度列表
lat_ 停留段纬度列表
return polygon 凸包
'''


def get_convex_hull(lon_, lat_):
    lons, lats = lon_, lat_
    lon_lats = list(zip(lons, lats))  # zip将经纬度打包为元组的列表
    polygon = MultiPoint(lon_lats).convex_hull  # 利用模块的函数计算多个点的凸包，凸包是一个包含多个点的列表
    return polygon


# 停留段生成含凸包的列表
'''
data 数据列表
stopnum 停留段个数
return hullsum
hullsum第一列为停留段所有轨迹点的索引，第二列为停留段所有轨迹点的pid，第三列为凸包，第四列为停留段起始时间，
第五列为停留段结束时间，第六列为停留段的标识，第七列为标识，为根据凸包合并停留段准备
'''


def toconvexHull(data, stopnum):
    hullsum = []
    flag = 0
    for j in range(1, stopnum + 1):  # 对所有的停留段都进行遍历，找到凸包，之后根据凸包来合并停留
        hull = []  # 每次对新段进行处理时，这一系列的中间列表都会刷新，到最后，这些中间列表都会被存储在一个大列表
        pix = []
        pid = []
        lat = []
        lon = []  # 一系列的中间列表
        for i in range(flag, len(data)):  # 遍历所有的数据点
            if data[i][7] == j:  # 如果当前点的标识表明该点位于当前的停留段
                pix.append(i)  # 提取该点的索引值，pid，以及经纬度坐标
                pid.append(data[i][0])
                lat.append(data[i][1])
                lon.append(data[i][2])
            if data[i][7] == j + 1 and j < stopnum:  # 健壮性，往后遍历时，若遍历到之后的停留段
                flag = i  # 提取出当前遍历点的索引值，下次遍历时从该点开始，不必重复遍历之前的点
                break
        hull.append(pix)  # 0 pix
        hull.append(pid)  # 1 pid
        polygon = get_convex_hull(lon, lat)  # 跟据经纬度找到凸包
        hull.append(polygon)  # 2 hull                         # 将凸包加到大列表中去
        hull.append(data[pix[0]][3])  # 3 starttime
        if pid[-1] != data[-1][0]:
            hull.append(data[pix[-1] + 1][3])  # 4 endtime
        else:
            hull.append(data[pix[-1]][3])
        hull.append(j)  # 5 stoptag
        hull.append(0)  # 6 identag
        hullsum.append(hull)
    return hullsum


# 绘制凸包
'''
hullsum 含凸包的列表
data 数据列表
'''


def drawhull(hullsum, data):
    for i in range(len(hullsum)):
        pix = hullsum[i][0]
        pn = hullsum[i][2]
        print(pn.area)
        lons = []
        lats = []
        lat = []
        lon = []
        for j in range(len(pix)):
            lons.append(data[pix[j]][2])
            lats.append(data[pix[j]][1])
        if pn.area != 0:
            for k in range(len(pn.exterior.coords)):
                lon.append(pn.exterior.coords[k][0])
                lat.append(pn.exterior.coords[k][1])
        if pn.area == 0:
            for k in range(len(pn.coords)):
                lon.append(pn.coords[k][0])
                lat.append(pn.coords[k][1])
        plt.plot(lons, lats, 'o')
        plt.plot(lon, lat, 'r--^', lw=2)
    plt.show()


# 根据停留段凸包相交以及时间间隔小于2*minmov合并停留段
'''
hullsum 含凸包的列表
data 数据列表
minmov 阈值【有意义的移动应该持续的最短时间】
return hullsum 停留段合并后的列表
'''
def combine1(hullsum, data, minmov):
    i = 0  # 做循环遍历，对含凸包的列表中所有的停留段做处理，从i = 0开始
    while (hullsum[i][6] == 0):  # 若第七列标识为0
        hullsum[i][6] = 1  # 将第七列的标识改为1
        t = 0
        num = 0
        for j in range(0, len(hullsum)):  # 循环嵌i是一层，j是二层
            # for j in range(i+1,len(hullsum)):                # 若为同一个停留段，此次循环跳到下一个，意思是每一个停留段都要和其他的停留段进行比较，本身不比较
            if j == i:
                continue
            # j停留段时间顺序完全在i后面
            if hullsum[j][3] > hullsum[i][4]:  # 如果二层循环j的起始时间大于一层循环的终止时间，即两个停留段没有相交部分【此时j停留是i停留段之后那一段】
                t = hullsum[j][3] - hullsum[i][4]  # 求出两段停留时间的时间间隔
            # j停留段时间顺序在i停留段中间
            if hullsum[j][3] > hullsum[i][3] and hullsum[j][4] < hullsum[i][4]:  # j在i中
                t = 1
            # j停留段时间顺序完全在i前面
            if hullsum[j][4] < hullsum[i][3]:  # j在i前
                t = hullsum[i][3] - hullsum[j][4]
            # i停留段时间顺序在j停留段中间                                                    # i在j中
            if hullsum[i][3] > hullsum[j][3] and hullsum[i][4] < hullsum[j][4]:
                t = 1
            # 还有没有两个停留段只有一部分相交的情况
            # 不要求连续，凸包相交    【凸包合并的条件】                                        # 两个凸包的时间间隔大于零，且小于二倍的时间阈值，并且凸包重叠【intersects判断两个凸包是否交叉】
            if t > 0 and t < 2 * minmov and hullsum[i][2].intersects(hullsum[j][2]):
                for n in range(len(hullsum[j][0])):  # hullnum[j][0]代表该停留段的所有点的索引值列表，对所有的点进行处理
                    hullsum[i][0].append(hullsum[j][0][n])  # 将二层循环j停留段的所有点的索引值加到一层循环i停留段中去，表明两个段已经合并
                hullsum[i][0].sort()  # 排序
                for k in range(len(hullsum[j][1])):  # 将就停留段的pid也添加到i停留段中去
                    hullsum[i][1].append(hullsum[j][1][k])
                hullsum[i][1].sort()  # 排序
                lats = []
                lons = []
                pix = hullsum[i][0]
                for m in range(len(pix)):  # 提取出来新的pix--索引值，在根据索引值将新点的经纬度提取出来
                    lats.append(data[pix[m]][1])
                    lons.append(data[pix[m]][2])
                hullsum[i][2] = get_convex_hull(lons, lats)  # 生成新的凸包，替换原来的凸包
                # hullsum starttime and endtime
                hullsum[i][3] = min(hullsum[i][3], hullsum[j][3])  # 新的起始时间
                hullsum[i][4] = max(hullsum[i][4], hullsum[j][4])  # 新的终止时间
                # stoptag
                hullsum[i][5] = min(hullsum[i][5], hullsum[j][5])  # 停留段标识，用小标识替代大标识，合并到前面的停留段中去
                hullsum[i][6] = 0
                hullsum[j][6] = 2  # 2表示已被新凸包替代
                if j < i:
                    num += 1
        if hullsum[i][6] == 1:  # 1表示该段已经被处理过了，故而i自增继续循环
            i += 1
        if num > 0:  # 如果是后边的凸包被前面的凸包合并，减去num得到正确的i以确保循环
            i = i - num
        g = 0
        while g < len(hullsum):  # 健壮性
            # print(i,len(hullsum),g,hullsum[g][6])                                      # 把被合并的多余停留段删除
            if hullsum[g][6] == 2:
                del hullsum[g]
                g -= 1
            g += 1
        # >= or ==
        if i >= len(hullsum):  # 健壮性
            break
    print('len of hullsum', len(hullsum))
    # print(hullsum)
    return hullsum


# 修改数据的停留标识
'''
data 数据列表
hullsum 含凸包的列表
'''
def changetag(data, hullsum):
    for i in range(len(hullsum)):  # i表明是第i个停留段
        pix = hullsum[i][0]  # 第i个停留段的第0项是pix，即停留段所有点的索引值
        for j in range(len(pix)):  # 将第i个停留段上点的标识改成i+1
            data[pix[j]][7] = i + 1
    return data


# 生成停留段MultiPoint的几何中心
'''
hullsum 含凸包的列表
data 数据列表
return stop_pt 停留段的几何中心
'''
def generate_stop_pt(hullsum, data):
    stop_pt = []
    for i in range(len(hullsum)):  # 对每个停留段进行遍历
        pt = []
        pix = hullsum[i][0]  # 提取pix
        lats = []
        lons = []
        for j in range(len(pix)):  # 对第i个停留段中的所有点进行
            lats.append(data[pix[j]][1])  # 提取这些点的经纬度
            lons.append(data[pix[j]][2])
        lon_lats = list(zip(lons, lats))  # 打包合并生成一个大列表，包含所有的停留点的经纬度坐标
        MP = MultiPoint(lon_lats)  # multipoint构造函数接收一系列的点元组，形成了一个multipoint类
        # print('type of MP',type(MP))
        c_lon = MP.centroid.x
        c_lat = MP.centroid.y  # 计算质心的坐标
        plt.scatter(c_lon, c_lat, c='black')  # 画出散点图
        c_time = hullsum[i][3]  # 提出停留段的起始时间
        pt.append(i)  # 停留段的序号，第几个停留段
        pt.append(round(c_lat, 5))  # 几何中心坐标，四舍五入到小数点后五位
        pt.append(round(c_lon, 5))
        pt.append(c_time)
        stop_pt.append(pt)  # stop_pt is a big list,it contains a lot of small lists which include :i coordinates of centroid and start time of residence segment
    # print(stop_pt)
    return stop_pt


# 修改原数据，删除原有停留段，替代为虚拟轨迹点
'''
data 数据列表【这里的data是存储原始数据的data数据项比较多，即data_i】
hullsum 含凸包的列表，
stop_pt 停留段的几何中心【要利用的部分】
'''


def changedata(data, hullsum, stop_pt):
    if hullsum == 0:  # first 如果data中没有停留段
        for i in range(len(data)):  # data[i]代表一个点的全部信息，标记为0
            data[i].append(0)
    else:  # 若存在停留段
        for i in range(len(data)):  # 标记为0
            data[i].append(0)
        pix = []
        n = 0
        for i in range(len(hullsum)):  # 对所有的停留段进行遍历
            pix = hullsum[i][0]  # 提取第i个停留段的pix
            # data[pix[0]][1] = stop_pt[i][1]
            data[pix[0]][2] = stop_pt[i][1]  # lat     # 用第i个停留段的几何中心的经纬度来替换停留段起始点的经纬度
            # data[pix[0]][2] = stop_pt[i][2]
            data[pix[0]][3] = stop_pt[i][2]  # lon
            data[pix[0]][-1] = 1  # 第i个停留段的起点的标识改为1
            for j in range(1, len(pix)):  # 第i个停留段：起始点之后的点的标识改为2
                data[pix[j]][-1] = 2  # 改一次n自增一
                n += 1
        # print(data)                                 # 循环完成之后，data中所有的停留段中的点都被修改
        k = 0
        while k < len(data):  # 对data中所有的点进行遍历
            if data[k][-1] == 2:  # 删除停留段中的非起点
                del data[k]
            else:
                k += 1  # 删除完毕之后，data中只剩下无状态点和所有停留段的起点【此时的起点其实是该停留段的几何中心点,之前已经被替换了】


# 读取数据，存为列表
'''
trajData 文件00路径
return data,data_i
data为用于整个数据处理的列表
--new：data的轨迹点之包含四项数据[pid,lat,lon,time]  索引值：0-3
data_i为存储原数据的列表
'''
def readtolist(trajData):
    data = []
    data_i = []
    with open(trajData) as f:
        for line in f.readlines():
            l = []
            li = []
            line = line.strip('\n')
            temp = line.split(',')
            l.append(int(temp[0]))  # pid
            l.append(float(temp[2]))  # lat
            l.append(float(temp[3]))  # lon
            l.append(float(temp[6]))  # time
            li.append(int(temp[0]))
            li.append(temp[1])  # name
            li.append(float(temp[2]))
            li.append(float(temp[3]))
            li.append(int(temp[4]))  # speed
            li.append(int(temp[5]))  # angle
            li.append(int(temp[6]))
            li.append(int(temp[7]))  # state
            data.append(l)
            data_i.append(li)
    return data, data_i


# 计算速度和方向角，添加到data列表
'''
data 数据列表
--new:多添加两项数据，索引值从0到5；索引4--方向角；索引5--速度
'''
def com_data(data):
    # print(len(data[1]))
    data = [i for i in data if len(i)==4]
    if len(data) == 1:
        data[0].append(0.0)
        data[0].append(0.0)
    if len(data) > 1:
        for j in range(len(data) - 1):
            t2 = data[j + 1][3] - data[j][3]
            data[j].append(getAngle(data[j][2], data[j][1], data[j + 1][2], data[j + 1][1]))
            data[j].append(getSpeed(data[j][2], data[j][1], data[j + 1][2], data[j + 1][1], t2))
        data[j + 1].append(0.0)
        data[j + 1].append(0.0)
    # 对最后的一个点进行处理


# 绘制轨迹数据和停留
'''
data 数据列表
'''
def drawdata(data):
    plt.figure()  # 画图前导入一张画板
    mov = []
    sto = []
    for k in range(len(data)):  # 对所有的点进行遍历处理
        te = []
        if data[k][7] == 0:  # 若该点为无状态
            te += [data[k][2], data[k][1]]  # 将无状态点的经纬度添加到te中去
            mov.append(te)  # 放到大列表mov中去,若干个小列表，代表一个个点的经纬度
        else:
            te += [data[k][2], data[k][1]]  # 否则将停留点放到te中
            sto.append(te)  # 放到大列表sto中去
    x1, y1 = zip(*mov)  # x1为无状态点的纬度，y1为经度【两者均为元组】
    x2, y2 = zip(*sto)  # x2，y2同理
    plt.scatter(x1, y1, c="green")
    plt.scatter(x2, y2, c="red")  # scatter用于生成散点图x，y长度相等
    plt.show()  # 红色是停留点，绿色是无状态点


# 文件输出
'''
trajData 文件路径
path 输出路径
data 数据列表【这里的data指的是存储原始数据的data，即data_i】
'''
def totxt(trajData, path, data):
    # fname字符串分割.txt前面的部分
    name = trajData.split('.')
    name = name[0].split('\\')
    txt_file2 = open(path + '\\' + name[-1] + '_s.txt', "w")
    for m in range(len(data)):
        lispoint = []
        lispoint += [str(m + 1), str(data[m][1]), str(data[m][2]), str(data[m][3]), str(data[m][4]), str(data[m][5]),
                     str(data[m][6]), str(data[m][7]), str(data[m][8])]
        if lispoint != "":
            lispoint = ",".join(j for j in lispoint)
            lispoint += "\n"
            txt_file2.writelines(lispoint)
    txt_file2.close()


# 先处理好轨迹的停留文件，然后再读入
'''
trajData 文件路径
storepath 输出路径
r 邻域半径，设置为30m
stopthre 停留指数阈值，设置为60
dr 剔除停留段阈值，设置为10s
mr 合并停留段阈值，设置为30s
'''


def trans(data):
    data1 = []
    for i in range(len(data)):
        row = []
        row.append(data[i][0])  # pid
        row.append(json.loads(data[i][2])['coordinates'][0])  # lon
        row.append(json.loads(data[i][2])['coordinates'][1])  # lat
        row.append(data[i][3])  # time
        data1.append(row)
    return data1


def main_stop(data):
    data1 = trans(data)
    for i in data1:
        i[3] = str(i[3])
    fr1 = data1
    for i in range(len(fr1)):
        timestr = fr1[i][3]
        try:
            datetime_obj = datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S.%f")
            obj_stamp = float(time.mktime(datetime_obj.timetuple()) * 1000.0 + datetime_obj.microsecond / 1000.0)
        except ValueError:
            datetime_obj = datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S")
            obj_stamp = float(time.mktime(datetime_obj.timetuple()) * 1000.0 + datetime_obj.microsecond / 1000.0)
        fr1[i][3] = obj_stamp / 1000
        fr1[i][1] = float(fr1[i][1])
        fr1[i][2] = float(fr1[i][2])
    com_data(fr1)
    data2 = main_stop1(fr1,32640,600,10,30)
    segnum = []
    coo = []
    for i in range(len(data2)):
        segnum.append(data2[i][7])
        items = []
        if data2[i][7] != 0:
            data[i][7]=3
            items.append(data2[i][2])
            items.append(data2[i][1])
            items.append(data2[i][7])
            coo.append(items)
    segmax = max(segnum)
    for i in coo:
        if i == []:
            del i
    if coo == []:
        coo = '该轨迹无停留！'
    results = {'Mode': 'Stop', 'StopNums': segmax, 'coordinates': coo}
    print(len(results['coordinates']))

    return coo

def main_stop1(data, r, thre, dr, mr):
    '''
    :param r: 领域半径--m
    :param thre: 停留指数阈值
    :param dr: 删除最小时间
    :param mr: 合并最小时间
    :return: data
    '''
    # data = []
    # data_i = []
    # data,data_i = readtolist(trajData)
    # com_data(data)
    calculateindex(data, r)
    indexdata(data, thre)
    # print(data[2])
    # print('ind',len(data[3]))
    delete(data, dr)
    # print('dle')
    # print(data[2])
    combine(data, mr)
    lasttag = []
    for i in range(len(data)):
        lasttag.append(data[i][7])
    lastnum = max(lasttag)
    # print('stopmax:', lastnum)
    # drawdata(data)
    if lastnum == 0:
        hullsum1 = 0
        stop_pt = 0
    if lastnum > 0:
        hullsum = toconvexHull(data, lastnum)
        # 生成含凸包的列表
        # drawhull(hullsum,data)
        hullsum1 = combine1(hullsum, data, mr)
        # 根据凸包合并
        # mr ：阈值【一个有意义的移动应该持续的最短时间】
        # drawhull(hullsum1,data)
        # print(hullsum1 == hullsum)
        # 判断两者是否相同
        data = changetag(data, hullsum1)
    return data





