import json
import os

import dotenv
import psycopg2
from flask import Flask, request

dotenv.load_dotenv()

app = Flask(__name__)


@app.route('/log-cat-status', methods=["POST"])
def log_cat_status():
    data = request.get_json()

    print(data)

    status = True if data["status"] == 1 else False
    timestamp = data["timestamp"]

    weather = json.loads(data["weather"])

    condition = weather["condition"]
    wind_bearing = weather["wind_bearing"]
    temperature = weather["temperature"]
    wind_speed = weather["wind_speed"]
    precipitation = weather["precipitation"]
    humidity = weather["humidity"]

    with psycopg2.connect(
            "dbname='postgres' user='postgres' host='192.168.1.72' password=%s" % (os.getenv("DB_PASS"))) as conn:
        with conn.cursor() as cursor:
            sql = " insert into public.cat_flap_history" \
                  "(timestamp, outside, condition, wind_bearing, temperature, wind_speed, precipitation, humidity)" \
                  "values (%s, %s, %s, %s, %s, %s, %s, %s)"

            query_data = (timestamp, status, condition, wind_bearing, temperature, wind_speed, precipitation, humidity)

            cursor.execute(sql, query_data)
            conn.commit()

    return [x for x in query_data]


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
