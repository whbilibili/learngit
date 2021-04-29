import psycopg2
import pandas as pd
import json
import Z_algorithm
import E_algorithm
from cluster import clusterfunc
import stopmove
import speed
import port_ship
import setsail_plane




def get_all(region,type,startTime,endTime,**kwargs):
    # test(**kwargs) ** 的作用则是把字典 kwargs 变成关键字参数传递。比如上面这个代码，如果 kwargs 等于 {'a':1,'b':2,'c':3} ，那这个代码就等价于 test(a=1,b=2,c=3)
    all_func=['Speedup','Portship','Sailplane','Pattern_z','Pattern_8','Stop']
    jsonTraj = readTraj('ShowTraj', region, type, startTime, endTime)
    if jsonTraj is None:
        exit()

    for func in all_func:

        jsonStr=readTraj(func,region,type,startTime,endTime)
        #tag=0是无状态；1是Z字；2是8字；3是停留；4是加速；5是减速；6是进港；7是离港；6是起飞；7是降落


        if isinstance(jsonStr,str):
            continue
        for point in jsonTraj:
            for point_new in jsonStr:
                if point_new[0]==point[0]:
                    if point_new[2]>0:
                        point[2]=point_new[2]
                        break
                else:
                    continue
    jsonAllTraj={"coordinates":jsonTraj}
    jsonAllTraj=json.dumps(jsonAllTraj)
    return jsonAllTraj
# readtraj 整个函数对各种行为识别模式的函数调用，使用时需要传入需要的模式识别的参数，一次调用，出一种结果
def readTraj(function_for,region,type,startTime,endTime,**kwargs):
    # test(**kwargs) ** 的作用则是把字典 kwargs 变成关键字参数传递。比如上面这个代码，如果 kwargs 等于 {'a':1,'b':2,'c':3} ，那这个代码就等价于 test(a=1,b=2,c=3)
    # postgres config
    postgres_host = "127.0.0.1"               # 数据库地址
    postgres_port = "5432"       # 数据库端口
    postgres_user = "postgres"              # 数据库用户名
    postgres_password = "123456"      # 数据库密码
    postgres_datebase = "new_db"      # 数据库名字
    postgres_table1 = "airplane_traj"           #数据库中的表的名字(轨迹元数据表)
    postgres_table2 = "ship_traj"
    postgres_table3 = "radar_point"         #数据库中的表的名字（轨迹点表）
    postgres_table4 = "ship_point"


    conn = psycopg2.connect(database=postgres_datebase,user=postgres_user,password=postgres_password, port="5432")
    cur=conn.cursor()

    if function_for=="ShowTraj":  # 轨迹段的显示
        sql_command1="SELECT ST_asgeojson(trajctory) from {0} where callsign='{1}' and \"startTime\">='{2}' and  \"startTime\"<='{3}';".format(postgres_table1,type,startTime,endTime)
        sql_command2="SELECT ST_asgeojson(trajctory) from {0} where callsign='{1}' and \"startTime\">='{2}' and  \"startTime\"<='{3}';".format(postgres_table2,type,startTime,endTime)
        # callsign是飞机的名称，开始时间和结束时间要用双引号括起来，用于字段的识别，时间查询用单引号括起来
        # 时间，名称确定，选取trajctory，json格式的字符串
        #print(sql_command1)
        try: #尝试执行语句
            cur.execute(sql_command1)
            rows = cur.fetchall()
            # print('rows\n',rows)
            # 执行sql语句1，关于飞机的，然后接受返回的数据。
            if len(rows) == 0:
                cur.execute(sql_command2)
                rows = cur.fetchall()
                # 嵌套一个if，如果查询之后没有数据，那么接着对轮船数据进行查询
                if len(rows) == 0:
                    print("No data!")
                    return json.dumps("")
                # 若是轮船没有数据，返回no data，dumps是将json格式的字符串转化为python的数据结构-->字典


            single_traj = json.loads(rows[0][0])
            # rows 是一个列表，列表里只有一个元组，元组中只有一个json格式的字符串，是集合类型的字符串解释
            # single_traj 是一个字典
            # print('s_t\n',single_traj)
            for point in single_traj['coordinates']:  # 读取坐标数据，坐标数据存储在一个大列表中
                point.append(0)  # 每个点添加标注 0

            # jsonStr = json.dumps(list_traj)
            conn.close()
            return single_traj['coordinates']  # 返回坐标数据，带有标注 0
        except: # 执行失败，执行之后的语句，数据导入失败
            print("load data from postgres failure !")
            exit()
