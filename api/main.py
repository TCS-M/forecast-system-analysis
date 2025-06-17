from fastapi import FastAPI
from typing import Optional
import pandas as pd
from datetime import datetime

app = FastAPI()

# CSV読み込み（必要に応じてパスを修正）
df = pd.read_csv("../data/onehot.csv")
df['日付'] = pd.to_datetime(df['日付'])
df = df.fillna(0)  # 欠損があっても動くように

@app.get("/api/history")
def get_history(date: Optional[str] = None):
    if date is None:
        return {"error": "date parameter is required."}

    try:
        target_date = pd.to_datetime(date)
    except:
        return {"error": "Invalid date format."}

    filtered_df = df[df['日付'] == target_date]

    if filtered_df.empty:
        return {}

    record = filtered_df.iloc[0].to_dict()

    # 日付を文字列に戻す
    record['日付'] = record['日付'].strftime("%Y-%m-%d")

    return record
