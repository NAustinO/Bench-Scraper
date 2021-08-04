import csv
import scrapy
from bs4 import BeautifulSoup, SoupStrainer
from urllib import request
from urllib.error import URLError, HTTPError
from scrapy import http
from scrapy.extensions import closespider


class TimesSpider(scrapy.Spider):
    name = "times"

    recipes = []
    '''
        def start_requests(self):
        pageUrls = []
        
        pageUrls.append("https://cooking.nytimes.com/search?q=&page={}".format(1))

        for url in pageUrls:
            yield scrapy.Request(url=url, callback=self.parse_page)
    '''

    def start_requests(self):
        pageUrls = []
        
        pageNumber = 1

        # iterates over each page to get the page urls in a list
        while True:
            url = "https://cooking.nytimes.com/search?q=&page={}".format(pageNumber)
            if pageNumber == 27:
                pageNumber = 28
                continue
            else:
                try:
                    response = request.urlopen(url=url)
                except URLError:
                    print("Last page of url was " + url)
                    break
                else:
                    print("Trying to reach url: {}".format(url))
                    pageNumber += 1
                    pageUrls.append(url)

        for url in pageUrls:
            yield scrapy.Request(url=url, callback=self.parse_page)
    
        self.removeDuplicates()

    #start_urls = ["https://cooking.nytimes.com/recipes/1016342-sweet-potato-quinoa-spinach-and-red-lentil-burger"]

    def parse_page(self, response):
        links_on_page = response.css('article.card a.card-link:not(.card-recipe-info)::attr(href)').getall()
        for link in links_on_page:
            if link.startswith("/recipes"):
                yield scrapy.Request(url="https://cooking.nytimes.com{}".format(link), callback=self.parse, encoding='utf-8')
            elif link[1].isdigit():
                yield scrapy.Request(url="https://cooking.nytimes.com{}".format(link), callback=self.parse_page, encoding='utf-8')
    
    def parse(self, response: http.TextResponse):
        try:
            print('Parsing page: ' + response.url)
            row = {
                'title': stringCleanup(response.css('h1.recipe-title::text').get()),
                'author': response.css('.nytc---recipebyline---bylinePart > a::text').get(),
                'yields': response.css('.recipe-yield-container > .recipe-yield-value::text').get(),
                'time': response.css('.recipe-time-yield li:nth-child(2) > .recipe-yield-value ::text').get(),
                'intro': response.css('.recipe-topnote-metadata .topnote p ::text').get(),
                'tags': response.css('.tags-nutrition-container > .tag ::text').getall(),
                'ingredients': self.getRecipeParts(response),
                'steps': response.css('.recipe-steps > li').getall(),
                'url': response.url
            }


            for k, v in row.items():
                if k == 'tags':
                    row[k] = [stringCleanup(item) for item in v]
                elif k == 'steps':
                    row[k] = [stringCleanup(item).replace('<li>', '').replace('</li>', '') for item in v]
                elif k == 'ingredients':
                    continue
                else:
                    if v is None:
                        continue
                    else:
                        row[k] = stringCleanup(v)

            with open('data.csv', 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=row.keys(), dialect='excel')
                writer.writerow(row)
        except Exception as err:
            raise closespider("Ran into an exception: " + err)

    
    def getRecipeParts(self, response):

        '''
        parts = {
            'for the crust': [
                {
                    'quantity': str
                    'ingredient': str
            }, 
            'main': []

            ]
        }
        '''

        #print("This is for getRecipeParts url: {}".format(response.url))
        parts = {}
        sections = response.css('.recipe-ingredients-wrap > .recipe-ingredients').getall()
        sectionHeaders = response.css('.recipe-ingredients-wrap > .part-name ::text').getall()
        for section in sections:
            if section.rfind("nutrition-container") != -1:
                sections.remove(section)

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
                entry['quantity'] = quantity
                entry['ingredient'] = ingredient
                ingContainer.append(entry)
            parts[sectionHeaders[i]] = ingContainer
        return parts

    def removeDuplicates(self):
        pass
        #TODO


    
class Recipe(object):
    def __init__(self, name, link, **kwargs) -> None:
        self.name = str(name)
        self.link = str(link)
        self.author = kwargs.get('author')
        self.yields = kwargs.get('yields')
        self.time = kwargs.get('time')
        self.intro = kwargs.get('intro')
        self.tags = []
        self.ingredients = None
        self.steps = []

    def setattr(self, name: str, value) -> bool:
        return super().__setattr__(name, value)


def stringCleanup(s: str): 
    return s.strip('\n').strip('"').strip()

