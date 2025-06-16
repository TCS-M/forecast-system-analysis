import pandas as pd
import jpholiday
import os

# 自動でCSVファイルの場所を探す（もう迷わない）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', '売上データ.csv')

# CSV読み込み
df = pd.read_csv(DATA_PATH, encoding="utf-8")

# 日付変換
df['日付'] = pd.to_datetime(df['日付'])

# 数値変換（カンマ除去）
df['売上合計(円)'] = df['売上合計(円)'].astype(str).str.replace(",", "").astype(int)

# 欠損埋め
df['予約件数'] = df['予約件数'].fillna(0)
df['予約人数'] = df['予約人数'].fillna(0)

# 特徴量追加
df['曜日'] = df['日付'].dt.weekday
df['祝日'] = df['日付'].apply(lambda x: jpholiday.is_holiday(x)).astype(int)

# 整形済データを確認
print(df.head())

# 整形済みデータ保存
OUTPUT_PATH = os.path.join(BASE_DIR, 'data', '整形済_売上データ.csv')
df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

print("✅ データ整形 完了しました！")
