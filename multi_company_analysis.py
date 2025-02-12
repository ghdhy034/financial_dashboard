# multi_company_analysis.py
import streamlit as st
import pandas as pd
import plotly.express as px

def multi_company_analysis(monthly_df, quarterly_df):
    st.header("多公司分析")
    # 篩選模式：依產業別、全選、自訂
    filter_mode = st.radio("選擇篩選模式", ("依產業別", "全選", "自訂"))
    if filter_mode == "依產業別":
        industries = sorted(monthly_df["產業別"].unique())
        selected_industry = st.selectbox("選擇產業", industries)
        companies_df = monthly_df[monthly_df["產業別"] == selected_industry][['公司代號', '公司名稱']].drop_duplicates().sort_values('公司代號')
    elif filter_mode == "自訂":
        companies_df = monthly_df[['公司代號', '公司名稱']].drop_duplicates().sort_values('公司代號')
        companies_df['display'] = companies_df['公司代號'].astype(str) + " - " + companies_df['公司名稱']
        selected = st.multiselect("選擇公司", companies_df['display'].tolist())
        companies_df = companies_df[companies_df['display'].isin(selected)]
    else:
        companies_df = monthly_df[['公司代號', '公司名稱']].drop_duplicates().sort_values('公司代號')
    
    if st.checkbox("是否顯示比較對象列表"):
        st.dataframe(companies_df.reset_index(drop=True))
    
    # 獨立的繪圖用公司選擇，預設為空
    st.subheader("繪圖用公司選擇")
    all_companies = monthly_df[['公司代號', '公司名稱']].drop_duplicates().sort_values('公司代號')
    all_companies['display'] = all_companies['公司代號'].astype(str) + " - " + all_companies['公司名稱']
    plot_choices = st.multiselect("請選擇用於繪圖的公司 (最多15間)", all_companies['display'].tolist(), default=[])
    if len(plot_choices) > 15:
        st.error("繪圖公司數量不可超過15間")
        return
    plot_codes = [int(x.split(" - ")[0]) for x in plot_choices]
    
    # 供計算用：所有符合篩選模式的公司
    company_codes = companies_df["公司代號"].tolist()
    
    metric_option = st.selectbox("選擇比較項目", ("月度營收增長率", "資產增長率"))
    
    if metric_option == "月度營收增長率":
        st.subheader("月度營收增長率比較")
        df_filtered = monthly_df[monthly_df["公司代號"].isin(company_codes)]
        df_filtered = df_filtered.sort_values(['年','月'])
        available_periods = df_filtered[['年','月']].drop_duplicates().sort_values(['年','月'])
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
        
        growth_results = []
        for code in company_codes:
            df_comp = df_filtered[df_filtered["公司代號"] == code]
            row_start = df_comp[(df_comp["年"] == start_tuple[0]) & (df_comp["月"] == start_tuple[1])]
            row_end = df_comp[(df_comp["年"] == end_tuple[0]) & (df_comp["月"] == end_tuple[1])]
            if row_start.empty or row_end.empty:
                growth = None
            else:
                rev_start = row_start["營業收入-當月營收"].values[0]
                rev_end = row_end["營業收入-當月營收"].values[0]
                if rev_start == 0:
                    growth = None
                else:
                    growth = (rev_end - rev_start) / rev_start * 100
            growth_results.append({"公司代號": code, 
                                   "公司名稱": companies_df[companies_df["公司代號"]==code]["公司名稱"].values[0] if not companies_df[companies_df["公司代號"]==code].empty else "未知",
                                   "增長率(%)": growth})
        growth_df = pd.DataFrame(growth_results).dropna(subset=["增長率(%)"])
        st.dataframe(growth_df.reset_index(drop=True))
        
        # 繪圖僅用自訂選擇的公司（若未選擇則顯示提示）
        if plot_codes:
            plot_df = growth_df[growth_df["公司代號"].isin(plot_codes)]
            fig_growth = px.bar(plot_df, x="公司代號", y="增長率(%)", text="增長率(%)",
                                title="月度營收增長率比較", labels={"公司代號": "公司代號", "增長率(%)": "增長率 (%)"})
            st.plotly_chart(fig_growth, use_container_width=True)
        else:
            st.info("未選擇繪圖用公司")
        
    elif metric_option == "資產增長率":
        st.subheader("資產增長率比較")
        df_quarter = quarterly_df[quarterly_df["公司代號"].isin(company_codes)]
        df_quarter = df_quarter.sort_values(['年','季'])
        available_quarters = df_quarter[['年','季']].drop_duplicates().sort_values(['年','季'])
        available_quarters['quarter_str'] = available_quarters['年'].astype(str) + " Q" + available_quarters['季'].astype(str)
        quarter_list = available_quarters['quarter_str'].tolist()
        if not quarter_list:
            st.error("無季度資料")
            return
        col1, col2 = st.columns(2)
        start_quarter = col1.selectbox("起始季度 (年 Q季)", quarter_list, index=0)
        end_quarter = col2.selectbox("結束季度 (年 Q季)", quarter_list, index=len(quarter_list)-1)
        def quarter_to_tuple(q):
            parts = q.split(" Q")
            return (int(parts[0]), int(parts[1]))
        if quarter_to_tuple(start_quarter) > quarter_to_tuple(end_quarter):
            st.error("起始季度必須早於或等於結束季度")
            return
        start_q_tuple = quarter_to_tuple(start_quarter)
        end_q_tuple = quarter_to_tuple(end_quarter)
        growth_results = []
        for code in company_codes:
            df_comp = df_quarter[df_quarter["公司代號"] == code]
            row_start = df_comp[(df_comp["年"] == start_q_tuple[0]) & (df_comp["季"] == start_q_tuple[1])]
            row_end = df_comp[(df_comp["年"] == end_q_tuple[0]) & (df_comp["季"] == end_q_tuple[1])]
            if row_start.empty or row_end.empty:
                growth = None
            else:
                asset_start = row_start["資產總計(額)"].values[0]
                asset_end = row_end["資產總計(額)"].values[0]
                if asset_start == 0:
                    growth = None
                else:
                    growth = (asset_end - asset_start) / asset_start * 100
            growth_results.append({"公司代號": code, 
                                   "公司名稱": companies_df[companies_df["公司代號"]==code]["公司名稱"].values[0] if not companies_df[companies_df["公司代號"]==code].empty else "未知",
                                   "增長率(%)": growth})
        growth_df = pd.DataFrame(growth_results).dropna(subset=["增長率(%)"])
        st.dataframe(growth_df.reset_index(drop=True))
        if plot_codes:
            plot_df = growth_df[growth_df["公司代號"].isin(plot_codes)]
            fig_growth = px.bar(plot_df, x="公司代號", y="增長率(%)", text="增長率(%)",
                                title="資產增長率比較", labels={"公司代號": "公司代號", "增長率(%)": "增長率 (%)"})
            st.plotly_chart(fig_growth, use_container_width=True)
        else:
            st.info("未選擇繪圖用公司")
