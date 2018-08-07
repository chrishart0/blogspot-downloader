# -*- coding: utf-8 -*-
# The MIT License (MIT)
# Copyright (c) 2018 limkokhole@gmail.com
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.
#from __future__ import absolute_import

__author__ = 'Lim Kok Hole'
__copyright__ = 'Copyright 2018'
__credits__ = []
__license__ = 'MIT'
__version__ = '1.0.1'
__maintainer__ = 'Lim Kok Hole'
__email__ = 'limkokhole@gmail.com'
__status__ = 'Production'

import traceback, shutil, resource
import sys, os, re, time
from dateutil import parser as date_parser #need `as` or else conflict name with ArgumentParser
import unicodedata
#import pkgutil #I think it should be the responsible of pypub/__init__.py, not this file even it can fix
#sys.path.append(os.path.dirname(pkgutil.get_loader("pypub").get_filename()))
import feedparser #for rss feed mode
import pdfkit #for pdf #also need `sudo apt install wkhtmltopdf`
if sys.version_info[0] >= 3:
    from urllib.request import urlopen
    from urllib.error import HTTPError
    from urllib.parse import urlparse
    import urllib.request
    def unicode(mystr): #python3
        return mystr
else:
    from urllib2 import urlopen, HTTPError
    import urllib2
    from urlparse import urlparse
    input = raw_input
try: from bs4 import BeautifulSoup, SoupStrainer #python3 #python2 also got, and python need use this or else error when `soup = BeautifulSoup(r, "lxml")` 
except ImportError: from BeautifulSoup import BeautifulSoup, SoupStrainer #python2
#import weasyprint #incomplete, so don't use
import argparse
parser = argparse.ArgumentParser(description='Blogspot Downloader')
args = ""
def slugify(value):
    if sys.version_info[0] >= 3:
        value = unicodedata.normalize('NFKD', value)
    #value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    #value = unicode(re.sub('[^\w\s-]', ' ', value, re.UNICODE).strip())
    if args.pdf:
        value = unicode(re.sub('[-/\s]+', ' ', value, re.UNICODE))
    else: #pypub always replace dot, so to make duplicated file checking works, need to replace here before feed pypub.
        value = unicode(re.sub('[-_./\s]+', ' ', value, re.UNICODE))
    return value
import locale, contextlib
@contextlib.contextmanager
def setlocale(*args, **kw):
  saved = locale.setlocale(locale.LC_ALL)
  yield locale.setlocale(*args, **kw)
  locale.setlocale(locale.LC_ALL, saved)

if sys.version_info[0] >= 3:
    r1 = '’'; r2 = "“"; r3 = "”"; r4 = '—'; r5 = '–'; r6 = '…'; r7 = '®'
else:
    r1 = '’'.decode('utf-8'); r2 = "“".decode('utf-8'); r3 = "”".decode('utf-8'); r4 = '—'.decode('utf-8'); r5 = '–'.decode('utf-8'); r6 = '…'.decode('utf-8'); r7 = '®'.decode('utf-8')
#import cgi #cgi.escape
def replacer(s):
    return s.replace('\\x26', "&").replace(r1, "'").replace(r2, '"').replace(r3, '"').replace(r4, '--').replace(r5, '-').replace(r6, '...').replace(r7, '(R)').replace('& ', '&amp;') #put \x26 first, and \x26amp; and \x26#39; means & and ' respectively

temp_dir_ext=".blogspot-downloader.temp"
import tempfile
sys_tmp_dir = tempfile.gettempdir()
def rm_tmp_files():
    #this is simply remove tmp trash files in /tmp/, and also need clean_up() to remove custom temp dir(set in epub_dir when invoke pypub.Epub(fname, epub_dir=fname+temp_dir_ext) or else pypub module use tempfile.mkdtemp() which doesn't clean up unless reboot), and /tmp/ might got limit also.
    #Note that the error "Too many open files" has nothing to do with temp files, which the actualy fix is resource.setrlimit. (`ulimit -n` to know your current open file soft limit)
    #note that it should only remove after create_epub() and don't remove directory or else need re-init pypub.Epub() and add_chapter from scratch
    for root, dirs, files in os.walk(sys_tmp_dir):
        for fname in files:
            path = os.path.join(root, fname)
            if (len(path) == 14) and path.startswith(os.path.join(sys_tmp_dir, "tmp")): #it may remove wrongly if you have tmpt<SOTDi> file, but it's under module and I don't know how to change its prefix, lolr
                #print('should remove: ' + path)
                try:
                    os.remove(path)
                except OSError as e:
                    print('Failed to remove file')
soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
#print('You might hit sort limit of open files ', soft, ", now try to change soft to hard limit: ", hard)
resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))

UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'

def get_locale_abbrev(s):
    try:
        with setlocale(locale.LC_TIME, args.locale):
            return date_parser.parse(s).strftime('%B %d, %Y, %H:%M %p')
    except locale.Error as e:
        print('\nPlease provide enabled locale alias in your system, e.g. zh_CN.UTF-8. In Linux, you may comment out desired locale in /etc/locale.gen file and then run `sudo locale-gen` to enable it\n')
        clean_up() 
        sys.exit(-1)

def process_rss_link(url):
    if '?' not in url:
        url+='?'
    if 'start-index=' not in url:
        url+='&start-index=1&max-results=25'
    return url.replace('&alt=rss', '').replace('?alt=rss', '?') #to prevent no next rss page link


def print_rss_err():
    print('\nSeems like no permission to access rss feed, consider use -a option to scrape in web mode. Or check your url typo OR network. Tips: you may lucky to find feed url by right-click on the webpage and choose "View Page Source", then search for "rss" keyword\n')

epub_dir = ""
download_once = False #if want support interactive, then need to changed this logic
def download(url, h, d_name, ext):
        global download_once
        global my_epub
        global epub_dir
        if not args.pdf:
            try:
                import pypub #for epub
            except ImportError:
                traceback.print_exc()
                print("\ncurrently epub not support in python 3, please run as python2 OR supply -p option to download as pdf\n")
                clean_up()
                sys.exit(-1)

        #e.g. 'https://diannaoxiaobai.blogspot.com/?action=getTitles&widgetId=BlogArchive1&widgetType=BlogArchive&responseType=js&path=https://diannaoxiaobai.blogspot.com/2018/'
        visit_link = url
        if args.all:
            y_url = url + "/?action=getTitles&widgetId=BlogArchive1&widgetType=BlogArchive&responseType=js&path=" + h
            print("Scraping year... " + y_url)
            try:
                r = urlopen(y_url).read()
            except HTTPError as he:
                print('\nNote that -a -s only allow if url has /year/[month] format, pls check your url\n')
                clean_up()
                os._exit(1)
            if sys.version_info[0] >= 3:
                r = r.decode('utf-8')
            t = r.split("'title'")
            t = t[1:]
        else:
            orig_url = url
            url = process_rss_link(url)
            print("Scraping rss feed... " + url)
            r = feedparser.parse(url) #, request_headers={'User-Agent': UA, 'Referer': url}) #I noticed https://blog.mozilla.org/security/feed/1 (/1 non exist) is working in feedparser, lolr
            #print(r.headers)
            t = r['entries']
            if (not t) or ("link" not in r['feed'].keys()): #'User does not have permission to read this blog.' of rss feed come here
                try:
                    print("Try to scrape rss feed url automatically ... " + orig_url)
                    ##r = urlopen(orig_url).read() #https://medium.com/bugbountywriteup got check UA if urllib2 UA then not authorized
                    if sys.version_info[0] >= 3:
                        req = urllib.request.Request(orig_url, data=None, headers={ 'User-Agent': UA })
                        r = urllib.request.urlopen(req).read()
                    else:
                        req = urllib2.Request(orig_url, headers={ 'User-Agent': UA })
                        r = urllib2.urlopen(req).read()
                except Exception as e:
                    print(e)
                    print("Request webpage failed, please check your network OR authorized to access that url.")
                    clean_up()
                    os._exit(1) #don't use sys.exit(-1) if don't want to traceback to main() to print exception
                soup = BeautifulSoup(r, "lxml")
                data = soup.findAll('link', attrs={'type':'application/rss+xml'})
                if data:
                    url = data[0].get("href")
                    url = process_rss_link(url)
                    if url.startswith('/'): #http://sectools.org/tag/sploits/ only has href="/feed/"
                        parsed_orig_uri = urlparse(orig_url)
                        url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_orig_uri) + url
                    print("Scraping rss feed one more time ... " + url)
                    r = feedparser.parse(url)
                    t = r['entries']
                    if not t:
                        t = []
                else:
                    t = []
            if ("keys" in dir(r)) and ('link' in r['feed'].keys()):
                l = r['feed']['links']
                if l:
                    got_next = False
                    for ll in l:
                        if ll['rel'] == 'next':
                            got_next = True
                            url = ll['href']
                            break;
                    if not got_next:
                        url = ''
                else:
                    url = ''
            elif not t: #no need care if next page rss index suddently change and no content case
                url = ''
                print_rss_err()
        count = 0
        for tt in t:
            count+=1
            title_raw = ''
            title_is_link = False
            if not args.all:
                #e.g. parser.parse('2012-12-22T08:36:46.043-08:00').strftime('%B %d, %Y, %H:%M %p')
                h = ''
                if args.locale:
                    if sys.version_info[0] >= 3:
                        t_date = get_locale_abbrev(tt['published'])
                    else:
                        t_date = get_locale_abbrev(tt['published']).decode('utf-8')
                else:
                    t_date = date_parser.parse(tt['published']).strftime('%B %d, %Y, %H:%M %p')
                
                for feed_links in tt['links']:
                    if feed_links['rel'] == 'alternate':
                        visit_link = feed_links['href']
                title_raw = tt['title'].strip()
                title_pad = title_raw + ' '
                if (not args.pdf) or (not tt['title']): #epub got problem copy link from text, so epub always shows link
                    tt['title'] = visit_link
                    title_is_link = True
                h = '<div><small>' + tt['author_detail']['name'] + ' ' +  t_date + '<br/><i>' + title_pad + '<a style="text-decoration:none;color:black" href="' + visit_link + '">' + tt['title'] + '</a></i></small><br/><br/></div>' #<hr style="border-top: 1px solid #000000; background: transparent;">
                #pdfkit need specific charset, epub seems no need
                if args.pdf: #just now got 1 post shows blank but got div in feed, then noticed it's white color font, lol
                    h = '<head><meta charset="UTF-8"></head><body>' + h + tt['summary'].replace('<div class="separator"', '<div class="separator" align="center" ') + '</body>'
                else: #epub can't set body/head
                    h = h + tt['summary'].replace('<div class="separator"', '<div class="separator" align="center" ')
                title = tt['title']
                t_url = visit_link
            else:
                field = tt.split("'")
                title = field[1]
                title_raw = title.strip()
                t_url = field[5]
            print('\ntitle: ' + title_raw)
            print('link: ' + t_url)
            if args.pdf:
                print('Download html as PDF, please be patient...' + str(count) + '/' + str(len(t)-1))
            else:
                print('Download html as EPUB, please be patient...' + str(count) + '/' + str(len(t)-1))
            if args.pdf:
                if title_is_link: #else just leave slash with empty
                    title = '/'.join(title.split('/')[-3:])
                if sys.version_info[0] >= 3:
                    fname = os.path.join( d_name, slugify(unicode(title)) )
                else:
                    print(title)
                    try:
                        title = title.decode('utf-8')
                    except:
                        pass #print('calm down, is normal decode error')
                    title = replacer(title)
                    #fname = os.path.join( d_name, slugify(title.decode('utf-8')))
                    fname = os.path.join( d_name, slugify(title))
            else: #no point do set fname based on title since epub is single file only with multiple chapters
                fname = d_name
            fpath = os.path.join( os.getcwd(), fname )
            if args.pdf:
                check_path = os.path.join( fpath + ext )
            else:
                check_path = fpath[:-1] + ext
            if (not download_once) and os.path.exists( check_path ):
                if args.pdf:
                    fpath = fpath + '_' + str(int(time.time())) + ext
                else:
                    fname = fname[:-1] + ' ' + str(int(time.time())) #pypub truncated _, so can't use '_'
            else:
                if args.pdf:
                    fpath+=ext
                else:
                    fpath = fpath[:-1] + ext
                    fname = fname[:-1]
            if args.pdf:
                print("file path: " + fpath)
                #pdf = weasyprint.HTML(t_url).write_pdf()
                #file( d_name + "/" + slugify(unicode(title)) + ".pdf", 'w' ).write(pdf)
                if args.all:
                    try:
                        pdfkit.from_url(t_url, fpath)
                    except IOError as ioe:
                        print("pdfkit IOError")
                else:
                    try:
                        #https://security.googleblog.com/2013/10/dont-mess-with-my-browser.html site can't open in kchmviewer bcoz of this
                        #, which you direct unzip .EPUB and open that xhtml will got error
                        #-f 'https://security.googleblog.com/feeds/posts/default?start-index=179&max-results=1' direct jump to desired index to test
                        #rf: https://www.w3.org/wiki/Common_HTML_entities_used_for_typography
                        #narrow down OEBPS/toc.nc by removing list of items, then download by index+repack+<open_in_web_browser_OR_kchmviewer> above to know which portion of items trigger the xml error #got case toc.nc itself contains '&' which must replace with `&amp;`
                        h = replacer(h)
                        pdfkit.from_string(h, fpath)
                    except IOError as ioe:
                        print('Exception IOError: ' + repr(ioe))
            else:
                if not download_once:
                    download_once = True
                    print("file path: " + fpath)
                    if os.path.exists(fname+temp_dir_ext):
                        print(fname+temp_dir_ext + " already exists, please move/backup that direcory to another place manually. Abort")#to not blindly replace file
                        os._exit(1)
                    tmp_dir = fname+temp_dir_ext
                    my_epub = pypub.Epub(fname, epub_dir=tmp_dir)
                    epub_dir = os.path.join( os.getcwd(), tmp_dir )
                    print("epub_dir: " + epub_dir)
                if title_raw:
                    try:
                        title = title.decode('utf-8')
                    except:
                        pass
                    title_raw = replacer(title_raw).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') #unlike content, title can replace '&'(no space) like that since & may no space
                    #, if content do like that will got no image, got visible &nbsp; text ...etc
                if args.all:
                    if title_raw:
                        my_chapter = pypub.create_chapter_from_url(title=title_raw, url=t_url)
                    else: #no choice like that and better not set with t_url, use other editor if kchmviewer error, should unlikely happen though
                        my_chapter = pypub.create_chapter_from_url(t_url)
                    my_chapter.content = replacer(my_chapter.content)
                    my_chapter.title = replacer(my_chapter.title)
                    #sigil viewer will warning and auto convert for you, e.g. /<img> become </>, replace <!DOCTYPE html> to <?xml version="1.0" encoding="utf-8"?><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">, Add  <title></title> ...etc, this isnormal and shouldn't have extra work to do, while kchmviewer able to render it without error.
                    try:
                        my_chapter.content = my_chapter.content.decode('utf-8')
                    except:
                        pass #print("decode content err")
                    try:
                        my_chapter.title = my_chapter.title.decode('utf-8')
                    except: #-a http://cuhkt48.blogspot.com/2016/07/blog-post.html
                        pass #print("decode title err")
                else:
                    h = replacer(h)
                    if title_raw:
                        my_chapter = pypub.create_chapter_from_string(h, title=title_raw, url=t_url)
                    else:
                        my_chapter = pypub.create_chapter_from_string(h, title='/'.join(title.split('/')[-3:]), url=t_url)
                    #print(my_chapter.content)
                    #my_chapter = pypub.create_chapter_from_string(r['entries'][0]['summary'].replace('<div class="separator"', '<div class="separator" align="center" '))
                my_epub.add_chapter(my_chapter)
                my_epub.create_epub(os.getcwd())
                rm_tmp_files()
        return url #return value used for rss feed mode only

