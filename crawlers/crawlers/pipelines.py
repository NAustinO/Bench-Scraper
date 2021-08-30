# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import json
import os
import shutil
import scrapy
import sys 
from pathlib import Path
from itemadapter import ItemAdapter
cwd = Path(__file__).parent.parent
sys.path.append(cwd)
from crawlers.items import Recipe
from scrapy.pipelines.images import ImagesPipeline


crawlers_root = Path(__file__).parent.parent


class RecipeExportPipeline:

    def process_item(self, item: Recipe, spider):
        
        '''
        This method is called for every item pipleine component. Must return an item object, return a Deferred or raise a DropItem exception
        '''

        # write the recipe as a JSON object to our target file
        line = json.dumps(ItemAdapter(item).asdict(), indent=4, ensure_ascii=False) + "," + "\n"
        
        self.file.write(line)
        self.recipe_key += 1 

        return item

    def open_spider(self, spider):
        '''
        This method is called when the spider is opened 
        '''

        if input("Are you sure you want to run this crawler? This may overwrite data like images (y/n)") != "y":
            exit()

        # counter for the 
        self.recipe_key = 0

        # open new raw data file
        raw_json_path = str(crawlers_root) + "/data/nyt_data_raw.json"
        self.file = open(raw_json_path, "w+", encoding="utf-8")

        # remove existing image folder if it exists, otherwise creates a new one
        image_dir_path = str(crawlers_root) + "/data/images"
        if os.path.isdir(image_dir_path) is True:
            shutil.rmtree(image_dir_path)
            os.mkdir(image_dir_path)
        else:
            os.mkdir(image_dir_path)

        # removes the previous scraping log if it exists 
        if os.path.isfile(str(crawlers_root) + "/data/scraping.log") is True:
            os.remove(str(crawlers_root) + "/data/scraping.log")

    def close_spider(self, spider):
        '''
        This method is called when the spider is closed. 
        Writes to the file to [] to make the file a list of JSON objects
        '''
        #self.file.write("\n ]")
        #self.file.seek(0,0)
        #self.file.write("[ \n")
        #self.file.close()
        print("Successfully scraped {} recipes".format(self.recipe_key))

