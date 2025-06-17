import os
import requests
from datetime import datetime
from collections import defaultdict

# 東京の座標
TOKYO_LAT = 35.6895
TOKYO_LON = 139.6917

API_URL = "https://api.open-meteo.com/v1/jma"

API_KEY = os.getenv("OPEN_METEO_API_KEY")  # 商用ユーザーでなければ不要
def fetch_tokyo_daily_open_meteo(
    forecast_days: int = 7,
    timezone: str = "Asia/Tokyo"
) -> list[dict]:
    """
    Open-Meteo JMA API で東京の「日別」予報を取得し、
    各日について平均気温・平均湿度・平均風速・降水量合計を返します。

    Parameters
    ----------
    forecast_days : int
        取得する予報日数（最大11）。デフォルトは5日。
    timezone : str
        タイムゾーン名。日付グルーピングの基準になる。

    Returns
    -------
    list of dict
        [
          {
            "date": "YYYY-MM-DD",
            "temp": float,       # 日平均気温(°C)
            "humidity": float,   # 日平均湿度(%)
            "wind_speed": float, # 日平均風速(m/s)
            "rain": float        # 日降水量合計(mm)
          },
          ...
        ]
    """
    params = {
        "latitude": TOKYO_LAT,
        "longitude": TOKYO_LON,
        "hourly": ",".join([
            "temperature_2m",
            "relativehumidity_2m",
            "windspeed_10m",
            "precipitation"
        ]),
        "forecast_days": forecast_days,
        "timezone": timezone,
        # 商用APIキーが必要な場合のみ
        # "apikey": API_KEY
    }

    resp = requests.get(API_URL, params=params)
    resp.raise_for_status()
    data = resp.json()

    # 時刻リストと各変数リストを取得
    times = data["hourly"]["time"]
    temps = data["hourly"]["temperature_2m"]
    hums  = data["hourly"]["relativehumidity_2m"]
    winds = data["hourly"]["windspeed_10m"]
    rains = data["hourly"]["precipitation"]

    # 日付ごとに集計用バケツを用意
    daily_bucket = defaultdict(lambda: {
        "temps": [], "hums": [], "winds": [], "rains": []
    })

    for t, tmp, hum, wnd, rn in zip(times, temps, hums, winds, rains):
        # "2025-06-17T03:00" → "2025-06-17"
        date_str = t.split("T", 1)[0]
        b = daily_bucket[date_str]
        b["temps"].append(tmp)
        b["hums"].append(hum)
        b["winds"].append(wnd)
        b["rains"].append(rn)

    # 辞書 → リストに変換＆平均・合計を計算
    result = []
    for i, (date, vals) in enumerate(sorted(daily_bucket.items())):
        if i >= forecast_days:
            break
        result.append({
            "date":      date,
            "temp":      sum(vals["temps"]) / len(vals["temps"]),
            "humidity":  sum(vals["hums"])  / len(vals["hums"]),
            "wind_speed":sum(vals["winds"])/ len(vals["winds"]),
            "rain":      sum(vals["rains"])
        })

    return result