from fastapi import FastAPI, HTTPException, Depends
from typing import Optional
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

import models

# FastAPI インスタンスは1回だけ
app = FastAPI()

# --- 実績・天気データ表示API ---
# CSV読み込み（必要に応じてパスを修正）
df = pd.read_csv("../data/onehot2.csv")
df['日付'] = pd.to_datetime(df['日付'])
df = df.fillna(0)  # 欠損があっても動くように

@app.get("/api/history")
def get_history(date: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None):
    # ① 特定の日付
    if date:
        try:
            target_date = pd.to_datetime(date)
            filtered_df = df[df['日付'] == target_date]
            if filtered_df.empty:
                return {"message": "データが見つかりません"}
            record = filtered_df.iloc[0].to_dict()
            record['日付'] = record['日付'].strftime("%Y-%m-%d")
            return record
        except:
            return {"error": "日付形式が不正です（YYYY-MM-DD）"}

    # ② 期間指定（start〜end）
    elif start and end:
        try:
            start_date = pd.to_datetime(start)
            end_date = pd.to_datetime(end)
            filtered_df = df[(df['日付'] >= start_date) & (df['日付'] <= end_date)]
            if filtered_df.empty:
                return {"message": "指定期間のデータがありません"}
            result = filtered_df.copy()
            result['日付'] = result['日付'].dt.strftime("%Y-%m-%d")
            return result.to_dict(orient="records")
        except:
            return {"error": "start/end の日付形式が不正です（YYYY-MM-DD）"}

    # ③ 全件表示（パラメータ無し）
    else:
        result = df.copy()
        result['日付'] = result['日付'].dt.strftime("%Y-%m-%d")
        return result.to_dict(orient="records")


# --- DB保存API ---
models.Base.metadata.create_all(bind=engine)  # DBテーブルを自動作成

# DBセッションを作る関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# POSTでデータを保存
@app.post("/api/save_data")
def save_data_from_api(payload: dict, db: Session = Depends(get_db)):
    try:
        name = payload["product_name"]
        price = payload["price"]
        date = datetime.strptime(payload["date"], "%Y-%m-%d").date()
        weather_info = payload["weather_info"]

        product = models.Product(
            name=name,
            price=price,
            production_date=date,
            expiration_date=date + timedelta(days=180)
        )
        weather = models.Weather(
            weather_date=date,
            weather_info=weather_info
        )
        db.add(product)
        db.add(weather)
        db.commit()

        return {"message": "保存に成功しました"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