def scrape(url, d_name, ext):
    try:
        #r = urlopen(url).read()
        if sys.version_info[0] >= 3:
            req = urllib.request.Request(url, data=None, headers={ 'User-Agent': UA })
            r = urllib.request.urlopen(req).read()
        else:
            req = urllib2.Request(url, headers={ 'User-Agent': UA })
            r = urllib2.urlopen(req).read()
    except Exception as e:
        print(e)
        print("Please check your network OR url.")
        clean_up()
        os._exit(1)
    soup = BeautifulSoup(r, "lxml")
    case = 0
    data = soup.findAll('a',attrs={'class':'post-count-link'})
    if not len(data):
        case = 1
        data = soup.findAll('li',attrs={'class':'archivedate'})
    year_l = []
    if len(data) == 0:
        print('\nNo data found. You may check your url OR try -f <rss feed url> instead. Also do not use -a if -f added.\n')
        os._exit(1)
    for div in data:
        if case == 0:
            h = div['href']
        else:
            h = div.a.get('href')
        dup = False
        for y in year_l:
            if h.startswith(y):
                dup = True
                break
        if not dup:
            year_l.append(h)
            if args.print_date:
                print(h)
            else:
                download(url, h, d_name, ext)

def clean_up():
    global epub_dir
    try:
        #traceback.print_exc()
        if (not args.pdf) and epub_dir:
            #print("Remove temp files")
            rm_tmp_files()
            temp_dir = os.path.join( os.getcwd(), epub_dir )
            if os.path.isdir(temp_dir): #may no temp dir if no images in feed
                shutil.rmtree( temp_dir )
            #print("Removed temp dir successfully -1")
    except Exception as e:
        #traceback.print_exc()
        print("Remove temp " + epub_dir + "  dir failed -1, please check if it exist and remove manually.")
        sys.exit(-1)

