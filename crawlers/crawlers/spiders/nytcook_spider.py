import datetime
from logging import root
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
from scrapy.exceptions import CloseSpider
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.trackref import NoneType
from crawlers.items import Recipe
from utils import get_image_urls

#TODO
""""
for some reason, the url /recipes/1022494-banana-cream-pie is not accepting the filters 
"""

def is_card_without_duplicate(tag: Tag):
    return (
        tag.name == "a"
        and tag.has_attr("class")
        and "card-link" in tag["class"]
        and "image-anchor" in tag["class"]
        and "card_recipe_info" not in tag["class"]
    )


def stringCleanup(s: str):
    return (
        s.strip("\n").strip('"').strip()
        if s is not None
        else ""
    )


class TimesSpider(scrapy.Spider):

    name = "times"

    def start_requests(self):
        self.start_url = "https://cooking.nytimes.com/search"
        self.recipes = {}
        """
            self.recipes format:
            {
                shorthandURL#1: {
                    "url": 3w4t,
                    "filters": [], 
                    "collections": []
                }
                shorthandURL#2: {...}
                shorthandURL#3: {...}
            }
        """
        self.initialize_recipe_dict()
        for url, recipe in self.recipes.items():
            full_url = "https://cooking.nytimes.com{}".format(url)
            yield scrapy.Request(
                full_url,
                callback=self.parse,
                errback=self.errback_httpbin,
                meta={"recipe": recipe}
            )

    def initialize_recipe_dict(self):
        """
        Wrapper method that fills the recipes dictionary attribute via the "search page method" and the "filter method"
        """

        """ 
        SEARCH PAGE METHOD:
        Gets all valid pages from the blank query search results page and
        parses them to get their containing recipe urls
        then adds the recipes attribute
        """
        # DEBUGGING. WHEN DONE UNCOMMENT THIS
        #replace_at = "GRASS"
        #root_url = "https://cooking.nytimes.com/search?q=&page={}".format(replace_at)
        #valid_search_page_urls = self.__url_paginating_from_root(root_url, replace_at)
        
        valid_search_page_urls = ["https://cooking.nytimes.com/search?q=&page=1"] # delete this when done debugging 
        # END DEBUGGING

        for url in valid_search_page_urls:
            # TODO error handling
            response = request.urlopen(url)

            soup = BeautifulSoup(response, "html.parser")

            # urls are in shorthand
            urls_on_page = set([
                a['href'] for a
                in soup.find_all("a", class_=["card-link", "card-recipe-info"])
            ])
            urls_on_page = list(urls_on_page)

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
                    full_url = "https://cooking.nytimes.com{}".format(url_on_page)
                    print(
                        "WARNING: In __initialize_recipe_dict"
                        "The given url ({}) did not qualify as a recipe or collection url. Investigate further"
                        .format(full_url)
                    )

        """
        Filter Method:
        Similar to the filter method.
        Applies each combination of filters on the results.
        Parses the results page for recipes.
        """
        filters_combinations = self.__get_filter_combinations(self.start_url)
        url_filter_dict = self.__get_recipe_urls_by_filter(filters_combinations)

        for url, filter_list in url_filter_dict.items():
            if self.recipes.get(url) is None:
                new_recipe = {}
                new_recipe["url"] = url
                new_recipe["filters"] = filter_list
                self.recipes[url] = new_recipe
            else:
                existing = self.recipes.get(url)
                if existing.get("filters") is None:
                    existing["filters"] = filter_list
                else:
                    existing_filters = list(existing["filters"])
                    existing["filters"] = zip(existing_filters, filter_list)
                self.recipes[url] = existing


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
            try:
                filters = list(recipe_info_dict.get("filters"))
            except ValueError:
                filters = []

            try:
                collections = list(recipe_info_dict.get("collections"))
            except ValueError:
                collections = []

            recipe["url"] = recipe_info_dict.get("url")
            recipe["filters"] = filters
            recipe["collections"] = collections
            recipe["image_urls"] = image_urls
            recipe["title"] = stringCleanup(
                response.css('h1.recipe-title::text').get()
            )

            recipe["author"] = stringCleanup(
                response.css(".nytc---recipebyline---bylinePart > a::text").get()
            )

            recipe["yields"] = stringCleanup(
                response.css(".recipe-yield-container > .recipe-yield-value::text")
                .get()
            )

            recipe["time"] = stringCleanup(
                response.css(".recipe-time-yield li:nth-child(2) > .recipe-yield-value::text")
                .get()
            )

            recipe["intro"] = stringCleanup(
                response.css('.recipe-topnote-metadata .topnote p ::text')
                .get()
            )

            # note that this is a list
            recipe["tags"] = [
                stringCleanup(tag)
                for tag
                in response.css('.tags-nutrition-container > .tag::text')
                .getall()
            ]

            # note that this is a list
            recipe["steps"] = [
                stringCleanup(item)
                .replace('<li>', '')
                .replace('</li>', '')
                for item in response.css('.recipe-steps > li').getall()
            ]

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

        # dictionary to return
        temp = {}

        try:
            response = request.urlopen(start_url)
        except Exception:
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
            # if the filter category does not already exist
            # a list of filters will be there as a value
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
        
        sections = response.css(
            '.recipe-ingredients-wrap > .recipe-ingredients'
        ).getall()

        sectionHeaders = response.css(
            '.recipe-ingredients-wrap > .part-name ::text'
        ).getall()

        for section in sections:
            if section.rfind("nutrition-container") != -1:
                sections.remove(section)

        # if there are unequal number of sections and headers
        # creates a "main" header and assigns to the first section
        if len(sections) != len(sectionHeaders):
            sectionHeaders.insert(0, "main")

        # iterates over each section
        for i in range(len(sections)):
            soup = BeautifulSoup(sections[i], 'html.parser')
            list_items = soup.find_all('li')
            ing_container = []
            for item in list_items:
                entry = {}
                # parse the quantity for the ingredient
                quantity = item.find("span", class_="quantity")
                if quantity is None:
                    quantity = ""
                else:
                    quantity = stringCleanup(quantity.get_text())

                # parses the ingredient phrase
                ingredient = item.find("span", class_="ingredient-name")
                if ingredient is None:
                    print(
                        "There was no ingredient in section: {}"
                        .format(section[i])
                        + "\n"
                        + response.url
                    )
                    raise ValueError("Ingredient was none in getRecipeParts")
                else:
                    ingredient = stringCleanup(ingredient.get_text())
                entry['display'] = quantity + " " + ingredient
                ing_container.append(entry)
            parts[sectionHeaders[i]] = ing_container
        return parts

    def __get_recipe_urls_by_filter(self, category_filter_dict: dict):
        """
        This method takes in the argument category_filter_dict. The example of the format is below.
            {
                "special_diets": ["low calorie", "low cholestrol", "low sugar", "low-carb], 
                "cuisines": ["african", "american"], 
                ...
            }
        It uses each combination of filter category and filter to find the filter results page urls. With each results page url, it will find the recipes on the page and match it to the filter it applies to. The return value is a dictionary with the keys being the recipe urls and the values being the list of filters that apply to it.
        Example of the return value:
            {
                SOME_RECIPE_URL: ["african", "low cholestrol", "low sugar"],
                ANOTHER_URL: ["dessert", "dairy-free"]
            }
        """

        print("In method: get_recipe_urls_by_filter")
        
        # This is the dictionary to be returned
        recipes = {}

        # Iterates over each category and filter in dictionary
        # For example: "special_diets", ["low calorie", "low cholestrol", "low sugar", "low-carb]
        for filter_category, filter_list in category_filter_dict.items():
            
            #  "low calorie" in ["low calorie", "low cholestrol", "low sugar", "low-carb]
            for filter in filter_list:

                print(
                    "Filter category: " + filter_category + "\n"
                    "Filter: " + filter
                )

                replace_at = "GRASS"

                url = "https://cooking.nytimes.com/search?filters%5B{}%5D%5B%5D={}&q=&page={}".format(
                    filter_category.replace(" ", "_"),
                    filter.replace(" ", "%20"),
                    replace_at
                )

                search_pagination_urls_list = self.__url_paginating_from_root(url, replace_at)

                for url in search_pagination_urls_list:
                    response = request.urlopen(url)
                    soup = BeautifulSoup(response, "html.parser")
                    cards = soup.find_all(is_card_without_duplicate)
                   # if len(cards) == 0:
                    #    break
                    for card in cards:
                        href = str(card["href"])
                        parsed_url = (
                            href if href.find("?action") == -1
                            else href[href.find("?action"):]
                        )

                        # if the url doesnt exist in data structure to return
                        if recipes.get(parsed_url) is None:
                            # start a list with the filter and
                            # add the url as a key to the recipe dictionary
                            recipes[parsed_url] = [filter]
                        # if url does exist in data structure to return
                        else:
                            current_filters = list(recipes.get(parsed_url))
                            current_filters.append(filter)
                            recipes[parsed_url] = current_filters
                        
            # debugging
            #filter_list = ", ".join(recipes.get("/recipes/1022494-banana-cream-pie"))
           # print("This is the filters for url /recipes/1022494-banana-cream-pie:".format(filter_list))
            print("Total URL count: " + str(len(recipes.keys())))
            return recipes
                   
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

    def __url_paginating_from_root(self, root_url: str, index_str: str) -> list:
        """
        Given the base_url (for example "https://cooking.nytimes.com/search?q=&page=SOM")
        this method will return a list containing the paginated urls that stem from the base_url
        by incrementing the page count until recipes are no longer showing up in the html page.

        It will find the index_str within the root_url to index where in root_url the substitution should occur
    
        Usage: 
            - self.__url_paginating_from_root("https://cooking.nytimes.com/search?q=&page=INDEXSTRING", "INDEXSTRING")
        Arguments:
            - root_url: a string of the full url to paginate from
                - **IMPORTANT: this argument must contain the index_str at the place where the substitution of page number will take place 
                - #**IMPORTANT: the index_str
            - index_str: the string within the root_url where the format substitution will be taking place 
            - replace_with: a list of tuple containing the values that wil be replacing the index_str in root_url
                - TUPLE FORMAT: 
                - IMPORTANT if the value in the tuple is of type(int), then it is assumed that it will be incremented 
        Returns:
            - a list object containing string urls that are able to be parsed further =
        """
    
        count = root_url.count(index_str)
        if count != 1:
            print(
                "The count of placeholder substrings did not match "
                "the number of strings to replace with"
            )
            raise CloseSpider("Spider closed")    

        # list of valid urls to return 
        valid_urls = []

        # keeps record of the urls inm between valid urls that are skipped
        # used for debugging purposes only
        skipped_urls = []

        page_number = 1

        end_loop_counter = 0

        while True:
            # DEBUGGING
            if page_number == 4: # DEBUGGIN
                break
            page_url = root_url.replace(index_str, str(page_number))
            try:
                response = request.urlopen(url=page_url)
                
            except URLError:
                skipped_urls.append(page_url)
                if end_loop_counter >= 3:
                    print("The last valid url page was " + page_url)
                    break
                else:
                    end_loop_counter += 1
                    page_number += 1
            soup = BeautifulSoup(response, "html.parser")
            # ends the loop if a page doesn't have any recipe cards on it 
            if len(soup.find_all(is_card_without_duplicate)) == 0:
                break
            print("Successfully reached url: {}".format(page_url))
            end_loop_counter = 0
            page_number += 1
            valid_urls.append(page_url)
        print(
            "The skipped urls are: ",
            *skipped_urls,
            sep=", "
        )
        return valid_urls








