from zydcrawler.helpers import update_cookies, extract_instagram_page_data
from zydcrawler.items import ZydaClientsItem
from json import loads as json_loads
from scrapy.loader import ItemLoader
from scrapy import Spider, Request

class ZydaClientsSpider(Spider):

    name = 'zyda_clients'
    allowed_domains = ['dashboard.zyda.com']
    zyda_clients_rests_url = 'https://dashboard.zyda.com/data_ops/zyda_clients'
    base_instagram_url = "https://www.instagram.com"
    custom_settings = {
        "ITEM_PIPELINES": {
            'zydcrawler.pipelines.ZydaClientPipeline': 300,
        },
        "LOG_FILE": "logs/zyda_clients.log",
        "DOWNLOADER_MIDDLEWARES": {
            "zydcrawler.downloader_middleware.InstagramMiddleware": 402,
            # 'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
            # 'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
        },
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 10,
        "AUTOTHROTTLE_DEBUG": True,
        "DOWNLOAD_DELAY": 45,
    }

    def start_requests(self):
        yield Request(self.zyda_clients_rests_url,
                      meta={"not_instagram": True},
                      dont_filter=True,
                      callback=self.parse_zyda_clients_restaurants
                      )

    def parse_zyda_clients_restaurants(self, response):
        
        if response.status != 200:
            self.logger.debug(f"[ZYDA-CLIENTS-RESTAURANTS-RESPONSE]: response {response.url} is status {response.status} with error: {response.text}")
        
        rests_data = json_loads(response.body)

        for i in rests_data:
            
            username_url = i[2]
            if username_url:
                if "instagram.com" not in username_url:
                    username_url = f"{self.base_instagram_url}/{username_url}/"

                yield Request(username_url,
                              dont_filter=True, 
                              callback=self.parse_restaurant,
                              meta={"store_id": i[0], "restaurant_name": i[1]})

    def parse_restaurant(self, response):

        if response.status != 200:
            self.logger.debug(f"[ZYDA-CLIENT-PARSE_RESTAURANT] response {response.url} error with status: {response.status} and body is: {response.text}")
            return
        
        if (
            "Content Unavailable &bull; Instagram" in response.text or 
            "Sorry, this page isn&#39;t available." in response.text):

            self.logger.debug(f"[ZYDA-CLIENT-PARSE_RESTAURANT] {response.url} this is url isn't found")
            
            return

        try:

            # update cookies
            update_cookies(self.settings, response)

            # extract page profile from page 
            profile_page_data = extract_instagram_page_data(response)

            # get user info
            user_info = profile_page_data.get("graphql", {}).get("user", {})


            data = response.meta

            itm = ItemLoader(item=ZydaClientsItem())

            itm.add_value('followers', user_info.get("edge_followed_by", {}).get("count", 0))
            itm.add_value('posts', user_info.get("edge_owner_to_timeline_media", {}).get("count", 0))
            itm.add_value("name", user_info.get("full_name") or data.get("restaurant_name"))
            itm.add_value("store_id", data.get("store_id"))
            itm.add_value("bio_url", user_info.get("external_url"))
            itm.add_value("bio", user_info.get("biography"))

            yield itm.load_item()
        
        except Exception as e:
            
            self.logger.debug(f"[ZYDA-CLIENT-PARSE_RESTAURANT] error when extract data from {response.url} with error: {str(e)}")
            
            return