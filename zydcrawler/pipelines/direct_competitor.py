from zydcrawler.helpers import handle_request
from .mongodb import MongoDBPipeline
from pymongo.errors import WriteError
import logging


logger = logging.getLogger(__name__)


class DirectCompetitorPipeline(MongoDBPipeline):
    db_name = "direct_competitor"

    def handle_collections(self):

        if "restaurants" not in self.db.list_collection_names():
            self.db.create_collection("restaurants", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["name", "url"],
                    "properties": {
                        "url": {
                            "bsonType": ["string"],
                            "description": "must be a string and is required"
                        },
                        "name": {
                            "bsonType": ["string"],
                            "description": "must be a string and is required"
                        },
                        "name_ar": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "file_name": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "logo": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "country": {
                            "bsonType": ["string", "null"],
                            "description": "must be a strinf"
                        },
                    }
                }
            })

            self.db['restaurants'].create_index([("url", 1), ("name", 1), ("file_name", 1)], unique=True)
    
        if "products" not in self.db.list_collection_names():
            self.db.create_collection("products", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["restaurant_id", "name"],
                    "properties": {
                        "restaurant_id": {
                            "bsonType": ["string"],
                            "description": "must be a string and is required"
                        },
                        "name": {
                            "bsonType": ["string"],
                            "description": "must be a string and is required"
                        },
                        "name_ar": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "description": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "description_ar": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "price": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "currency": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "logo": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "category": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        }
                    }
                }
            })

            self.db['products'].create_index([("restaurant_id", 1), ("name", 1)], unique=True)
        
        if "variants" not in self.db.list_collection_names():
            self.db.create_collection("variants", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["product_id", "name"],
                    "properties": {
                        "product_id": {
                            "bsonType": ["string"],
                            "description": "must be a string and is required"
                        },
                        "name": {
                            "bsonType": ["string"],
                            "description": "must be a string and is required"
                        },
                        "name_ar": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "min_choice": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "max_choice": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "description": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "options": {
                            "bsonType": ["array", "null"],
                            "items": {
                                "bsonType": ["object"],
                                "properties": {
                                    "name": {
                                        "bsonType": ["string"],
                                        "description": "must be a string"
                                    },
                                    "name_ar": {
                                        "bsonType": ["string", "null"],
                                        "description": "must be a string"
                                    },
                                    "price": {
                                        "bsonType": ["string"],
                                        "description": "must be a string"
                                    },
                                }
                            }
                        }
                    }
                }
            })

            self.db['variants'].create_index([("product_id", 1), ("name", 1)], unique=True)
                    
    def process_item(self, item, spider):
        
        restaurant_db = self.db.restaurants
        product_db = self.db.products
        variant_db = self.db.variants

        product = item.pop("product")

        try:
            restaurant_db.update_one({"file_name": item.get("file_name"), "name": item.get("name"), "url": item.get("url")},{
                                    "$set": {
                                        "file_name": item.get("file_name"),
                                        "url": item.get("url"),
                                        "name": item.get("name"),
                                        "name_ar": item.get("name_ar"),
                                        "logo": item.get("logo"),
                                        "country": item.get("country"),
                                    }
                                    }, upsert=True)
            
            restaurant_id = str(restaurant_db.find_one({"file_name": item.get("file_name"), "name": item.get("name"), "url": item.get("url")}, {"_id": 1}).get("_id"))

            product_db.update_one({"restaurant_id": restaurant_id, "name": product['name']}, {
                "$set": {
                    "restaurant_id": restaurant_id,
                    "name": product.get("name"),
                    "name_ar": product.get("name_ar"),
                    "description": product.get("description"),
                    "description_ar": product.get("description_ar"),
                    "price": product.get("price"),
                    "currency": product.get("currency"),
                    "logo": product.get("logo"),
                    "category": product.get("category"),
                }
            }, upsert=True)

            if "variant" in product:
                
                variant = product.get("variant")

                product_id = str(product_db.find_one({"restaurant_id": restaurant_id, "name": product.get("name")}, {"_id": 1}).get("_id"))

                variant_db.update_one({"product_id": product_id, "name": variant['name']}, {
                    "$set": {
                        "product_id": product_id,
                        "name": variant.get("name"),
                        "name_ar": variant.get("name_ar"),
                        "description": variant.get("description"),
                        "min_choice": variant.get("min_choice"),
                        "max_choice": variant.get("max_choice"),
                        "options": variant.get("options")
                    }
                }, upsert=True)

        except (WriteError, Exception) as e:
            logger.debug(f"[DIRECT-COMPETITOR-STORE-ERROR] Error when save data: {str(e)}")
            raise e

        return item