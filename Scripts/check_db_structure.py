import sqlite3

conn = sqlite3.connect('skillsheet_data.db')
cursor = conn.cursor()

# テーブル一覧を取得
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("テーブル一覧:", tables)

# 各テーブルの構造を確認
for table in tables:
    print(f"\n=== {table} の構造 ===")
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

conn.close()
