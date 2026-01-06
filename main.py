from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow
from werkzeug.utils import secure_filename
import subprocess, json, os, pandas as pd, re
from marshmallow import fields
from pathlib import Path
from flask_cors import CORS, cross_origin
from scrapy import spiderloader
from scrapy.utils import project
from datetime import datetime
import schedule, time

BASE_DIR = Path(__name__).resolve().parent

app = Flask(__name__)

ma = Marshmallow(app)
CORS(app, resources={r"*": {"origin": "*"}})

ALLOWED_EXTENSIONS = ['csv', 'xlsx', "xls"]
INSTAGRAM_RESTAURANTS_PATH = "media/uploads/instagram_restaurants"
COLUMNS_SHEET = ['Country', 'IG URL', 'Active', 'Direct Competitors', 'Food Aggregators']

# update config uploads
app.config['UPLOAD_INST_REST_FOLDER'] = f"{BASE_DIR}/{INSTAGRAM_RESTAURANTS_PATH}"

app.config['FOOD_AGGREGATOR'] = ['talabat', "elmenus"]

class CrawlSchema(ma.Schema):
    username = fields.Str(required=True)
    country = fields.Str(required=True)
    food_aggregator = fields.Str()
    direct_competitor = fields.Str()

    class Meta:
        fields = ("username", "country", "food_aggregator", "direct_competitor")

def get_spiders_names():
    settings = project.get_project_settings()
    spider_loader = spiderloader.SpiderLoader.from_settings(settings)
    return spider_loader.list()

crawlSchema = CrawlSchema()


# make schedule for zyda clients updates
# def zyda_clients_scheduler():
#     subprocess.Popen(["scrapy", "crawl", "zyda_clients"])

# schedule.every(28).day.at("00:00").do(zyda_clients_scheduler)

# while True:
#     schedule.run_pending()
#     time.sleep(518400)


@app.route('/scrape/instagram/recrawl', methods=['POST'])
@cross_origin()
def recrawl_instagram():
    
    try:
        data = request.json

    except Exception as e:
        return jsonify({"message": "invalid request data!"}), 400
    
    validate = crawlSchema.validate(data)

    if validate:
        return jsonify(validate), 400

    subprocess.Popen(["scrapy", "crawl", "instagram", "-a", f"recrawler={json.dumps(data)}"])

    return jsonify({"message": "successfully Recrawled"})


@app.route('/scrape/instagram/crawl')
@cross_origin()
def crawl_instagram():
    
    subprocess.Popen(["scrapy", "crawl", "instagram"])

    return jsonify({"message": "successfully Crawled"})

@app.route("/scrape/zyda_clients/crawl")
@cross_origin()
def crawl_zyda_clients():
    subprocess.Popen(["scrapy", "crawl", "zyda_clients"])

    return jsonify({"message": "successfully Crawled"})

@app.route("/scrape/food/aggregator/talabat/crawl")
@cross_origin()
def crawl_talabat():
    subprocess.Popen(["scrapy", "crawl", "talabat"])

    return jsonify({"message": "successfully Crawled"})

@app.route("/scrape/food/aggregator/elmenus/crawl")
@cross_origin()
def crawl_elmenus():
    subprocess.Popen(["scrapy", "crawl", "elmenus"])

    return jsonify({"message": "successfully Crawled"})

@app.route("/scrape/file/crawl", methods=['GET'])
@cross_origin()
def crawl_file_instagram():

    if 'filename' in request.args:
        
        path_name = f"{app.config['UPLOAD_INST_REST_FOLDER']}/{request.args['filename']}"
        
        if not os.path.exists(path_name):
            return jsonify({"message": "Please enter the correct filename"}), 400
        
        subprocess.Popen(["scrapy", "crawl", "instagram", "-a", f"file_path={path_name}"])

        return jsonify({"message": "crawling in progress"})
    
    return jsonify({"message": "invalid request!"}), 400

@app.route("/scrape/food/aggregator/crawl", methods=['GET'])
@cross_origin()
def crawl_food_aggregator():

    if 'url' in request.args:
        
        url = request.args['url']
        
        if not url.startswith("https://"):
            return jsonify({"message": "invalid request!"}), 400

        flag = False
        name = None

        for domain_name in app.config['FOOD_AGGREGATOR']:
            if domain_name in url:
                flag = True
                name = domain_name
                break
        
        if not flag:
            return jsonify({"message": "invalid request!"}), 400
        
        subprocess.Popen(["scrapy", "crawl", name, "-a", f"url={url}"])

        return jsonify({"message": "crawling in progress"})
    
    return jsonify({"message": "invalid request!"}), 400

