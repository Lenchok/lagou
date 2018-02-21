import requests
import pandas as pd
import pymysql
import uuid
from multiprocessing import Pool
from sqlalchemy import create_engine
import matplotlib.pyplot as plt #绘图
import matplotlib as mob #配置字体
import jieba.analyse
from wordcloud import WordCloud,ImageColorGenerator
from PIL import Image # 打开图片
import numpy as np # 处理图片
import pylab as pl
import time



# 随机生成uuid
def get_uuid():
    return str(uuid.uuid4())

def get_one_page(page,keyword):
    url = 'https://www.lagou.com/jobs/positionAjax.json?needAddtionalResult=false&isSchoolJob=0'
    # 提交post请求的数据，页码及关键字
    data = {'first': 'false',
            'pn': '1',
            'kd': 'python'}
    # 连接数据库
    conn = pymysql.connect(host='127.0.0.1', user='root', password='root', db='lagou', port=3306, charset='utf8')
    # # 创建游标
    cursor = conn.cursor()

    try:
            #不停更改cookie的值，使服务器识别不了机器人
            cookie = "JSESSIONID=" + get_uuid() + ";"
            "user_trace_token=" + get_uuid() + "; LGUID=" + get_uuid() + "; index_location_city=%E6%88%90%E9%83%BD; "
            "SEARCH_ID=" + get_uuid() + '; _gid=GA1.2.717841549.1514043316; '
            '_ga=GA1.2.952298646.1514043316; '
            'LGSID=' + get_uuid() + "; "
            "LGRID=" + get_uuid() + "; "
            headers = {'cookie': cookie, 'origin': "https://www.lagou.com", 'x-anit-forge-code': "0",
                       'accept-encoding': "gzip, deflate, br", 'accept-language': "zh-CN,zh;q=0.8,en;q=0.6",
                       'user-agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
                       'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
                       'accept': "application/json, text/javascript, */*; q=0.01",
                       'referer': "https://www.lagou.com/jobs/list_Java?px=new&city=%E6%88%90%E9%83%BD",
                       'x-requested-with': "XMLHttpRequest", 'connection': "keep-alive", 'x-anit-forge-token': "None",
                       'cache-control': "no-cache", 'postman-token': "91beb456-8dd9-0390-a3a5-64ff3936fa63"}
            # 随机等待2到5秒
            #time.sleep(random.randint(2,4))
            #更新页码数
            data['pn']=str(page)
            data['kd'] = str(keyword)
            headers[cookie]=cookie
                #获取访问json数据
            respone=requests.post(url,headers=headers,data=data).json()

            #json返回的数据是字典类型，需一层层找到需要的数据
            data2=respone["content"]["positionResult"]["result"]
            for data1 in data2:
                companyId=int(data1['companyId'])
                companyShortName=data1['companyShortName']
                companyFullName=data1['companyFullName']
                positionName=data1['positionName']
                salary=data1['salary']
                city=data1['city']
                education=data1['education']
                workYear=data1['workYear']
                longitude=data1['longitude']
                latitude=data1['latitude']
                sql='insert into lagoudata values(%d,%s,%s,%s,%s,%s,%s,%s,%s,%s,%d,%s)'%(companyId,"'"+companyShortName+"'","'"+companyFullName+"'","'"+positionName+"'","'"+salary+"'","'"+city+"'","'"+education+"'","'"+workYear+"'","'"+str(longitude)+"'","'"+str(latitude)+"'",page,"'"+str(keyword)+"'")
                cursor.execute(sql)
                conn.commit()
            print('正写入第%d页数据'%(page))
    except KeyError as e:
          print(e)
    cursor.close()
    conn.close()

#创建更新工作经验对应工资的表
def create_workyear_salary():
    # 连接数据库
    conn = pymysql.connect(host='127.0.0.1', user='root', password='root', db='lagou', port=3306, charset='utf8')
    # # 创建游标
    cursor = conn.cursor()
    sql = "CREATE OR REPLACE VIEW v_workyear_salary AS SELECT DISTINCT keyword,workyear,avg(REPLACE(SUBSTR(salary,1,2),'k','')) avg_salary from lagoudata group by keyword,workyear"
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()

