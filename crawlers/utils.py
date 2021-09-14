import json 
import csv
from os import name 
import sys
from pathlib import Path
import time 
from selenium import webdriver
import requests 
import shutil 
import os


sys.path.append(Path(__file__).parent)

def toCSV(file_path):
    """
    applies the parsed ingredient data to a csv 
    csv headers: 
    key, section, qty, unit, name, comment, alternative, category, ingredient_phrase, 

    categories: 

    """
    json_file = open(file_path, 'r')
    csv_file = open('crawlers/data/parsed_ing_output.csv', "w+", newline="")

    fieldnames = ["id", "section", "quantity", "unit", "name", "comment", "alternative", "category", "input", "range_end"]
    json_data = json.load(json_file)
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    for id, recipe_object in json_data.items():
        for section_name, ingredients_list in recipe_object.items():
            for ingredient_object in ingredients_list:
                row = {
                    "id": id,
                    "section": section_name,
                    "quantity": ingredient_object.get("qty"),
                    "unit": ingredient_object.get("unit"),
                    "name": ingredient_object.get("name"),
                    "comment": ingredient_object.get("comment"),
                    "alternative": None,
                    "category": None,
                    "input": ingredient_object.get("input"),
                    "range_end": ingredient_object.get("range_end")
                }
                csv_writer.writerow(row)
    print("done")


def print_unique_keys(file_path):
    
    """
    this prints the values of the attributes for the ingredient object so I know if there are any that I need to consider 
    """

    json_file = open(file_path, 'r')
    json_data = json.load(json_file)
    attributes_set = set()
    for id, recipe_object in json_data.items():
        for section_name, ingredients_list in recipe_object.items():
            for ingredient_object in ingredients_list:
                for attribute in ingredient_object.keys():
                    attributes_set.add(attribute)

    for attr in list(attributes_set):
        print(attr)
    
                 
def main():
    file_path = "crawlers/data/parsed_ing_output.json"
    toCSV(file_path)


if __name__ == "__main__":
    main()



def get_image_urls(query: str, num: int=1): 
    """
    This returns a list of google image urls based on the search query using the selenium ChromeDriver
    @params:
    query - search query
    num - number of urls to return 
    TODO make this compatible with numbers greater than 1 
    """
    
    try:
        driver = webdriver.Chrome("/Users/nickozawa/Documents/Programming Projects/PanTree/chromedriver")
        
        query_url = 'https://www.google.com/search?q={}&source=lnms&tbm=isch&sa=X&ved=2ahUKEwie44_AnqLpAhUhBWMBHUFGD90Q_AUoAXoECBUQAw&biw=1920&bih=947'.format(query.replace(" ", "+"))

        urls_list = []
        driver.get(query_url)
        time.sleep(.01)
        for i in range(num):
            img = driver.find_element_by_xpath("/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div[1]/div[1]/span/div[1]/div[1]/div[1]/a[1]/div[1]/img")
            img.click()
            time.sleep(.01)
            img_url = driver.find_element_by_xpath("/html/body/div[2]/c-wiz/div[3]/div[2]/div[3]/div/div/div[3]/div[2]/c-wiz/div/div[1]/div[1]/div[2]/div[1]/a/img").get_attribute("src")
            urls_list.append(img_url)
            ""
        driver.quit()
        return urls_list
    except Exception as e:
        print("There was an error in get_image_urls for query: " + query)
        print(sys.exc_info()[0], "occurred.")
        #exit()
        


