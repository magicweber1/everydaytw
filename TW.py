import requests
import re
import base64
import subprocess
import time
import json
from lxml import etree
import urllib3
urllib3.disable_warnings()
import os
import threading

class iptv_new():
    def __init__(self):
        self.header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54'}

    def get_tw_channel(self):  #获得电视台名字和播放网页
        channel_list = 'https://everydaytv.top/list-3.html'
        #channel_list = 'https://everydaytv.top/list-4.html'
        channel_resp = requests.get(url=channel_list,headers=self.header)
        #print(channel_resp.text)
        channel_page = etree.HTML(channel_resp.text)  #把网页源代码装入etree中，准备拿来xpth提取出台明和播放页面地址

        channel_name = channel_page.xpath('/html/body/div/div[2]/div/ul/li/div/a/center/h3/text()')  #提出电视台名字
        channel_video_url = channel_page.xpath('/html/body/div/div[2]/div/ul/li/div/a/@href')   #提出电视台播放页面链接

        total_nums = len(channel_name)

        #print(channel_video_url)

        tv_info = []  #空列表存储电视台信息

        for i in range(total_nums):
            tv = {'name':channel_name[i],
                  'video':'https://everydaytv.top/' + channel_video_url[i]}
            tv_info.append(tv)
        #print(tv_info)

        return tv_info

    def get_api_url(video):
        resp1 = requests.get(url=video,timeout=5)
        api = 'https://everydaytv.top' + re.findall('<iframe src="(.*?)" wid',resp1.text)[0]
        #print(api)

        return api

    def get_m3u8_url(api,video):  #获得 单一 电视台名字 和 真实m3u8地址
        header1 = {'Host': 'everydaytv.top',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.78',
                'Referer': video}

        resp = requests.get(url=api,headers=header1,verify=False,timeout=5)  #请求第三方接口

        #print(resp.text)

        base_first = re.findall('var str=(.*?)replace',resp.text)[0].lstrip('de("').rstrip('").')  #掐头去尾，去掉没用的引号
        replace_word = re.findall('replace\(/(.*?)/g',resp.text)[0]   #找出替换的字符串

        base_second = base_first.replace(replace_word, "M").replace("'", "H").replace("?", "L").replace(";",
                                                                                                        "N").replace(
            "!", "S").replace("_", "V").replace("(", "Z").replace("%", "G").replace("@", "D").replace("~", "A").replace(
            ":", "B").replace("&", "J").replace("#", "F").replace(")", "X").replace("-", "C")
        #print(base_second)

        # 对加密字符串进行一系列处理  和替换

        decode = base64.b64decode(base_second).decode('utf-8').replace("flv", "m3u8")
        print(decode)
        return decode



    def write_m3u8_file(self,list2):
        #print(list2)
        with open('TW.m3u','w',encoding='utf-8') as f:
            f.write("#EXTM3U url-tvg='http://epg.51zmt.top:8000/e.xml'" + '\n')
            for i in list2:
                f.write('#EXTINF:-1 ,' + i['name'] + '\n' + i['m3u8'] + '\n')

    def get_start_and_end_html(self,list2):
        # 读取 temp/start_html.txt 中的内容并保存到 start_html 变量中
        with open('temp/start_html.txt', 'r', encoding='utf-8') as f:
            start_html = f.read()

        # 读取 temp/end_html.txt 中的内容并保存到 end_html 变量中
        with open('temp/end_html.txt', 'r', encoding='utf-8') as f:
            end_html = f.read()

        with open('TW.html', 'w', encoding='utf-8') as html_temp_f:   #再写html临时文件
            html_temp_f.write(start_html) # 写入 start_html 中的内容
            for i in list2:
                li = '<li class="channel"><div class="channel-link-wrap"><a id="computer" class="channel-link" href="http://www.luweibo.top/dplayer/dplayer.html?url={}">{}</a></div></li>'.format(i['m3u8'],i['name'])
                #先写好<li>标签
                html_temp_f.write(li)

            html_temp_f.write(end_html)   # 写入 end_html 中的内容



if __name__ == '__main__':
    a = iptv_new()


    def loop(single_tv,m3u8_list):

        Flag = True
        t = 0  # 失败次数

        while Flag:
            try:

                api = iptv_new.get_api_url(video=single_tv['video'])  # 获得动态的api地址

                m3u8 = iptv_new.get_m3u8_url(api=api, video=single_tv['video'])  # 获得实时的m3u8地址
                if m3u8.startswith('No Signal'):  #m3u8地址为No Signal的不加入列表中
                    break


                resp_test = requests.get(url=m3u8)

                Flag1 = True  #判断直播源有效性的标志
                n = 0   #尝试次数
                while Flag1:

                    if resp_test.status_code == 200:   #如果尝试3次都失败
                        print(single_tv['name'] + ' m3u8链接有效')
                        tv_m3u = {
                            'name': single_tv['name'],
                            'm3u8': m3u8
                            # 'id': tv['id'],
                            # 'logo': tv['logo']
                        }  # 在遍历的过程，同时创建字典

                        m3u8_list.append(tv_m3u)  # 列表中存放多个字典
                        print(single_tv['name'] + '获取成功')
                        Flag1 = False


                    else:
                        n += 1
                        if n >= 3:
                            print(single_tv['name'] + '失效')

                            Flag1 = False


                Flag = False  # 成功了则不需要再尝试

            except:
                print(single_tv['name'] + '获取m3u8失败')
                time.sleep(0.1)  # 失败了就休息2秒再尝试
                t += 1
                if t == 5:  # 失败1次则跳过，选择放弃
                    Flag = False
        #print(m3u8_list)

    def run():

        Flag = True
        t = 0  # 失败次数
        while Flag:
            try:
                tv_info = a.get_tw_channel()   #获得频道总列表
                Flag = False     #获得总列表成功，则不需要再循环做了
            except:
                print('a.get_tw_channel() 频道总列表获取失败了')
                time.sleep(0.1)
                t += 1
                if t == 3:  # 失败3次则跳过，选择放弃
                    Flag = False

        m3u8_list = []  # 创建空列表，用于【能够播放】的真实m3u8地址，重点是，真的能够播放的台  list2

        threads = []
        print(tv_info)  #输出频道总列表
        for single_tv in tv_info:
            t = threading.Thread(target=loop, args=(single_tv,m3u8_list))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        print(m3u8_list)
        a.write_m3u8_file(m3u8_list)  # 写入动态m3u文件中
        a.get_start_and_end_html(m3u8_list)  # 写入动态html中



    while True:
        run()
        current_time = time.localtime()
        print(current_time)
        time.sleep(100)


    # is_first_run = True
    #
    # while True:
    #     # 获取当前时间
    #     current_time = time.localtime()
    #     print(current_time)
    #
    #     # 如果是第一次运行程序，则立即执行函数 loop
    #     if is_first_run:
    #         run()
    #         is_first_run = False
    #
    #     # 如果当前时间是偶数整点，则执行函数 a
    #     if current_time.tm_min == 11 and current_time.tm_hour % 2 == 0:
    #         for i in range(8):
    #             run()
    #             time.sleep(600)
    #
    #     # 每隔10秒钟检查一次时间
    #     time.sleep(10)

        # 创建两个线程
    # thread1 = threading.Thread(target=t1)
    # thread2 = threading.Thread(target=t2)
    #
    # # 启动两个线程
    # thread1.start()
    # thread2.start()
    #
    # # 等待两个线程结束
    # thread1.join()
    # thread2.join()