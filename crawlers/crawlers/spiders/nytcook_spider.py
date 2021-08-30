import datetime
from re import search
import sys, os
import urllib
import scrapy
import csv

from datetime import date
from pathlib import Path
from bs4 import BeautifulSoup
from urllib import request
from urllib.error import URLError

# scrapy imports 
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError
from scrapy import http
from scrapy.http import Response
from scrapy.extensions import closespider
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.trackref import NoneType
from crawlers.items import Recipe
from utils import get_image_urls

class TimesSpider(scrapy.Spider):

    name = "times"

    path = Path(__file__)
    IMAGES_DIR_PATH = str(path.parents[2]) + "/data/images"
    DATA_DIR_PATH = str(path.parents[2]) + "/data/"

    #DEBUGGING
    '''def start_requests(self):
        self.__process_filter_keys()
        yield scrapy.Request(url="https://cooking.nytimes.com/search?q=&page=1",callback=self.parse_search)'''

    def start_requests(self):
        """
        This method gathers all the individual recipe urls for each search page and passes them to the prase method
        """
        #self.__process_filter_keys()
        valid_search_page_urls = self.__get_search_page_urls()
        
        for url in valid_search_page_urls:
            yield scrapy.Request(url=url, callback=self.parse_search)

    def __process_filter_keys(self):
        """
        This method writes to: 
            ../../data/cat_filters.csv and url_filters.csv table entries for the filter-category, filter 1-to-many relationships with duplicate filter-category entries

            ../../data/url_filters.csv entries for shortened-url , filter 1-to-many relationships with duplicate shortened-url entries

        """
        cat_record_count = 0
        url_record_count = 0 

        category_filter_dict = self.__get_recipe_filters() 

        cat_filters_csvfile = open(TimesSpider.DATA_DIR_PATH + "cat_filters.csv", "w+")
        url_filters_csvfile = open(TimesSpider.DATA_DIR_PATH + "url_filters.csv", "w+")

        cat_csvwriter = csv.writer(cat_filters_csvfile)
        url_csvwriter = csv.writer(url_filters_csvfile)

        # headers for csv files 
        cat_headers = ["category", "filter"]
        url_headers = ["url", "filter"]

        cat_csvwriter.writerow(cat_headers)
        url_csvwriter.writerow(url_headers)
        
        for filter_category, filter_list in category_filter_dict.items():
            for filter in filter_list:
                cat_csvwriter.writerow([filter_category, filter])
                cat_record_count += 1
                cat_filters_csvfile.flush() 

                filter_no_space = filter.replace(" ", "+")
                page_num = 1 
                end_loop_counter = 0

                while True:

                    url = "https://cooking.nytimes.com/search?filters%5B{}%5D%5B%5D={}&q=&page={}".format(filter_category, filter.replace(" ", "+"), page_num)

                    try:
                        response = request.urlopen(url=url)
                    except URLError as e:
                        if end_loop_counter >= 3:
                            print("The last url for the filter page was: " + url)
                            print("Error code was: " + e)
                            break
                        else:
                            end_loop_counter += 1 
                            page_num += 1
                    else:
                        print("Successfully reached url: {}. Now parsing the recipe urls to each filter category".format(url))

                        soup = BeautifulSoup(response, "html.parser")
                        
                        ### DEBUGGING
                        val = soup.find("div", id="pagination-count")
                        if type(val) is NoneType:
                            pass
                        else:
                            results_count = soup.find("div", id="pagination-count").find_next("b").string.replace("\n", "").strip().replace(" ", "")
                            print("Search Result Count: " + str(results_count))
                        #############

                        cards = soup.find_all("a", class_=["card-link","card-recipe-info"])
                        if len(cards) == 0:
                            break
                        for card in cards:
                            if 'image-anchor' in card["class"] and "card_recipe_info" not in card["class"]:
                                query_url = str(card["href"])
                                idx = query_url.find("?action")
                                href = query_url[idx:] if idx != -1 else query_url
                                url_csvwriter.writerow([href, filter])
                                url_record_count += 1
                                url_filters_csvfile.flush()
                        end_loop_counter = 0
                        page_num += 1
        print("Completed writing the csv data files")
        print("Successfully wrote {} records to url_filters.csv and {} records to cat_filters.csv".format(url_record_count, cat_record_count))
        cat_filters_csvfile.close()
        url_filters_csvfile.close()


    def parse_search(self, response):
        """
        This method serves as the callback for start_requests. This parses the response data of the search page urls. Given the response from the search page, it will find all urls that lead to either recipe cards, or recipe-collection cards.

        If the url is a recipe card, it will be yielded as a request to self.parse with no metadata for the collection name
        If the url is a recipe-collection card, the recipe card urls are further extracted from the page and yielded to the parse method with the collection name in the metadata 
        """
        urls_on_search_page = list(response.css("article.card a.card-link:not(.card-recipe-info)::attr(href)").getall())
        for url in urls_on_search_page:
            full_url = "https://cooking.nytimes.com{}".format(url)

            if url.startswith("/recipes"): # if the url is for a recipe
                yield scrapy.Request(url=full_url, callback=self.parse, errback=self.errback_httpbin, encoding='utf-8')

            elif url[1].isdigit():  # if the url is for a recipe collection
                collection_dict = self.get_urls_from_collection(full_url)
                for k,v in collection_dict.items(): # k is the collection name, v is list of shortened urls for recipes 
                    for url in v: 
                        url_to_recipe = "https://cooking.nytimes.com{}".format(url)
                        yield scrapy.Request(url=url_to_recipe, callback=self.parse, errback= self.errback_httpbin, encoding="utf-8", meta={"collection": k})

            else: # Not sure when this would be the case 
                pass

    
    def parse(self, response: http.TextResponse):
        """
        This method handles parsing all recipe page information and instantiates a new Recipe item with attributes fielded from page. The item is used and passed through the pipelines 
        """
        print('Parsing page: ' + response.url)
        image_urls = []
        try:
            imageURL = response.css('.recipe-intro>.media-container img').attrib['src']
        except KeyError:
            title_for_query = stringCleanup(response.css('h1.recipe-title::text').get())
            image_urls = get_image_urls(title_for_query, 1)
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
            collection_name = response.meta.get("collection") 
           
            recipe = Recipe(title=title, author=author, url=url, yields=yields, time=time, intro=intro, tags=tags, steps=steps, ingredients=ingredients, image_urls=image_urls, collection_name=collection_name)
        
            yield recipe

        except Exception as err:
        
            print('An error occured')
            raise closespider("Ran into an exception: " + err)


    def errback_httpbin(self, failure):
        # log all errback failures,
        # in case you want to do something special for some errors,
        # you may need the failure's type

        self.logger.error(repr(failure))

        #if isinstance(failure.value, HttpError):
        if failure.check(HttpError):
            # you can get the response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        #elif isinstance(failure.value, DNSLookupError):
        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        #elif isinstance(failure.value, TimeoutError):
        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)


    def __get_search_page_urls(self):
        """
        This method checks each increment of 1 @ https://cooking.nytimes.com/search?q=&page= and returns a list containing the urls as strings that are valid and able to be parsed further for recipe urls 
        """

        urls = [] 

        skipped_urls = []

        search_page_number = 1

        end_loop_counter = 0 #stores the number of times the request url fails to return a valid page. Once it has reached 3, the loop will end 

        while True:
            page_url = "https://cooking.nytimes.com/search?q=&page={}".format(search_page_number)
            try:
                response = request.urlopen(url=page_url)
            except URLError:
                skipped_urls.append(page_url)
                if end_loop_counter >= 3:
                    print("The last valid url page was " + page_url)
                    break
                else:
                    end_loop_counter += 1 
                    search_page_number += 1
            else:
                print("Successfully reached url: {}".format(page_url))
                end_loop_counter = 0 
                search_page_number += 1
                urls.append(page_url)

        print("The skipped urls are: ")
        print(*skipped_urls, sep=", ") # prints all the page numbers that were skipped for debugging 
        return urls 


    def get_urls_from_collection(self, collection_url:str):
        """
        This method returns a dictionary with the key as the collection name, and the value as a list of urls scraped from the collection page 
        @params: 
        collection_url: the full url to request 
        @returns:
        {SomeCollectionName: list(hrefs)}
        """
        collection_dict = {}
        hrefs = []
        try:
            response = request.urlopen(url=collection_url)
        except URLError as e:
            print("Not a valid url for get_urls_from_collection. Exception: " + str(e))
            return
        else:
            soup = BeautifulSoup(response, "html.parser")
            cards = soup.find_all("a", class_="card-link")
            collection_name = stringCleanup(soup.find("h1", attrs={"class":"name"}).string)
            for card in cards:
                if 'image-anchor' in card["class"] and "card_recipe_info" not in card["class"]:
                    hrefs.append(card["href"])
            collection_dict[collection_name] = hrefs
        return collection_dict


    def __get_recipe_filters(self) -> dict():
        """
        This method returns a dictionary where the key is the tag.key attribute and the value is a list containing the term attribute for each term that corresponds to the key
        <br>
        Example below:
        <div class="checkbox" key="special_diets" term="low calorie">
        <div class="checkbox" key="special_diets" term="low cholesterol">
        <div class="checkbox" key="special_diets" term="low sugar">
        <div class="checkbox" key="special_diets" term="low-carb">
        <div class="checkbox" key="cuisines" term="african">
        <div class="checkbox" key="cuisines" term="american">   
        {
            "special_diets": ["low calorie", "low cholestrol", "low sugar", "low-carb], 
            "cuisines": ["african", "american"]
        }
        """

        category_filter_dict = {}
        url = "https://cooking.nytimes.com/search?q=&page=1"
        response = request.urlopen(url)
        soup = BeautifulSoup(response, "html.parser")
        filter_tags = soup.find_all("div", class_="checkbox")
        for tag in filter_tags:
            filter_key = tag["key"]
            filter = tag["term"]
            if category_filter_dict.get(filter_key) is None: # if the key does not exist already 
                filter_list = [filter]
                category_filter_dict[filter_key] = filter_list
            else: # if the key does already exist and a list will already be there 
                current_list = list(category_filter_dict.get(filter_key))
                current_list.append(filter)
                category_filter_dict[filter_key] = current_list
        return category_filter_dict


    @classmethod
    def getRecipeParts(self, response):
        """
        This method returns a dictionary with the recipe parts as keys (some recipes break their ingredients into parts, "for the salad", "for the dressing", "for the croutons") and values as a list of dictionaries with "display" as keys and the ingredient phrase as values

        Data structure as shown below:
        {
            main : [
                {"display": SOME_INGREDIENT_PHRASE (i.e. 4 tablespoons olive oil)},
                {"display": ANOTHER_PHRASE},
                ...
            ],
            ANOTHER_PART_NAME: [
                {"display": SOME_INGREDIENT_PHRASE (i.e. 4 tablespoons olive oil)},
                ...
                
            ]
        }

        """
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

