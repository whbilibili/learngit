import psycopg2
import json
import time


'''
speed处理流程：
一、readSQL中的调用
（1）readSQL中按照单条的sql语句读取数据。返回数据data。此时的data是一个大列表，列表中含有若干个小的元组
每个元组都代表一个轨迹点，含有了所需要的的相关信息【pid，tid，json格式的坐标数据：'{"type":"Point","coordinates":[123.0965955,23.9980586]}'，speed，time】
（2）在readSQL中调用speed的主函数，将data传给main_fun进行处理。接着转入speed中。
二、转入speed中的处理流程
（1）trans:首先对出传入的数据data进行预处理，将json格式的坐标数据转化为经纬度处理完成之后得到一个新的数据data1
data1也是一个列表，列表中包含系列的小列表，每个小列表都代表一个轨迹点，小列表的索引值从0到5【pid，tid，lon，lat，speed，time】
（2）Threshold:利用data1中的time和speed算出每两个相邻轨迹点之间的加速度ac。特别指出：第一个点归类为无状态点，循环开始前将其加速度赋值为零；之后相邻两点之间计算出来的加速度赋予后者，
此时data1中又多了一项数据：加速度【ac】，若ac大于0，放入acceup中间列表中去；反之放到accedown中间列表中去，计算完之后，对两个中间列表进行排序，选取加减速段的值域。放到一个列表中去：【加速，减速】
（3）根据选取出来的加减速值域，对data1中每个点的加速度：索引值--6，与阈值进行比较，大于加速阈值：追加4；小于减速阈值：追加5；无状态：追加0；第一点追加0。此时，data1中又多了一项数据，状态标注
索引值--7，【0：无状态；4：加速状态；5：减速状态】，到此为止，一段轨迹的所有轨迹点的加减速状态的判断就完成了。
（4）最后做封装处理，返回所需形式的数据，可以自行调整。

数据样例：
data = [pid,tid,'{"type":"Point","coordinates":[123.0965955,23.9980586]}',speed,time]
data1 = [pid,tid,lon,lat,speed,time,ac,tag]
'''


def trans(data):
	data1 = []
	for i in range(len(data)):
		row = []
		row.append(data[i][0]) #pid
		row.append(data[i][1]) #tid
		row.append(json.loads(data[i][2])['coordinates'][0]) #lon
		row.append(json.loads(data[i][2])['coordinates'][1]) #lat
		row.append(data[i][3]) #speed
		row.append(data[i][4]) #time
		data1.append(row)
	return data1

def Threshold(data1):
	acceup = []
	accedown = []
	data1[0].append(0)
	for i in range(len(data1)-1):
		if data1[i][5] == data1[i+1][5]:
			continue
		ac = (data1[i+1][4]-data1[i][4])/(data1[i+1][5]-data1[i][5])
		data1[i+1].append(ac)
		# 加速度加入，索引值为6
		if ac > 0:
			acceup.append(ac)
		elif ac < 0:
			accedown.append(ac)
	acceup.sort()
	accedown.sort()

	if len(acceup)>0 and len(accedown)>0:
		up=acceup[4*len(acceup)//5]
		down=accedown[len(accedown)//5]
	elif len(acceup) == 0 and len(accedown) > 0:
		up=0
		down=accedown[len(accedown)//5]
	elif len(acceup) > 0 and len(accedown) == 0:
		up=acceup[4*len(acceup)//5]
		down=0
	else:
		up=0
		down=0
	#print('阈值：'+str([up,down]))
	return [up,down]
			
def iden(data1,thre):
	for i in range(len(data1)-1):
		if i == 0 :
			#无状态
			data1[i].append(0)

		elif data1[i+1][5] == data1[i][5]:
			data1[i+1].append(0)

		elif data1[i][6] >= thre[0] :
			#加速
			data1[i].append(4)

		elif data1[i][6] <= thre[1]:
			#减速
			data1[i].append(5)
		else:
			#无状态
			data1[i].append(0)

	return data1

def main_fun(data):

	data1=trans(data)
	# print(len(data1[1]))
	data1 = [i for i in data1 if len(i)==6]
	thre=Threshold(data1)
	data1=iden(data1,thre)
	# print(len(data1[1]))
	data1 = [i for i in data1 if len(i)==8]
	coo=[]
	upn=0
	downn=0
	for i in range(len(data1)):
		item=[data1[i][2],data1[i][3],data1[i][7]]
		if data1[i][7] == 4: #加速
			upn += 1
		elif data1[i][7] == 5: #减速
			downn += 1
		coo.append(item)
	result={"mode":"speed","segmentNum":upn+downn,"coordinates":coo}
	# result = json.dumps(result['coordinates'])
	# return result
	return result['coordinates']

#selectp('加油机2号','2016-4-13','2016-4-30','美国','南海')
#main('plane','加油机2号','2016-4-13','2016-4-30','美国','南海')
