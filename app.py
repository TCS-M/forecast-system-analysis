import os
import onnxruntime as ort
import pandas as pd
from fastapi import FastAPI, HTTPException
import numpy as np

from utils.weather import fetch_tokyo_daily_open_meteo
from utils.features import make_feature_df

# モデルファイルのパスは環境変数から取得
ONNX_PATH = os.getenv("MODEL_PATH", "models/stack_sales_model.onnx")

# ONNX ランタイムを初期化（起動時一度だけ）
ort_sess = ort.InferenceSession(ONNX_PATH)
# 入力名は ONNX ファイル中の最初の input を使う
input_name = ort_sess.get_inputs()[0].name

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
    except Exception as e:
        raise HTTPException(
           status_code=500,
           detail=f"ONNX 推論に失敗しました: {e}"
       )

    # レスポンス整形
    predictions = [
        {"date": entry["date"], "forecast": float(pred)}
        for entry, pred in zip(weather_data, preds)
    ]

    return {"predictions": predictions}
