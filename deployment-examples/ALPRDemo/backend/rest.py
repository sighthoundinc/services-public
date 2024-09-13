from flask import Flask, request, jsonify, send_file, g
import sqlite3
import io
import os
import time
import json
import uuid
import traceback
from Database import LicensePlate, LicensePlateDB
from datetime import datetime
from threading import Lock, local
from MCP import MCPClient


#========================================================================
class CacheStore:
    def __init__(self, factory_method, param1=None):
        """
        Initialize the CachedObject with a factory method and optional parameters.

        :param factory_method: A callable that generates the cached object.
        :param param1: Optional parameter 1 for the factory method.
        :param param2: Optional parameter 2 for the factory method.
        :param param3: Optional parameter 3 for the factory method.
        """
        self._thread_local = local()
        self._thread_local.cache = None
        self._factory_method = factory_method
        self._param1 = param1

    def get(self):
        """
        Retrieve the cached object, creating it using the factory method if necessary.

        :return: The cached object.
        """
        if not hasattr(self._thread_local, 'cache'):
            if self._param1 is None:
                self._thread_local.cache = self._factory_method()
            else:
                self._thread_local.cache = self._factory_method(self._param1)
        return self._thread_local.cache




app = Flask(__name__)

gDBCache = CacheStore(LicensePlateDB, os.environ.get("DB_PATH", "/data/sighthound/db/lpdb.sqlite"))


#========================================================================
gUploadCache = {}
gUploadCacheMtx = Lock()

def get_upload_cache_entry(id):
    with gUploadCacheMtx:
        return gUploadCache.get(id, None)

def set_upload_cache_entry(id,value):
    with gUploadCacheMtx:
        gUploadCache[id] = value

#========================================================================
def convert_to_epoch(date_str, time_str):
    # Combine date and time strings into a single datetime string
    datetime_str = f"{date_str} {time_str}"

    # Parse the combined string into a datetime object
    dt = datetime.strptime(datetime_str, "%Y%m%d %H%M")

    # Convert the datetime object to an epoch timestamp
    epoch_timestamp = int(dt.timestamp())

    return epoch_timestamp

#========================================================================
# Establish a global database connection
def get_db():
    return gDBCache.get()

#========================================================================
# Establish a global MCP client object
def create_mcp():
    # Create MCP Client
    mcp_conf = {}
    mcp_conf["host"] = os.environ.get("MCP_HOST", "mcp_svc")
    mcp_conf["port"] = os.environ.get("MCP_PORT", 9097)
    mcp_conf["username"] = os.environ.get("MCP_USERNAME", None)
    mcp_conf["password"] = os.environ.get("MCP_PASSWORD", None)
    mcp = MCPClient(mcp_conf)
    return mcp

gMCPCache = CacheStore(create_mcp)

def get_mcp():
    return gMCPCache.get()

#========================================================================
def plates_between_times(start_time, end_time):
    db = get_db()
    plates = db.get_by_time_range(start_time, end_time)
    plates_as_dicts = [obj.to_dict() for obj in plates]
    return jsonify(plates_as_dicts)

#========================================================================
@app.route('/plates/bytimeanddate/<string:startdate>/<string:startime>', methods=['GET'])
@app.route('/plates/bytimeanddate/<string:startdate>/<string:startime>/<string:enddate>/<string:endtime>', methods=['GET'])
def get_plates_between(startdate, starttime, enddate=None, endtime=None):
    start_time = convert_to_epoch(startdate, starttime)
    if not enddate is None:
        end_time = convert_to_epoch(enddate, endtime)
    else:
        end_time = int(time.time())
    return plates_between_times(start_time, end_time)

#========================================================================
@app.route('/plates/latest', methods=['GET'])
@app.route('/plates/latest/<int:count>', methods=['GET'])
def get_latest_plates(count=10):
    db = get_db()
    plates = db.get_most_recent(count)
    plates_as_dicts = [obj.to_dict() for obj in plates]
    return jsonify(plates_as_dicts)

#========================================================================
@app.route('/plates/search', methods=['GET'])
@app.route('/plates/search/<string:startdate>/<string:startime>', methods=['GET'])
@app.route('/plates/search/<string:startdate>/<string:startime>/<string:enddate>/<string:endtime>', methods=['GET'])
def get_plates_matching(startdate=None, starttime=None, enddate=None, endtime=None):
    start_time = None
    end_time = None
    if not startdate is None:
        start_time = convert_to_epoch(startdate, starttime)
        if not enddate is None:
            end_time = convert_to_epoch(enddate, endtime)
        else:
            end_time = int(time.time())
    search_term = request.args.get('plate')
    search_term = search_term.replace('*','%').replace('?','_')
    db = get_db()
    plates = db.get_by_plate_string(search_term, start_time, end_time)
    plates_as_dicts = [obj.to_dict() for obj in plates]
    return jsonify(plates_as_dicts)

#========================================================================
@app.route('/plates/image/<string:source_id>', methods=['GET'])
def get_image(source_id):
    image_id = request.args.get('id')
    img_data = get_mcp().get_image(source_id, image_id, "source")

    if not img_data is None:
        return send_file(
            io.BytesIO(img_data),
            mimetype='image/jpeg',
            as_attachment=False
        )
    else:
        return jsonify({"error": "Image not found"}), 404



#========================================================================
# Route to upload a file
ALLOWED_EXTENSIONS = [ 'jpeg', 'webp', 'bmp', 'jpg', 'png', 'mp4', 'mkv', 'ts' ]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/folderwatch/upload/<string:region>', methods=['POST'])
def upload_file(region):
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    if region != 'eu' and region != 'us':
        return jsonify({'error': 'Invalid region'}), 400

    file = request.files['file']

    # If the user does not select a file
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    # Generate a unique filename using UUID and retain the file extension
    id = uuid.uuid4()
    ext = os.path.splitext(file.filename)[1]
    filename = f"{id}{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], region, filename)

    # Save the file
    file.save(filepath)
    set_upload_cache_entry(f"{id}", (region, filename))

    return jsonify({'message': 'File successfully uploaded', 'filename': filename, 'id' : id}), 200

#========================================================================
# Check processing status
@app.route('/folderwatch/status/<string:upload_id>', methods=['GET'])
def upload_status(upload_id):
    fm = get_upload_cache_entry(upload_id)
    if fm is None:
        print(f"Upload id {upload_id} isn't found. Uploads:")
        return jsonify({'error': 'Invalid upload id'}), 400

    region, filename = fm
    pathUploaded = os.path.join(app.config['UPLOAD_FOLDER'], region, filename)
    if os.path.isfile(pathUploaded):
        return jsonify({'status': 'pending' }), 200
    pathProcessed = os.path.join(app.config['UPLOAD_FOLDER'], region, 'processed', filename + ".json")
    if os.path.isfile(pathProcessed):
        with open(pathProcessed, 'r') as f:
            result_data = json.load(f)
        return jsonify({'status': 'completed', 'result':result_data }), 200

    print(f"File {pathUploaded} or {pathProcessed} isn't found.")
    return jsonify({'error': 'File not found'}), 400

#========================================================================
# Get result

if __name__ == '__main__':
    port = int(os.getenv("REST_PORT", 5000))
    host = os.getenv("REST_HOST", '0.0.0.0')
    app.config['UPLOAD_FOLDER'] = os.getenv("UPLOAD_FOLDER", '/data/folder-watch-input')
    try:
        print(f"Running REST provider on {host}:{port}")
        app.run(host=host, port=port, debug=True)
    except:
        print(f"{traceback.format_exc()}")
        raise
