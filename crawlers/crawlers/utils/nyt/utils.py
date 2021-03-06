import sys
from urllib.error import URLError
from bs4 import BeautifulSoup
from urllib import request
from scrapy.exceptions import CloseSpider
from ...utils.nyt.selectors import is_card_without_duplicate
from selenium import webdriver




def stringCleanup(s: str):
    """
    Processes input string by removing:
        - newline characters
        - quotation marks 
        - and whitespace
    
    If input string is None, returns a blank string ""
    """
    return (
        s.strip("\n").strip('"').strip()
        if s is not None
        else ""
    )

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

def query_for_image(query: str) -> list:
    """
    This method used the query to search Google and scrape 
    the source url for the first image in the results

    Arguments:
        - query: the search string to query Google for
    Returns:
        - A list of google image source urls that resulted from
        the Selenium ChromeDriver
    """
    
    urls_list = []

    try:
        driver = webdriver.Chrome("/Users/nickozawa/Documents/Programming Projects/PanTree/chromedriver")
        query_url = "https://www.google.com/search?q={}&source=lnms&tbm=isch&sa=X&ved=2ahUKEwie44_AnqLpAhUhBWMBHUFGD90Q_AUoAXoECBUQAw&biw=1920&bih=947".format(query.replace(" ", "+"))
        driver.get(query_url)
        img = driver.find_element_by_xpath(
            "/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div[1]/div[1]/"
            "span/div[1]/div[1]/div[1]/a[1]/div[1]/img"
        )
        img.click()
        img_url = driver.find_element_by_xpath(
            "/html/body/div[2]/c-wiz/div[3]/div[2]/div[3]/div/div/div[3]"
            "/div[2]/c-wiz/div/div[1]/div[1]/div[2]/div[1]/a/img"
        ).get_attribute("src")
        urls_list.append(img_url)
        # driver.quit() Does commenting this out make it faster?
    except Exception:
        print("There was an error in query_for_image for query: " + query)
        #print(sys.exc_info()[0], "occurred.")
    return urls_list

    