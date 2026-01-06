from scrapy.loader import ItemLoader
from scrapy import Spider, Request
from zydcrawler.items import (
    RestaurantItem, RestaurantOptionValueItem, RestaurantProductItem, 
    RestaurantVariantItem, RestaurantOptionItem
)
from json import (
    loads as json_loads, 
    JSONDecodeError,
)
import pandas as pd, requests


class TalabatSpider(Spider):
    name = 'talabat'
    allowed_domains = ['api.talabat.com', "talabat.com"]
    api_url = 'https://api.talabat.com/api/v1'
    web_url = "https://www.talabat.com"
    start_url = f'{api_url}/pages/landing'
    custom_settings = {
        "ITEM_PIPELINES": {
            'zydcrawler.pipelines.TalabatPipeline': 300,
        },
        "LOG_FILE": "logs/talabat.log",
    }
    
    def __init__(self, url=None, external=None, **kwargs):
        
        if external:
            external = True

        super().__init__(url=url, external=external, **kwargs)

    def start_requests(self):
        yield Request(self.start_url, 
                      dont_filter=True, 
                      callback=self.parse_countries,
                      errback=self._logerror)

    def parse_countries(self, response):
        
        if response.status != 200:
            self.logger.debug(f"[TALBAT-PARSE-COUNTRIES] response {response.url} error: {response.text}")
            return

        try:
            countries = json_loads(response.body).get("result", {}).get("countries", None)

        except JSONDecodeError:
            self.logger.debug(f"[TALBAT-PARSE-COUNTRIES] response {response.url} error when load body: {response.text}")

            return 

        # check if response is list of countries
        if not isinstance(countries, list):
            self.logger.debug(f"[TALBAT-PARSE-COUNTRIES] response {response.url} is not a list, body is: {response.body}")
            return

        if self.url:

            country_name = self.url.split("/")[3]

            # request to get all cities from each country
            for country in countries:
                
                if country_name.lower() != country.get("na", "").lower(): continue

                yield Request(f"{self.api_url}/apps/cities/{country.get('id')}",
                            callback=self.parse_cities, 
                            dont_filter=True,
                            errback=self._logerror,
                            meta={
                                "country_slug": country.get("sl"),
                                "country_id": country.get("id"),
                                "country_name": country.get("na", "").lower()
                            })
                break

        else:

            # request to get all cities from each country
            for country in countries:

                yield Request(f"{self.api_url}/apps/cities/{country.get('id')}",
                            callback=self.parse_cities, 
                            dont_filter=True,
                            errback=self._logerror,
                            meta={
                                "country_slug": country.get("sl"),
                                "country_id": country.get("id"),
                                "country_name": country.get("na", "").lower()
                            })

    def parse_cities(self, response):

        if response.status != 200:
            self.logger.debug(f"[TALBAT-PARSE-CITIES] response {response.url} error: {response.text}")
            return

        try:
            cities = json_loads(response.body).get("result", {}).get("cities", None)

        except JSONDecodeError:
            self.logger.debug(f"[TALBAT-PARSE-CITIES] response {response.url} error when load body: {response.text}")

            return 
        
        # check if response is list of cities
        if not isinstance(cities, list):
            self.logger.debug(f"[TALBAT-PARSE-CITIES] response {response.url} is not a list, body is: {response.body}")
            return

        if self.url:
            aid = self.url.split("aid=")[1]

            # get all areas from each city
            for area in pd.DataFrame(cities)['area'].sum():
                if str(area.get('id')) != aid: continue

                yield Request(f"{self.web_url}/{response.meta['country_name']}/restaurants/{area.get('id')}/{area.get('sl')}",
                            callback=self.parse_restaurants,
                            errback=self._logerror,
                            dont_filter=True,
                            meta={
                                **response.meta,
                                "area_id": area.get('id'),
                                "area_name": area.get("an"),
                                "area_slug": area.get("sl")
                            })
                break
        
        else:

            # get all areas from each city
            for area in pd.DataFrame(cities)['area'].sum():

                yield Request(f"{self.web_url}/{response.meta['country_name']}/restaurants/{area.get('id')}/{area.get('sl')}",
                            callback=self.parse_restaurants,
                            errback=self._logerror,
                            dont_filter=True,
                            meta={
                                **response.meta,
                                "area_id": area.get('id'),
                                "area_name": area.get("an"),
                                "area_slug": area.get("sl")
                            })

    def parse_restaurants(self, response):
        
        if response.status != 200:
            self.logger.debug(f"[TALBAT-PARSE-RESTAURANTS] response {response.url} error: {response.text}")
            return

        if self.url:
            yield Request(self.url,
                            dont_filter=True, 
                            meta=response.meta, 
                            callback=self.parse_restaurant, 
                            errback=self._logerror
                        )
            
        else:
            # parse each restaurant
            for link in response.css("div.list-itemstyles__VendorListItemContainer-sc-ia2hbn-0 a::attr(href)").extract():
                
                yield Request(f"{self.web_url}{link}", 
                            dont_filter=True, 
                            meta=response.meta, 
                            callback=self.parse_restaurant, 
                            errback=self._logerror
                            )

            if response.meta.get("next_page", None) is None:
                try:
                    last_page = int(response.css("div.paginationstyles__PaginationContainer-sc-wz3rb7-0.cSuGGb a.d-block.text-center.clickable::text").extract()[-1])
                    response.meta['last_page'] = last_page
                except Exception:
                    return

            if response.meta.get("next_page", 2) <= response.meta.get("last_page"):
                url = response.url
                if "?page=" in url:
                    url = url.split("?page=")[0]

                url += f"?page={str(response.meta.get('next_page', 2))}" 

                yield Request(url, 
                            dont_filter=True, 
                            callback=self.parse_restaurants,
                            errback=self._logerror,
                            meta={
                                **response.meta,
                                "next_page": response.meta.get("next_page", 2) + 1,
                            })

    def parse_restaurant(self, response):

        page_data = response.css("#__NEXT_DATA__::text").extract_first()

        try:
            json_data = json_loads(page_data)

        except JSONDecodeError:
            
            self.logger.debug(f"[TALABAT_PARSE_RESTAURANT] cannot load page data from {response.url}")

            return
        
        restaurant_data = json_data.get("props", {}).get("pageProps", {}).get("initialMenuState", {})
        
        if restaurant_data:
            yield from self.handle_restaurant_products(restaurant_data)
    
    def handle_restaurant_products(self, data):
        
        branch_id = data.get("restaurant").get("id")
        restaurant_products = data.get("menuData").get("items", [])

        if self.url and self.external:
            products = []
        
            for product in restaurant_products:
                pro = {
                    "name": product.get("name"),
                    "description": product.get("description"),
                    "price": product.get("price"),
                    "image": product.get("image"),
                    "section_name": product.get("originalSection"),
                    "category_name": product.get("originalSection"),
                }

                if product.get("hasChoices", False):

                    pro['variant'] = list(self.product_variant(branch_id, product.get('id')))
                        
                products.append(pro)

            yield dict({
                "name": data.get("restaurant").get("name"),
                "area_name": data.get("area").get("name"),
                "logo": data.get("restaurant").get("logo"),
                "city": data.get("city").get("name"),
                "country": data.get("currentCountry").get("name"),
                "products": products,
                "external": True,
            })
                        
        else:

            for product in restaurant_products:
    
                itm = ItemLoader(item=RestaurantProductItem())
                itm.add_value("name", product.get("name"))
                itm.add_value("description", product.get("description"))
                itm.add_value("price", product.get("price"))
                itm.add_value("image", product.get("image"))
                itm.add_value("section_name", product.get("originalSection"))
                itm.add_value("category_name", product.get("originalSection"))

                if product.get("hasChoices", False):

                    itm.add_value('variant', self.product_variant(branch_id, product.get('id')))
                
                # extract and save data
                item = ItemLoader(item=RestaurantItem())
                item.add_value('name', data.get("restaurant").get("name"))
                item.add_value('area_name', data.get("area").get("name"))
                item.add_value('logo', data.get("restaurant").get("logo"))
                item.add_value('city', data.get("city").get("name"))
                item.add_value('country', data.get("currentCountry").get("name"))
                item.add_value("products", dict(itm.load_item()))
            
                yield dict(item.load_item())

    def product_variant(self, branch_id, product_id):

        # get all choices for a product
        try:
            resp = requests.get(f"{self.web_url}/nextMenuApi/v2/branches/{branch_id}/menu/{str(product_id)}/choices")

            if resp.status_code != 200:
                self.logger.debug(f"[TALABAT-PRODUCT-VARIANT] response error {resp.text}")
                return
            
            json_data = resp.json()

        except (requests.ConnectionError,
                requests.ReadTimeout,
                requests.ConnectTimeout,
                requests.JSONDecodeError) as e:
            
            self.logger.debug(f"[TALABAT-PRODUCT-VARIANT] error when make request choices {str(e)}")
            return
        
        # extract all selections
        choice_selections = json_data.get("result").get("choiceForItem")[0].get("choiceSections")

        # get first index as a variant product
        variant = choice_selections.pop(0)
        
        # loop to extract and save the deault group options
        default_options = []

        for i in choice_selections:
            option_item = ItemLoader(item=RestaurantOptionItem())

            option_item.add_value("name", i.get("nm"))
            option_item.add_value("min_choice", i.get("mnq"))
            option_item.add_value("max_choice", i.get("mxq"))
            
            options_values = []

            for op in i.get("ich"):
                option_value_item = ItemLoader(item=RestaurantOptionValueItem())

                option_value_item.add_value("name", op.get("nm"))
                option_value_item.add_value("price", op.get("pr"))

                options_values.append(dict(option_value_item.load_item()))
            
            option_item.add_value("options_values", options_values)


            default_options.append(dict(option_item.load_item()))


        if self.url and self.external:
            variants = []

            # return variant with each option has either other group option or default group option
            for op in variant.get("ich"):
                
                if op.get("hsc", False):
                    options = default_options

                else:
                    options = self.variant_options(branch_id, op.get("id"))

                variants.append({
                    "name": variant.get("nm"),
                    "min_choice": variant.get("mnq"),
                    "max_choice": variant.get("mxq"),
                    "variants_values": {
                        "name": op.get("nm"),
                        "price": op.get("pr"),
                        "options": options,
                    },
                })
                
            yield variants

        else:

            for op in variant.get("ich"):
    
                variant_value_item = ItemLoader(item=RestaurantOptionValueItem())

                variant_value_item.add_value("name", op.get("nm"))
                variant_value_item.add_value("price", op.get("pr"))

                if op.get("hsc", False):
                    variant_value_item.add_value("options", default_options)

                else:
                    variant_value_item.add_value("options", self.variant_options(branch_id, op.get("id")))

                variant_item = ItemLoader(item=RestaurantVariantItem())

                variant_item.add_value("name", variant.get("nm"))
                variant_item.add_value("min_choice", variant.get("mnq"))
                variant_item.add_value("max_choice", variant.get("mxq"))
                variant_item.add_value("variants_values", dict(variant_value_item.load_item()))

                yield dict(variant_item.load_item())

    def variant_options(self, branch_id, choice_id):

        # get all sub choices for a choice from a product
        try:
            req_body = {
                "branch_Id": branch_id, 
                "choice_Ids": f"{str(choice_id)}",
                "restaurant_Id": 0
            }
            resp = requests.post(f"{self.web_url}/nextMenuApi/v2/subchoices", json=req_body)

            if resp.status_code != 200:
                self.logger.debug(f"[TALABAT-PRODUCT-VARIANT-SUB-OPTIONS] response error {resp.text}")
                return
            
            json_data = resp.json()

        except (requests.ConnectionError,
                requests.ReadTimeout,
                requests.ConnectTimeout,
                requests.JSONDecodeError) as e:
            
            self.logger.debug(f"[TALABAT-PRODUCT-VARIANT-SUB-OPTIONS] error when make request choices {str(e)}")
            return
                
        options = []

        for group_option in json_data.get("result").get("choiceForItem")[0].get("choiceSections"):
            options_values = []

            for option_value in group_option.get("ich"):

                itm = ItemLoader(item=RestaurantOptionValueItem())
                itm.add_value("name", option_value.get("nm"))
                itm.add_value("price", option_value.get("pr"))
                
                if option_value.get("hsc", False):
                
                    sub_options = self.variant_options(branch_id, choice_id=option_value.get("id"))
                    itm.add_value("options", sub_options)
                
                options_values.append(dict(itm.load_item()))
            
            itm = ItemLoader(item=RestaurantOptionItem())
            itm.add_value("name", group_option.get("nm"))
            itm.add_value("min_choice", group_option.get("mnq"))
            itm.add_value("max_choice", group_option.get("mxq"))
            itm.add_value("options_values", options_values)

            options.append(dict(itm.load_item()))

        return options

    def _logerror(self, failure):
        self.logger.debug(f"[TALABAT-SPIDER] failure: {failure.value}")