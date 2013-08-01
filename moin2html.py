"""
moin2html.py - mirror a moin site

Usage: python moin2html.py <site> <url> <outdir>

eg. python moin2html.py http://example.com /wiki/somewiki/Main wikidump

Creates file 'url_cache.json' which can be deleted after a successful run.

https://github.com/tbnorth/moin2html
"""
# Terry Brown, Terry_N_Brown@yahoo.com, Tue Jul 30 13:17:30 2013

import json
import os
import re
import sys
import time

Python3 = sys.version_info[0] > 2
if Python3:
    import urllib.request as urllib
else:
    import urllib2 as urllib  

from lxml import etree

if len(sys.argv) == 4:
    SITE, URL, OUTDIR = sys.argv[1:]
else:
    print __doc__
    exit(10)

HTML_parser = etree.HTMLParser()

TIMESTAMP = time.asctime()

# structure of moin attachment URLs
#?action=AttachFile
#?action=AttachFile&do=get&target=sitemap.tdraw
#?action=AttachFile&do=view&target=CRP2007.zip
re_attach_page = re.compile(r"\?action=AttachFile$")
# re_attach_link = re.compile(
#     r"\?action=AttachFile&do=(get|view)&target=(?P<filename>.*)$")
# download the get version, not the view version
re_attach_link = re.compile(
    r"\?action=AttachFile&do=get&target=(?P<filename>.*)$")

# load URL cache to avoid re-getting pages
json_state_file = "url_cache.json"
if not os.path.exists(json_state_file):
    json.dump({'url':{}}, open(json_state_file, 'w'))
url_cache = json.load(open(json_state_file))

if 0:  # clear failed urls
    url_cache['url'] = dict([(k,v) for k,v in url_cache['url'].items()
                             if v is not None])

def get_url(url):
    
    if url not in url_cache['url']:
        try:
            url_cache['url'][url] = urllib.urlopen(url).read()
        except urllib.HTTPError as err:
            print(err)
            if err.code in (404, 500):
                url_cache['url'][url] = None
            else:
                raise
            
    return url_cache['url'][url]

def main():
    
    todo = {
        'pages': [URL],
        'links': [],
        'images': [],
    }
    done = set()
    
    while any(todo.values()):
        process(todo, done)
        
def process(todo, done):
    
    while todo['pages']:
        process_pages(todo, done)
    while todo['links']:
        process_links(todo, done)
    while todo['images']:
        process_images(todo, done)

def local_filter(x):
    return (x.get('href', x.get('src'))[0] == '/' and
            '?' not in x.get('href', x.get('src')))

def process_pages(todo, done):
    
    URL = todo['pages'].pop(0)
    
    print('\n==================================')
    print(URL)
        
    data = get_url(SITE+URL)
    done.add(URL)
    
    if not data:
        return
    
    dom = etree.fromstring(data, parser=HTML_parser)
    links = dom.xpath('//link[@href]')
    images = dom.xpath('//img[@src]')
    all_hrefs = dom.xpath('//a[@href]')

    hrefs = []
    for href in all_hrefs:
        if local_filter(href):
            hrefs.append(href)
        elif  re_attach_page.search(href.get('href')):
            hrefs.append(href)
        elif  re_attach_link.search(href.get('href')):
            hrefs.append(href)
        else:
            if href.get('href')[0] == '/':
                href.set('style', 'color: red')
                href.tag = 'span'
                href.set('title', href.get('href'))
                # span = etree.Element('span')
                # span.set('style', 'color: red')
                # span.text = href.text
                # href.text = ''
                # href.append(span)
            
    links = [i for i in links if local_filter(i)]
    images = [i for i in images if local_filter(i)]
    
    for href in hrefs:
        url_target = href.get('href').split('#', 1)
        if len(url_target) > 1:
            href_url, target = url_target
            target = "#"+target
        else:
            href_url = url_target[0]
            target = ""
        
        attach = re_attach_link.search(href_url)

        if href_url in done:
            print("{%s}" % href_url)
        else:
            if not attach:
                print("%s" % href_url)
                todo['pages'].append(href_url)
            
        if not attach and re_attach_page.search(href_url):
            href_url = href_url.replace('?action=AttachFile', '/_attachments')

        if attach:
            filename = attach.groupdict()['filename']
            data_url = href_url
            href_url = href_url.split('?', 1)[0]  # remove ?action=Attach...
            href_url += '/_attachments/%s' % filename
            new_url = os.path.relpath(href_url, '/dummy/'+URL)
            
            if data_url not in done:
                use_url = SITE+data_url
                print('GET %s %s' % (filename, use_url))
                done.add(data_url)
                try:
                    path = os.path.normpath(OUTDIR + href_url)
                    if not os.path.exists(os.path.dirname(path)):
                        os.makedirs(os.path.dirname(path))
                    if not os.path.exists(path):
                        data = urllib.urlopen(use_url).read()
                        open(path, 'wb').write(data)
                except (urllib.HTTPError, urllib.URLError):
                    pass

        else:
            
            if not re_attach_page.search(URL):
                new_url = os.path.relpath(href_url, URL)
            else:
                new_url = os.path.relpath(href_url, '/dummy/'+URL)
                
            new_url = new_url + "/index.html" + target
        
        href.set('href', new_url)
        
    for link in links:
        link_url = link.get('href')
        
        if link_url in done:
            print("{%s}" % link_url)
        else:
            print("%s" % link_url)
            todo['links'].append(link_url)
            done.add(link_url)
            
        new_url = os.path.relpath(link_url, URL)
        if '?action=AttachFile' in URL:
            new_url = os.path.relpath(link_url, '/dummy'+URL)
        
        link.set('href', new_url)
        
    for image in images:
        image_url = image.get('src')
        
        if image_url in done:
            print("{%s}" % image_url)
        else:
            print("%s" % image_url)
            done.add(image_url)
            
            use_url = SITE+image_url
            print('GET %s %s' % (image_url, use_url))
            try:
                path = os.path.normpath(OUTDIR + image_url)
                if not os.path.exists(os.path.dirname(path)):
                    os.makedirs(os.path.dirname(path))
                if not os.path.exists(path):
                    data = urllib.urlopen(use_url).read()
                    open(path, 'wb').write(data)
            except (urllib.HTTPError, urllib.URLError):
                pass
            
        new_url = os.path.relpath(image_url, URL)
        
        image.set('src', new_url)
        
    if '?action=AttachFile' in URL:
        URL = URL.replace('?action=AttachFile', '/_attachments')
     
    path = OUTDIR + URL + "/index.html"
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    ts = etree.Comment(
        " Exported from moin to static HTML by moin2html.py %s " % TIMESTAMP)
    dom.xpath('//html')[0].insert(0, ts)
    etree.ElementTree(dom).write(path)
        
def process_links(todo, done):
    
    URL = todo['links'].pop(0)
    
    print('\n==================================')
    print(URL)
        
    data = get_url(SITE+URL)
    done.add(URL)
    
    if not data:
        return
     
    path = OUTDIR + URL
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    
    if not os.path.exists(path):
        open(path, 'wb').write(data.encode('utf-8'))
        
if __name__ == '__main__':

    try:
        main()
    finally:
        json.dump(url_cache, open(json_state_file, 'w'), indent=4)
