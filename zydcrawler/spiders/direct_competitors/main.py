from .itsorderable import ItsOrderable
from .mnasati import Mnasati
from scrapy import Spider, Request, FormRequest
from zydcrawler.items import (
    RestaurantMainItem, ProductMainItem,
    VariantMainItem, OptionMainItem
)
from scrapy.loader import ItemLoader
from urllib.parse import urlparse
import pandas as pd
import json

class DirectCompetitorSpider(Spider, ItsOrderable, Mnasati):
    name = "direct_competitor"

    custom_settings = {
        "ITEM_PIPELINES": {
            'zydcrawler.pipelines.DirectCompetitorPipeline': 300,
        },
        "LOG_FILE": "logs/direct_competitor.log",
    }
    
    def __init__(self, file_path=None, url=None, platform=None, name=None, **kwargs):
        super().__init__(name, file_path=file_path, url=url, platform=platform, **kwargs)
        
        self._url_parse = urlparse
        self.request_class = Request
        self.form_request_class = FormRequest
        self.json_pack = json
        self._item_loader = ItemLoader
        self.restaurant_item_class = RestaurantMainItem
        self.restaurant_product_item_class = ProductMainItem
        self.restaurant_variant_item_class = VariantMainItem
        self.restaurant_variant_options_item_class = OptionMainItem

    def start_requests(self):
        
        if self.url:
            assert self.platform, "You should pass platform type"

            if "itsorderable" in self.platform:
                yield from self.start_itsorderable(self.url)
            
            elif "mnasati" in self.platform:
                yield from self.start_mnasati(self.url)
                
        else:
            file_name, extension = self.file_path.rsplit("/", 1)[1].rsplit(".", 1)

            if extension == "csv":
                df = pd.read_csv(self.file_path)

            else:
                
                df = pd.read_excel(self.file_path)
            
            df = df.where(pd.notnull(df), "")

            count_db = self.db['restaurants'].count_documents({"file_name": file_name})

            if count_db > 0 and count_db < df.__len__():

                exclude = [i['url'] for i in self.db['restaurants'].find({"file_name": file_name}, {"url": 1})]

                df['URL'].isin(exclude)
                
                df = df[~exclude]

            for _, val in df[["URL", 'Country', 'Direct Competitor']].iterrows():
                
                if 'itsorderable' in val['Direct Competitor'].lower():
                    
                    yield from self.start_itsorderable(val['URL'], val['Country'], file_name)
                
                elif 'mnasati' in val['Direct Competitor'].lower():
                    pass
            
    def _logerror(self, failure):
        
        if hasattr(failure.value, "response"):
            response = failure.value.response

            self.logger.debug(f"[DIRECT-COMPETITOR-ERROR-SPIDER] failure: in response {response.url} and error ===> {response.text}") 

        else:
            self.logger.debug(f"[DIRECT-COMPETITOR-ERROR-SPIDER] failure: {failure.value}") 
