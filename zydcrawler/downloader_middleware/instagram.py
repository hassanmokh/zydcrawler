from twisted.internet.defer import maybeDeferred
from scrapy.utils.httpobj import urlparse_cached
from scrapy.exceptions import StopDownload
from json import loads as json_loads, dumps as json_dumps
from urllib.parse import urlencode
from scrapy import Request
import logging, os, random
from zydcrawler.helpers import process_headers, extract_value

logger = logging.getLogger(__name__)


class InstagramMiddleware(object):
    
    DOWNLOAD_PRIORITY = 1000

    def __init__(self, crawler):

        self._crawler = crawler
        self.settings = self._crawler.settings
        self.login_url = 'accounts/login/ajax/'
        self.main_headers = self.settings['INSTAGRAM_HEADERS']
        self.base_dir = self._crawler.settings['BASE_DIR']
        self.creds_file_name = self._crawler.settings['CREDS_HEADER_FILE_NAME']
        self.creds_login_file_name = self._crawler.settings['CREDS_FILE_NAME']
        self.main_cookies_keys = self._crawler.settings['MAIN_COOKIES_KEYS']

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        
        # check if the current request is login instagram also
        # check if instgram already logged in or not
        if request.meta.get("login") or request.meta.get("not_instagram", False):
            return    
        
        # check request is redirect to login
        if request.meta.get("redirect_times", 0) <= 0:

            # check if file already exists
            if os.path.exists(self.base_dir / self.creds_file_name):
                with open(self.base_dir / self.creds_file_name, "r") as f:
                    creds = json_loads(f.read())
                
                creds_choice = random.choice(list(creds.keys()))

                request.headers.update(self.main_headers)
                
                request.cookies.update(creds[creds_choice])
                
                return
        
        # add new schedular for request login with higher priority
        # before running any request
        return maybeDeferred(self.login_parser, request, spider)
        
    def login_parser(self, request, spider):
        '''
            it's the higher priority request that need to be run it before
            any request made.
            So we need to reorder the scheduler to run the login request firstly
            the main goal here is handle the request login if we need to authenticate through instagram
        '''
        # get netloc from request url
        url = urlparse_cached(request)

        # check if request is for instagram
        if "instagram.com" not in url.netloc:
            logger.debug(f"[LOGIN-PARSER-INSTAGRAM] {request.url} isn't instgram request")
            return
            
        if os.path.exists(self.base_dir / self.creds_login_file_name):
            with open(self.base_dir / self.creds_login_file_name, "r") as f:
                creds = json_loads(f.read())
        
        else:
            logger.warning(f"[LOGIN-PARSER-INSTAGRAM] the {self.creds_login_file_name} isn't found")
            StopDownload()
                
        # get creds login
        creds = random.choice(creds)
        
        req = Request(f"{url.scheme}://{url.netloc}/{self.login_url}",
                      meta={"login": True, "main_cookie": creds['cookie']},
                      method="POST",
                      priority=self.DOWNLOAD_PRIORITY,
                      headers=self.main_headers,
                      cookies=creds["cookie"],
                      body=urlencode(creds['body']))
        
        # pass request to the download to run it
        dfd = self._crawler.engine.download(req)

        # add callback after make these request
        dfd.addCallback(self._login_parse, request)

        # if has an error then handle the callback error
        dfd.addErrback(self._logerror, request)

        return dfd

    def _login_parse(self, resp, request):

        # check status of response
        if resp.status == 200 and resp.json().get("status", "fail") == "ok":

            # get cookies from response
            cookies = process_headers(resp)

            resp_cookies = {k: extract_value(cookies, f"{k}=") for k in self.main_cookies_keys}

            if resp_cookies.__len__() == 0:

                logger.debug(f"[LOGIN-RESPONSE-INSTAGRAM] Cookies: {cookies} ~ doesn't have any main cookies in response: {resp.__dict__}")
                return

            logged_cookies = {
                "ds_user_id": json_loads(resp.body)['userId'],
                **resp_cookies,
                **resp.meta.get('main_cookie', {})
            }
            
            request.headers.update(self.main_headers)
            request.cookies = logged_cookies
            
            try:
                # get all creds 
                with open(self.base_dir / self.creds_file_name, "r") as f:
                    all_creds = json_loads(f.read())

                # append last creds
                with open(self.base_dir / self.creds_file_name, "w") as f:
                    all_creds.update({
                        logged_cookies['ds_user_id']: logged_cookies
                    })
                    f.write(json_dumps(all_creds, indent=3))

            except Exception:

                # add first creds
                with open(self.base_dir / self.creds_file_name, "w") as f:
                    f.write(json_dumps({
                        logged_cookies['ds_user_id']: logged_cookies
                    }, indent=3))

            return
        
        logger.debug(f"[LOGIN-RESPONSE-INSTAGRAM] response fail: {resp.__dict__}")
        raise StopDownload()

    def _logerror(self, failure, request):
        logger.error(f"[INSTAGRAM-ERROR] failure: {failure.__dict__}, when login to instagram")
        raise StopDownload()
