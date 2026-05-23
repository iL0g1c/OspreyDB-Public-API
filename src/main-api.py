from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from bson.json_util import dumps
import json
from dotenv import load_dotenv
import os
import flask_monitoringdashboard as dashboard
from datetime import datetime
import re

# --- CONFIGURATION ---
load_dotenv()
DATABASE_TOKEN = os.getenv('DATABASE_TOKEN')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_IP = os.getenv('DATABASE_IP')
DATABASE_USER = os.getenv('DATABASE_USER')
DASHBOARD_TOKEN = os.getenv('DASHBOARD_TOKEN')

app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)
app.config["MONGO_URI"] = f"mongodb://{DATABASE_USER}:{DATABASE_TOKEN}@{DATABASE_IP}:27017/{DATABASE_NAME}?directConnection=true&serverSelectionTimeoutMS=2000&authSource={DATABASE_NAME}"
mongo = PyMongo(app)

def get_cloudflare_ip():
    return request.headers.get("CF-Connecting-IP", request.remote_addr)

limiter = Limiter(
    key_func=get_cloudflare_ip,
    app=app,
    application_limits=["10 per second"], 
    storage_uri="memory://", 
)

# --- UTILITIES ---
def parse_json(data):
    """Converts MongoDB BSON objects (like ObjectIds) to standard JSON."""
    return json.loads(dumps(data))

def paginate_query(collection, query=None, projection=None):
    """Paginates through a collection of documents."""
    if query is None:
        query = {}
        
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        if page < 1: page = 1
        if per_page < 1: per_page = 1
        if page > 1000000: page = 1000000
        if per_page > 100: per_page = 100 
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

def paginate_document_array(collection, query, array_field):
    """Paginates a massive array inside a single document using $slice."""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50)) # Default 50 for events
        
        if page < 1: page = 1
        if per_page < 1: per_page = 1
        elif per_page > 100: per_page = 100 
    except ValueError:
        return jsonify({"error": "Pagination parameters must be integers"}), 400

    skip = (page - 1) * per_page

    document = collection.find_one_or_404(
        query, 
        {array_field: {"$slice": [skip, per_page]}, "_id": 0}
    )
    
    # Extract the array from the document, defaulting to empty list if it doesn't exist
    results = parse_json(document).get(array_field, [])
    
    return jsonify({
        "page": page,
        "per_page": per_page,
        "results": results,
        "count": len(results)
    })


# --- V1 API ENDPOINTS ---

@app.route('/api/v1/users/<int:acid>', methods=['GET'])
def get_account(acid):
    """
    Returns a specific account by its exact Account ID (acid).
    """
    # Use find_one_or_404 to ensure a proper error if the acid doesn't exist
    account = mongo.db.users.find_one_or_404({"accountID": acid})
    return jsonify(parse_json(account))

@app.route('/api/v1/users/<int:acid>/events', methods=['GET'])
@limiter.limit("5 per second")
def get_account_events(acid):
    """Returns just the events array for a specific account."""
    return paginate_document_array(mongo.db.users, {"accountID": acid}, "events")

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

