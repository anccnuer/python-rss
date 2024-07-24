import feedparser
import requests
import json
from dateutil import parser
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed


def standardize_times(time_str):
    try:
            # 解析时间字符串
        dt = parser.parse(time_str)
            # 格式化为ISO 8601格式
        standardized_time = dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        return standardized_time
    except ValueError as e:
           return time_str
def read_xml_file(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    body = root.find('body')
    urls = []

    for child in body:
        for sub_child in child:
            urls.append(sub_child.attrib['xmlUrl'])
    return urls
def is_today(time_str):
    return datetime.now(timezone.utc).date() == datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ').date()

def parser_rss_r(rss):
    res = []
    try:
        icon = title = ''
        i = 0
        response = requests.get(rss, timeout=10)
        response.raise_for_status() 
        # 将获取的内容传递给feedparser解析
        rss_feed = feedparser.parse(response.content)
        if 'icon' in rss_feed.feed:
            icon = rss_feed.feed.icon
        if 'title' in rss_feed.feed:
            title = rss_feed.feed.title
        for entry in rss_feed.entries:
            text = {
                'success': True,
                'icon': icon,
                'site-title': title,
                'istoday': is_today(standardize_times(entry.published)),
                'title': entry.title,
                'link': entry.link,
                'published': standardize_times(entry.published),
                'summary': entry.summary,
                'summary_detail': entry.get('summary_detail', {}).get('value', 'null'),
                'content': entry['content'][0].get('value', None) if entry.get('content') and len(entry['content']) > 0 else 'null'
            }
            res.append(text)
            i += 1
            if i > 3:
                break
    except requests.exceptions.Timeout:
        return [{'success': False, 'error': 'Timeout'}]
    except requests.exceptions.HTTPError as e:
        return [{'success': False, 'error': f'HTTP错误：{e}'}]
    except requests.exceptions.RequestException as e:
        return [{'success': False, 'error': f'请求错误：{e}'}]
    return res

def output_json(results):
    with open('my_list.json', 'w') as json_file:
        json.dump(results, json_file, ensure_ascii=False)

if __name__ == '__main__':
    urls = read_xml_file('feed.xml')
    threads = []
    results = []
  
    with ThreadPoolExecutor(max_workers=5) as executor:
        # 提交所有URL到线程池
        future_to_url = {executor.submit(parser_rss_r, url): url for url in urls}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result()
            except Exception as exc:
                print(f'{url} generated an exception: {exc}')
            else:
                # print(f'{url} page is {data}')
                results.append(data)
    output_json(results)