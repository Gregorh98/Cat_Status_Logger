import json
import os

import dotenv
import psycopg2
from flask import Flask, request, jsonify

dotenv.load_dotenv()

app = Flask(__name__)


@app.route('/cat-status/log/add-cat-status', methods=["POST"])
def log_cat_status():
    data = str(request.get_json()).replace("'", "\"").replace("\"{", "{").replace("}\"", "}")

    print(data)

    data = json.loads(data)

    status = True if data["status"] == "1" else False
    timestamp = data["timestamp"]

    weather = data["weather"]

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


@app.route('/cat-status/log/manual-correction', methods=["POST"])
def log_cat_status_manual_correction():
    data = str(request.get_json()).replace("'", "\"").replace("\"{", "{").replace("}\"", "}")
    print(data)
    data = json.loads(data)

    status = True if data["status"] == "1" else False

    with psycopg2.connect(
            "dbname='postgres' user='postgres' host='192.168.1.72' password=%s" % (os.getenv("DB_PASS"))) as conn:
        with conn.cursor() as cursor:
            sql = "update public.cat_flap_history set outside = %s where id = (select max(id) from public.cat_flap_history);"

            query_data = (status,)

            cursor.execute(sql, query_data)
            conn.commit()

    return [x for x in query_data]


@app.route('/cat-status/stats', methods=["GET"])
def get_stats():
    with psycopg2.connect(
            "dbname='postgres' user='postgres' host='192.168.1.72' password=%s" % (os.getenv("DB_PASS"))) as conn:
        with conn.cursor() as cursor:
            sql = "select * from public.cat_flap_history order by timestamp asc"

            cursor.execute(sql)
            data = cursor.fetchall()

    max_time_gap = None
    start_time = None
    end_time = None

    for i in range(1, len(data)):
        if data[i - 1][2] is True and data[i][2] is False:
            time_gap = data[i][1] - data[i - 1][1]
            if max_time_gap is None or time_gap > max_time_gap:
                max_time_gap = time_gap
                start_time = data[i - 1][1]
                end_time = data[i][1]

    # Convert the max_time_gap to hours and minutes
    hours, remainder = divmod(max_time_gap.total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)

    longest_cat_time = f"{int(hours)} hours {int(minutes)} minutes"

    """
    print("The greatest time gap between two records with True and False in the third column is:", longest_cat_time)
    if start_time and end_time:
        print("Start time:", start_time.strftime('%Y-%m-%d %H:%M:%S'))
        print("End time:", end_time.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        print("No matching records found.")
    """

    cat_stats = {"longest_time": longest_cat_time}

    return jsonify(cat_stats)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
