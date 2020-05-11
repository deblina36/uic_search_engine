import queue
import html2text
import time 
import json
from bs4 import BeautifulSoup
from bs4.dammit import EncodingDetector
from urllib.parse import urlparse
import os 
import requests
import random
import urllib.parse

# Initialize Beautiful Soup for crawling
def get_soup_for_url(base_url):
  resp = requests.get(base_url)
  http_encoding = resp.encoding if 'charset' in resp.headers.get('content-type', '').lower() else None
  html_encoding = EncodingDetector.find_declared_encoding(resp.content, is_html=True)
  encoding = html_encoding or http_encoding
  soup = BeautifulSoup(resp.content, from_encoding=encoding)
  return soup

# check if the given URL is relative path or not
def is_absolute(url):
  return bool(urlparse(url).netloc)


class UserAgent:
    ua_source_url='https://deviceatlas.com/blog/list-of-user-agent-strings#desktop'
    def __init__(self):
        self.new_ua = random.choice(self.get_ua_list())
        
    def get_ua_list(self, source=ua_source_url):
        r = requests.get(source)
        soup = BeautifulSoup(r.content, "html.parser")
        tables = soup.find_all('table')
        return [table.find('td').text for table in tables]
        
user_agent = UserAgent().new_ua
headers = {
        'user-agent': user_agent,
    }

# check if the URL is an endpoint or leaf node
def is_url_end_point(url_str):
  filter_words = [".docx", ".doc", ".avi", ".mp4", ".jpg", ".jpeg", ".png", ".gif", ".pdf", ".gz", ".rar", ".tar", ".tgz", ".zip", ".exe", ".js", ".css", ".ppt", "tel:", "fax:", "mailto:", "#", ".rdf", ".ps", ".xlsx", "?"]
  if any(word in url_str for word in filter_words): 
    return True
  return False

# cgathers all the links from a given URL
def get_all_uic_links_from_url(base_url, h = None):
  resp = requests.get(base_url, headers = headers)
  base_url = resp.url
  if is_url_end_point(base_url):
    return [], ""
  http_encoding = resp.encoding if 'charset' in resp.headers.get('content-type', '').lower() else None
  html_encoding = EncodingDetector.find_declared_encoding(resp.content, is_html=True)
  encoding = html_encoding or http_encoding
  
  soup = BeautifulSoup(resp.content, from_encoding=encoding)
  uic_link_list = []
  for link in soup.find_all('a', href=True):
    if is_url_end_point(link['href']):
      continue
    target_url = ''
    o = urlparse(link['href'])
    if "uic.edu" in o.netloc: 
      target_url = link['href'].rstrip('/')
    elif not is_absolute(link['href']):
      target_url = (urllib.parse.urljoin(base_url, link['href'])).rstrip('/')
    target_url = target_url.replace("http:", "https:")
    
    if target_url is not '':
      uic_link_list.append(target_url)
  return list(set(uic_link_list)), h.handle(resp.text)

# Crawling initialised
def main_function():
    
    # Used for parsing texts from HTML
    h = html2text.HTML2Text()
    h.ignore_images = True
    h.ignore_links = True
    h.inline_links = False
    h.wrap_links = False
    h.unicode_snob = True  # Prevents accents removing
    h.skip_internal_links = True
    h.ignore_anchors = True
    h.body_width = 0
    h.use_automatic_links = True
    h.ignore_tables = True

    #Queue initialised for BFS
    queue_uic_links = queue.Queue()
    set_visited_uic_links = set()
    base_url = "https://cs.uic.edu"
    queue_uic_links.put(base_url)
    uic_link_document_list = []
    uic_link_document_dict = {}
    uic_link_document_outer_degree_dict = {}
    count = 0
    global_start_time = time.time()

    visited_data = []
    queue_data = []
    print(os.getcwd())

    # Saved files are loaded to resume from the last saved checkpoint
    if os.path.isfile("set_visited_uic_links.json"):
        with open('set_visited_uic_links.json') as f1:
            visited_data = json.load(f1)
            set_visited_uic_links = set(visited_data)

    if os.path.isfile("queue_uic_links.json"):
        with open('queue_uic_links.json') as f2:
            queue_data = json.load(f2)
            for i in queue_data:
                queue_uic_links.put(i) 

    if os.path.isfile("uic_link_document_list.json"):
        with open('uic_link_document_list.json') as f3:
            uic_link_document_list = json.load(f3)
            
    if os.path.isfile("uic_link_document_dict.json"):
        with open('uic_link_document_dict.json') as f4:
            uic_link_document_dict = json.load(f4)
            
    if os.path.isfile("uic_link_document_outer_degree_dict.json"):
        with open('uic_link_document_outer_degree_dict.json') as f9:
            uic_link_document_outer_degree_dict = json.load(f9)
    print("uic_link_document_dict size", len(uic_link_document_dict.keys()))

    # BFS starts
    while queue_uic_links.qsize() > 0:
        try:
          current_url = queue_uic_links.get()

          count += 1
          start = time.time()
          temp_list, text = get_all_uic_links_from_url(current_url, h)
          end = time.time()
          uic_link_document_dict[current_url] = text
          uic_link_document_outer_degree_dict[current_url] = temp_list

          for index, link in enumerate(temp_list):
            if link not in queue_uic_links.queue and link not in set_visited_uic_links:
              queue_uic_links.put(link)

          set_visited_uic_links.add(current_url)
        
          # create checkpoint every 50th iteration
          if count % 50 == 0:
              print(count, current_url, queue_uic_links.qsize(), end - start, time.time() - global_start_time)
              with open('set_visited_uic_links.json', 'w') as f5:
                  json.dump(list(set_visited_uic_links), f5)
              with open('queue_uic_links.json', 'w') as f6:
                  json.dump(list(queue_uic_links.queue), f6)
              with open('uic_link_document_list.json', 'w') as f7:
                  json.dump(uic_link_document_list, f7)
              with open('uic_link_document_dict.json', 'w') as f8:
                  json.dump(uic_link_document_dict, f8)
              with open('uic_link_document_outer_degree_dict.json', 'w') as f10:
                  json.dump(uic_link_document_outer_degree_dict, f10)
          
        # Push back the link to the queue if Network Exceptions happen 
        except Exception as e:
            print(e)
            print("uic_link_document_dict size", len(uic_link_document_dict.keys()))
            print(count, current_url, queue_uic_links.qsize(), time.time() - start, time.time() - global_start_time)
            queue_uic_links.put(current_url)
        
