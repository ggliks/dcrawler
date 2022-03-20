<h1 align="center">Dcrawler 🎈</h1>

## 📺简介  
dcrawler: 快速爬取网站中a标签中的链接,发送到xray进行安全测试
  
## 📺使用说明
- 安装  
```
python3 -m pip install -r requirements.txt
```
或者
```
pip3 install -r requirements.txt
```
- 参数说明
```
-h : 显示帮助文档
-u : 设置单个url进行测试
-f : 设置目标文件进行测试
-d : 设置链接爬取深度,默认为1000,方式某些网站链接过多导致目标测试时间过长
-op : 设置写入文件
-p : 设置xray监听端口,默认为7777
```

## 📺例子
打开xray监听:`./xray.exe webscan --listen 127.0.0.1:7777 --html-output test.html`  

运行: `python3 dcrawler.py -u http://www.runoob.com -d 100 -op test.txt`
  ![image](https://github.com/y3ff18/dcrawler/blob/master/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202022-03-18%20133142.jpg)
  ![image](https://github.com/y3ff18/dcrawler/blob/master/img/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202022-03-18%20133111.jpg)
  
 <h1>
测试网站仅作为演示使用,其他任何人进行非法攻击与本人无关!
</h1>