#z 字识别代码，
    elif function_for=="Pattern_z":
        sql_command1="SELECT tid from {0} where callsign='{1}' and \"startTime\">='{2}' and  \"startTime\"<='{3}';".format(postgres_table1,type,startTime,endTime)
        sql_command2="SELECT tid from {0} where callsign='{1}' and \"startTime\">='{2}' and  \"startTime\"<='{3}';".format(postgres_table2,type,startTime,endTime)
        # 选取的tid，限定条件是名称、时间，轨迹的tid
        #print(sql_command2)
        # try:
        # 执行语句，返回数据，改变类型，如果没有返回数据，则执行轮船的查询语句，执行语句。返回数据，改变类型，若没有轮船数据返回。。。
        cur.execute(sql_command1)
        rows = cur.fetchall()
        # rows 是一个列表，列表中的元素就是一个个的元组
        category="airplane"
        if len(rows) == 0:
            cur.execute(sql_command2)
            rows = cur.fetchall()
            category="ship"
            if len(rows) == 0:
                print("No data!")
                return ()
        traj_data = []
        for row in rows:
            trajID=row[0]
            if category == "airplane":
                sql_command = "SELECT ST_X(\"coordinates\"), ST_Y(\"coordinates\"), storage_time From {0} where composite_lot_number={1} ORDER BY storage_time".format(
                    postgres_table3, trajID)
            else:
                sql_command = "SELECT ST_X(point), ST_Y(point), time From {0} where tid={1} ORDER BY time".format(
                    postgres_table4, trajID)

            traj_data.append(pd.read_sql(sql_command, conn))
        # 得到的是一个dataframe格式的数据，可以通过(df.values).tolist()将df数据转化为list数据，这样就比较好操作了
        cur.close()
        conn.close()
        #print(traj_data)
        #windowLength = 12 & windowStep = 9 & angleThreshold = 30 & minLength = 17
        return Z_algorithm.main_fun(traj_data,3,3,20,3)
    # 通过z字识别代码对df数据进行处理，但是具体的内部功能不太了解

    elif function_for=="Pattern_8":
        sql_command1 = "SELECT tid from {0} where callsign='{1}' and \"startTime\">='{2}' and  \"startTime\"<='{3}';".format(
            postgres_table1, type, startTime, endTime)
        sql_command2 = "SELECT tid from {0} where callsign='{1}' and \"startTime\">='{2}' and  \"startTime\"<='{3}';".format(
            postgres_table2, type, startTime, endTime)
        # print(sql_command2)
        # try:
        cur.execute(sql_command1)
        rows = cur.fetchall()
        category = "airplane"
        if len(rows) == 0:
            cur.execute(sql_command2)
            rows = cur.fetchall()
            category = "ship"
            if len(rows) == 0:
                print("No data!")
                return ()
        traj_data = []
        for row in rows:
            trajID = row[0]
            if category == "airplane":
                sql_command = "SELECT ST_X(\"coordinates\"), ST_Y(\"coordinates\"), storage_time From {0} where composite_lot_number={1}".format(postgres_table3, trajID)
            else:
                sql_command = "SELECT ST_X(point), ST_Y(point), time From {0} where tid={1}".format(postgres_table4,trajID)
            traj_data.append(pd.read_sql(sql_command, conn))
        cur.close()
        conn.close()
        # http://127.0.0.1:5000/trajectoryAnalysis/?mode=Pattern_8&windowLength=12&windowStep=8&minLength=12
        return E_algorithm.main_fun(traj_data,3,2,2)

    elif function_for == "Cluster":
        traj_dataList = []

        sql_command1 = "SELECT tid from {0} where country='{1}' and \"startTime\">='{2}' and  \"startTime\"<='{3}';".format(
            postgres_table1, kwargs["country"], startTime, endTime)
        sql_command2 = "SELECT tid from {0} where country='{1}' and \"startTime\">='{2}' and  \"startTime\"<='{3}';".format(
            postgres_table2, kwargs["country"], startTime, endTime)

        cur.execute(sql_command1)
        rows = cur.fetchall()
        category = "airplane"
        if len(rows) == 0:
            cur.execute(sql_command2)
            rows = cur.fetchall()
            category = "ship"
            if len(rows) == 0:
                print("No data!")
                return ()

        for row in rows:
            trajID = row[0]

            if category == "airplane":
                sql_command = "SELECT tid, ST_X(\"coordinates\"), ST_Y(\"coordinates\"), storage_time From {0} where composite_lot_number={1}".format(postgres_table3, trajID)
            else:
                sql_command = "SELECT tid, ST_X(point), ST_Y(point), time From {0} where tid={1}".format(postgres_table4, trajID)
            traj_data = pd.read_sql(sql_command, conn)
            sparse_traj_data=traj_data.iloc[lambda x:x.index%10==0]
            if sparse_traj_data.iloc[0,2]>19.5:
                sparse_traj_data['st_x']+=4.0
            traj_dataList.append(sparse_traj_data)

        cur.close()
        conn.close()

        return str(clusterfunc.main_fun(traj_dataList,clusterNum=int(kwargs['clusternum'])))

    elif function_for=="Stop":
        sql_command1 = 'select atraj.tid,atraj.number from ' + postgres_table1 + ' as atraj ' + 'where atraj.callsign=' + '\'' + type + '\'' + ' and atraj."startTime" between ' + '\'' + startTime + '\'' + ' and ' + '\'' + endTime + '\'' + ';'
        #sql = 'select atraj.tid,atraj.number from public.airplane_traj as atraj join public.roi_1 as r on ST_Intersects(atraj.trajctory,r.geom) and r.name_2=' + '\'' + region + '\'' + 'where atraj.callsign=' + '\'' + name + '\'' + ' and atraj.country=' + '\'' + country + '\'' + 'and atraj."startTime" between ' + '\'' + a + '\'' + ' and ' + '\'' + b + '\'' + ';'
        sql_command2 = 'select atraj.tid,atraj.number from ' + postgres_table2 + ' as atraj ' + 'where atraj.callsign=' + '\'' + type + '\'' + ' and atraj."startTime" between ' + '\'' + startTime + '\'' + ' and ' + '\'' + endTime + '\'' + ';'

        # print(sql_command2)
        # try:
        cur.execute(sql_command1)
        rows = cur.fetchall()
        category = "airplane"
        if len(rows) == 0:
            cur.execute(sql_command2)
            rows = cur.fetchall()
            category = "ship"
            if len(rows) == 0:
                print("No data!")
                return ()
        json_forstop = {}
        index = 0  # 计数器
        jsonstop = []
        for row in rows:
            trajID = row[0]
            if category == "airplane":
                sql_command = 'select pid,composite_lot_number,ST_AsGeoJSON(\"coordinates\"),storage_time from public.radar_point where composite_lot_number=' + str(
                    trajID) + ' order by storage_time'
            else:
                sql_command = 'select pid,tid,ST_AsGeoJSON(point),time from public.ship_point where tid=' + str(
                    trajID) + ' order by time'
            cur.execute(sql_command)
            data = cur.fetchall()
            key = 'json' + str(index)
            index = index + 1
            jsonstop.append(stopmove.main_stop(data))

        cur.close()
        conn.close()
        jsonstop.insert(0,'轨迹段数：{}'.format(len(jsonstop)))
        return jsonstop

    elif function_for=="Speedup":
        sql_command1 = 'select atraj.tid,atraj.number from ' + postgres_table1 + ' as atraj ' + 'where atraj.callsign=' + '\'' + type + '\'' + ' and atraj."startTime" between ' + '\'' + startTime + '\'' + ' and ' + '\'' + endTime + '\'' + ';'
        sql_command2 = 'select atraj.tid,atraj.number from ' + postgres_table2 + ' as atraj ' + 'where atraj.callsign=' + '\'' + type + '\'' + ' and atraj."startTime" between ' + '\'' + startTime + '\'' + ' and ' + '\'' + endTime + '\'' + ';'
        json_forspeed = {}
        # print(sql_command2)
        # try:
        cur.execute(sql_command1)
        rows = cur.fetchall()
        # print('rows',rows)
        category = "airplane"
        if len(rows) == 0:
            cur.execute(sql_command2)
            rows = cur.fetchall()
            category = "ship"
            if len(rows) == 0:
                print("No data!")
                json_forspeed['json0'] = '无数据！'
                return json_forspeed
        index=0
        jsonspeed = []
        for row in rows:
            trajID = row[0]
            if category == "airplane":
                sql_command = 'select pid,composite_lot_number,ST_AsGeoJSON(\"coordinates\"),speed,extract(epoch from storage_time ::timestamp) from public.radar_point where composite_lot_number='+str(trajID)+' order by storage_time'
            else:
                sql_command = 'select pid,tid,ST_AsGeoJSON(point),speed,extract(epoch from time ::timestamp) from public.ship_point where tid='+str(trajID)+' order by time'
            cur.execute(sql_command)
            data = cur.fetchall()
            key='json'+ str(index)
            index=index+1
            #json_forspeed[key]=speed.main_fun(data)
            jsonspeed.append(speed.main_fun(data))
        cur.close()
        conn.close()

        return jsonspeed

    elif function_for=='Portship':
        sql_command1 = 'select atraj.tid,atraj.number from ' + postgres_table1 + ' as atraj ' + 'where atraj.callsign=' + '\'' + type + '\'' + ' and atraj."startTime" between ' + '\'' + startTime + '\'' + ' and ' + '\'' + endTime + '\'' + ';'
        sql_command2 = 'select atraj.tid,atraj.number from ' + postgres_table2 + ' as atraj ' + 'where atraj.callsign=' + '\'' + type + '\'' + ' and atraj."startTime" between ' + '\'' + startTime + '\'' + ' and ' + '\'' + endTime + '\'' + ';'
        json_forport = {} # 并没有被使用
        # print(sql_command2)
        # try:
        cur.execute(sql_command1)
        rows = cur.fetchall()
        category = "airplane"
        if len(rows) == 0:
            cur.execute(sql_command2)
            rows = cur.fetchall()
            category = "ship"
            if len(rows) == 0:
                print("No data!")
                jsonport= '无数据！'
                return jsonport
        index = 0
        jsonport = []
        for row in rows:
            trajID = row[0]
            if category == "airplane":
                jsonport = '起航/到港分析仅适用于轮船，请重新选择目标！'
                conn.close()
                return jsonport
                #sql_command = 'select pid,tid,ST_AsGeoJSON(point),time from public.airplane_point where tid=' + str(trajID) + ' order by time'
            else:
                sql_command = 'select pid,tid,ST_AsGeoJSON(point),time from public.ship_point where tid=' + str(trajID) + ' order by time'
            cur.execute(sql_command)
            data = cur.fetchall()
            key = 'json' + str(index)
            index = index + 1
            try:
                jsonport.append(port_ship.main_fun(data))
            except Exception:
                jsonport = '数据异常，分析失败！'  # 尝试执行语句，若无数据，报错，在主函数中还要调用

            cur.close()
            conn.close()

            return jsonport

    elif function_for=='Sailplane':
        sql_command1 = 'select atraj.tid,atraj.number from ' + postgres_table1 + ' as atraj ' + 'where atraj.callsign=' + '\'' + type + '\'' + ' and atraj."startTime" between ' + '\'' + startTime + '\'' + ' and ' + '\'' + endTime + '\'' + ';'
        sql_command2 = 'select atraj.tid,atraj.number from ' + postgres_table2 + ' as atraj ' + 'where atraj.callsign=' + '\'' + type + '\'' + ' and atraj."startTime" between ' + '\'' + startTime + '\'' + ' and ' + '\'' + endTime + '\'' + ';'
        json_forsail = {}
        cur.execute(sql_command1)
        rows = cur.fetchall()
        category = "airplane"
        if len(rows) == 0:
            cur.execute(sql_command2)
            rows = cur.fetchall()
            category = "ship"
            if len(rows) == 0:
                print("No data!")
                jsonsail = '无数据！'  # 没有被使用
                return json_forsail  # 若无数据，则返回一个空字典
        # 若数据非空
        index = 0
        jsonsail = []
        for row in rows:
            trajID = row[0]  # 根据tid来选取point列表中的东西。
            if category == "airplane":
                sql_command = 'select pid,composite_lot_number,ST_AsGeoJSON(\"coordinates\"),height,storage_time from public.radar_point where composite_lot_number=' + str(trajID) + ' order by storage_time'
            else:
                jsonsail = '起飞/着陆分析仅适用于飞机，请重新选择目标！'  # 未被打印
                conn.close()
                return json_forsail
            cur.execute(sql_command)
            data = cur.fetchall()
            key = 'json' + str(index)
            index = index + 1
            try:
                jsonsail.append(setsail_plane.main_fun(data))
            except Exception:
                jsonsail = '数据异常，分析失败！'
        cur.close()
        conn.close()
        return jsonsail


    #conn.commit()
    conn.close()

#print(readTraj("Cluster",'南海',['加油机1号','加油机2号','加油机131号','加油机10号','加油机132号'],'2016-01-1','2019-10-5',clusternum=1))
#print(readTraj("Pattern_z",'南海','加油机4676号','2016-01-1','2019-10-5'))
#print(readTraj("Pattern_8",'南海','加油机1号','2016-01-1','2019-10-5'))
# print(readTraj("Speedup",'南海','加油机12号','2016-01-1','2019-10-5'))
# print(readTraj("Stop",'南海','加油机1号','2016-01-1','2019-10-5'))
#print(readTraj("Portship",'南海','加油机1号','2016-01-1','2019-10-5'))
#print(readTraj("ShowTraj",'南海','加油机1号','2016-01-1','2019-10-5'))
#print(readTraj("Sailplane",'南海','加油机1号','2016-01-1','2019-10-5'))
#print(readTraj("ShowTraj",'南海','加油机1号','2016-01-1','2019-10-5'))

#print(get_all('南海','驱逐舰27号','2016-01-1','2019-10-5'))