# --- V2 API ENDPOINTS ---
@app.route('/api/v2/events/filter', methods=['GET'])
def get_filtered_events():
    """Filter any event by a aggregation pipeline server side."""

    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        if page < 1: page = 1
        if per_page < 1: per_page = 1
        if page > 1000000: page = 1000000
        if per_page > 100: per_page = 100 
    except ValueError:
        return jsonify({"error": "Pagination parameters must be integers"}), 400
    
    skip = (page - 1) * per_page

    acid = request.args.get('acid', type=int)
    event_type =request.args.get('event_type', default='all')
    after_date_str = request.args.get('after')
    before_date_str = request.args.get('before')

    pipeline = []

    # Stage 1: Initial Match
    if acid is not None:
        pipeline.append({"$match": {"accountID": acid}})

    # Stage 2: Unwind the array so we can filter individual events
    pipeline.append({"$unwind": "$events"})

    # Stage 3: Event-Level Match
    event_match = {}
    
    if event_type and event_type.lower() != "all":
        if event_type.lower() == "on-off":
            event_match["events.eventType"] = {"$in": ["online", "offline"]}
        else:
            event_match["events.eventType"] = event_type

    if after_date_str or before_date_str:
        event_match["events.timestamp"] = {}
        if after_date_str:
            event_match["events.timestamp"]["$gte"] = datetime.fromisoformat(after_date_str)
        if before_date_str:
            event_match["events.timestamp"]["$lte"] = datetime.fromisoformat(before_date_str)

    if event_match:
        pipeline.append({"$match": event_match})

    # Stage 4: Sort (Descending)
    pipeline.append({"$sort": {"events.timestamp": -1}})

    # Stage 5: Paginate
    pipeline.append({
        "$facet": {
            "metadata": [{"$count": "total"}],
            "data": [
                {"$skip": skip},
                {"$limit": per_page},
                {
                    "$project": {
                        "_id": 0,
                        "accountID": 1,
                        "event": "$events"
                    }
                }
            ]
        }
    })

    cursor = list(mongo.db.users.aggregate(pipeline))

    total_count = cursor[0]["metadata"][0]["total"] if cursor[0]["metadata"] else 0
    results = cursor[0]["data"]

    return jsonify({
        "page": page,
        "per_page": per_page,
        "count": total_count,
        "results": parse_json(results)
    })

@app.route('/api/v2/users/', methods=['GET'])
def get_account_v2():
    """
    Returns a specific account by its exact Account ID (acid).
    """
    acid = request.args.get('acid', type=int)
    # Use find_one_or_404 to ensure a proper error if the acid doesn't exist
    account = mongo.db.users.find_one_or_404({"accountID": acid})
    return jsonify(parse_json(account))

