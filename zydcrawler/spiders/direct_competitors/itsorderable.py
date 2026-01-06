from zydcrawler.items import ItsOrderableProductItem


class ItsOrderable:
    itsorderable_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json;q=0.9,*/*;q=0.8"
    }

    def start_itsorderable(self, url, country=None, file_name=None):
        uri = self._url_parse(url)

        yield self.request_class(f"{uri.scheme}://{uri.netloc}/store/",
                                 method="POST",
                                 callback=self.__parse_itsorderable_restaurant,
                                 errback=self._logerror,
                                 dont_filter=True,
                                 headers=self.itsorderable_headers,
                                 meta={
                                    "country": country,
                                    "file_name": file_name,
                                    "base_url": url,
                                    "uri_res": uri 
                                })

    def __parse_itsorderable_restaurant(self, response):
            
        if response.status != 200:
            self.logger.debug(f"[ORDERABLE-PARSE] failed in url {response.url} ===> error: {response.text}")
            return
        
        try:
            data = response.json()

        except self.json.JSONDecodeError as e:
            self.logger.debug(f"[ORDERABLE-PARSE] failed decode data in {response.url} error: {str(e)} ===> body: {response.text}")
            return
        
        url = response.meta.get("uri_res")

        yield self.request_class(f"{url.scheme}://{url.netloc}/products_second_load/",
                                 method='POST',
                                 callback=self.__parse_itsorderable_categories,
                                 errback=self._logerror,
                                 headers=self.itsorderable_headers,
                                 meta={
                                    **response.meta,
                                    "name": data.get("name"),
                                    "name_ar": data.get("ar_name"),
                                    "slogan": data.get("slogan"),
                                    "slogan_ar": data.get("ar_slogan"),
                                    "slug": data.get("slug"),
                                    "base_country": data.get("base_country"),
                                    "default_dial_code": data.get("default_dial_code"),
                                    "logo": data.get("logo"),
                                 })

    def __parse_itsorderable_categories(self, response):
        if response.status != 200:
            self.logger.debug(f"[ORDERABLE-PARSE-MENUS] failed in url {response.url} ===> error: {response.text}")
            return
        
        try:
            data = response.json()

        except self.json.JSONDecodeError as e:
            self.logger.debug(f"[ORDERABLE-PARSE] failed decode data in {response.url} error: {str(e)} ===> body: {response.text}")
            return
        
        url = response.meta.get("uri_res")

        for category in data.get("categories", []):

            yield self.request_class(f"{url.scheme}://{url.netloc}/category_product_list_fetch/",
                                      method="POST",
                                      callback=self.__parse_itsorderable_products,
                                      errback=self._logerror,
                                      headers=self.itsorderable_headers,
                                      body=self.json_pack.dumps({
                                        'availableCategories': [category.get('id')],
                                        'page': 1,
                                        'slug': category.get('slug'),
                                        'used_components': {},
                                        'country_code': None
                                      }),
                                      meta={
                                        **response.meta,
                                        "category_name": category.get("name"),
                                        "category_name_ar": category.get("ar_name"),
                                        "logo": category.get("photo") or category.get("photo_medium"),
                                        "minimum_order_value": category.get("minimum_order_value")
                                    })

    def __parse_itsorderable_products(self, response):

        if response.status != 200:
            self.logger.debug(f"[ORDERABLE-PARSE-MENUS] failed in url {response.url} ===> error: {response.text}")
            return
        
        try:
            data = response.json()

        except self.json.JSONDecodeError as e:
            self.logger.debug(f"[ORDERABLE-PARSE] failed decode data in {response.url} error: {str(e)} ===> body: {response.text}")
            return

        url = response.meta.get("uri_res")

        for category in data.get('categories', []):
            for product in category.get("products", []):

                yield self.request_class(f"{url.scheme}://{url.netloc}/load_options/",
                                         method="POST",
                                         body=self.json_pack.dumps({
                                            "country_code": None,
                                            "product_id": product.get("id")
                                         }),
                                         callback=self.__parse_itsorderable_options,
                                         errback=self._logerror,
                                         headers=self.itsorderable_headers,
                                         meta={
                                            **response.meta,
                                            "product_name": product.get("name"),
                                            "product_image": product.get("photo"),
                                            "product_description": product.get("short_description"),
                                            "product_price": str(product.get("price")),
                                            "product_currency": product.get("currency"),
                                         })
    
    def __parse_itsorderable_options(self, response):
        
        if response.status != 200:
            self.logger.debug(f"[ORDERABLE-PARSE-MENUS] failed in url {response.url} ===> error: {response.text}")
            return
        
        try:
            data = response.json()

        except self.json.JSONDecodeError as e:
            self.logger.debug(f"[ORDERABLE-PARSE] failed decode data in {response.url} error: {str(e)} ===> body: {response.text}")
            return
        
        meta_data = response.meta

        if data.__len__() == 0:

            product_item = self._item_loader(item=ItsOrderableProductItem())

            product_item.add_value("category", meta_data.get("category_name"))
            product_item.add_value("name", meta_data.get("product_name"))
            product_item.add_value("logo", meta_data.get("product_image"))
            product_item.add_value("description", meta_data.get("product_description"))
            product_item.add_value("price", meta_data.get("product_price"))
            product_item.add_value("currency", meta_data.get("product_currency"))

            restaurant_item = self._item_loader(item=self.restaurant_item_class())

            restaurant_item.add_value("name", meta_data.get("name"))
            restaurant_item.add_value("name_ar", meta_data.get("name_ar"))
            restaurant_item.add_value("file_name", meta_data.get("file_name"))
            restaurant_item.add_value("url", meta_data.get("base_url"))
            restaurant_item.add_value("logo", meta_data.get("logo"))
            restaurant_item.add_value("country", meta_data.get("base_country"))
            restaurant_item.add_value("product", dict(product_item.load_item()))

            yield dict(restaurant_item.load_item())
        
        elif "options" in data:
    
            for option in data.get("options", []):
                
                options = []

                for choice in option.get("choices"):
                    option_item = self._item_loader(item=self.restaurant_variant_options_item_class())

                    option_item.add_value("name", choice.get("value"))
                    option_item.add_value("name_ar", choice.get("value_ar"))
                    option_item.add_value("price", str(choice.get("price")))

                    options.append(dict(option_item.load_item()))

                variant_item = self._item_loader(item=self.restaurant_variant_item_class())

                variant_item.add_value("name", option.get("name"))
                variant_item.add_value("name_ar", option.get("ar_name"))
                variant_item.add_value("description", option.get("description"))
                variant_item.add_value("min_choice", str(option.get("minimum")))
                variant_item.add_value("max_choice", str(option.get("maximum")))
                variant_item.add_value("options", options)

                product_item = self._item_loader(item=ItsOrderableProductItem())

                product_item.add_value("category", meta_data.get("category_name"))
                product_item.add_value("name", meta_data.get("product_name"))
                product_item.add_value("logo", meta_data.get("product_image"))
                product_item.add_value("description", meta_data.get("product_description"))
                product_item.add_value("price", meta_data.get("product_price"))
                product_item.add_value("currency", meta_data.get("product_currency"))
                product_item.add_value("variant", dict(variant_item.load_item()))


                restaurant_item = self._item_loader(item=self.restaurant_item_class())

                restaurant_item.add_value("name", meta_data.get("name"))
                restaurant_item.add_value("file_name", meta_data.get("file_name"))
                restaurant_item.add_value("url", meta_data.get("base_url"))
                restaurant_item.add_value("logo", meta_data.get("logo"))
                restaurant_item.add_value("country", meta_data.get("base_country"))
                restaurant_item.add_value("product", dict(product_item.load_item()))

                yield dict(restaurant_item.load_item())
