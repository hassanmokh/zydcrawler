from zydcrawler.helpers import handle_request
from .mongodb import MongoDBPipeline
from pymongo.errors import WriteError
import logging


logger = logging.getLogger(__name__)


class InstagramPipeline(MongoDBPipeline):
    
    db_name = "instagram"

    def handle_collections(self):

        if "restaurants" not in self.db.list_collection_names():
            self.db.create_collection("restaurants", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["username", "name_en", "active"],
                    "properties": {
                        "name_en": {
                            "bsonType": ["string"],
                            "description": "must be a string and is required"
                        },
                        "name_ar": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "username": {
                            "bsonType": ["string"],
                            "description": "must be a string"
                        },
                        "logo": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "url": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "description": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "file_name": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "expiration_date": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "followers": {
                            "bsonType": ["int", "null"],
                            "description": "must be a int"
                        },
                        "type": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "posts": {
                            "bsonType": ["int", "null"],
                            "description": "must be a int"
                        },
                        "country": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "active": {
                            "bsonType": "bool",
                            "description": "must be a boolean"
                        },
                        "food_aggregaror": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "phone_numbers": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                    }
                }
            })

            self.db['restaurants'].create_index("username", unique=True)

    def process_item(self, item, spider):

        restaurants = self.db.restaurants

        try:
            restaurants.update_one({"username": item.get('username')}, {
                "$set": {
                    "name_en": item.get('name_en', None),
                    "name_ar": item.get('name_ar', None),
                    "username": item.get('username'),
                    "logo": item.get('logo', None),
                    "url": item.get('url', None),
                    "description": item.get('description', None),
                    "file_name": item.get('file_name', None),
                    "expiration_date": item.get('expiration_date', None),
                    "followers": item.get('followers', None),
                    "type": item.get('type', None),
                    "posts": item.get('posts', None),
                    "country": item.get('country', None),
                    "active": item.get('active', False),
                    "food_aggregaror": item.get('food_aggregaror', None),
                    "phone_numbers": item.get('phone_numbers', None),
                }
            }, upsert=True)

        except (WriteError, Exception) as e:
            logger.debug(f"[INSTAGRAM-PIPELINE-ERROR] cannot save data: {item} with error {str(e)}")
            raise e
            
        return item


class ZydCrawlerAnalyitcsPipeline:

    def process_item(self, item, spider):

        req_body = {
            "data": {
                "title_en": item.get('name_en'), 
                "title_ar": item.get('name_ar'), 
                "logo_url": item.get('logo'), 
                "restaurant_url": item.get("url"),
                "instagram_uid": item.get('username'),
                "description": item.get('description'),
                "list_name": item.get('file_name'),
                "expiration_date": item.get('expiration_date'),
                "followers_count": item.get('followers'),
                "platform_type": item.get('type'),
                "posts_count": item.get('posts'),
                "country": item.get('country'),
                "is_active": item.get('active'),
                "food_aggregaror": item.get('food_aggregaror'),
                "phone_num": item.get('phone_numbers'),
            }
        }

        headers = {
            "Content-Type": "application/json", 
            'Accept': 'application/json'
        }
        
        status, reason = handle_request(spider.settings['ADD_NEW_RESTAURANT_URL'], req_body, headers)

        if not status:    
            logger.debug(f"[INSTAGRAM-REQUEST-BACKEND] request fail: {reason}")
        
        return


class ZydaClientPipeline:
    
    def process_item(self, item, spider):

        req_body = {
            "insta_followers_count": item.get('followers'),
            "insta_posts_count": item.get('posts'),
            "store_id": item.get('store_id'),
            "title_en": item.get('name'),
            "bio": item.get('bio'),
            "instagram_bio_url": item.get('bio_url'),
        }

        headers = {
            "Content-Type": "application/json", 
            'Accept': 'application/json'
        }
        
        status, reason = handle_request(spider.settings['UPDATE_ZYDA_CLIENTS_RESTAURANT_URL'], req_body, headers)

        if not status:    
            logger.debug(f"[INSTAGRAM-REQUEST-BACKEND] request fail: {reason}")
        
        return
