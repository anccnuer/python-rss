import feedparser
import requests
import threading
import xml.etree.ElementTree as ET

def parser_rss(rss):
    rss_feed = feedparser.parse(rss)
    for entry in rss_feed.entries:
        print(entry.title+"\n")
        # print(entry.link+"\n")
        # print(entry.published+"\n")
        # print(entry.description+"\n")
        # print(entry.content[0]['value'])
        break
def read_xml_file(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    body = root.find('body')
    urls = []

    for child in body:
        for sub_child in child:
            urls.append(sub_child.attrib['xmlUrl'])
    return urls


def parser_rss_r(rss):
    try:
        response = requests.get(rss, timeout=10)
        response.raise_for_status()  # 如果响应状态不是200，将抛出HTTPError异常
        # 将获取的内容传递给feedparser解析
        rss_feed = feedparser.parse(response.content)
        for entry in rss_feed.entries:
            print(entry.title+"\n")
            break
    except requests.exceptions.Timeout:
        print("请求超时，无法获取RSS feed。")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP错误：{e.response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"请求错误：{e}")

if __name__ == '__main__':
    urls = read_xml_file('feed.xml')
    threads = []
    # for url in urls:
    #     # parser_rss(url)
    #     parser_rss_r(url)
    for url in urls:
        thread = threading.Thread(target=parser_rss_r, args=(url,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()