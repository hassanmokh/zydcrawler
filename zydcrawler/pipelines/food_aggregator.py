from zydcrawler.helpers import handle_request
from .mongodb import MongoDBPipeline
import logging, copy


logger = logging.getLogger(__name__)


class FoodAggregatorPipeline(MongoDBPipeline):
    
    platform = None
    log_name = None
    db_restaurant_name = "restaurant"
    db_product_name = "restaurant_product"
    db_variant_name = "restaurant_product_variant"
    db_variant_values_name = "restaurant_product_variant_values"

    def __init__(self):
        assert self.platform, "You should assgin `platform` when you need to inherit from the  `FoodAggregatorPipeline` class"
        assert self.log_name, "You should assgin `log_name` when you need to inherit from the  `FoodAggregatorPipeline` class"
        self.db_name = self.platform

    def handle_collections(self):

        list_collections = self.db.list_collection_names()
        
        if self.db_restaurant_name not in list_collections:
            self.db.create_collection(self.db_restaurant_name, validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["platform", "name", "area", "city", "country"],
                    "properties": {
                        "platform": {
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
                        "area": {
                            "bsonType": "string",
                            "description": "must be a string and is required"
                        },
                        "area_ar": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "logo": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "city": {
                            "bsonType": "string",
                            "description": "must be a string and is required"
                        },
                        "city_ar": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "country": {
                            "bsonType": "string",
                            "description": "must be a string and is required"
                        },
                        "country_ar": {
                            "bsonType": ["string", "null"],
                            "description": "must be a int"
                        },
                        
                    }
                }
            })

            self.db[self.db_restaurant_name].create_index("name", unique=True)

        if self.db_product_name not in list_collections:
            self.db.create_collection(self.db_product_name, validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["restaurant_id", "name", "price", "section_name", "category_name"],
                    "properties": {
                        "restaurant_id": {
                            "bsonType": ["string"],
                            "description": "must be a string and is required"
                        },
                        "name": {
                            "bsonType": ["string"],
                            "description": "must be a string and is required"
                        },
                        "description": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "price": {
                            "bsonType": ["double", "string", "int"],
                            "description": "must be a string and is required"
                        },
                        "image": {
                            "bsonType": ["string", "null"],
                            "description": "must be a string"
                        },
                        "section_name": {
                            "bsonType": ["string"],
                            "description": "must be a string and is required"
                        },
                        "category_name": {
                            "bsonType": "string",
                            "description": "must be a string and is required"
                        }
                    }
                
                }
            })

            self.db[self.db_product_name].create_index([("restaurant_id", 1), ("name", 1)], unique=True)
     
        if self.db_variant_name not in list_collections:
            self.db.create_collection(self.db_variant_name, validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["product_id", "name", "min_choice", "max_choice"],
                    "properties": {
                        "product_id": {
                            "bsonType": "string",
                            "description": "must be a string and is required"
                        },
                        "name": {
                            "bsonType": "string",
                            "description": "must be a string and is required"
                        },
                        "min_choice": {
                            "bsonType": "int",
                            "description": "must be a int and is required"
                        },
                        "max_choice": {
                            "bsonType": "int",
                            "description": "must be a int and is required"
                        }
                    }                
                }
            })

            self.db[self.db_product_name].create_index([("product_id", 1), ("name", 1)], unique=True)
        
        if self.db_variant_values_name not in list_collections:
            self.db.create_collection(self.db_variant_values_name, validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["variant_id", "name", "price"],
                    "properties": {
                        "variant_id": {
                            "bsonType": ["string"],
                            "description": "must be a string and is required"
                        },
                        "name": {
                            "bsonType": "string",
                            "description": "must be a string and is required"
                        },
                        "price": {
                            "bsonType": ["double", "int"],
                            "description": "must be a double or int and is required"
                        },
                        "old_price": {
                            "bsonType": ["double", "int", "null"],
                            "description": "must be a double or int and is required"
                        },
                        "options": {
                            "bsonType": ["array", "null"],
                            "items": {
                                "bsonType": ["object"],
                                "properties": {
                                    "name": {
                                        "bsonType": "string",
                                        "description": "must be a string and is required",
                                    },
                                    "min_choice": {
                                        "bsonType": "int",
                                        "description": "must be a int and is required",
                                    },
                                    "max_choice": {
                                        "bsonType": "int",
                                        "description": "must be a int and is required",
                                    },
                                    "options_values": {
                                        "bsonType": ["array", "null"],
                                        "items": {
                                            "bsonType": ["object"],
                                            "properties": {
                                                "name": {
                                                    "bsonType": "string",
                                                    "description": "must be a string and is required"
                                                },
                                                "price": {
                                                    "bsonType": ["double", "int"],
                                                    "description": "must be a double or int and is required"
                                                },
                                                "old_price": {
                                                    "bsonType": ["double", "int", "null"]
                                                },
                                                "options": {
                                                    "bsonType": ["array", "null"]
                                                }
                                            }
                                        
                                        },
                                    
                                    }
                                
                                }
                            }
                        },
                    
                    
                    }                
                }
            })

            self.db[self.db_product_name].create_index([("variant_id", 1), ("name", 1)], unique=True)

    def process_item(self, item, spider):

        if "external" in item:
            item.pop("external")
            self._extract_restaurant_to_excel(item, spider)

        else:
            data = copy.deepcopy(item)

            self._store_data(item)

            self._send_request_backend(data, spider)

        return item

    def _extract_restaurant_to_excel(self, item, spider):
        import pandas as pd, re, os

        products = item.pop("products")
    
        variants = []
        for pro in products:
            if "variant" in pro:
    
                for variant in pro.pop("variant")[0]:
                    
                    vrs = {}
                    if "variants_values" in variant:

                        vr = variant['variants_values']
                        options = vr.get("options") if "options" in vr and vr.get("options").__len__() > 0 else ""
                        
                        vrs = {
                            "variant_value_name": vr.get('name', ""),
                            "variant_value_price": vr.get('price', ""),
                            "variant_value_old_price": vr.get('old_price', ""),
                            "variant_value_options": options,
                        }
                    variants.append({
                        "product_name": pro['name'],
                        "name": variant['name'],
                        "min_choice": variant.get('min_choice', ""),
                        "max_choice": variant.get('max_choice', ""),
                        **vrs
                    })
        
        excel_name = re.sub(r'[^a-zA-Z]+', '', item['name'])
        
        base_dir = spider.settings['BASE_DIR']
        
        path = str(base_dir / f"exports/{self.platform}")
        
        if not os.path.exists(path):
            os.makedirs(path)

        save_file = f"{path}/{excel_name}.xlsx"

        pd.DataFrame([item], columns=item.keys()).to_excel(save_file, index=False, sheet_name="restaurant")

        writer = pd.ExcelWriter(save_file, mode="a", engine="openpyxl")

        pd.DataFrame(products).to_excel(writer, index=False, sheet_name="products")
        pd.DataFrame(variants).to_excel(writer, index=False, sheet_name="variants")

        writer.save()
        writer.close()

    def _store_data(self, item):

        restaurant_db = getattr(self.db, self.db_restaurant_name)
        restaurant_product_db = getattr(self.db, self.db_product_name)
        restaurant_product_variant_db = getattr(self.db, self.db_variant_name)
        restaurant_product_variant_values_db = getattr(self.db, self.db_variant_values_name)

        product = item.pop('products')

        variant = None
        variant_value = None

        if "variant" in product:

            variant = product.pop("variant")
            
            variant_value = variant.pop("variants_values")
        
        # import ipdb; ipdb.set_trace()
        
        # update or insert restaurant
        restaurant_db.update_one({"platform": self.platform, "name": item['name']}, {
            "$set": {
                "platform": self.platform, 
                "name": item.get('name', None), 
                "name_ar": item.get('name_ar', None), 
                "area": item.get('area_name', None), 
                "area_ar": item.get('area_ar', None), 
                "city": item.get('city', None), 
                "city_ar": item.get('city_ar', None), 
                "country": item.get('country', None), 
                "country_ar": item.get('country_ar', None), 
                "logo": item.get('logo', None),
            }, 
        }, upsert=True)

        restaurant_id = str(restaurant_db.find_one({"platform": self.platform, "name": item['name']}, {"_id": 1}).get("_id"))
        
        # update or insert product
        restaurant_product_db.update_one({"restaurant_id": restaurant_id, "name": product['name']}, {
            "$set": {
                "restaurant_id": restaurant_id, 
                "name": product.get('name', None), 
                "description": product.get('description', None), 
                "price": product.get('price', None),
                "image": product.get('image', None),
                "section_name": product.get('section_name', None),
                "category_name": product.get('category_name', None),
            }, 
        }, upsert=True)
        
        if variant:
            # import ipdb; ipdb.set_trace()
            product_id = str(restaurant_product_db.find_one({"restaurant_id": restaurant_id, "name": product['name']}, {"_id": 1}).get("_id"))
            
            # update or insert product variant
            restaurant_product_variant_db.update_one({"product_id": product_id, "name": variant['name']}, {
                "$set": {
                    "product_id": product_id, 
                    "name": variant.get('name', None), 
                    "min_choice": variant.get('min_choice', None), 
                    "max_choice": variant.get('max_choice', None)
                }, 
            }, upsert=True)

            if variant_value:

                variant_id = str(restaurant_product_variant_db.find_one({"product_id": product_id, "name": variant['name']}, {"_id": 1}).get("_id"))

                # update or insert variant_values
                restaurant_product_variant_values_db.update_one({"variant_id": variant_id, "name": variant_value['name']}, {
                                "$set": {
                                    "variant_id": variant_id, 
                                    "name": variant_value.get('name', None), 
                                    "price": variant_value.get('price', None), 
                                    "old_price": variant_value.get('old_price', None),
                                    "options": variant_value.get('options', None),
                                }, 
                            }, upsert=True)

        return

    def _send_request_backend(self, data, spider):

        req_body = {
            "data": {
                "menu_platform": self.platform,
                **dict(data)
            }
        }

        headers = {
            "Content-Type": "application/json", 
            'Accept': 'application/json'
        }
        
        status, reason = handle_request(spider.settings['IMPORT_RESTAURANT_URL'], req_body, headers)

        if not status:    
            logger.debug(f"[INSTAGRAM-REQUEST-BACKEND] request fail: {reason}")
        
        return


class ElMenusPipeline(FoodAggregatorPipeline):
    platform = "elmenus"
    log_name = "ELMENUS"

class TalabatPipeline(FoodAggregatorPipeline):
    platform = "talabat"
    log_name = "TALABAT"