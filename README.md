# blogspot downloader

This python script download all posts from blogspot and convert into epub or pdf, either in web page looks or rss feed looks.

Not only blogspot, if any webpage contains rss feed, especially for wordpress, then it able to download in rss mode.

## Why ?

The existing online services either need to paid, has limit of files, need to copy per-page manually, only support rss feed, or only support epub. This python script is free, no files limit as it run in your local machine/ip, download all pages/feed automatically, support both rss and web scraping(some blog rss is private or only one page), support both epub and pdf. It also support custom locale date. The most important thing: this is simple python code and you can feel free to modify it, e.g. custom html color, extra html header/footer, default directory ... etc :)

## How to setup(Only support python3):
    git clone https://github.com/limkokhole/blogspot-downloader.git

    pip3 install -r requirements_py3.txt #python 3

    In ubuntu, run `sudo apt install wkhtmltopdf`

## How to run (Only support python3):

    python3 blogspot_downloader.py [url]

    OR

    $ python3 blogspot_downloader.py --help

    usage: blogspot_downloader.py [-h] [-a] [-s] [-d] [-p] [-l LOCALE] [-f FEED]
                                  [-1]
                                  [url]

    Blogspot Downloader

    positional arguments:
      url                   Blogspot url

    optional arguments:
      -h, --help            show this help message and exit
      -a, --all             Display website mode instead of rss feed mode. Only
                            support blogspot website but you can try your luck in
                            other site too
      -s, --single          Download based on provided url year/month instead of
                            entire blog, will ignored in rss feed mode and
                            --print_date
      -d, --print_date      Print main date info without execute anything
      -p, --pdf             Output in PDF instead of EPUB but might failed in some
                            layout
      -l LOCALE, --locale LOCALE
                            Date translate to desired locale, e.g. -l zh_CN.UTF-8
                            will shows date in chinese
      -f FEED, --feed FEED  Direct pass full rss feed url. e.g. python
                            blogspot_downloader.py http://www.ulduzsoft.com/feed/
                            -f http://www.ulduzsoft.com/feed/. Note that it may
                            not able to get previous rss page in non-blogspot
                            site.
      -1, --one             Scrape url of ANY webpage as single pdf(-p) or epub
      -lo, --log-link-only  print link only log for -f feed, temporary workaround
                            to copy into -1, in case -f feed only retrieve
                            summary.

## Details:

It will asked the blogspot url if you don't pass [url] in command option.

Use -f rss_feed_url to download from rss feed, or -a webpage_url to download from webpage. Tips: you may lucky to find feed url by right-click on the webpage and choose "View Page Source", then search for "rss" keyword. Note that rss_feed / path might has impact to narrow the scope of feed, e.g. https://example.com/2018/05/ might narrow the feed only for may only, and https://example.com/2018/ might narrow the feed for year 2018.

Not all blogs works in -p pdf mode, you will quickly noticed this if you found duplicated layout for first few pages, then you can ctrl+c to stop it. Try remove -p or use -f feed_url instead in this case, or download epub only.

This script designate in Linux and never test in Windows. This script also not designate run in multi process since it will remove /tmp trash file.

To make pypub works in python 3, read how_to_make_epub_work_in_python3.guide to change it manually yourself, or simply fork the module from https://github.com/limkokhole/pypub . I recommend using python 3 since I noticed python 2 has issue when parsing table tags.

Duplicated filename will not replace but suffix with current timestamp.

ePUB file can edit manually. Simply change name to .zip, unzip it, edit the xhtml, and (inside epub directory) do `zip -rX ../<epub direcory name>.epub minetype.txt META-INF/ OEBPS/` to repack it easily.  I recommend Kchmviewer viewer and Sigli, but if it doesn't open since it may too strict in xhtml syntax, then you can try other viewer in this case (Sigli will try auto fix for you), and please don't feel hesitate to issue a ticket.

## Sample Screenshots:

download non-blogspot site as rss feed in pdf:  

![medium](/medium.png?raw=true "download non-blogspot site as rss feed in pdf")  

download blogspot site as rss feed in pdf without file limits:

![google](/google.png?raw=true "download blogspot site as rss feed in pdf without file limits")  

download blogspot site as web scraping in ePUB which able to include comments section:

![eat](/eat.png?raw=true "download blogspot site as web scraping in ePUB")

download blogspot site as rss feed in ePUB, plus custom locale date in Chinese:  

![locale](/locale.png?raw=true "download blogspot site as rss feed in ePUB, plus custom locale")

pdf keep color, while ePUB don't:  

![color](/color.png?raw=true "pdf keep color, while ePUB don't")

With --one option, you can paste any webpage link manually to make custom ebook chapter :D (Tip: You can download this extension https://addons.mozilla.org/en-US/firefox/addon/link-gopher to get all the link then copy/paste all in once(No need to paste one by one) into prompt, and don't forget last link need to press Enter. You can also use `< urls.txt` style.)

![color](/perl.png?raw=true "You can even paste any webpage link to create a nice ePUB ebook :D")

## Demonstration video (Click image to play at YouTube): ##
[![watch in youtube](https://i.ytimg.com/vi/B6QzTmMglEo/hqdefault.jpg)](https://www.youtube.com/watch?v=B6QzTmMglEo "Blogspot_downloader")


