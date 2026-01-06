

class Mnasati:
    __mnasati_headers = {
        "authorization": "Basic bW5hc2F0aS1hZG1pbjp1aWd0Yy4xMjRAIQ==",
        "accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "x-app-type": "web",
    }
    __mnasati_url = "https://mnasatiapi.com/v2"

    def start_mnasati(self, url, country="kuwait", file_name=None):
        uri = self._url_parse(url)

        yield self.request_class(f"{uri.scheme}://{uri.netloc}/assets/config/config.json",
                                 callback=self.__mnasati_parse_config,
                                 errback=self._logerror,
                                 dont_filter=True,
                                 meta={
                                    "country": country,
                                    "file_name": file_name,
                                    "base_url": url,
                                    "uri_res": uri 
                                 })

    def __mnasati_parse_config(self, response):

        if response.status != 200:
            self.logger.debug(f"[MNASATI-PARSE-CONFIG] failed in url {response.url} ===> error: {response.text}")
            return
        
        try:
            data = response.json()

        except self.json.JSONDecodeError as e:
            self.logger.debug(f"[MNASATI-PARSE-CONFIG] failed decode data in {response.url} error: {str(e)} ===> body: {response.text}")
            return
        
        self.__mnasati_headers['x-api-key'] = data.get("api", {}).get("key")

        yield self.request_class(f"{self.__mnasati_url}/mobileapi/home_branches/",
                                 method="POST",
                                 body=self.json_pack.dumps({
                                    "country_id": 1,
                                    "schedule_order": 0
                                 }),
                                 callback=self.__parse_mnasati_restaurant,
                                 errback=self._logerror,
                                 dont_filter=True,
                                 headers=self.__mnasati_headers,
                                 meta=response.meta)
    
    def __parse_mnasati_restaurant(self, response):

        if response.status != 200:
            self.logger.debug(f"[MNASATI-PARSE-RESTAURANT] failed in url {response.url} ===> error: {response.text}")
            return
        
        try:
            data = response.json()

        except self.json.JSONDecodeError as e:
            self.logger.debug(f"[MNASATI-PARSE-RESTAURANT] failed decode data in {response.url} error: {str(e)} ===> body: {response.text}")
            return

        restaurant_data = data.get("branches")[0]

        for category in data.get("categories", []):
            details = category.get("details")

            for product in category.get("products", []):
                yield self.request_class(f"{self.__mnasati_url}/api/product/",
                                        method="POST",
                                        body=self.json_pack.dumps({
                                            "product_id": product.get("product_id"),
                                        }),
                                        callback=self.__mnasati_parse_options,
                                        errback=self._logerror,
                                        dont_filter=True,
                                        headers={
                                            **self.__mnasati_headers,
                                            "Content-Type": "application/json" 
                                        },
                                        meta={
                                            **response.meta,
                                            "name": restaurant_data.get("name").rstrip(),
                                            "name_ar": restaurant_data.get("name_ar").rstrip(),
                                            "category_name": details.get("category_name").rstrip(),
                                            "category_name_ar": details.get("category_name_ar").rstrip(),
                                            "category_logo": details.get("image"),
                                            "product_description": product.get("description").rstrip(),
                                            "product_description_ar": product.get("description_ar").rstrip(),
                                            "product_image": product.get("image"),
                                            "product_price": str(product.get("sale_price")),
                                            "product_name": product.get("title"),
                                            "product_name_ar": product.get("title_ar"),
                                        })
    
    def __mnasati_parse_options(self, response):

        if response.status != 200:
            self.logger.debug(f"[MNASATI-PARSE-RESTAURANT] failed in url {response.url} ===> error: {response.text}")
            return
        
        try:
            data = response.json()

        except self.json.JSONDecodeError as e:
            self.logger.debug(f"[MNASATI-PARSE-RESTAURANT] failed decode data in {response.url} error: {str(e)} ===> body: {response.text}")
            return
        
        options = data.get("data", {}).get("options", [])
        meta_data = response.meta

        if options.__len__() == 0:

            product_item = self._item_loader(item=self.restaurant_product_item_class())

            product_item.add_value("category", meta_data.get("category_name"))
            product_item.add_value("name", meta_data.get("product_name"))
            product_item.add_value("name_ar", meta_data.get("product_name_ar"))
            product_item.add_value("logo", meta_data.get("product_image"))
            product_item.add_value("description", meta_data.get("product_description"))
            product_item.add_value("description_ar", meta_data.get("product_description_ar"))
            product_item.add_value("price", meta_data.get("product_price"))

            restaurant_item = self._item_loader(item=self.restaurant_item_class())

            restaurant_item.add_value("name", meta_data.get("name"))
            restaurant_item.add_value("name_ar", meta_data.get("name_ar"))
            restaurant_item.add_value("file_name", meta_data.get("file_name"))
            restaurant_item.add_value("url", meta_data.get("base_url"))
            restaurant_item.add_value("logo", meta_data.get("logo"))
            restaurant_item.add_value("country", meta_data.get("base_country"))
            restaurant_item.add_value("product", dict(product_item.load_item()))

            yield dict(restaurant_item.load_item())

        else:

            for option in options:

                choices = []

                for choice in option.get("values", []):
                    option_item = self._item_loader(item=self.restaurant_variant_options_item_class())

                    option_item.add_value("name", choice.get("name"))
                    option_item.add_value("name_ar", choice.get("name_ar"))
                    option_item.add_value("price", str(choice.get("price")))

                    choices.append(dict(option_item.load_item()))

                variant_item = self._item_loader(item=self.restaurant_variant_item_class())

                variant_item.add_value("name", option.get("title"))
                variant_item.add_value("name_ar", option.get("title_ar"))
                variant_item.add_value("min_choice", str(option.get("minimum")))
                variant_item.add_value("max_choice", str(option.get("maximum")))
                variant_item.add_value("options", choices)

                product_item = self._item_loader(item=self.restaurant_product_item_class())

                product_item.add_value("category", meta_data.get("category_name"))
                product_item.add_value("name", meta_data.get("product_name"))
                product_item.add_value("name_ar", meta_data.get("product_name_ar"))
                product_item.add_value("logo", meta_data.get("product_image"))
                product_item.add_value("description", meta_data.get("product_description"))
                product_item.add_value("description_ar", meta_data.get("product_description_ar"))
                product_item.add_value("price", meta_data.get("product_price"))
                product_item.add_value("variant", dict(variant_item.load_item()))

                restaurant_item = self._item_loader(item=self.restaurant_item_class())

                restaurant_item.add_value("name", meta_data.get("name"))
                restaurant_item.add_value("name_ar", meta_data.get("name_ar"))
                restaurant_item.add_value("file_name", meta_data.get("file_name"))
                restaurant_item.add_value("url", meta_data.get("base_url"))
                restaurant_item.add_value("logo", meta_data.get("logo"))
                restaurant_item.add_value("country", meta_data.get("country"))
                restaurant_item.add_value("product", dict(product_item.load_item()))

                yield dict(restaurant_item.load_item())