@app.route("/files", methods=['GET'])
@cross_origin()
def list_files():
    if not os.path.exists(app.config["UPLOAD_INST_REST_FOLDER"]):
        os.makedirs(app.config["UPLOAD_INST_REST_FOLDER"])

    # list all files 
    return jsonify({"files": [{"name": file.rsplit(".", 1)[0], "extension": file} for file in os.listdir(app.config["UPLOAD_INST_REST_FOLDER"])]}), 200

@app.route("/files/upload", methods=['POST'])
@cross_origin()
def file_upload():

    def allowed_files(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    def validate_columns_names(file):
        if file.filename.rsplit(".", 1)[1] == 'csv':
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        incom_columns = df.columns.values.tolist()
        
        return all(col in incom_columns for col in COLUMNS_SHEET), df

    if 'file' not in request.files:
        return jsonify({"message": "please upload the file"}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({"message": "No file uploaded"}), 400
    
    if file and allowed_files(file.filename):

        filename = secure_filename(file.filename)

        path_name = f"{app.config['UPLOAD_INST_REST_FOLDER']}/{filename}"

        if os.path.exists(path_name):
            os.remove(path_name)

        if not os.path.exists(app.config["UPLOAD_INST_REST_FOLDER"]):
            os.makedirs(app.config["UPLOAD_INST_REST_FOLDER"])

        status, df = validate_columns_names(file)
        
        if not status:
            try:
                os.remove(path_name)

            except Exception:
                pass

            return jsonify({"message": f"The columns `{', '.join(COLUMNS_SHEET)}` should be in the file"}), 400
        
        if filename.rsplit(".", 1)[1] == "csv":
            df.to_csv(path_name)
        else:
            df.to_excel(path_name)

        return jsonify({'message': "Successfully uploaded"}), 201

    return jsonify({"message": "please upload file correctly"}), 400

@app.route("/files/delete", methods=['DELETE'])
@cross_origin()
def file_delete():

    if "filename" not in request.args:
        return jsonify({"message": "invalid request!"}), 400
    
    if not os.path.exists(f"{app.config['UPLOAD_INST_REST_FOLDER']}/{request.args['filename']}"):
        return jsonify({"message": "this file isn't found"}), 400
    
    try:
        os.remove(f"{app.config['UPLOAD_INST_REST_FOLDER']}/{request.args['filename']}")

        return jsonify({"message": "Successfully deleted!"}), 200
        
    except Exception:
        return jsonify({"message": "This file isn't found!"}), 400

@app.route("/crawler/status", methods=['GET'])
@cross_origin()
def crawler_status():

    if "crawl" not in request.args:
        return jsonify({"message": "invalid request!"}), 400

    spiders_names = get_spiders_names()

    crawl_name = request.args['crawl'].lower()

    if crawl_name not in spiders_names:
        return jsonify({"message": "invalid Data Sent!"}), 400
    
    path_file = BASE_DIR / f"logs/{crawl_name}.log"
    
    if not os.path.exists(path_file):
        return jsonify({"message": f"The {crawl_name} crawler isn't started yet!"}), 400

    with open(path_file, "r") as f:
        last_100_lines = " ======== ".join(f.readlines()[-100:])

    kwords_failure = ["CRITICAL", "TypeError", "Traceback", "request fail"]
    
    flag = False

    for k in kwords_failure:
        if k in last_100_lines:
            flag = True
            break

    if flag:
        return jsonify({"status": False}), 200
    
    return jsonify({"status": True}), 200

@app.route("/crawler/health", methods=['GET'])
@cross_origin()
def crawler_health():

    if "crawl" not in request.args:
        return jsonify({"message": "invalid request!"}), 400

    spiders_names = get_spiders_names()

    crawl_name = request.args['crawl'].lower()

    if crawl_name not in spiders_names:
        return jsonify({"message": "invalid Data Sent!"}), 400
    
    path_file = BASE_DIR / f"logs/{crawl_name}.log"
    
    if not os.path.exists(path_file):
        return jsonify({"message": f"The {crawl_name} crawler isn't started yet!"}), 400

    with open(path_file, "r") as f:
        last_line = " ".join(f.readlines()[-100:])
    
    dates = re.findall(r"(\d+-\d+-\d+ \d+:\d+:\d+)", last_line)

    last_date = dates[-1] if dates.__len__() > 0 else None

    if last_date:

        last_line_date = datetime.strptime(last_date, "%Y-%m-%d %H:%M:%S")

        date_now = datetime.now()

        if last_line_date.date() != date_now.date():
            return jsonify({"status": False}), 200

        if last_line_date.hour < date_now.hour:
            return jsonify({"status": False}), 200

        if last_line_date.minute < date_now.minute:
            return jsonify({"status": False}), 200
        
        return jsonify({"status": True}), 200

    return jsonify({"status": False}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5001)