@app.route('/api/v2/callsign-cross-check', methods=['GET'])
def get_callsign_cross_check():
    """
    Cross account callsign similarity pairing.
    Calculates seed documents, extracts callsigns, and paginates through matches.
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        if page < 1: page = 1
        if per_page < 1: per_page = 1
        if page > 1000000: page = 1000000
        if per_page > 100: per_page = 100 
    except ValueError:
        return jsonify({"error": "Pagination parameters must be integers"}), 400
    
    skip = (page - 1) * per_page

    acid = request.args.get('acid', type=int)
    pattern = request.args.get('pattern')

    if not acid and not pattern:
        return jsonify({"error": "Must provide 'acid' or 'pattern'"}), 400
    
    # Stage 1: Build seed query to find initial accounts
    seed_query = {}
    if acid:
        seed_query["accountID"] = acid
    elif pattern:
        # Parse the input for slashes and valid MongoDB flags (i, m, x, s)
        match = re.match(r'^/(.+)/([a-z]*)$', pattern)
        if match:
            core_pattern, flags = match.group(1), match.group(2)
        else:
            core_pattern, flags = pattern, ""
            
        valid_mongo_flags = set("imxs")
        safe_flags = "".join(f for f in flags if f in valid_mongo_flags)
        
        regex_query = {"$regex": core_pattern}
        if safe_flags:
            regex_query["$options"] = safe_flags

        seed_query["pastCallsigns"] = regex_query

    # Fetch seed documents (limit execution time if pattern matching)
    cursor = mongo.db.users.find(seed_query)
    if pattern:
        cursor = cursor.max_time_ms(2000)
        
    seed_documents = list(cursor)

    # Stage 2: Extract mapping of seed callsigns to their ACIDs
    seed_callsigns = set()
    seed_cs_to_acids = {}
    seed_account_ids = set()

    for doc in seed_documents:
        _acid = doc.get("accountID")
        if _acid is not None:
            seed_account_ids.add(_acid)

        for cs in doc.get("pastCallsigns", []):
            if isinstance(cs, str) and cs.strip():
                cs_stripped = cs.strip()
                seed_callsigns.add(cs_stripped)
                
                if cs_stripped not in seed_cs_to_acids:
                    seed_cs_to_acids[cs_stripped] = set()
                if _acid is not None:
                    seed_cs_to_acids[cs_stripped].add(_acid)

    # If the seed accounts yielded no callsigns, short-circuit
    if not seed_callsigns:
        return jsonify({
            "page": page,
            "per_page": per_page,
            "count": 0,
            "results": []
        })
    
    # Stage 3: Build query for second generation matching accounts
    query = {
        "pastCallsigns": {"$in": list(seed_callsigns)}
    }
    if seed_account_ids:
        query["accountID"] = {"$nin": list(seed_account_ids)}

    # Stage 4: Paginate and format the final matched accounts
    total_count = mongo.db.users.count_documents(query)
    second_gen_cursor = mongo.db.users.find(query).skip(skip).limit(per_page)
    
    results = []
    for doc in second_gen_cursor:
        past = [cs for cs in doc.get("pastCallsigns", []) if isinstance(cs, str) and cs.strip()]
        matched = [cs for cs in past if cs in seed_callsigns]
        
        if matched:
            matched_details = []
            for cs in matched:
                acids = sorted(list(seed_cs_to_acids.get(cs, set())))
                if acids:
                    matched_details.append(f"{cs} (seed ACID(s): {', '.join(map(str, acids))})")
                else:
                    matched_details.append(cs)
                    
            results.append({
                "accountID": doc.get('accountID'),
                "currentCallsign": doc.get('currentCallsign'),
                "matchedDetails": matched_details
            })

    return jsonify({
        "page": page,
        "per_page": per_page,
        "count": total_count,
        "results": results
    })
@app.route('/api/v2/events/earliest', methods=['GET'])
def earliest_event():
    """
    Returns the earliest event.
    """
    acid = request.args.get('acid', type=int)

    if not acid:
        return jsonify({"error": "Missing 'acid' parameter"}), 400
    
    pipeline = [
        {"$match": {"accountID": acid}},
        {"$unwind": "$events"},
        {"$sort": {"events.timestamp": 1}},
        {"$limit": 1},
        {"$project": {
            "_id": 0, 
            "event": "$events"
        }}
    ]

    cursor = list(mongo.db.users.aggregate(pipeline))
    if not cursor:
        return jsonify({"error": "No events found for this account"}), 404
    
    return jsonify(parse_json(cursor[0]))

@app.route('/api/v2/users/search', methods=['GET'])
def search_users_v2():
    """
    Search accounts by exact pastCallsign or regex pattern.
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        if page < 1: page = 1
        if per_page < 1: per_page = 1
    except ValueError:
        return jsonify({"error": "Pagination parameters must be integers"}), 400

    skip = (page - 1) * per_page

    exact_callsign = request.args.get('exact_callsign')
    pattern = request.args.get('pattern')

    if not exact_callsign and not pattern:
        return jsonify({"error": "Must provide 'exact_callsign' or 'pattern'"}), 400

    query = {}
    
    if exact_callsign:
        query = {
            "pastCallsigns": {
                "$elemMatch": {
                    "$regex": f"^{re.escape(exact_callsign)}$",
                    "$options": "i"
                }
            }
        }
    elif pattern:
        # Parse regex flags
        match = re.match(r'^/(.+)/([a-z]*)$', pattern)
        if match:
            core_pattern, flags = match.group(1), match.group(2)
        else:
            core_pattern, flags = pattern, ""
            
        valid_mongo_flags = set("imxs")
        safe_flags = "".join(f for f in flags if f in valid_mongo_flags)
        
        regex_query = {"$regex": core_pattern}
        if safe_flags:
            regex_query["$options"] = safe_flags

        query = {"pastCallsigns": regex_query}

    # Fetch data
    total_count = mongo.db.users.count_documents(query)
    cursor = mongo.db.users.find(query).skip(skip).limit(per_page)
    
    if pattern:
        cursor = cursor.max_time_ms(2000)
        
    results = parse_json(list(cursor))

    return jsonify({
        "page": page,
        "per_page": per_page,
        "count": total_count,
        "results": results
    })

dashboard.config.security_token = DASHBOARD_TOKEN
# dashboard.bind(app)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5011)