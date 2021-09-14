# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import json
import os
import sys 
import time
from datetime import datetime
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

        """
        This method is called when the spider is opened only once.
        """
    
        if input("Are you sure you want to run this crawler? This may overwrite data like images (y/n)") != "y":
            exit()

        # for determining duration of process
        self.start_time = time.monotonic()

        data_folder_name = datetime.now().strftime("%b-%d-%y (%I:%M:%S)")
        folder_path = str(crawlers_root) + "/data/{}".format(data_folder_name)
        images_folder_path = folder_path + "/images"

        os.mkdir(folder_path)
        os.mkdir(images_folder_path)

        self.file = open(folder_path + "/nyt_data_raw.json", "w+", encoding="utf-8")
        spider.custom_settings = {
            "IMAGES_STORE" : images_folder_path,
        }

        self.recipe_key = 0

    def close_spider(self, spider):
        '''
        This method is called when the spider is closed. 
        Writes to the file to [] to make the file a list of JSON objects
        '''
        self.file.write("\n ]")
        self.file.seek(0,0)
        self.file.write("[ \n")
        self.file.close()
        
        # TODO ADD POST PROCESSING FOR FILE TO PARSE INTO INDIVIDUAL CSV FILES 
        print(
            "Successfully scraped {} recipes\n".format(self.recipe_key),
            "Time to run (min:sec): {}:{}" #TODO
        )

