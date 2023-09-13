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

    max_time_gap_outside = None
    max_time_gap_inside = None

    for i in range(1, len(data)):
        if data[i - 1][2] is True and data[i][2] is False:
            time_gap = data[i][1] - data[i - 1][1]
            if max_time_gap_outside is None or time_gap > max_time_gap_outside:
                max_time_gap_outside = time_gap

        if data[i - 1][2] is False and data[i][2] is True:
            time_gap = data[i][1] - data[i - 1][1]
            if max_time_gap_inside is None or time_gap > max_time_gap_inside:
                max_time_gap_inside = time_gap

    # Convert the max_time_gap to hours and minutes
    hours, remainder = divmod(max_time_gap_outside.total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)

    longest_cat_time_outside = f"{int(hours)} hours {int(minutes)} minutes"

    hours, remainder = divmod(max_time_gap_inside.total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)

    longest_cat_time_inside = f"{int(hours)} hours {int(minutes)} minutes"

    cat_stats = {"longest_time_outside": longest_cat_time_outside, "longest_time_inside": longest_cat_time_inside}
    print(cat_stats)

    return jsonify(cat_stats)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
