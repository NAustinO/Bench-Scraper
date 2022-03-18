import os,sys
from scrapy import crawler 
from scrapy.crawler import CrawlerProcess
from crawlers.crawlers.spiders import nytcook_spider

def main():

    crawl_dir_path = os.chdir('crawlers')
    sys.path.append(crawl_dir_path)
    process = CrawlerProcess()
    process.crawl(nytcook_spider)
    process.start()

if __name__=='__main__':
    main()