#!/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time : 2022-03-14 21:29
# @Author : y3ff18
# @File : dcwler.py
# @Version : python3.9
import asyncio
import sys
from loguru import logger
import time
from tqdm import tqdm as tqdm_list
from aiohttp.client_exceptions import InvalidURL
from urllib.parse import parse_qs
from bs4 import BeautifulSoup
import aiohttp
import queue
from urllib.parse import urlparse
import argparse
import random
import tldextract
import os
import requests
import urllib3
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Dcrawler():
    def banner(self):
        print('''
      _                         _           
     | |                       | |          
   __| | ___ _ __ __ ___      _| | ___ _ __ 
  / _` |/ __| '__/ _` \ \ /\ / / |/ _ \ '__|
 | (_| | (__| | | (_| |\ V  V /| |  __/ |   
  \__,_|\___|_|  \__,_| \_/\_/ |_|\___|_| 
                                author: y3ff18
                                usage: python3 dcrawler.py -h
        ''')

    def argparse(self):
        parse = argparse.ArgumentParser()
        parse.add_argument('-u','--url',help='Input a Url',default='http://www.njupt.edu.cn/')
        parse.add_argument('-f','--file',help='Input a File Name',default=None)
        parse.add_argument('-t','--timeout',help='Set page timeout,default is 10s',default=10,type=int)
        parse.add_argument('-d','--deep',help='Set max page amount,default is 1000',default=100,type=int)
        parse.add_argument('-op','--output',help='OutPut to a file',default=None)
        parse.add_argument('-p','--xray_port',help='Set Xray Port,default ip and port 127.0.0.1:7777',default=7777,type=int)
        parse.add_argument('-fuzz','--fuzz',help='if set this parameter,Start fuzz path,Set fuzz path file',default=None)
        return parse.parse_args()

    def __init__(self):
        #初始化参数:
        self.banner()
        self.arg = self.argparse()
        self.tasks = []
        #初始化整个url队列
        self.url_queue = queue.Queue()
        #主域名
        self.get_url_queue = queue.Queue()
        self.domain = ''
        self.url = ''
        self.parameter = set()
        self.timeout = aiohttp.ClientTimeout(total=15)
        self.black_extend_list = ['png', 'jpg', 'gif', 'jpeg', 'ico', 'svg', 'bmp', 'mp3', 'mp4', 'avi', 'mpeg', 'mpg',
                                  'mov', 'zip', 'rar', 'tar', 'gz', 'mpeg', 'mkv', 'rmvb', 'iso', 'css', 'txt', 'ppt',
                                  'dmg', 'app', 'exe', 'pem', 'doc', 'docx', 'pkg', 'pdf', 'xml', 'eml', 'ini', 'so',
                                  'vbs', 'json', 'webp', 'woff', 'ttf', 'otf', 'log', 'image', 'map', 'woff2', 'mem',
                                  'wasm', 'pexe', 'nmf']
        self.url_set = set()
        self.loop = asyncio.get_event_loop()


        if self.arg.url != None:
            self.check_target(self.arg.url)

        elif os.path.isfile(self.arg.file):
            with open(self.arg.file,'r',encoding='utf-8') as file_stream:
                for url_link in file_stream:
                    self.check_target(url_link)



    def start(self):
        #创建事件循环
        try:
            while not self.url_queue.empty():
                # 第一次进入循环
                self.url = self.url_queue.get()
                # 初始化队列
                self.url_set.clear()
                self.get_url_queue.put(self.url)
                # 初始化参数列表
                self.parameter.clear()
                # 初始化url域名
                self.domain = urlparse(self.url).netloc
                # print(self.domain)
                self.send_req()
                logger.info('[+] Done {}'.format(self.domain))
                self.output_file(self.arg.output)
                self.check_xray()
                if self.arg.fuzz != None:
                    #如果设置该参数,则对网站进行路径fuzz,
                    pass
        except KeyboardInterrupt:
            sys.exit(0)


    def send_req(self):
        while self.get_url_queue.qsize() > 0 and len(self.url_set) < self.arg.deep:
            self.tasks = []
            i = 0
            while i < 50 and not self.get_url_queue.empty() and len(self.url_set) < self.arg.deep:
                # print(len(self.url_set))
                i += 1
                url = self.get_url_queue.get()
                self.tasks.append(self.get_html(url))

            if self.tasks:
                self.loop.run_until_complete(asyncio.wait(self.tasks))



    def check_target(self,url):
        if not str(url).startswith(('http://', 'https://')):
            target_url = 'http://' + urlparse(url).netloc
            if target_url.endswith('/'):
                self.url_queue.put(target_url[:-1])
            else:
                self.url_queue.put(target_url)
        else:
            if str(url).endswith('/'):
                self.url_queue.put(str(urlparse(url).scheme + '://' + str(urlparse(url).netloc)))
            else:
                self.url_queue.put(str(urlparse(url).scheme + '://' + str(urlparse(url).netloc)))

    def check_xray(self):
        logger.info('[+] send to xray...')
        headers = self.get_header()
        proxies = {
                 'http':'http://127.0.0.1:{}'.format(self.arg.xray_port),
                 'https':'https://127.0.0.1:{}'.format(self.arg.xray_port),
             }
        try:
            for url in tqdm_list(self.url_set):
                requests.get(url=url,headers=headers,verify=False,timeout=10,proxies=proxies)
                logger.info('[+] send seccuss')
        except:
            pass

    def search_parameter(self,url):
        #此函数的url都是有参数的url,不能传没有参数的url
        for key in parse_qs(urlparse(url).query).keys():
            if urlparse(url).path + "?" + key in self.parameter:
                continue
            else:
                return False
        return True

    def get_file_extend(self,url_file):
        return os.path.splitext(url_file)[-1]


    async def get_html(self,url):
        logger.info(url)
        headers = self.get_header()
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False),timeout=self.timeout) as session:
                async with asyncio.Semaphore(2048) :
                    async with session.get(url,headers=headers,) as response:
                        if response.status == 200:
                            await asyncio.sleep(1)
                            response_html = await response.text()
                            # print(response_html)
                            #返回一个href链接的列表
                            links_result = self.get_links(html=response_html)
                            for link in links_result:
                                if str(link).endswith('/'):
                                    link = link[:-1]
                                #黑名单字符
                                if link in [None,'/'] or 'javascript' in link or link in self.black_extend_list:
                                    continue
                                #域名不一致
                                elif str(urlparse(link).netloc) != self.domain and str(urlparse(link).netloc) != '':
                                    continue
                                #出现//
                                elif str(link).startswith('//'):
                                    if self.domain == str(link)[2:]:
                                        link = urlparse(self.url).scheme + '://' + link[2:]
                                        if len(parse_qs(urlparse(link).query).keys()) > 0:
                                            #判断当前链接参数是否被包含在大参数列表中
                                            if not self.search_parameter(link):
                                                self.url_set.add(link)
                                                self.get_url_queue.put(link)
                                        elif link not in self.url_set:
                                            self.url_set.add(link)
                                            self.get_url_queue.put(link)
                                #如果以/开头,需要对其进行域名组合,小部分情况不考虑
                                elif str(link).startswith('/'):
                                    link = self.url + link
                                    if len(parse_qs(urlparse(link).query).keys()) > 0:
                                        if not self.search_parameter(link):
                                            self.url_set.add(link)
                                            self.get_url_queue.put(link)
                                    elif link not in self.url_set:
                                        self.url_set.add(link)
                                        self.get_url_queue.put(link)
                                #以http,https开头,并且域名一致
                                elif str(link).startswith(('http://','https://')) and urlparse(str(link)).netloc != self.domain:
                                    if len(parse_qs(urlparse(link).query).keys()) > 0:
                                        if not self.search_parameter(link):
                                            self.url_set.add(link)
                                            self.get_url_queue.put(link)
                                    elif link not in self.url_set:
                                        self.url_set.add(link)
                                        self.get_url_queue.put(link)
                                for key in parse_qs(urlparse(link).query).keys():
                                    self.parameter.add(urlparse(link).path+"?"+key)

        except InvalidURL:
            logger.warning('[!] InvalidURL')
        except UnicodeDecodeError:
            logger.warning('[!] UnmicodeDecodeError')
        except aiohttp.client_exceptions.ClientConnectorError:
            logger.warning('[!] ClientConnectorError')
    def get_links(self,html):
        #通过被协程调用返回一个页面中包含a链接的列表
        url_links = []
        soup = BeautifulSoup(html,'html.parser')
        links = soup.find_all('a')
        for link in links:
            url_links.append(link.get('href'))
        return url_links

    def output_file(self,file_name):
        if file_name != None:
            with open(file_name, 'a', encoding='utf-8') as file:
                for url in self.url_set:
                    file.write(str(url) + '\n')
            logger.info('[+] write file success')
        else:
            return 0



    def get_header(self):
        Tencent = {
            'User-Agent': 'Mozilla/4.0(compatible;MSIE7.0;WindowsNT5.1;TencentTraveler4.0)',
            'Referer':'https://www.google.com'
        }
        TheWorld = {
            'User-Agent': 'Mozilla/4.0(compatible;MSIE7.0;WindowsNT5.1)',
            'Referer': 'https://www.google.com'
        }
        the_360 = {
            'User-Agent':'Mozilla/4.0(compatible;MSIE7.0;WindowsNT5.1;360SE)',
            'Referer': 'https://www.google.com'
        }
        safair = {
            'User-Agent':'Mozilla/5.0(Macintosh;U;IntelMacOSX10_6_8;en-us)AppleWebKit/534.50(KHTML,likeGecko)Version/5.1Safari/534.50',
            'Referer': 'https://www.google.com'
        }
        windows = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
            'Referer': 'https://www.google.com'
        }
        IE = {
            'User-Agent':'Mozilla/5.0(compatible;MSIE9.0;WindowsNT6.1;Trident/5.0;',
            'Referer': 'https://www.google.com'
        }
        NokiaN97 = {
            'User-Agent':'Mozilla/5.0(SymbianOS/9.4;Series60/5.0NokiaN97-1/20.0.019;Profile/MIDP-2.1Configuration/CLDC-1.1)AppleWebKit/525(KHTML,likeGecko)BrowserNG/7.1.18124',
            'Referer': 'https://www.google.com'
        }
        Opera = {
            'User-Agent':'Opera/9.80(WindowsNT6.1;U;en)Presto/2.8.131Version/11.11',
            'Referer': 'https://www.google.com'
        }
        return random.choices([Tencent,TheWorld,the_360,safair,windows,IE,NokiaN97,Opera])[0]


if __name__ == '__main__':
    start = time.time()
    Dcrawler().start()
    logger.info('[+] time amount {}'.format(time.time()-start))