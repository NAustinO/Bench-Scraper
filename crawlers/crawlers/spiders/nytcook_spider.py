import datetime
from re import search
import sys, os
import urllib
from bs4.element import Tag
import scrapy
import csv

from datetime import date
from pathlib import Path
from bs4 import BeautifulSoup
from urllib import request
from urllib.error import URLError
from collections import defaultdict

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

#TODO 
""""
for some reason, the url /recipes/1022494-banana-cream-pie is not accepting the filters 
"""

def is_card_without_duplicate(tag: Tag):
    return tag.name == "a" and tag.has_attr("class") and "card-link" in tag["class"] and "image-anchor" in tag["class"] and "card_recipe_info" not in tag["class"]

def stringCleanup(s: str):
    if s is None:
        return ""
    else:
        return s.strip('\n').strip('"').strip()


class TimesSpider(scrapy.Spider):
    """
    
    """
    name = "times"


    def start_requests(self):
        self.start_url = "https://cooking.nytimes.com/search"
        self.recipes = {}
        """
            self.recipes format: 
            {
                url#1: {
                    "url": 3w4t,
                    "filters": [], 
                    "collections": []
                }
                url#2: {}
                url#3: {}
            }
        """

        self.initialize_recipe_dict()
        
        for url, recipe in self.recipes.items():
            full_url = "https://cooking.nytimes.com{}".format(url)
            yield scrapy.Request(full_url, callback=self.parse, errback=self.errback_httpbin, meta={"recipe": recipe})


    def initialize_recipe_dict(self):
        """
        Wrapper method that fills the recipes dictionary attribute via the "search page method" and the "filter method"
        """
        """ 
        SEARCH PAGE METHOD:
        Gets all valid pages from the blank query search results page and parses them to get their containing recipe urls. Adds the recipes attribute 
        """
        # DEBUGGING. WHEN DONE UNCOMMENT THIS
        #valid_search_page_urls = self.__get_search_page_urls()
        
        valid_search_page_urls = ["https://cooking.nytimes.com/search?q=&page=1"] # delete this when done debugging 

        # END DEBUGGING
        for url in valid_search_page_urls:
            response = request.urlopen(url) # TODO error handling

            soup = BeautifulSoup(response, "html.parser")

            urls_on_page = list(set([a['href'] for a in soup.find_all("a", class_=["card-link","card-recipe-info"])])) #shorthand url 

            for url_on_page in urls_on_page:

                # if the url found on the search page is a recipe and does not already exist in recipes, add it
                if url_on_page.startswith("/recipes"):
                    if self.recipes.get(url_on_page) is None:
                        value = {}
                        value["url"] = url_on_page
                        self.recipes[url_on_page] = value 
                
                # if the url found on the search page is a collection url, go to the page and add its recipe urls if they don't exist. Also adding to the collections list attribute in Recipe item
                elif url_on_page[2].isdigit():
                    full_url = "https://cooking.nytimes.com{}".format(url_on_page)
                    self.__get_urls_from_collection_page(full_url)
                    
                #  This should not happen 
                else:
                    print("WARNING: In __initialize_recipe_dict. the given url ({}) did not qualify as a recipe or collection url. Investigate further".format("https://cooking.nytimes.com{}".format(url_on_page)))
        """
        Filter Method: 
        Similar to the filter method. Applies each combination of filters on the results and parses the results page for recipes.  
        """
        url_filter_dict = self.__get_recipe_urls_by_filter(self.__get_filter_combinations(self.start_url))
        
        for url, filter_list in url_filter_dict.items():
            if self.recipes.get(url) is None:
                new_recipe = {}
                new_recipe["url"] = url
                new_recipe["filters"] = filter_list
                self.recipes[url] = new_recipe
            else:
                self.recipes[url] = self.recipes.get(url).get("filters", []) + filter_list if filter_list is not None else self.recipes.get(url).get("filters") #TODO MAKE SURE TIS WORKS

        
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
    

    def parse(self, response: http.TextResponse):
        """
        
        """
        print("Now parsing page: " + response.url)

        """
        This part sets up the image scraper. If the recipe webpage has an image, it will use that as the image_urls image, otherwise it will create a query from the recipe title and use selenium to google one"""
        recipe = Recipe()
        recipe_info_dict = response.meta.get("recipe")

        if recipe is None:
            print("Recipe was none in parse. Check why")

        image_urls = []
        try:
            imageURL = response.css('.recipe-intro>.media-container img').attrib['src']
        except KeyError:
            title_for_query = stringCleanup(response.css('h1.recipe-title::text').get())
            image_urls = get_image_urls(title_for_query, 1)
        else:
            image_urls.append(imageURL)
        
        try:
            recipe["url"] = recipe_info_dict.get("url")
            recipe["filters"] = recipe_info_dict.get("filters")
            recipe["collections"] = recipe_info_dict.get("collections")
            recipe["image_urls"] = image_urls
            recipe["title"] = stringCleanup(response.css('h1.recipe-title::text').get())
            recipe["author"] = stringCleanup(response.css('.nytc---recipebyline---bylinePart > a::text').get())
            recipe["yields"] = stringCleanup(response.css('.recipe-yield-container > .recipe-yield-value::text').get())
            recipe["time"] = stringCleanup(response.css('.recipe-time-yield li:nth-child(2) > .recipe-yield-value ::text').get())
            recipe["intro"] = stringCleanup(response.css('.recipe-topnote-metadata .topnote p ::text').get())
            recipe["tags"] = [stringCleanup(tag) for tag in response.css('.tags-nutrition-container > .tag ::text').getall()]
            recipe["steps"] = [stringCleanup(item).replace('<li>', '').replace('</li>', '') for item in response.css('.recipe-steps > li').getall()]
            recipe["ingredients"] = self.__parse_recipe_ingredients(response)
            recipe["full_url"] = response.url
        except Exception as e:
            print("An error occurred in parse")
            raise closespider("Ran into an exception: " + e)
        else:
            yield recipe 


    def __get_filter_combinations(self, start_url: str):
        """
            @Args:
                - start_url: the url for the search page of the new york times cooking

            This method returns a dictionary where the key is the tag.key attribute and the value is a list containing the term attribute for each term that corresponds to the key
            <br>
            Example below:
            <div class="checkbox" key="special_diets" term="low calorie">
            <div class="checkbox" key="special_diets" term="low cholesterol">
            <div class="checkbox" key="special_diets" term="low sugar">
            <div class="checkbox" key="special_diets" term="low-carb">
            <div class="checkbox" key="cuisines" term="african">
            <div class="checkbox" key="cuisines" term="american">   
            
            @Returns a dictionary where the filter categories are the keys, and the values are a list of different filters applicable to the category. Example below
            {
                "special_diets": ["low calorie", "low cholestrol", "low sugar", "low-carb], 
                "cuisines": ["african", "american"]
            }
        """
        print("in method get_filter_combinations")

        temp = {}
        try:
            response = request.urlopen(start_url)
        except:
            print("__get_filter_combinations failed to successfully reach a response from {}".format(start_url))
            scrapy.Spider.close("Closing spider")
        
        soup = BeautifulSoup(response, "html.parser")
        filter_tags = soup.find_all("div", class_="checkbox")
        for tag in filter_tags:
            filter_category = tag["key"] # will be used as the key for the dict 
            filter = tag["term"]

            # if the key does not exist already
            if temp.get(filter_category) is None:
                filter_list = [filter]
                temp[filter_category] = filter_list

            # if the filter category does not already exist, a list of filters will be there as a value
            else: 
                current_filters_list = list(temp.get(filter_category))
                current_filters_list.append(filter)
                temp[filter_category] = current_filters_list
        
        return temp


    def __parse_recipe_ingredients(self, response) -> dict: 
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


    def __get_recipe_urls_by_filter(self, category_filter_dict: dict):

        """
        This method takes in the argument category_filter_dict. The example of the format is below.
            {
                "special_diets": ["low calorie", "low cholestrol", "low sugar", "low-carb], 
                "cuisines": ["african", "american"], 
                ...
            }
        It uses each combination of filter category and filter to find the filter results page urls. With each results page url, it will find the recipes on the page and match it to the filter it applies to. The return value is a dictionary with the keys being the recipe urls and the values being the list of filters that apply to it. Example below: 
            {
                SOME_RECIPE_URL: ["african", "low cholestrol", "low sugar"]
            }
        
        """
        print("In method: get_recipe_urls_by_filter")
        recipes = {}

        #   "special_diets", ["low calorie", "low cholestrol", "low sugar", "low-carb] 
        for filter_category, filter_list in category_filter_dict.items(): 

            #  "low calorie" in ["low calorie", "low cholestrol", "low sugar", "low-carb] 
            for filter in filter_list:

                page_num = 1 
                end_loop_counter = 0 # maintains the number of times a response successfully tries to open a page. The while loop will end once a certain count is reached 

                while True:
               
                    url = "https://cooking.nytimes.com/search?filters%5B{}%5D%5B%5D={}&q=&page={}".format(filter_category.replace(" ", "_"), filter.replace(" ", "%20"), page_num)
                    
                    #url = "https://cooking.nytimes.com/search?filters%5Bspecial_diets%5D%5B%5D=vegetarian&q=&page=85"
                    try:
                        response = request.urlopen(url)
                    except URLError as e:
                        if end_loop_counter >= 3:
                            print("The last url for the filter page was: " + url)
                            break
                        else:
                            end_loop_counter += 1 
                            page_num += 1
                    print("Successfully reached filter url: {}. Now scraping the recipe urls for each filter category".format(url))

                    soup = BeautifulSoup(response, "html.parser")

                    #cards = soup.find_all("a", class_=["card-link","card-recipe-info"]) # cards are the html containers for the recipes
                    #TODO MAKE this into a function seletor instead
                    cards = soup.find_all(is_card_without_duplicate)

                    if len(cards) == 0:
                        break
                    for card in cards:
                        # example of raw_url: https://cooking.nytimes.com/recipes/1022347-butter-mochi?action=click&module=Global%20Search%20Recipe%20Card&pgType=search&rank=1
                        raw_url = str(card["href"]) 


                        index_to_replace = raw_url.find("?action")
                        parsed_url = raw_url[index_to_replace:] if index_to_replace != -1 else raw_url

                        # if the url doesnt exist
                        if recipes.get(parsed_url) is None:

                            # start a list with the filter and add the url as a key to the recipe dictionary
                            recipes[parsed_url] = [filter]

                        # if url does exist
                        else:

                            current_filters = list(recipes.get(parsed_url))
                            current_filters.append(filter)
                            recipes[parsed_url] = current_filters

                    end_loop_counter = 0
                    page_num += 1
                    break # DELETE THIS AFTER DEBUGGING 

            # debugging
        
            filter_list = ", ".join(recipes.get("/recipes/1022494-banana-cream-pie"))
            print("This is the filters for url /recipes/1022494-banana-cream-pie:".format(filter_list))
            print("Total URL count: " + str(len(recipes.keys())))
            return recipes 


    def __get_search_page_urls(self):
        """
        This method checks each increment of 1 @ https://cooking.nytimes.com/search?q=&page=NUMBERHERE and returns a list containing the urls as strings that are valid and able to be parsed further for recipe urls 
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
                if end_loop_counter >= 5:
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
    
                   
    def __get_urls_from_collection_page(self, collection_page_url):
        """
        This method takes in a url for a collection webpage (complete url) and parses the recipe urls from the page. It modifies the self.recipe attribute by adding a url, Recipe(url) as key value pairs if it does not eixst, otherwise adding to the current Recipe item by adding to its collections attribute
        """
        try:
            response = request.urlopen(collection_page_url)
        except URLError as e:
            print("Not a valid url for get_urls_from_collection. Exception: " + str(e))
            return
        soup = BeautifulSoup(response, "html.parser")
        cards = soup.find_all(is_card_without_duplicate) #TODO MAKE this into a function seletor instead
        collection_name = stringCleanup(soup.find("h1", attrs={"class":"name"}).string)
        for card in cards:    

            href = card["href"]

            # if recipes does not contain url, create a new recipe item and add it to the recipe collection
            if self.recipes.get(href) is None:
                new_recipe = {}
                new_recipe["url"] = href 
                new_recipe["collections"] = [collection_name]
                self.recipes[href] = new_recipe
            
            else:
                existing_recipe = dict(self.recipes.get(href))
                # adds to the collection list if it exists otherwise creates a new one
                existing_recipe["collections"] = existing_recipe.get("collections", []) + [collection_name]
                self.recipes[href] = existing_recipe



