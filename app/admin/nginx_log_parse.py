import re
import time
import json
import datetime
import requests
from collections import namedtuple
from qqwry import QQwry


# LOG_PATH = "/home/cabbage/Documents/blog_log/flaskblog_access.log"  # 日志文件
# QQWRY_PATH = "/home/cabbage/Documents/blog_log/qqwry_lastest.dat"  # 纯真数据库文件

LOG_PATH = "/share/flaskblog_access.log"  # 日志文件
QQWRY_PATH = "/share/qqwry_lastest.dat"  # 纯真数据库文件

# 匹配日志的正则
COMBINED_LOGLINE_PAT = re.compile(
r'(?P<origin>\d+\.\d+\.\d+\.\d+) '+ \
r'(?P<identd>-|\w*) (?P<auth>-|\w*) '+ \
r'\[(?P<date>[^\[\]:]+):(?P<time>\d+:\d+:\d+) (?P<tz>[\-\+]?\d\d\d\d)\] '+ \
r'"(?P<method>\w+) (?P<path>[\S]+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<bytes>-|\d+)'+ \
r'( (?P<referrer>"[^"]*")( (?P<client>"[^"]*")( (?P<cookie>"[^"]*"))?)?)?\s*\Z'
)


# 去除BOT的正则
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
    """
    解析日志
    :param log_text:log的文件
    :return:解析的日志list[dict{}, dict{},...]
    """
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
    """
    格式化时间
    :param date_str:日期的str
    :param tz_str:时区的str
    :return:对应的当地时间
    """
    tt = time.strptime(date_str, "%d/%b/%Y:%H:%M:%S")
    tt = tt[:6] + (0, timezone(tz_str))
    return datetime.datetime(*tt)


def get_log_text(filename):
    """
    读取日志转成list
    :param filename:日志文件
    :return:返回list
    """
    log_file = open(filename, 'r')
    log_text = [line for line in log_file] 
    return log_text


def bot_check(match_info):
    """
    判断是否是爬虫
    :param match_info:一条日志文件
    :return:boolean
    """
    for pat, botname in BOT_TRACES:
        if pat.match(match_info.group('client')):
            return True
    return False


def get_address_by_ip(log_line, q, flag):
    """
    使用纯真数据库返回ip对应的地理位置
    :param log_line:一条日志
    :param q:纯真数据库对象的实例化
    :param flag:如果失败则换用ip-api
    :return:str城市名
    """
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


def get_raw_data():
    """
    得到raw_data
    :return:返回预处理后的数据
    """
    filename = LOG_PATH
    qqwry_path = QQWRY_PATH

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

    raw_data = []
    Ip_raw_data = namedtuple('ip_data', ['log_time', 'ip', 'referrer', 'client',\
                                   'method', 'status', 'city'])
    for line in parsed_log_list:
        log_time = parse_nginx_date(line['date']+':'+line['time'], line['tz'])
        log_ip = line['origin']
        if log_ip not in ip_dict:
            ip_dict[log_ip] = get_address_by_ip(line, q, flag)
        log_city = ip_dict[log_ip]
        raw_data.append(Ip_raw_data(log_time, log_ip, line['referrer'], line['client'],\
                                    line['method'], line['status'], log_city))
    return raw_data


def get_json_raw_data():
    """
    使用json返回raw_data
    :return: dict{raw_data}
    """
    raw_data = get_raw_data()
    json_raw_data = []
    for line in raw_data:
        log_time = line.log_time
        log_ip = line.ip
        log_referrer = line.referrer
        log_client = line.client
        log_method = line.method
        log_status = line.status
        log_city = line.city
        log_dict = {'time': log_time.strftime('%Y-%m-%d %H:%M:%S'), 
                'ip': log_ip, 
                'referrer': log_referrer, 
                'client': log_client,
                'method': log_method, 
                'status': log_status,
                'city': log_city,
        }
        json_raw_data.append(log_dict)
        json_raw_data.sort(key=lambda x: x['time'], reverse=True)
    return json_raw_data


def stat_daily_page_view():
    """
    统计每天的pv
    :return:dict{date:cnt}
    """
    raw_data = get_raw_data()
    daily_page_view_dict = {}
    for line in raw_data:
        date = line.log_time.strftime('%Y-%m-%d')
        if date not in daily_page_view_dict:
            daily_page_view_dict[date] = 0
        daily_page_view_dict[date] += 1
    return daily_page_view_dict


def stat_daily_user_view():
    """
    统计每天的uv
    :return:dict{date:cnt}
    """
    raw_data = get_raw_data()
    daily_user_view_middle_dict = {}
    for line in raw_data:
        date = line.log_time.strftime('%Y-%m-%d')
        if date not in daily_user_view_middle_dict:
            daily_user_view_middle_dict[date] = set()
        daily_user_view_middle_dict[date].add(line.ip)
    daily_user_view_dict = {}
    for date in daily_user_view_middle_dict:
        daily_user_view_dict[date] = len(daily_user_view_middle_dict[date])
    return daily_user_view_dict


if __name__ == '__main__':
    print(get_json_raw_data())
    print(stat_daily_page_view())
    print(stat_daily_user_view())
