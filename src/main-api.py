from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from bson.json_util import dumps
import json
from dotenv import load_dotenv
import os
import flask_monitoringdashboard as dashboard

# --- CONFIGURATION ---
load_dotenv()
DATABASE_TOKEN = os.getenv('DATABASE_TOKEN')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_IP = os.getenv('DATABASE_IP')
DATABASE_USER = os.getenv('DATABASE_USER')

app = Flask(__name__)
app.config["MONGO_URI"] = f"mongodb://{DATABASE_USER}:{DATABASE_TOKEN}@{DATABASE_IP}:27017/{DATABASE_NAME}?directConnection=true&serverSelectionTimeoutMS=2000&authSource={DATABASE_NAME}"
mongo = PyMongo(app)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["10 per second"],
    storage_uri="memory://", 
)

# --- UTILITIES ---
def parse_json(data):
    """Converts MongoDB BSON objects (like ObjectIds) to standard JSON."""
    return json.loads(dumps(data))

def paginate_query(collection, query=None, projection=None):
    """Scaffolding that allows any query to paginate."""
    if query is None:
        query = {}
        
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        if page < 1: 
            page = 1
        if per_page > 100: 
            per_page = 100 
    except ValueError:
        return jsonify({"error": "Pagination parameters must be integers"}), 400

    skip = (page - 1) * per_page

    if projection:
        cursor = collection.find(query, projection).sort([("_id", -1)]).skip(skip).limit(per_page)
    else:
        cursor = collection.find(query).sort([("_id", -1)]).skip(skip).limit(per_page)
        
    results = parse_json(cursor)
    
    return jsonify({
        "page": page,
        "per_page": per_page,
        "results": results,
        "count": len(results)
    })

# --- API ENDPOINTS ---

@app.route('/api/v1/users/<int:acid>', methods=['GET'])
def get_account(acid):
    """
    Returns a specific account by its exact Account ID (acid).
    """
    # Use find_one_or_404 to ensure a proper error if the acid doesn't exist
    print(acid)
    account = mongo.db.users.find_one_or_404({"accountID": acid})
    return jsonify(parse_json(account))

@app.route('/api/v1/users/<int:acid>/events', methods=['GET'])
@limiter.limit("5 per second")
def get_account_events(acid):
    """Returns just the events array for a specific account."""
    account = mongo.db.users.find_one_or_404({"accountID": acid}, {"events": 1, "_id": 0})
    return jsonify(parse_json(account))

@app.route('/api/v1/online', methods=['GET'])
def get_online():
    """Returns a paginated list of all currently online accounts."""
    return paginate_query(mongo.db.users, {"Online": True})

@app.route('/api/v1/search', methods=['GET'])
def search_callsign():
    """
    Returns a paginated list of accounts matching a callsign.
    Searches both current and past callsigns.
    """
    callsign = request.args.get('callsign')
    
    if not callsign:
        return jsonify({"error": "Missing 'callsign' query parameter"}), 400
        
    query = {
        "$or": [
            {"currentCallsign": callsign},
            {"pastCallsigns": callsign}
        ]
    }
    
    return paginate_query(mongo.db.users, query)

dashboard.bind(app)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5011)