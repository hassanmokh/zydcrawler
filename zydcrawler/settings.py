from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

BOT_NAME = 'zydcrawler'

SPIDER_MODULES = ['zydcrawler.spiders']
NEWSPIDER_MODULE = 'zydcrawler.spiders'

USER_AGENT = "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False
COOKIES_DEBUG = True

CREDS_HEADER_FILE_NAME = "cookies.json"
CREDS_FILE_NAME = "creds.json"

DOMAIN_BACKEND = os.getenv("DOMAIN_BACKEND")

ADD_NEW_RESTAURANT_URL = f"{DOMAIN_BACKEND}/restaurants/add_restaurant"

IMPORT_RESTAURANT_URL = f"{DOMAIN_BACKEND}/menu_items/import_menu_item"

UPDATE_ZYDA_CLIENTS_RESTAURANT_URL = f"{DOMAIN_BACKEND}/zyda_clients/update_zyda_client"

ZYDA_CLIENTS_RESTAURANTS_URL = "https://dashboard.zyda.com/data_ops/zyda_clients"


# configuration db
MONGO_DB_HOST = os.getenv("MONGO_DB_HOST")
MONGO_DB_PORT = os.getenv("MONGO_DB_PORT")
MONGO_DB_USER = os.getenv("MONGO_DB_USER")
MONGO_DB_PASSWORD = os.getenv("MONGO_DB_PASSWORD")
MONGO_URL= f"mongodb://{MONGO_DB_USER}:{MONGO_DB_PASSWORD}@{MONGO_DB_HOST}:{MONGO_DB_PORT}/"


DOWNLOADER_MIDDLEWARES={
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
    "scrapy_fake_useragent.middleware.RandomUserAgentMiddleware": 400,
    "scrapy_fake_useragent.middleware.RetryUserAgentMiddleware": 401,
}


FAKEUSERAGENT_PROVIDERS = [
    "scrapy_fake_useragent.providers.FakerProvider",
    "scrapy_fake_useragent.providers.FakeUserAgentProvider",
    "scrapy_fake_useragent.providers.FixedUserAgentProvider",
]

RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408, 429]


ROTATING_PROXY_LIST = [
    'http://zydaproxy:ayshay@sg.proxymesh.com:31280',
    'http://zydaproxy:ayshay@us-il.proxymesh.com:31280',
    'http://zydaproxy:ayshay@us.proxymesh.com:31280',
    'http://zydaproxy:ayshay@us-dc.proxymesh.com:31280',
    'http://zydaproxy:ayshay@open.proxymesh.com:31280',
]


# main instagram headers
INSTAGRAM_HEADERS = {
    "Sec-Ch-Ua": '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
    "X-Ig-App-Id": 936619743392459,
    "X-Ig-Www-Claim": "hmac.AR1mnkiySPFdT_WbrQeTo5jKWcNzPyy80jfbB0j_eN9P_-yX",
    "Sec-Ch-Ua-Mobile": "?0",
    "X-Instagram-Ajax": "301424afbdb8",
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Requested-With": "XMLHttpRequest",
    "X-Asbd-Id": 198387,
    "X-Csrftoken": "Ou55PlSo3rHkuzRV3GPXNlE45R01n4p2",
    "Sec-Ch-Ua-Platform": "macOS",
    "Origin": "https://www.instagram.com",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": 'cors',
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://www.instagram.com",
    "Accept-Encoding": "gzip, deflate",
}

MAIN_COOKIES_KEYS = [
    'sessionid', 
    "rur",
]

DIRECT_ORDERS = [
    'zyda', 
    'mnasati', 
    'itsordable', 
    'zyda_closed', 
    'plugn', 
    'upayments', 
    'tryorder', 
    'chatfood', 
    'chownow', 
    'bentobox', 
    'gloriafood', 
    'simple broker'
]

'''
    @key: is the name the will store and sent to the backend
    @value: (`search in`, `search key`, `type key => direct comp | food agg | indirect comp`)
'''
ORDERS_KEYS = {

    # direct_competitor
    "zyda": ('head', "zyda", 'direct_competitor'),
    "mnasati": ('head', "mnasati", 'direct_competitor'),
    "itsordable": ('head', "tapcom-live.ams3.cdn.digitaloceanspaces.com", 'direct_competitor'),
    "plugn": ('head', "plugn", 'direct_competitor'),
    "simple broker": ('body', "simple broker", 'direct_competitor'),
    "chat food": ('head', "Chatfood", 'direct_competitor'),
    "taker": ('head', "web-production-b.my.taker.io", 'direct_competitor'),
    "blinkco": ('body', "Blinkco", 'direct_competitor'),
    "upayments": ('body', "Upayments", 'direct_competitor'),
    "zvendo": ('head', "Zvendo", 'direct_competitor'),
    "zammit": ('head', "Zammit", 'direct_competitor'),
    "Bentobox": ('head', "getbento.com", 'direct_competitor'),
    "chownow": ('body', "chownow", 'direct_competitor'),
    "Gloriafood": ("body", "fbgcdn", 'direct_competitor'),
    "TryOrder": ("body", "tryorder", 'direct_competitor'),
    "payzah": ("body", "tryorder", 'direct_competitor'),

    # food_aggregator
    "talabat": ("head", "talabat", "food_aggregator"),
    "el menus": ("head", "elmenus", "food_aggregator"),
    "carriage": ("head", "trycarriage", "food_aggregator"),
    "deliveroo": ("head", "deliveroo", "food_aggregator"),
    "Zomato": ("head", "zomato", "food_aggregator"),
    "Careem": ("head", "careem", "food_aggregator"),
    "Bilbayt": ("head", "bilbayt", "food_aggregator"),
    "Clicks": ("head", "clicks", "food_aggregator"),
    "Cravez": ("head", "cravez", "food_aggregator"),
    "Hungerstation": ("head", "hungerstation", "food_aggregator"),

    # indirect_competitor
    "V-Thru": ("head", "v-thru", "indirect_competitor"),
    "Finedine": ("head", "finedine", "indirect_competitor"),
    "Kitopi": ("head", "kitopi", "indirect_competitor"),
    "Whatsapp": ("head", "whatsapp", "indirect_competitor"),
    "linktr.ee": ("head", "linktr.ee", "indirect_competitor"),
}

URL_PATTERN_EXCLUDE = [
    'facebook', 
    'twitter', 
    'instagram', 
    'tiktok', 
    'youtube', 
    'telegram',
    'google',
    'apple',
    'snapchat',
]

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'zydcrawler.middlewares.ZydcrawlerSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'zydcrawler.middlewares.ZydcrawlerDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'zydcrawler.pipelines.ZydcrawlerPipeline': 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
