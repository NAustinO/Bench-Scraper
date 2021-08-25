import datetime
import sys, os
import scrapy
from datetime import date
from pathlib import Path
from bs4 import BeautifulSoup
from urllib import request
from urllib.error import URLError
from scrapy import http
from scrapy.http import Response
from scrapy.extensions import closespider
from scrapy.pipelines.images import ImagesPipeline
from crawlers.items import Recipe
from utils import get_image_urls




class TimesSpider(scrapy.Spider):

    name = "times"

    path = Path(__file__)
    IMAGES_DIR_PATH = str(path.parents[2]) + "/data/images"

    #start_urls = ["https://cooking.nytimes.com/recipes/4796-lemon-glazed-cardamom-pear-tea-bread"]

    '''
    def start_requests(self):
        pageUrls = []
        
        pageNumber = 1

        end_loop_trigger = 0 # stores the number of times the request url fails to return a valid page. 

        # iterates over each page to get the page urls in a list
        while True:
            url = "https://cooking.nytimes.com/search?q=&page={}".format(pageNumber)

            try:
                #TODO find a way to identify if a page is a valid collection page vs a error handling page 

                response = request.urlopen(url=url)
            except URLError:
                if end_loop_trigger >= 3:
                    print("The last valid url page was " + url)
                    break
                else:
                    end_loop_trigger += 1
                    pageNumber += 1 
                    
            else:
                print("Successfully reached url: {}".format(url))
                end_loop_trigger = 0 
                pageNumber += 1
                pageUrls.append(url)


        for url in pageUrls:
            yield scrapy.Request(url=url, callback=self.parse_page)
    '''

    def start_requests(self):
        """
        This method gathers all the urls for both recipes and recipe collections for all pages to be parsed further in  the parse_page method
        """
        pageUrls = []
        
        pageNumber = 1

        end_loop_trigger = 0 # stores the number of times the request url fails to return a valid page. 

        # iterates over each page to get the page urls in a list
        while True:
            url = "https://cooking.nytimes.com/search?q=&page={}".format(pageNumber)

            try:
                response = request.urlopen(url=url)
            except URLError:
                if end_loop_trigger >= 3:
                    print("The last valid url page was " + url)
                    break
                else:
                    end_loop_trigger += 1
                    pageNumber += 1 
                    
            else:
                print("Successfully reached url: {}".format(url))
                end_loop_trigger = 0 
                pageNumber += 1
                pageUrls.append(url)

        for url in pageUrls:
            yield scrapy.Request(url=url, callback=self.parse_page)

    def parse_page(self, response: Response):
        """
        This method takes the response for each url given from start_urls method and redirects them to the parse method if the response shows that it is a recipe, or recursively if the response indicaes that it is a recipe collection page 
        """
      
        response_metadata = dict(response.cb_kwargs)

        #if response_metadata.get("collection") is not None:

        links_on_page = response.css("article.card a.card-link:not(.card-recipe-info)::attr(href)").getall()

        for link in links_on_page:
            if link.startswith("/recipes"): # if the link is a url for a recipe
                yield scrapy.Request(url="https://cooking.nytimes.com{}".format(link), callback=self.parse, encoding='utf-8')
                
            elif link[1].isdigit(): # link is a url for a collection of recipes
                collection_page = request.urlopen(url=link)
                soup = BeautifulSoup(collection_page, "html.parser")
                collection_name = soup.find("h1", attrs={"class":"name"}).string

                collection_set = set()
                collection_set.add(collection_name)
                metadata = {
                    "collection": collection_set
                }
                yield scrapy.Request(url="https://cooking.nytimes.com{}".format(link), callback=self.parse_page, encoding='utf-8', cb_kwargs=metadata)

    
    def parse(self, response: http.TextResponse):
        print('Parsing page: ' + response.url)
        image_urls = []
        try:
            imageURL = response.css('.recipe-intro>.media-container img').attrib['src']
        except KeyError:
            title_for_query = stringCleanup(response.css('h1.recipe-title::text').get())
            image_urls = get_image_urls(title_for_query, 1)
            #response = request.urlopen("https://www.google.com/search?q={}&tbm=isch".format(title_for_query))
           # print("Recipe had no image")
            #image_urls = []
            pass
        else:
            image_urls.append(imageURL)

        try:
            title = stringCleanup(response.css('h1.recipe-title::text').get())
            author = stringCleanup(response.css('.nytc---recipebyline---bylinePart > a::text').get())
            yields = stringCleanup(response.css('.recipe-yield-container > .recipe-yield-value::text').get())
            time = stringCleanup(response.css('.recipe-time-yield li:nth-child(2) > .recipe-yield-value ::text').get())
            intro = stringCleanup(response.css('.recipe-topnote-metadata .topnote p ::text').get())
            tags = response.css('.tags-nutrition-container > .tag ::text').getall()
            tags = [stringCleanup(tag) for tag in tags]
            url = response.url
            steps = response.css('.recipe-steps > li').getall()
            steps = [stringCleanup(item).replace('<li>', '').replace('</li>', '') for item in steps]
            ingredients = self.getRecipeParts(response)
            date = datetime.datetime.today()
    
            recipe = Recipe(title=title, author=author, url=url, yields=yields, time=time, intro=intro, tags=tags, steps=steps, ingredients=ingredients, image_urls=image_urls, date_scraped=date)
        
            yield recipe

        except Exception as err:
            print('An error occured')
            raise closespider("Ran into an exception: " + err)


    ''' Returns a dictionary containing the recipe parts broken down further into quantity and ingredient 
        {
            PARTNAME : [{
                'quantity':
                'ingredient': 
                'display': 
            },
                
            ]
        }
    '''
    def getRecipeParts(self, response):
        '''
        Returns a dictionary containing the recipe parts broken own further into quantity, ingredient, and display as 
        '''
        parts = {}
        sections = response.css('.recipe-ingredients-wrap > .recipe-ingredients').getall()
        sectionHeaders = response.css('.recipe-ingredients-wrap > .part-name ::text').getall()
        for section in sections:
            if section.rfind("nutrition-container") != -1:
                sections.remove(section)

        # checks that there are equal number of headers and content sections
        if len(sections) != len(sectionHeaders):
            sectionHeaders.insert(0, 'main')

        for i in range(len(sections)):
            soup = BeautifulSoup(sections[i], 'html.parser')
            listItems = soup.find_all('li')
            ingContainer = []
            for item in listItems:
                entry = {}
                quantity =  "" if item.find("span", class_="quantity") is None else stringCleanup(item.find("span", class_="quantity").get_text())
                ingredient = item.find("span", class_="ingredient-name")
                if ingredient is None:
                    print(response.url)
                    raise ValueError("Ingredient was none in getRecipeParts")
                else:
                    ingredient = stringCleanup(item.find("span", class_="ingredient-name").get_text())
                entry['display'] = quantity + " " + ingredient
                ingContainer.append(entry)
            parts[sectionHeaders[i]] = ingContainer
        return parts

def stringCleanup(s: str):
    if s is None:
        return ""
    else:
        return s.strip('\n').strip('"').strip()