#绘画城市分布柱形图
def draw_city_bar(data,keyword):
    mob.rcParams["font.sans-serif"] = ["SimHei"]
    data['city'].value_counts().plot(kind='bar',color='rgb',title='工作城市分布纵向柱形图')
    path = ('./image/' + '%s' + '_city_bar.jpg') % (str(keyword))
    plt.savefig(path)
    plt.show()

#绘画学历要求横向柱形图
def draw_edu_barh(data,keyword):
    mob.rcParams["font.sans-serif"] = ["SimHei"]
    data['education'].value_counts().plot(kind='barh',color='rgb',title='学历要求横向柱形图')
    path = ('./image/' + '%s' + '_education_barh.jpg') % (str(keyword))
    plt.savefig(path)
    plt.show()

#绘画工作经验对应工资
def draw_salary_barh(data,keyword):
    mob.rcParams["font.sans-serif"] = ["SimHei"]
    x=data['workyear']
    y=data['avg_salary']
    pl.title('全国工作经验对应工资的最低平均值')
    pl.plot(x,y,'b')
    path = ('./image/' + '%s' + '_workyear_salary.jpg') % (str(keyword))
    plt.savefig(path)
    plt.show()

#绘画词云图
def draw_position_wordcould(data,keyword):
    mob.rcParams["font.sans-serif"] = ["SimHei"]
    # word_data=data['position']
    final = ''
    stopword = ['PYTHON', 'Python', 'python','java','php', '工程师', '(', ')', '/']  # 停止分词
    for n in range(data.shape[0]):  # data.shape[0]第一列最后一行
        seg_list = list(jieba.cut(data['position'][n]))  # 切割分词
        for seg in seg_list:
            if seg not in stopword:
                final = final + seg + ' '
    path = ('./image/' + '%s' + '_position_wordcould.jpg') % (str(keyword))
    # 打开图片
    img_mark = Image.open('./image/qiaoba.jpg')
    # 处理图片
    imag = np.array(img_mark)
    img_colors = ImageColorGenerator(imag)

    # generate可以自动分词
    my_wordcloud = WordCloud(font_path=r'F:\font\simfang_ttf\huawenxihei.ttf', background_color='White',max_words=50,mask=imag).generate(final)

    plt.imshow(my_wordcloud)
    plt.axis('off')
    plt.show()
    my_wordcloud.to_file(path)

def main():

    #搜索关键字
    print("请输入需要搜索的关键字：")
    keyword = input()
    print("开始采集数据，请耐心等候。。。")
    # 页码
    page = [i for i in range(1, 31)]
    pool = Pool(processes=20)
    for i in page:
        pool.apply_async(get_one_page, args=(i,str(keyword)))

    pool.close()
    pool.join()
    print('数据采集完毕，数据来源：拉勾网，共采集450条数据！')
    print('\n')
    # time.sleep(2)
    print('攻城狮要开始一笔一划绘图啦。。。')
    print('\n')
    # print('请输入你想攻城狮画哪种图：')
    # print('1-工作城市分布图')
    # print('2-学历要求图')
    # print('3-工作经验对应工资图')
    # print('4-岗位词云图')
    # int_data=int(input())
    # 更新工作经验对应工资的表
    create_workyear_salary()
    # 数据库连接参数
    db_info = {'user': 'root',
               'password': 'root',
               'host': '127.0.0.1',
               'database': 'lagou'
               }
    # 创建数据库连接
    engine = create_engine('mysql+pymysql://%(user)s:%(password)s@%(host)s/%(database)s?charset=utf8' % db_info,
                           encoding='utf-8')

    # 读取数据库的数
    parser_sql = "select * from lagoudata where keyword=%s" % ("'" + keyword + "'")
    parser_data = pd.read_sql(parser_sql, engine)
    work_sql= "select * from v_workyear_salary where keyword=%s" % ("'" + keyword + "'")
    word_data = pd.read_sql(work_sql, engine)
    # if int_data==1:
    draw_city_bar(parser_data, keyword)
    # elif int_data==2:
    draw_edu_barh(parser_data, keyword)
    # elif int_data==3:
    draw_salary_barh(word_data, keyword)
    # elif int_data==4:
    draw_position_wordcould(parser_data, keyword)
    # else:
    #     print('请输入正确的数字')



if __name__=='__main__':
    main()