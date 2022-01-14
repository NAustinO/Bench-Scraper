import sys, scrapy
from pathlib import Path
from bs4 import BeautifulSoup
from urllib import request
from urllib.error import URLError
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError
from scrapy import http
from scrapy.extensions import closespider
from scrapy.exceptions import CloseSpider
from crawlers.items import Recipe
path = Path(__file__)
sys.path.append(path.parents[2])


from ..utils.nyt.utils import (
    stringCleanup,
    query_for_image
) 

from ..utils.nyt.parse_helpers import (
    parse_recipe_ingredients,
    paginate_urls_from_root,
    get_filter_combinations
)
from ..utils.nyt.selectors import is_card_without_duplicate


class TimesSpider(scrapy.Spider):

    name = "times"

<<<<<<< HEAD
    path = Path(__file__)
    IMAGES_DIR_PATH = str(path.parents[2]) + "/data/images"

=======
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
                },
                shorthandURL#2: {...},
                shorthandURL#3: {...}
                }
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
        Wrapper method that fills the recipes dictionary attribute via the 
        "search page method" and the "filter method"
        """
        print("Initializing the recipes data structure\n")

        # SEARCH PAGE METHOD:
        # Gets all valid pages from the blank query search results page and
        # parses them to get their containing recipe urls
        # then adds to the recipes attribute data structure

        replace_at = "GRASS"
        root_url = "https://cooking.nytimes.com/search?q=&page={}".format(replace_at)
        valid_search_page_urls = paginate_urls_from_root(root_url, replace_at, page="search")
        
        for url in valid_search_page_urls:
            print("Searching page: " + str(url))
            response = request.urlopen(url)
            soup = BeautifulSoup(response, "html.parser")
            # urls are in shorthand
            urls_on_page = set([
                a['href'] for a
                in soup.find_all("a", class_=["card-link", "card-recipe-info"])
            ])

            # urls_on_page = ["/recipes/1019708-cauliflower-gratin-with-leeks-and-white-cheddar", ...]
            urls_on_page = list(urls_on_page)
            for url_on_page in urls_on_page:
                # if the url found on the search page is a recipe
                # and does not already exist in recipes data structure
                # adds the url as a key with a value as an empty dict object
                if url_on_page.startswith("/recipes"):
                    if self.recipes.get(url_on_page) is None:
                        entry = {}
                        entry["url"] = url_on_page
                        self.recipes[url_on_page] = entry
        
                # if the url found on the search page is a collection url,
                # go to the page and add the recipe urls if they don't exist in recipes data structure.
                # Also adding to the collections list attribute for each dict object
                elif url_on_page[2].isdigit():
                    full_url = "https://cooking.nytimes.com{}".format(url_on_page)
                    self.__get_urls_from_collection_page(full_url)
                
                # start corner cases 
                elif url_on_page.startswith("/thanksgiving"):
                    full_url = "https://cooking.nytimes.com{}".format(url_on_page)
                    self.__get_urls_from_collection_page(full_url)
                elif url_on_page.startswith("/guides"):
                    pass
        
                #  This should not happen
                else:
                    full_url = "https://cooking.nytimes.com{}".format(url_on_page)
                    print(
                        "WARNING: In __initialize_recipe_dict .\n"
                        "The given url ({}) did not qualify as a recipe or collection url. Investigate further"
                        .format(full_url)
                    )

        # FILTER METHOD:
        # Similar to the Search Page Method
        # Applies each combination of filters on the results.
        # Parses the results page for recipes.

        filters_combinations = get_filter_combinations(self.start_url)

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
>>>>>>> reimplement_crawler

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
        This method is responsible for parsing each recipe page and filling the Recipe object fields from the html.
        """
        print("Now parsing page: " + response.url)

        recipe = Recipe()
        recipe_info_dict = response.meta.get("recipe")

<<<<<<< HEAD
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
=======
        recipe["url"] = recipe_info_dict.get("url")
