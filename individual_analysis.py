# individual_analysis.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def individual_stock_analysis(monthly_df, quarterly_df):
    st.header("各股分析")
    # 以公司代號查詢，顯示「代號 - 公司名稱」
    unique_companies = monthly_df[['公司代號', '公司名稱']].drop_duplicates().sort_values('公司代號')
    unique_companies['display'] = unique_companies['公司代號'].astype(str) + " - " + unique_companies['公司名稱']
    selected_display = st.selectbox("選擇公司 (請選擇公司代號)", unique_companies['display'].tolist())
    selected_code = int(selected_display.split(" - ")[0])
    
    monthly_company = monthly_df[monthly_df["公司代號"] == selected_code].copy()
    quarterly_company = quarterly_df[quarterly_df["公司代號"] == selected_code].copy()
    
    # ── 月度資料時間區間篩選 ─────────────────────────
    monthly_company = monthly_company.sort_values(['年', '月'])
    available_periods = monthly_company[['年', '月']].drop_duplicates().sort_values(['年','月'])
    available_periods['period_str'] = available_periods['年'].astype(str) + '-' + available_periods['月'].astype(str)
    period_list = available_periods['period_str'].tolist()
    if not period_list:
        st.error("無月度資料")
        return
    col1, col2 = st.columns(2)
    start_period = col1.selectbox("起始期間 (年-月)", period_list, index=0)
    end_period = col2.selectbox("結束期間 (年-月)", period_list, index=len(period_list)-1)
    def period_to_tuple(p):
        parts = p.split('-')
        return (int(parts[0]), int(parts[1]))
    if period_to_tuple(start_period) > period_to_tuple(end_period):
        st.error("起始期間必須早於或等於結束期間")
        return
    start_tuple = period_to_tuple(start_period)
    end_tuple = period_to_tuple(end_period)
    monthly_company = monthly_company[monthly_company.apply(lambda row: (row['年'], row['月']) >= start_tuple and (row['年'], row['月']) <= end_tuple, axis=1)]
    monthly_company['年月'] = monthly_company['年'].astype(str) + '-' + monthly_company['月'].astype(str)
    
    # 調整月度詳細數據欄位順序
    cols_order = ["年", "月", "公司代號", "公司名稱", "產業別", "營業收入-當月營收", "MoM", "YoY", "QOQ", "年月", "備註"]
    monthly_company = monthly_company[cols_order]
    
    # ── 季報資料時間區間篩選 ─────────────────────────
    quarterly_company = quarterly_company.sort_values(['年','季'])
    available_quarters = quarterly_company[['年','季']].drop_duplicates().sort_values(['年','季'])
    available_quarters['quarter_str'] = available_quarters['年'].astype(str) + " Q" + available_quarters['季'].astype(str)
    quarter_list = available_quarters['quarter_str'].tolist()
    if not quarter_list:
        st.error("無季度資料")
        return
    col3, col4 = st.columns(2)
    start_quarter = col3.selectbox("起始季度 (年 Q季)", quarter_list, index=0)
    end_quarter = col4.selectbox("結束季度 (年 Q季)", quarter_list, index=len(quarter_list)-1)
    def quarter_to_tuple(q):
        parts = q.split(" Q")
        return (int(parts[0]), int(parts[1]))
    if quarter_to_tuple(start_quarter) > quarter_to_tuple(end_quarter):
        st.error("起始季度必須早於或等於結束季度")
        return
    start_q_tuple = quarter_to_tuple(start_quarter)
    end_q_tuple = quarter_to_tuple(end_quarter)
    quarterly_company = quarterly_company[quarterly_company.apply(lambda row: (row['年'], row['季']) >= start_q_tuple and (row['年'], row['季']) <= end_q_tuple, axis=1)]
    quarterly_company['季期'] = quarterly_company['年'].astype(str) + " Q" + quarterly_company['季'].astype(str)
    
    # 分頁顯示：月度與季度分析
    tabs = st.tabs(["月度營收分析", "季度財報分析"])
    
    with tabs[0]:
        st.subheader("營收折線圖")
        fig_revenue = go.Figure()
        fig_revenue.add_trace(go.Scatter(x=monthly_company['年月'], y=monthly_company["營業收入-當月營收"],
                                         mode='lines+markers', name="營收"))
        fig_revenue.update_layout(title=f"{selected_display} - 營收趨勢",
                                  xaxis_title="年月", yaxis_title="營收")
        st.plotly_chart(fig_revenue, use_container_width=True)
        
        st.subheader("YoY 與 MoM 趨勢")
        fig_growth = go.Figure()
        fig_growth.add_trace(go.Scatter(x=monthly_company['年月'], y=monthly_company["YoY"],
                                        mode='lines+markers', name="YoY (%)"))
        fig_growth.add_trace(go.Scatter(x=monthly_company['年月'], y=monthly_company["MoM"],
                                        mode='lines+markers', name="MoM (%)"))
        fig_growth.update_layout(title=f"{selected_display} - YoY 與 MoM 趨勢",
                                 xaxis_title="年月", yaxis_title="百分比 (%)")
        st.plotly_chart(fig_growth, use_container_width=True)
        
        st.subheader("月度詳細數據")
        st.dataframe(monthly_company.reset_index(drop=True))
    
    with tabs[1]:
        st.subheader("季度財報詳細數據")
        cols_to_show = ['季期', '資產總計(額)', '負債總計(額)', '流動資產', '非流動資產', 
                        '流動負債', '非流動負債', '流動比率', '負債比率', '毛利率', 'EPS',
                        '流動比率_QoQ', '負債比率_QoQ', '毛利率_QoQ', 'EPS_QoQ']
        st.dataframe(quarterly_company[cols_to_show].reset_index(drop=True))
        st.subheader("季度指標圖表")
        metric_options = st.multiselect("選擇要繪製的指標", 
                                        options=['資產總計(額)', '負債總計(額)', '流動資產', '非流動資產', 
                                                 '流動負債', '非流動負債', '流動比率', '負債比率', '毛利率', 'EPS'],
                                        default=['資產總計(額)', '負債總計(額)'])
        if metric_options:
            fig_q = go.Figure()
            for metric in metric_options:
                fig_q.add_trace(go.Bar(x=quarterly_company['季期'], y=quarterly_company[metric], name=metric))
            fig_q.update_layout(title=f"{selected_display} - 季度指標比較",
                                barmode='group', xaxis_title="季期")
            st.plotly_chart(fig_q, use_container_width=True)
