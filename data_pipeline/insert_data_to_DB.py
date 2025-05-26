import os
import sqlite3
import pandas as pd

class DatabaseManager:
    def __init__(self, db_name="financial_data.db"):
        """初始化資料庫名稱"""
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def create_table_from_csv(self, sample_csv_path, table_name):
        """
        根據 CSV 檔案建立資料表 (不使用 id)
        - sample_csv_path: CSV 檔案路徑 (用來分析欄位)
        - table_name: 要建立的資料表名稱
        """
        df = pd.read_csv(sample_csv_path)

        # 轉換 Pandas 資料型別為 SQLite 適用的型別
        column_types = {}
        for col in df.columns:
            if df[col].dtype == "int64":
                column_types[col] = "INTEGER"
            elif df[col].dtype == "float64":
                column_types[col] = "REAL"
            else:
                column_types[col] = "TEXT"

        # 動態建立 SQL 語法 (移除 id 欄位)
        columns_sql = ", ".join([f'"{col}" {col_type}' for col, col_type in column_types.items()])
        create_table_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_sql})'
        
        self.cursor.execute(create_table_sql)
        self.conn.commit()

        print(f"✅ 成功建立 {table_name} 資料表")

    def insert_data_from_csv(self, folder_path, table_name):
        """
        從 CSV 資料夾讀取數據並存入指定資料表
        """
        files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]
        if not files:
            print(f"⚠️ 找不到任何 CSV 檔案於 {folder_path}")
            return

        # 先用第一個 CSV 建表
        sample_csv_path = os.path.join(folder_path, files[0])
        self.create_table_from_csv(sample_csv_path, table_name)

        # 讀取並插入所有 CSV
        for file in files:
            file_path = os.path.join(folder_path, file)
            df = pd.read_csv(file_path)
            df.to_sql(table_name, self.conn, if_exists="append", index=False)
            print(f"✅ {file} 已成功存入 {table_name} 資料表")

    def close_connection(self):
        """關閉資料庫連線"""
        self.conn.close()

def main():
    db_manager = DatabaseManager()

    # 設定 CSV 資料夾路徑
    monthly_revenue_folder = "monthly_revenue_processed"
    quarterly_report_folder = "quarterly_report_processed"

    # 將 CSV 存入資料庫
    db_manager.insert_data_from_csv(monthly_revenue_folder, "monthly_revenue")
    db_manager.insert_data_from_csv(quarterly_report_folder, "quarterly_report")

    # 關閉資料庫連線
    db_manager.close_connection()

if __name__ == "__main__":
    main()