>>>>>>> reimplement_crawler

        # image scraping (from page or Google if not available)
        try:
            image_urls = []
            imageURL = response.css('.recipe-intro>.media-container img').attrib['src']
            image_urls.append(imageURL)
        except KeyError:
            try:
                query = stringCleanup(response.css('h1.recipe-title::text').get())
                image_urls = query_for_image(query)
            except Exception:
                image_urls = []
        finally:
            recipe["image_urls"] = image_urls

        # filters
        try:
            recipe["filters"] = list(recipe_info_dict.get("filters"))
        except Exception:
            recipe["filters"] = []

        # categories
        try:
            recipe["collections"] = list(recipe_info_dict.get("collections"))
        except Exception:
            recipe["collections"] = []
        
        # recipe title
        try:
            recipe["title"] = stringCleanup(
                response.css('h1.recipe-title::text').get()
            )
        except Exception:
            recipe["title"] = None

        # author
        try:
            recipe["author"] = stringCleanup(
                response.css(".nytc---recipebyline---bylinePart > a::text").get()
            )
        except Exception:
            recipe["author"] = None
        
        # yield amount
        try:
            recipe["yields"] = stringCleanup(
                response.css(".recipe-yield-container > .recipe-yield-value::text")
                .get()
            )
        except Exception:
            recipe["yields"] = None

        # time to prepare
        try:
            recipe["time"] = stringCleanup(
                response.css(".recipe-time-yield li:nth-child(2) > .recipe-yield-value::text")
                .get()
            )
        except Exception:
            recipe["time"] = None

        # recipe intro paragraph
        try:
            recipe["intro"] = stringCleanup(
                response.css('.recipe-topnote-metadata .topnote p ::text')
                .get()
            )
        except Exception:
            recipe["intro"] = None
    
        # recipe tags
        try:
            recipe["tags"] = [
                stringCleanup(tag)
                for tag
                in response.css('.tags-nutrition-container > .tag::text')
                .getall()
            ]
        except Exception:
            recipe["tags"] = None

        # recipe steps
        try:
            recipe["steps"] = [
                stringCleanup(item)
                .replace('<li>', '')
                .replace('</li>', '')
                for item in response.css('.recipe-steps > li').getall()
            ]
        except Exception:
            recipe["steps"] = None
        
        # ingredients
        try:
            recipe["ingredients"] = parse_recipe_ingredients(response)
        except Exception:
            recipe["ingredients"] = {}

        # full url
        try:
            recipe["full_url"] = response.url
        except Exception:
            recipe["full_url"] = None

        yield recipe


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

        print("Getting the recipe urls filter lists")
        
        # This is the dictionary to be returned
        recipes = {}

        # Iterates over each category and filter in dictionary
        # For example: "special_diets", ["low calorie", "low cholestrol", "low sugar", "low-carb]
        for filter_category, filter_list in category_filter_dict.items():
            #  "low calorie" in ["low calorie", "low cholestrol", "low sugar", "low-carb"]
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
                search_pagination_urls_list = paginate_urls_from_root(url, replace_at)
                for url in search_pagination_urls_list:
                    response = request.urlopen(url)
                    soup = BeautifulSoup(response, "html.parser")
                    cards = soup.find_all(is_card_without_duplicate)
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
        print("Total URL count: " + str(len(recipes.keys())))
        return recipes
           
    def __get_urls_from_collection_page(self, collection_page_url):
        """
        This method takes in a url for a collection webpage (complete url) and
        parses the recipe urls from the page. It modifies the self.recipe
        attribute by adding a url, Recipe(url) as key value pairs if it
        does not exist, otherwise adding to the current Recipe item by adding
        to its collections attribute
        """
        print("Getting urls from collection url: " + str(collection_page_url))
        try:
            response = request.urlopen(collection_page_url)
        except URLError as e:
            print("Not a valid url for get_urls_from_collection. Exception: " + str(e))
            return
        soup = BeautifulSoup(response, "html.parser")
        try:
            collection_name = stringCleanup(
                soup.find("h1", attrs={"class":"name"}).string
            )
        except Exception:
            if collection_page_url == "https://cooking.nytimes.com/68861692-nyt-cooking/29280939-our-50-most-popular-vegetarian-recipes-of-2020":
                collection_name = "Our 50 Most Popular Vegetarian Recipes of 2020"
            else:
                collection_name = "" #TODO fix this <----
        cards = soup.find_all(is_card_without_duplicate)
        for card in cards:
            href = card["href"]
            # if recipes does not contain url, creates a new recipe item 
            # and adds it to the recipe collection
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
