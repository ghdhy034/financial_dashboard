# main.py
import streamlit as st
from data_access import load_data
from metrics import calculate_monthly_metrics, calculate_monthly_qoq, calculate_quarterly_metrics
from individual_analysis import individual_stock_analysis
from multi_company_analysis import multi_company_analysis
from overall_sorting import overall_sorting

def main():
    st.title("Financial Analysis Dashboard")
    st.markdown("本應用程式從 SQLite 資料庫讀取數據，提供各股分析、多公司分析與整體排序功能。")
    
    menu = st.sidebar.radio("選擇功能", ("各股分析", "多公司分析", "整體排序"))
    
    monthly_df, quarterly_df = load_data()
    monthly_df = calculate_monthly_metrics(monthly_df)
    monthly_df = calculate_monthly_qoq(monthly_df)
    quarterly_df = calculate_quarterly_metrics(quarterly_df)
    
    if menu == "各股分析":
        individual_stock_analysis(monthly_df, quarterly_df)
    elif menu == "多公司分析":
        multi_company_analysis(monthly_df, quarterly_df)
    elif menu == "整體排序":
        overall_sorting(monthly_df, quarterly_df)

if __name__ == '__main__':
    main()
