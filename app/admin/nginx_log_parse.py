import re
import time
import json
import datetime
import requests
from qqwry import QQwry

COMBINED_LOGLINE_PAT = re.compile(
r'(?P<origin>\d+\.\d+\.\d+\.\d+) '+ \
r'(?P<identd>-|\w*) (?P<auth>-|\w*) '+ \
r'\[(?P<date>[^\[\]:]+):(?P<time>\d+:\d+:\d+) (?P<tz>[\-\+]?\d\d\d\d)\] '+ \
r'"(?P<method>\w+) (?P<path>[\S]+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<bytes>-|\d+)'+ \
r'( (?P<referrer>"[^"]*")( (?P<client>"[^"]*")( (?P<cookie>"[^"]*"))?)?)?\s*\Z'
)

BOT_TRACES = [
    (re.compile(r".*http://help\.yahoo\.com/help/us/ysearch/slurp.*"),
        "Yahoo robot"),
    (re.compile(r".*\+http://www\.google\.com/bot\.html.*"),
        "Google robot"),
    (re.compile(r".*\+http://about\.ask\.com/en/docs/about/webmasters.shtml.*"),
        "Ask Jeeves/Teoma robot"),
    (re.compile(r".*\+http://www\.bing\.com/bingbot.htm.*"),
        "Bing robot"),
    (re.compile(r".*http://www\.entireweb\.com/about/search_tech/speedy_spider/.*"),
        "Speedy Spider"),
    (re.compile(r".*\+http://www\.baidu\.com/search/spider\.html.*"),
        "Baidu spider"),
    (re.compile(r".*\+http://www\.gigablast\.com/spider\.html.*"),
        "Gigabot robot"),
    (re.compile(r".*Googlebot.*"),
        "Googlebot robot"),
    (re.compile(r".*http://mj12bot\.com/.*"),
        "mj12 robot"),
    (re.compile(r".*\+http://www\.semrush\.com/bot\.html.*"),
        "semrush robot"),
    (re.compile(r".*\+http://www\.sogou\.com/docs/help/.*"),
        "sogou robot"),
]


def parse(log_text):
    '''
    解析日志
    return: list[{},{},...]
    '''
    parsed_log_list = [] #保存解析结果的list

    for line in log_text:
        match_info = COMBINED_LOGLINE_PAT.match(line)
        if match_info: #是否匹配到
            if not bot_check(match_info): #是否是爬虫
                parsed_log_list.append(match_info.groupdict())
    return parsed_log_list


class timezone(datetime.tzinfo):
    '''时区转换'''
    def __init__(self, name="+0000"):
        self.name = name
        seconds = int(name[:-2])*3600+int(name[-2:])*60
        self.offset = datetime.timedelta(seconds=seconds)
 
    def utcoffset(self, dt):
        return self.offset
 
    def dst(self, dt):
        return datetime.timedelta(0)
 
    def tzname(self, dt):
        return self.name


def parse_nginx_date(date_str, tz_str):
    '''格式化时间'''
    tt = time.strptime(date_str, "%d/%b/%Y:%H:%M:%S")
    tt = tt[:6] + (0, timezone(tz_str))
    return datetime.datetime(*tt)


def get_log_text(filename):
    '''读取日志文件转成list'''
    log_file = open(filename, 'r')
    log_text = [line for line in log_file] 
    return log_text


def bot_check(match_info):
    '''判断是否是爬虫'''
    for pat, botname in BOT_TRACES:
        if pat.match(match_info.group('client')):
            return True
    return False


def get_address_by_ip(log_line, q, flag):
    ip = log_line['origin']
    #默认使用纯真ip库
    ip_list = q.lookup(ip)
    if ip_list:
        city = ip_list[0]
    else:
        flag = -1
    if flag == -1:
        ori = requests.get('http://ip-api.com/json/%s' % ip)
        ip_dict = json.loads(ori.text)
        city = ip_dict['city']
    return city


def main(filename, qqwry_path):
    result = [] # 结果list
    ip_dict = {} # 存不重复的ip及其city
    log_text = get_log_text(filename) # 获取日志原始文件
    parsed_log_list = parse(log_text) # 获取解析完的日志


    #加载纯真ip数据库
    flag = 0
    q = QQwry()
    while not q.is_loaded():
        # 加载3次失败后改用其他方案
        if flag == 3:
            break
        q.load_file(qqwry_path)
        flag += 1
    
    for line in parsed_log_list:
        log_time = parse_nginx_date(line['date']+':'+line['time'], line['tz'])
        log_ip = line['origin']
        log_referrer = line['referrer']
        log_client = line['client']
        log_method = line['method']
        log_status = line['status']
        if log_ip not in ip_dict:
            ip_dict[log_ip] = get_address_by_ip(line, q, flag)
        log_city = ip_dict[log_ip]
        log_dict = {'time': log_time.strftime('%Y-%m-%d %H:%M:%S'), 
                'ip': log_ip, 
                'referrer': log_referrer, 
                'client': log_client,
                'method': log_method, 
                'status': log_status,
                'city': log_city,
        }
        result.append(log_dict)
    return json.dumps(result)


if __name__ == '__main__':
    filename = '/home/cabbage/Documents/blog_log/flaskblog_access.log'
    qqwry_path = "/home/cabbage/Documents/blog_log/qqwry.dat"
    print(main(filename, qqwry_path))
