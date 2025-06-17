import datetime
import pandas as pd


def make_feature_row(day_data: dict) -> dict:
    """
    与えられた日別データから特徴量行を生成します。

    Parameters
    ----------
    day_data : dict
        {
            "date": "YYYY-MM-DD",
            "temp": float,
            "humidity": float,
            "wind_speed": float,
            "rain": float
        }
    Returns
    -------
    dict
        {
            "降水量": float,
            "平均気温": float,
            "平均湿度": float,
            "平均風速": float,
            "weekday_月": 0 or 1,
            ...
            "weekday_日": 0 or 1
        }
    """
    # 日付文字列を datetime へ変換
    date_str = day_data.get("date")
    if date_str:
        # ISOフォーマット "YYYY-MM-DD" をパース
        dt = datetime.datetime.fromisoformat(date_str)
    else:
        # UNIX timestamp からの場合
        dt = datetime.datetime.fromtimestamp(day_data.get("dt", 0))

    # 基本特徴量
    row = {
        "降水量": day_data.get("rain", 0.0),
        "平均気温": day_data.get("temp", 0.0),
        "平均湿度": day_data.get("humidity", 0.0),
        "平均風速": day_data.get("wind_speed", 0.0),
    }

    # 曜日ワンホット (datetime.weekday(): 月=0, ... 日=6)
    labels = ["weekday_月", "weekday_火", "weekday_水", "weekday_木", "weekday_金", "weekday_土", "weekday_日"]
    for idx, label in enumerate(labels):
        row[label] = 1 if dt.weekday() == idx else 0

    return row


def make_feature_df(forecast_days: list[dict]) -> pd.DataFrame:
    """
    複数の日別データをまとめて DataFrame 化します。

    Parameters
    ----------
    forecast_days : list of dict
        make_feature_row に渡せる日別データのリスト

    Returns
    -------
    pandas.DataFrame
        特徴量行が並んだ DataFrame
    """
    rows = [make_feature_row(d) for d in forecast_days]
    return pd.DataFrame(rows)
