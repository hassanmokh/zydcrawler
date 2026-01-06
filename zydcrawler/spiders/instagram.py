from zydcrawler.helpers import extract_instagram_page_data
from zydcrawler.items import InstagramItem
from scrapy.loader import ItemLoader
from scrapy import Request, Spider
import pandas as pd, whois, re, json


class InstagramSpider(Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    web_url = "https://www.instagram.com"
    default_path_dir = "default"
    default_filename = "IG - Marketing.xlsx"
    
    custom_settings = {
        "ITEM_PIPELINES": {
            'zydcrawler.pipelines.InstagramPipeline': 300,
            'zydcrawler.pipelines.ZydCrawlerAnalyitcsPipeline': 301,
        },
        "LOG_FILE": "logs/instagram.log",
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

    def __init__(self, recrawler=None, file_path=None, **kwargs):

        if recrawler or file_path:
            
            self.custom_settings['AUTOTHROTTLE_START_DELAY'] = 45

        super().__init__(recrawler=recrawler, file_path=file_path, **kwargs)
        
        if self.recrawler:
            self.recrawler = json.loads(self.recrawler)
         
    def start_requests(self):
        ''' start crawl '''
        
        if self.recrawler is not None:

            self.logger.debug(f"[INSTAGRAM-RECRAWL] start request with data: {self.recrawler}")

            yield Request(f'{self.web_url}/{self.recrawler["username"]}/', 
                          callback=self.parse,
                          dont_filter=True,
                          meta={
                            "country": self.recrawler["country"],
                            "active": True,
                            "direct_comp": self.recrawler.get("direct_competitor"),
                            "food_agg": self.recrawler.get("food_aggregator"),
                          })
            
        else:
            
            file_path = self.file_path or str(self.crawler.settings['BASE_DIR'] / f"{self.default_path_dir}/{self.default_filename}")
            file_name, extension = file_path.rsplit("/", 1)[1].rsplit(".", 1)

            if extension == 'csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            df = df.where(pd.notnull(df), "")

            # continue crawl excel if some of data not in the db
            if self.db['restaurants'].count_documents({"file_name": file_name}) < df.__len__():
                
                # exclude rows the already crawled from pandas
                exclude = [f"{self.web_url}/{i['username']}/" for i in self.db['restaurants'].find({"file_name": file_name}, {"username": 1})]
                
                # get all excluded rows from pandas
                exclude = df['IG URL'].isin(exclude)
                
                # get rows uncrawled
                df = df[~exclude]

            for _, val in df[['Country', 'IG URL', 'Active', 'Direct Competitors', 'Food Aggregators']].iterrows():
                    
                if val['IG URL'] is not None and val["Active"] == "Active":

                    # updating API instagram 13-6-2022
                    # the update is fetch page data from api without need to get object from script tag in html page
                    # it's updated from instagram

                    url = val['IG URL'].rsplit("?")[0]
                    
                    username = url.replace("https://www.instagram.com/", "").replace("/", "")
                    
                    yield Request(f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}",
                                callback=self.parse,
                                errback=self._logerror,
                                dont_filter=True,
                                meta={
                                    "file_name": file_name,
                                    "country": val['Country'].lower(),
                                    "active": val["Active"].lower() == "active",
                                    "direct_comp": val['Direct Competitors'],
                                    "food_agg": val['Food Aggregators'],
                                })
                    
    def parse(self, response):
       
        if response.status != 200:
            self.logger.debug(f"[RESPONSE-PARSE_PAGE] failed in url {response.url} ==> error: {response.text}")
            return

        try:
            data = response.json()

        except json.JSONDecodeError as e:
            self.logger.debug(f"[ERROR-PARSE] failure in parse: {response} , {str(e)}")
            return

        # get user info
        user_info = data.get("data", {}).get("user", {})
        
        external_url = user_info.get("external_url")
        

        # replace any http to https if url exists
        if external_url:
            if "https://" not in external_url:
                external_url = f'https://{"".join(external_url.split("://")[1:])}'
        
        data = {
            **response.meta,
            "posts": user_info.get("edge_owner_to_timeline_media", {}).get("count", 0),
            "username": user_info.get("username"),
            "followers": user_info.get("edge_followed_by", {}).get("count", 0),
            "description": user_info.get("biography"),
            "restaurant_url": external_url,
            "name_en": user_info.get("full_name"),
            "name_ar": user_info.get("full_name"),
            "logo": user_info.get("profile_pic_url"),
        }

        yield from self.get_restaurant_url(data)
    
    def get_restaurant_url(self, data):
        
        # extract phones from description
        if data.get("description"):

            # extract phone number if exists
            phones = ", ".join(re.findall(r"[0-9]{5,}", data.get("description")))

            data['phone_numbers'] = phones

        restaurant_url = data.get("restaurant_url")
        
        # check if restaurant url already exist
        if restaurant_url:
                
            # turn off proxies when call any other instagram request 
            data['_rotating_proxy'] = False
            data['proxy'] = None
            data['not_instagram'] = True
            
            yield Request(restaurant_url, 
                        dont_filter=True, 
                        callback=self.parse_restaurant_url, 
                        errback=self._logerror,
                        meta=data)
                
        else:
            yield from self.store_data(data)

    def parse_restaurant_url(self, response):
        
        if response.status != 200:
            self.logger.debug(f"[RESPONSE-PARSE-RESTAURANTS] failed in url {response.url} ==> error : {response.text}")
            return

        # update restaurant url
        response.meta["restaurant_url"] = response.url
        
        flag_media = False

        # check if url is not in social_media list
        for social in self.settings['URL_PATTERN_EXCLUDE']:
            if social in response.url:
                flag_media = True
                break
        
        if not flag_media:
    
            # get type of url
            type = ('direct_competitor', None)

            for key, val in self.settings["ORDERS_KEYS"].items():
                if val[1] in (response.css(val[0]).extract_first() or ''):
                    type = (val[2], key)
                    break
            
            response.meta[type[0]] = type[1]

            if type[1] != "indirect_competitor":

                try: # if the domain is not valid then will fire exception

                    # use whois to get info about the domain
                    data_whois = whois.whois(response.url)
                    
                    exp_date = data_whois.get("expiration_date", [])

                    # check if expiration_date is list or string
                    if isinstance(exp_date, list):
                        exp_date = ", ".join([str(date) for date in exp_date])

                    else:
                        exp_date = str(exp_date)

                    response.meta['expiration_date'] = exp_date

                except Exception as e:
                    self.logger.debug(f"[INSTAGRAM-RESTAURANT-WHOIS] error when get expiration date from domain with error: {str(e)}")

        yield from self.store_data(response.meta)

    def store_data(self, data):
        itm = ItemLoader(item=InstagramItem())

        itm.add_value("name_en", data.get("name_en") or data.get("username"))
        itm.add_value("name_ar", data.get("name_ar") or data.get("username"))
        itm.add_value("description", data.get("description"))
        itm.add_value("logo", data.get("logo"))
        itm.add_value("url", data.get("restaurant_url"))
        itm.add_value("file_name", data.get("file_name"))
        itm.add_value("username", data.get("username"))
        itm.add_value("expiration_date", data.get("expiration_date"))
        itm.add_value("followers", data.get("followers"))
        itm.add_value("type", data.get('direct_comp') or data.get('direct_competitor'))
        itm.add_value("posts", data.get("posts"))
        itm.add_value("country", data.get('country'))
        itm.add_value("active", data.get('active'))
        itm.add_value("food_aggregaror", data.get('food_aggregator'))
        itm.add_value("phone_numbers", data.get('phone_numbers'))

        yield itm.load_item()

    def _logerror(self, failure):
        self.logger.debug(f"[INSTAGRAM-ERROR-SPIDER] failure: {failure.value}")
