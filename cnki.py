import requests
from random import random
import csv
import os
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--input", help="搜索主题所在的文件", default='./category.txt')
parser.add_argument("-o", "--output", help="输出目录", default="./data")
parser.add_argument("-c", "--cookie", help="cookie所在的目录", default="./cookie.txt")
parser.add_argument("-l", "--line", help="每个文件最多存多少行", default=1000, type=int)
parser.add_argument("-m", "--max", help="每个主题最多搜多少条数据", default=200, type=int)
parser.add_argument("-s", "--single", help="单次搜索条数", default=20, type=int)

args = parser.parse_args()
header = ['category', 'title', 'abstract']

# 读取配置文件
with open(args.input, 'r') as f:
    category_list = map(lambda x: x[:-1], f.readlines())


def mkdir(path):
    path = path.strip()
    path = path.rstrip("\\")
    if not os.path.exists(path):
        os.makedirs(path)
        return True
    else:
        return False


mkdir(args.output)

with open(args.cookie, 'r') as f:
    cookie = f.read().replace('\n', '')

hd = {
    "Cookie": cookie,
    "Referer": "http://www.wanfangdata.com.cn/searchResult/getAdvancedSearch.do?searchType=",
    "User-Agent": "Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}


def search_home(kw, page_num=1, page_size=20):
    url = "http://www.wanfangdata.com.cn/searchResult/getCoreSearch.do?d=" + str(random())
    query = {
        'paramStrs': "中图分类号:(\"{0}\")".format(kw),
        "startDate": "1900",
        "endDate": "2019",
        "updateDate": "",
        "classType": "wfpublish-perio_artical,degree-degree_artical,conference-conf_artical",
        "pageNum": page_num,
        "pageSize": page_size,
        "sortFiled": "",
        "isSearchSecond": False,
        "chineseEnglishExpand": False,
        "topicExpand": False,
        "searchWay": "AdvancedSearch",
        "corePerio": False
    }
    return requests.post(url, data=query, headers=hd)


data = {}
index = 0


def save():
    global index, data
    with open(os.path.join(args.output, '{0}.csv'.format(index)), 'w') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for key in data:
            writer.writerow(data[key])
    index += 1
    data = {}


class Spider:
    def __init__(self, kw, _data, page_size, max_page):
        self.data = _data
        self.kw = kw
        self.page_size = page_size
        self.page_num = 1
        page_total = self.parse_home()
        page_total = min(page_total, max_page)
        self.page_num += 1
        while self.page_num < page_total:
            self.parse_home()
            self.page_num += 1

    def parse_home(self):
        print("{0} / {1}".format(self.kw, self.page_num))
        try:
            r = search_home(self.kw, self.page_num, self.page_size)
            r.raise_for_status()
            r.encoding = 'utf-8'
            d = r.json()
            page_total = d.get('pageTotal', 0)
            page_row = d.get('pageRow', [])
            for page in page_row:
                _id = page.get('id', '0')
                category = page.get('class_code', [])
                if isinstance(category, list):
                    category = ';'.join(category)
                summary = page.get('summary', "")
                title = page.get('title', "")
                self.data[_id] = [category, title, summary]
            return page_total
        except Exception as e:
            print(e)
            return 0


try:
    for c in category_list:
        Spider(c, data, args.single, args.max / args.single)
        if len(data) >= args.line:
            save()
except Exception as e:
    print(e)
finally:
    save()
