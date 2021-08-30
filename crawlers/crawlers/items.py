# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Recipe(scrapy.Item):

    url = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    yields = scrapy.Field()
    time = scrapy.Field()
    intro = scrapy.Field()
    tags = scrapy.Field()
    ingredients = scrapy.Field()
    steps = scrapy.Field()
    date_scraped = scrapy.Field()
    comments = scrapy.Field() # not used
    collection_name = scrapy.Field() 
    filters = scrapy.Field() # TODO
    

    ##### required for images pipeline
    image_urls = scrapy.Field()
    images = scrapy.Field()
    #####
    