def main():
        if args.url:
            url = args.url
        else:
            url = input('Blogspot URL: ').strip()
        if (url.startswith("'") and url.endswith("'")) or (url.startswith('"') and url.endswith('"')):
            url = url[1:-1]
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        if url.endswith('.html'):
            url = "/".join(url.split('/')[:-1])
        parsed_uri = urlparse(url)
        netloc = '{uri.netloc}/'.format(uri=parsed_uri)
        d_name = slugify(unicode(netloc))
        if args.pdf:
            if not os.path.isdir(d_name):
                os.makedirs(d_name)
            ext = '.pdf'
        else:
            ext = '.epub'
        if args.print_date:
            print('Debugging\n')
            scrape(url, d_name, ext)
        elif not args.all:
            print('Download in rss feed mode')
            if args.feed:
                url = args.feed
            #else: shouldn't do like that, it should depends on later scrape the rss link in webpage, or else https://blog.mozilla.org/security/ not working
            #    url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri) + 'feeds/posts/default?start-index=1&max-results=25'
            while url:
                url = download(url, url, d_name, ext)
        elif args.single:
            print('Download single year/month in website mode')
            download(url, url, d_name, ext)
        else:
            print('Download all in website mode')
            scrape(url, d_name, ext)
        print("\nDone")

