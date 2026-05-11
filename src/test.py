from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def test_route():
    return jsonify({
        "status": "success",
        "message": "Routing to gms-admin.net is functional",
        "port": 5011
    }), 200

if __name__ == '__main__':
    # Binding to 0.0.0.0 ensures it listens on all interfaces
    app.run(host='0.0.0.0', port=5011)