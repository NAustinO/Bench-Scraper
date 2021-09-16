
from urllib import request
from urllib.error import URLError
from scrapy import http
from bs4 import BeautifulSoup
from scrapy.exceptions import CloseSpider
from ..nyt.selectors import is_card_without_duplicate
from ..nyt.utils import stringCleanup


def parse_recipe_ingredients(response: http.TextResponse) -> dict:
    """
    This method parses a recipe page response into a dict object.
    This is needed for when a recipe has their recipes broken into parts. 
    For example, a salad recipe may have "for the salad", "for the dressing",
    "for the croutons" as part of their recipe.
    
    Arguments:
        - response: the Scrapy response object
    
    Returns:
        - a dict where the recipe parts are the keys
        and values a list of list of dictionaries
        - data structure as shown below:
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


def paginate_urls_from_root(root_url: str, index_str: str, page: str) -> list:
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

        Returns:
            - a list object containing string urls that are able to be parsed further
    """

    if page == "search":
        selector = ""
    # validates that there is only one index_str placeholder in root_url
    if root_url.count(index_str) != 1:
        print(
            "The count of placeholder substrings did not match "
            "the number of stringst o replace with in paginate_urls_from_root"
        )
        raise CloseSpider("Closed from paginate_urls_from_root")

    # list of valid urls to return
    valid_urls = []
    # keeps record of the urls inm between valid urls that are skipped
    # used for debugging purposes only
    skipped_urls = []
    page_number = 1
    end_loop_counter = 0

    while True:
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


def get_filter_combinations(start_url: str = "https://cooking.nytimes.com/search") -> dict:
    """
        start_url default is "https://cooking.nytimes.com/search"

        This method parses the start_url page for the filters and filter categories in the filter-by section.

        Here is an example of what the css selector will search for:
        <div class="checkbox" key="special_diets" term="low calorie">
        <div class="checkbox" key="special_diets" term="low cholesterol">
        <div class="checkbox" key="special_diets" term="low sugar">
        <div class="checkbox" key="special_diets" term="low-carb">
        <div class="checkbox" key="cuisines" term="african">
        <div class="checkbox" key="cuisines" term="american">

        Arguments:
            - start_url: the url for the search page of the new york times cooking

        Returns:
            - A dictionary where the keys are the filter categories (for example, 'Meal_Types') and the
            values are the lists of filters (for example, ["Breakfast", "Brunch"]) that corresponds to the key
            based on the filters dropdown box of the filter-by section
                - example of format:
                    {
                        "special_diets": ["low calorie", "low cholestrol", "low sugar", "low-carb],
                        "cuisines": ["african", "american"]
                    }
    """

    # dictionary to return
    temp = {}

    try:
        response = request.urlopen(start_url)
    except Exception:
        print("get_filter_combinations failed to successfully reach a response from {}".format(start_url))

    soup = BeautifulSoup(response, "html.parser")
    filter_tags = soup.find_all("div", class_="checkbox")

    for tag in filter_tags:
        # filter_category will be used as the key for the dict 
        filter_category = tag["key"] 
        filter = tag["term"]
        # if the filter_category does not exist already
        # creates a new filter list and adds to it
        if temp.get(filter_category) is None:
            filter_list = [filter]
            temp[filter_category] = filter_list

        # if the filter category does already exist
        # a list of filters will be there as a value.
        # adds the current filter to the list and
        # applies back to the data structure
        else:
            current_filters_list = list(temp.get(filter_category))
            current_filters_list.append(filter)
            temp[filter_category] = current_filters_list

    return temp


