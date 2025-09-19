import sqlite3

# データベースに接続
conn = sqlite3.connect('skillsheet_data.db')
cursor = conn.cursor()

# テーブル一覧を取得
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("データベース内のテーブル一覧:")
for table in tables:
    print(f"- {table[0]}")

print("\n各テーブルの構造:")
for table in tables:
    table_name = table[0]
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print(f"\n{table_name} テーブル:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

# データの件数を確認
print("\n各テーブルのデータ件数:")
for table in tables:
    table_name = table[0]
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"- {table_name}: {count}件")

conn.close()
