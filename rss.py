import feedparser
import requests
import json
from dateutil import parser, tz
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
# 读取订阅文件
def read_xml_file(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    body = root.find('body')
    urls = []

    for child in body:
        classify = child.attrib['text']
        if classify == '博客' or classify == '技术宅' or classify == '竹白':
            important = True
        else:
            important = False
        for sub_child in child:
            url = sub_child.attrib['xmlUrl']
            urls.append({'important': important, 'url': url})
    return urls

def standardize_times(time_str):
    try:
        dt = parser.parse(time_str)
        standardized_time = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        return standardized_time
    except ValueError as e:
        return time_str

def is_today(date_str):
    try:
        today = get_today()
        yesterday = today - timedelta(days=1)
        date_str = date_str.split("T", 1)[0]
        test_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        if test_date == today:
            return True
        elif test_date == yesterday:
            return False
        else:
            return 'no'
    except ValueError:
        print(f"Invalid date format: {date_str}")


def get_today():
    return datetime.now(tz=tz.tzlocal()).date()

def parser_rss_r(rss):
    res = []
    url = rss['url']
    important = rss['important']
    try:
        icon = title = ''
        response = requests.get(url, timeout=10)
        response.raise_for_status() 
        # 将获取的内容传递给feedparser解析
        rss_feed = feedparser.parse(response.content)
        if 'icon' in rss_feed.feed:
            icon = rss_feed.feed.icon
        if 'title' in rss_feed.feed:
            title = rss_feed.feed.title
        for entry in rss_feed.entries:
            if 'published' in entry:
                published = entry.published
                t = standardize_times(published)
                istoday = is_today(t)
            else:
                t = '未知'
                istoday = 'no'
            if istoday == 'no':
                continue
            text = {
                'success': True,
                'important': important,
                'icon': icon,
                'site-title': title,
                'istoday': istoday,
                'title': entry.title,
                'link': entry.link,
                'published': t,
                'summary': entry.summary,
                'summary_detail': entry.get('summary_detail', {}).get('value', 'null'),
                'content': entry['content'][0].get('value', None) if entry.get('content') and len(entry['content']) > 0 else 'null'
            }
            res.append(text)
    except requests.exceptions.Timeout:
        return [{'success': False, 'error': 'Timeout'}]
    except requests.exceptions.HTTPError as e:
        return [{'success': False, 'error': f'HTTP错误：{e}'}]
    except requests.exceptions.RequestException as e:
        return [{'success': False, 'error': f'请求错误：{e}'}]
    return res

def output_json(results):
    with open('content/my_list.json', 'w', encoding='utf-8') as json_file:
        json.dump(results, json_file, ensure_ascii=False)

if __name__ == '__main__':
    urls = read_xml_file('feed.xml')
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(parser_rss_r, url) for url in urls]
        results = []
        for future in as_completed(futures):
            results.extend(future.result())
    output_json(results)