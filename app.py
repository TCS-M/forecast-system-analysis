import os
import glob
import onnxruntime as ort
import pandas as pd
from fastapi import FastAPI, HTTPException
import numpy as np

from utils.weather import fetch_tokyo_daily_open_meteo
from utils.features import make_feature_df

# モデルファイルのパスは環境変数から取得
ONNX_PATH = os.getenv("MODEL_PATH", "models/stack_sales_model.onnx")
MODEL_DIR = os.getenv("MODEL_DIR", "models/onnx")

# ONNX ランタイムを初期化（起動時一度だけ）
ort_sess = ort.InferenceSession(ONNX_PATH)
# 入力名は ONNX ファイル中の最初の input を使う
input_name     = ort_sess.get_inputs()[0].name
# ONNX ランタイムを初期化（各ビール銘柄モデル） ← 追加
beer_sessions     = {}
beer_input_names  = {}
for path in glob.glob(os.path.join(MODEL_DIR, "sales_forecast_*.onnx")):
    beer = os.path.splitext(os.path.basename(path))[0].replace("sales_forecast_", "")
    sess = ort.InferenceSession(path)
    beer_sessions[beer]    = sess
    beer_input_names[beer] = sess.get_inputs()[0].name

# FastAPI アプリケーション定義
app = FastAPI(
    title="Beer Sales Forecast API",
    description="東京の日別天気予報を元にビール売上を予測します。",
    version="1.0"
)

@app.get("/forecast")
def get_forecast(days: int = 7):
    """
    東京の過去/未来 days 日分の売上予測を返します。

    Parameters
    ----------
    days : int, optional
        予測日数 (1〜11), デフォルトは7
    """
    if days < 1 or days > 11:
        raise HTTPException(
            status_code=400,
            detail="days パラメータは 1〜11 の範囲で指定してください。"
        )

    # 天気データ取得
    weather_data = fetch_tokyo_daily_open_meteo(forecast_days=days)

    # 特徴量生成
    df = make_feature_df(weather_data)

    # 予測
    X = df.values.astype(np.float32)
    try:
        preds = ort_sess.run(None, {input_name: X})[0]
        total_preds = preds  # Define total_preds using the main ONNX model predictions
    except Exception as e:
        raise HTTPException(
           status_code=500,
           detail=f"ONNX 推論に失敗しました: {e}"
       )
    # 2) 各ビール銘柄モデルで予測 ← 追加
    beer_preds = {}
    for beer, sess in beer_sessions.items():
        try:
            beer_preds[beer] = sess.run(
                None, {beer_input_names[beer]: X}
            )[0]
        except Exception as e:
            raise HTTPException(500, f"{beer} モデル推論失敗: {e}")
    # 3) レスポンス整形
    weekday_map = {0:"月", 1:"火", 2:"水", 3:"木", 4:"金", 5:"土", 6:"日"}
    predictions = []

    for i, entry in enumerate(weather_data):
        date_str = entry["date"]
        wd       = pd.to_datetime(date_str).weekday()
        wd_jp    = weekday_map[wd]

        item = {
            "date":    date_str,
            "weekday": wd_jp,
        }

        if wd_jp == "日":
            # 日曜日は全て NaN
            item["total"] = None
            for beer in beer_sessions:
                item[beer] = None
        else:
            item["total"] = float(total_preds[i])
            for beer, preds in beer_preds.items():
                item[beer] = float(preds[i])

        predictions.append(item)

    return {"predictions": predictions}