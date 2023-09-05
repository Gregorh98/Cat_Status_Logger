from flask import Flask, request

app = Flask(__name__)

@app.route('/log-cat-status', methods=["POST"])
def log_cat_status():
    data = request.get_json()
    print(data["status"])
    print(data["timestamp"])


if __name__ == '__main__':
   app.run()