# data_access.py
import sqlite3
import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    """
    從 local SQLite 資料庫讀取資料。
    資料庫檔案需與此程式同目錄，檔名為 financial_data.db
    """
    conn = sqlite3.connect("financial_data.db")
    monthly_df = pd.read_sql_query('SELECT * FROM monthly_revenue', conn)
    quarterly_df = pd.read_sql_query('SELECT * FROM quarterly_report', conn)
    conn.close()
    return monthly_df, quarterly_df
