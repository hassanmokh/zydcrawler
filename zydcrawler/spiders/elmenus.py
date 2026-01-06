from zydcrawler.items import (
    RestaurantItem, RestaurantProductItem,
    RestaurantVariantItem, RestaurantOptionItem,
    RestaurantOptionValueItem
)
from zydcrawler.helpers import extract_value
from scrapy.loader import ItemLoader
from scrapy import Spider, Request
import json, math


class ElmenusSpider(Spider):
    name = 'elmenus'
    allowed_domains = ['elmenus.com']
    start_urls = ['https://elmenus.com/']
    web_url = "https://elmenus.com"
    PAGE_SIZE = 200
    custom_settings = {
        "ITEM_PIPELINES": {
            'zydcrawler.pipelines.ElMenusPipeline': 300,
        },
        "LOG_FILE": "logs/elmenus.log",
    }
    required_headers = {
        "x-client-id": "0417b144-0f3f-11e8-87cc-0242ac110002",
    }

    def __init__(self, url=None, external=None, **kwargs):
        
        if external:
            external = True

        super().__init__(url=url, external=external, **kwargs)
    
    def parse(self, response):
        
        if response.status != 200:
            self.logger.debug(f"[ELMENUS-MAIN-PARSE] response: {response.url} ==> error: {response.text}")
            return

        data = response.css("#script-should-remove::text").extract_first().replace("var pickData = {", "").replace("lookups: ", "").replace("      }\n   ", "").split(",\n        profile")[0]
        
        json_data = json.loads(data)

        cities = {i['uuid']: {
            'country_uuid': i['ref']['countryUUID'],
            "name": i['data']['name'],
            "name_ar": i['data']['otherName']
        } for i in json_data['cities']}

        areas = {i['uuid']: {
            'city': {
                "city_uuid": i['ref']['cityUUID'],
                **cities[i['ref']['cityUUID']],
            },
            'name': i['data']['name'],
            'name_ar': i['data']['otherName'],

        } for i in json_data['areas']}

        zones = { i['uuid']: {
            "area": {
                "area_uuid": i['ref']['areaUUID'],
                **areas[i['ref']['areaUUID']],

            },
            "name": i['data']['name'],
            "name_ar": i['data']['otherName'],

        } for i in json_data['zones']}

        if self.url:
            
            city_name = self.url.split("/")[3]

            for uuid, zone in zones.items():
                
                if city_name.lower() != zone['area']['city']['name'].lower(): continue
                
                area_uuid = zone['area']['area_uuid']
                zone_uuid = uuid
                xdevice_id = extract_value(response.headers.to_unicode_dict()['set-cookie'], "payload=")
                auth = extract_value(response.headers.to_unicode_dict()['set-cookie'], 'Authorization=')

                yield Request(f"{self.web_url}/2.0/discovery/delivery/search?area={area_uuid}&zone={zone_uuid}&pageSize={self.PAGE_SIZE}",
                            callback=self.parse_zone_restaurants,
                            errback=self._log_error,
                            headers={
                                "Authorization": f"Bearer {auth}",
                                **self.required_headers,
                                "x-device-id": xdevice_id,
                            },
                            meta={
                                "zone_name": zone["name"],
                                "zone_name_ar": zone["name_ar"],
                                "elmenus_x-device-id": xdevice_id,
                                "elmenus_auth": auth,
                                "area_name": zone['area']['name'],
                                "area_name_ar": zone['area']['name_ar'],
                                "city_name": zone['area']['city']['name'],
                                "city_name_ar": zone['area']['city']['name_ar'],
                                "country_name": "Egypt",
                                "country_name_ar": "مصر",
                            })
                break

        else:

            # loop for each zone to extract all restaurants
            for uuid, zone in zones.items():
                area_uuid = zone['area']['area_uuid']
                zone_uuid = uuid
                xdevice_id = extract_value(response.headers.to_unicode_dict()['set-cookie'], "payload=")
                auth = extract_value(response.headers.to_unicode_dict()['set-cookie'], 'Authorization=')

                yield Request(f"{self.web_url}/2.0/discovery/delivery/search?area={area_uuid}&zone={zone_uuid}&pageSize={self.PAGE_SIZE}",
                            callback=self.parse_zone_restaurants,
                            errback=self._log_error,
                            headers={
                                "Authorization": f"Bearer {auth}",
                                **self.required_headers,
                                "x-device-id": xdevice_id,
                            },
                            meta={
                                "zone_name": zone["name"],
                                "zone_name_ar": zone["name_ar"],
                                "elmenus_x-device-id": xdevice_id,
                                "elmenus_auth": auth,
                                "area_name": zone['area']['name'],
                                "area_name_ar": zone['area']['name_ar'],
                                "city_name": zone['area']['city']['name'],
                                "city_name_ar": zone['area']['city']['name_ar'],
                                "country_name": "Egypt",
                                "country_name_ar": "مصر",
                            })
    
    def parse_zone_restaurants(self, response):

        if response.status != 200:
            self.logger.debug(f"[ELMENUS-PARSE-ZONE-RESTAURANTS] response: {response.url} ==> error: {response.text}")
            return

        try:
            json_data = response.json()

        except json.JSONDecodeError as e:
            self.logger.debug(f"[ELMENUS-PARSE-ZONE-RESTAURANTS] error when get response body: {str(e)}")
            return
        
        # get token from previous request
        auth = response.meta['elmenus_auth']

        # get device id from previous request
        xdevice_id = response.meta['elmenus_x-device-id']
        
        if self.url:

            yield Request(self.url,
                        callback=self.parse_restauarant,
                        errback=self._log_error,
                        headers={
                            "Authorization": f"Bearer {auth}",
                            **self.required_headers,
                            "x-device-id": xdevice_id,
                        },
                        meta={
                            **response.meta,
                            "crawled_restaurant": True,
                        })

        else:
            # loop in data to extract restaurants
            for restaurant in json_data.get("data", []):
                
                data = restaurant['data']
                
                # get branch code for each restaurant
                branch_code = data['branchShortCode']

                logo = data.get("logo")

                if logo is not None:
                    logo = logo.replace("{{PHOTO_VERSION}}", "Normal").replace("{{PHOTO_EXTENSION}}", "jpg")

                yield Request(f"{self.web_url}/2.0/branch/{branch_code}/menus",
                            callback=self.parse_restauarant,
                            errback=self._log_error,
                            headers={
                                "Authorization": f"Bearer {auth}",
                                **self.required_headers,
                                "x-device-id": xdevice_id,
                            },
                            meta={
                                **response.meta,
                                "restaurant_review": data.get('reviewsRating'),
                                "restaurant_name": data.get('name'),
                                "restaurant_logo": logo
                            })
                    
            if response.meta.get("count_pages", 0) == 0:
                counts = json_data['count']
                response.meta['count_pages'] = math.ceil(int(counts) / self.PAGE_SIZE)
                response.meta['next_page'] = 2

            if response.meta['next_page'] <= response.meta['count_pages']:
            
                yield Request(f'{response.request.url.split("&pageSize=")[0]}&pageSize={self.PAGE_SIZE}&page={response.meta["next_page"]}',
                            headers=response.request.headers,
                            callback=self.parse_zone_restaurants,
                            errback=self._log_error,
                            meta={
                                **response.meta,
                                "next_page": response.meta['next_page'] + 1,
                            })

    def parse_restauarant(self, response):

        if response.status != 200:
            self.logger.debug(f"[ELMENUS-PARSE-RESTAURANT] response: {response.url} ==> error: {response.text}")
            return

        if self.url and response.meta.get("crawled_restaurant", False):
            try:
                data = None
                for dt in response.css("script[type='application/ld+json']::text").extract():
                    dt = json.loads(dt)
                    
                    if "menu" in dt.keys():
                        data = dt
                        break
                
                branch_code = data['menu'].rsplit("-", 1)[1]

                yield Request(f"{self.web_url}/2.0/branch/{branch_code}/menus",
                              callback=self.parse_restauarant,
                              errback=self._log_error,
                              headers=response.request.headers,
                            meta={
                                **response.meta,
                                "restaurant_name": data.get('name'),
                                "restaurant_logo": data['logo'],
                                "crawled_restaurant": False,
                            })

            except (
                json.JSONDecodeError,
                Exception
            )as e:
                self.logger.debug(f"[ELMENUS-PARSE-RESTAURANT] error when get response body: {str(e)}")
                return
            
            return

        try:
            json_data = response.json()

        except json.JSONDecodeError as e:
            self.logger.debug(f"[ELMENUS-PARSE-RESTAURANT] error when get response body: {str(e)}")
            return

        if self.url and self.external:
            products = []
            
            # complex O(n^4)
            for menu in json_data['menus']:
                
                for category in menu['data']['categories']:
                    
                    for product in category['data']['items']:
                        product = product['data']
                        main_price = 0
                        variants = []

                        variant_group_options = self._product_variant_options(product['extraCategories'])

                        # loop for get variant options
                        for index, option in enumerate(product['sizes']):
                            option = option['data']

                            if index == 0:
                                main_price = option.get("price")

                            option_name = option.get("name")

                            option_values = {
                                "name": option_name,
                                "price": option.get("price"),
                                "old_price": option.get("oldPrice")
                            }
                            
                            if option_name in variant_group_options:
                                option_values["options"] = variant_group_options[option_name]

                            variants.append({
                                "name": "Select Size",
                                "min_choice": 1,
                                "max_choice": 1,
                                "variants_values": option_values
                            })
                        
                        image = product.get("photoUrl")

                        if image:
                            image = image.replace("{{PHOTO_VERSION}}", "Normal").replace("{{PHOTO_EXTENSION}}", "jpg")

                        products.append({
                            "name": product.get("name"),
                            "description": product.get("description"),
                            "price": main_price,
                            "image": image,
                            "category_name": category['data'].get("name"),
                            "section_name": menu['data'].get("name") or "other category",
                            "variant": [variants]
                        })

            yield {
                "name": response.meta["restaurant_name"],
                "logo": response.meta["restaurant_logo"],
                "area_name": response.meta["area_name"],
                "area_ar": response.meta["area_name_ar"],
                "city": response.meta["city_name"],
                "city_ar": response.meta["city_name_ar"],
                "country": response.meta["country_name"],
                "country_ar": response.meta["country_name_ar"],
                "products": products,
                "external": True
            }

        else:

            # complex O(n^4)
            for menu in json_data['menus']:
                
                for category in menu['data']['categories']:
                    
                    for product in category['data']['items']:
                        # if product.get("name") == ""
                        product = product['data']
                        main_price = 0
                        variant_options = []

                        variant_group_options = self._product_variant_options(product['extraCategories'])

                        # loop for get variant options
                        for index, option in enumerate(product['sizes']):
                            option = option['data']

                            if index == 0:
                                main_price = option.get("price")

                            option_name = option.get("name")

                            itm_option = ItemLoader(item=RestaurantOptionValueItem())

                            itm_option.add_value("name", option_name)
                            itm_option.add_value("price", option.get("price"))
                            itm_option.add_value("old_price", option.get("oldPrice"))
                            
                            if option_name in variant_group_options:
                                itm_option.add_value("options", variant_group_options[option_name])

                            variant_options.append(dict(itm_option.load_item()))
                        
                        # prepare variant of product
                        item_variant = ItemLoader(item=RestaurantVariantItem())

                        item_variant.add_value("name", "Select Size")
                        item_variant.add_value("min_choice", 1)
                        item_variant.add_value("max_choice", 1)
                        item_variant.add_value("variants_values", variant_options)

                        # prepare product
                        itm = ItemLoader(item=RestaurantProductItem())
                        
                        image = product.get("photoUrl")

                        if image:
                            image = image.replace("{{PHOTO_VERSION}}", "Normal").replace("{{PHOTO_EXTENSION}}", "jpg")

                        itm.add_value("name", product.get("name"))
                        itm.add_value("description", product.get("description"))
                        itm.add_value("price", main_price)
                        itm.add_value("image", image)
                        itm.add_value("category_name", category['data'].get("name"))
                        # updates category 20-06-2022
                        itm.add_value("section_name", category['data'].get("name")) #menu['data'].get("name") or "other category")
                        itm.add_value("variant", dict(item_variant.load_item()))
                        
                        # get restaurant data
                        itm_restaurant = ItemLoader(item=RestaurantItem())

                        itm_restaurant.add_value("name", response.meta["restaurant_name"])
                        itm_restaurant.add_value("logo", response.meta["restaurant_logo"])
                        itm_restaurant.add_value("area_name", response.meta["area_name"])
                        itm_restaurant.add_value("area_ar", response.meta["area_name_ar"])
                        itm_restaurant.add_value("city", response.meta["city_name"])
                        itm_restaurant.add_value("city_ar", response.meta["city_name_ar"])
                        itm_restaurant.add_value("country", response.meta["country_name"])
                        itm_restaurant.add_value("country_ar", response.meta["country_name_ar"])
                        itm_restaurant.add_value("products", dict(itm.load_item()))

                        yield dict(itm_restaurant.load_item())

    def _product_variant_options(self, extraCategories):
        
        variant_group_options = {}

        for extra in extraCategories:
            group_options = {}
                
            for extra_item in extra['data']['items']:
                extra_item = extra_item['data']
                
                for extra_item_size in extra_item['sizes']:

                    extra_item_size = extra_item_size['data']

                    itm_option = ItemLoader(item=RestaurantOptionValueItem())

                    itm_option.add_value("name", extra_item['name'])
                    itm_option.add_value("price", extra_item_size.get('price'))

                    dict_itm_option = dict(itm_option.load_item())

                    if extra_item_size.get("name") in group_options:

                        group_options[extra_item_size.get("name")].append(dict_itm_option)
                    
                    else:
                        group_options[extra_item_size.get("name")] = [dict_itm_option]
  
            for size in group_options:
                variant_option = ItemLoader(item=RestaurantOptionItem())

                variant_option.add_value("name", extra['data']['name'])
                variant_option.add_value("min_choice", extra['data']['minimumAllowedExtra'])
                variant_option.add_value("max_choice", extra['data']['maximumAllowedExtra'])
                variant_option.add_value("options_values", group_options[size])

                data_variant_option = dict(variant_option.load_item())

                if size in variant_group_options:
                    variant_group_options[size].append(data_variant_option)

                else:
                    variant_group_options[size] = [data_variant_option]

        return variant_group_options

    def _log_error(self, failure):
        self.logger.debug(f"[ELMENUS-LOG-ERROR] failure : {failure.value}")