if sys.version_info[0] < 3:
    sys.exc_clear() #do not produce eception of import part.
if __name__ == "__main__":
    parser.add_argument('-a', '--all', action='store_true', help='Display website mode instead of rss feed mode. Only support blogspot website but you can try yuor luck in other site too')
    parser.add_argument('-s', '--single', action='store_true', help='Download based on provided url year/month instead of entire blog, will ignored in rss feed mode and --print_date')
    parser.add_argument('-d', '--print_date', action='store_true', help='Print main date info without execute anything')
    parser.add_argument('-p', '--pdf', action='store_true', help='Output in PDF instead of EPUB but might failed in some layout')
    parser.add_argument('-l', '--locale', help='Date translate to desired locale, e.g. -l zh_CN.UTF-8 will shows date in chinese')
    parser.add_argument('-f', '--feed', help='Direct pass full rss feed url. e.g. python blogspot_downloader.py http://www.ulduzsoft.com/feed/ -f http://www.ulduzsoft.com/feed/. Note that it may not able to get previous rss page in non-blogspot site.')
    parser.add_argument('url', nargs='?', help='Blogspot url') #must add nargs='?' or else always need url but -f shouldn't need
    args, remaining  = parser.parse_known_args() #don't use normal parse_args() which can't ignore above url
    if args.feed:
        #if got -f <feed url> then use feed url as url and no need normal url
        args.url = args.feed
    try:
        main()
    except Exception as e:
        if traceback.format_exc() != 'None\n':
            #traceback.print_exc()
            print(traceback.format_exc())
            print("Exception -2") #this one might not called if ctrl+c inside pypub.create_chapter_from_url's urllib3, so we need another finally to do clean_up 
        if args:
            clean_up()
    finally: #https://stackoverflow.com/questions/4606942/why-cant-i-handle-a-keyboardinterrupt-in-python
        #traceback.print_exc() #finally doesn't always means exception, it will run even in normal flow, so no need clean_up in other place
        #f = open(os.devnull, 'w') #don't print anthing for traceback.print_exc
        #sys.stdout = f
        if traceback.format_exc() != 'None\n':
            print(traceback.format_exc())
            print("Exception -1")
        if args:
            clean_up()

