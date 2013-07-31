"""
moinmirror.py - mirror a moin site

Terry Brown, Terry_N_Brown@yahoo.com, Tue Jul 30 13:17:30 2013
"""

import os
import sys
import urllib2

from lxml import etree

SITE = "http://gisdata.nrri.umn.edu"
URL = "/wiki/gislabwiki/Main"
OUTDIR = "test"

HTML_parser = etree.HTMLParser()

import json

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
            url_cache['url'][url] = urllib2.urlopen(url).read()
        except urllib2.HTTPError, err:
            print err
            if err.code in (404, 500):
                url_cache['url'][url] = None
            else:
                raise
            
    return url_cache['url'][url]

def main():
    
    todo = {
        'pages': [URL],
        'links': [],
        'scripts': [],
    }
    done = set()
    
    while any(todo.values()):
        process(todo, done)
        
def process(todo, done):
    
    while todo['pages']:
        process_pages(todo, done)
    while todo['links']:
        process_links(todo, done)
    while todo['scripts']:
        process_scripts(todo, done)

def local_filter(x):
    return x.get('href')[0] == '/' and '?' not in x.get('href')

def process_pages(todo, done):
    
    URL = todo['pages'].pop(0)
    
    print
    print '=================================='
    print URL
        
    data = get_url(SITE+URL)
    done.add(URL)
    
    if not data:
        return
    
    dom = etree.fromstring(data, parser=HTML_parser)
    links = dom.xpath('//link[@href]')
    scripts = dom.xpath('//script[@src]')
    all_hrefs = dom.xpath('//a[@href]')

#?action=AttachFile
#?action=AttachFile&do=get&target=sitemap.tdraw
#?action=AttachFile&do=view&target=CRP2007.zip

    hrefs = []
    for href in all_hrefs:
        if local_filter(href):
            hrefs.append(href)
        elif href.get('href').endswith('?action=AttachFile'):
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
    
    for href in hrefs:
        url_target = href.get('href').split('#', 1)
        if len(url_target) > 1:
            href_url, target = url_target
            target = "#"+target
        else:
            href_url = url_target[0]
            target = ""
        
        if href_url in done:
            print "{%s}" % href_url
        else:
            print "%s" % href_url
            todo['pages'].append(href_url)
            
        if href_url.endswith('?action=AttachFile'):
            href_url = href_url.replace('?action=AttachFile', '/_attachments')
            #X new_url = os.path.relpath(href_url, '/dummy/'+URL)
            
        new_url = os.path.relpath(href_url, URL)
            
        new_url = new_url + "/index.html" + target
        
        href.set('href', new_url)
        
    for link in links:
        link_url = link.get('href')
        
        if link_url in done:
            print "{%s}" % link_url
        else:
            print "%s" % link_url
            todo['links'].append(link_url)
            done.add(link_url)
            
        new_url = os.path.relpath(link_url, URL)
        if '?action=AttachFile' in URL:
            new_url = os.path.relpath(link_url, '/dummy'+URL)
        new_url = new_url
        
        link.set('href', new_url)
        
    if '?action=AttachFile' in URL:
        print URL, '->',
        URL = URL.replace('?action=AttachFile', '/_attachments')
        print URL
     
    path = OUTDIR + URL + "/index.html"
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    print path
    etree.ElementTree(dom).write(path)
        
def process_links(todo, done):
    
    URL = todo['links'].pop(0)
    
    print
    print '=================================='
    print URL
        
    data = get_url(SITE+URL)
    done.add(URL)
    
    if not data:
        return
     
    path = OUTDIR + URL
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    print path
    
    if not os.path.exists(path):
        open(path, 'w').write(data)
        
if __name__ == '__main__':

    try:
        main()
    finally:
        json.dump(url_cache, open(json_state_file, 'w'), indent=4)
