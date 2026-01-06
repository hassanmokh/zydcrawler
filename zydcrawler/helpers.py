from json import loads as json_loads, dumps
import requests

def process_headers(response, extract="set-cookie"):
    '''
        extract headers from response object

        @extract: list / str / None
            - list: for extract more than one key
            - str: extract one key only
            - None: return all haeders
    '''

    headers = response.headers.to_unicode_dict()
    if isinstance(extract, list):
        return [ headers.get(i) for i in extract]
    
    elif isinstance(extract, str):
        return headers.get(extract)
    
    return response


def extract_value(string, key):

    value = ""

    for dt in string.split(";"):
        if key in dt:
            value = dt.split(key)[1]

    return value


def update_cookies(settings, response):
    base_dir = settings['BASE_DIR']
        
    file_name = settings['CREDS_HEADER_FILE_NAME']

    # get cookies from response
    cookies = process_headers(response)

    # get user_id form cookie
    ds_user_id = extract_value(cookies, "ds_user_id=")

    # check user_id is not empty
    if ds_user_id:

        # get all main cookies keys
        # to update each of them into stored sessions
        resp_cookies = {}

        for k in settings['MAIN_COOKIES_KEYS']:
            dt = extract_value(cookies, f"{k}=")
            if dt:
                resp_cookies.update({k: dt})

        # get all saved sessions
        with open(base_dir / file_name, "r") as f:
            all_creds = json_loads(f.read())

        # check user_id into the exist creds
        if ds_user_id in all_creds:
            all_creds[ds_user_id].update(**resp_cookies)

        # otherwise will create a new session with the incoming user
        else:
            all_creds.update({
                ds_user_id: resp_cookies
            })
        
        # save the updated session into the creds
        with open(base_dir / file_name, "w") as f:
            f.write(dumps(all_creds, indent=3))


def extract_instagram_page_data(response):

    # get all info about the page instagram
    script_page_data = response.xpath("//*[contains(text(), 'window._sharedData =')]").css("::text").extract_first()

    # get json data from variable script
    page_data = script_page_data.split("window._sharedData =")[1].replace("};", "}")

    # load json data to python dict
    json_data = json_loads(page_data)

    # get profile page from json
    profile_page_data = json_data.get("entry_data", {}).get("ProfilePage", [])

    if profile_page_data.__len__() == 0:
        return
    
    return profile_page_data[0]
    
def handle_request(url, data, headers, **kwargs):

    try:
        
        resp = requests.post(url, json=data, headers=headers, **kwargs)

        if resp.status_code not in [ 200, 201, 204]:
            return False, resp.text

    except (requests.ConnectionError,
            requests.ReadTimeout,
            requests.ConnectTimeout,
            requests.JSONDecodeError) as e:
        
        return False, str(e)
    
    return True, None