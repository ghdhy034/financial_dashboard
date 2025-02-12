# overall_sorting.py
import streamlit as st
import pandas as pd

def compute_previous_period(is_monthly, year, period_value, mode):
    # is_monthly=True：period_value 為月份；False：為季度
    if is_monthly:
        if mode == "MOM":
            if period_value == 1:
                return year - 1, 12
            else:
                return year, period_value - 1
        elif mode == "QOQ":
            total = year * 12 + period_value
            prev_total = total - 3
            prev_year = prev_total // 12
            prev_month = prev_total % 12
            if prev_month == 0:
                prev_month = 12
                prev_year -= 1
            return prev_year, prev_month
        elif mode == "YOY":
            return year - 1, period_value
        else:
            return None
    else:
        if mode in ["MOM", "QOQ"]:
            if period_value == 1:
                return year - 1, 4
            else:
                return year, period_value - 1
        elif mode == "YOY":
            return year - 1, period_value
        else:
            return None

def compute_sort_value(row, df_full, col, sort_mode, is_monthly):
    if sort_mode == "數值":
        return row[col]
    else:
        if is_monthly:
            year = row['年']
            month = row['月']
            prev_year, prev_month = compute_previous_period(True, year, month, sort_mode)
            df_prev = df_full[(df_full["公司代號"] == row["公司代號"]) & (df_full["年"] == prev_year) & (df_full["月"] == prev_month)]
            if df_prev.empty:
                return None
            prev_value = df_prev.iloc[0][col]
        else:
            year = row['年']
            quarter = row['季']
            prev_year, prev_quarter = compute_previous_period(False, year, quarter, sort_mode)
            df_prev = df_full[(df_full["公司代號"] == row["公司代號"]) & (df_full["年"] == prev_year) & (df_full["季"] == prev_quarter)]
            if df_prev.empty:
                return None
            prev_value = df_prev.iloc[0][col]
        if prev_value == 0 or prev_value is None:
            return None
        current_value = row[col]
        return (current_value - prev_value) / prev_value * 100

def overall_sorting(monthly_df, quarterly_df):
    st.header("整體排序功能")
    st.info("請使用下方多選框選擇目前的公司（格式：公司代號 - 公司名稱），可輸入部分文字自動補全，並直接點選標籤右側的刪除按鈕。")
    dataset_option = st.radio("選擇資料來源", ("月營收", "季財報"))
    if dataset_option == "月營收":
        is_monthly = True
        df_full = monthly_df.copy()
        filter_mode = st.selectbox("選擇篩選模式", ("依產業別", "全選", "自訂"))
        if filter_mode == "依產業別":
            industries = sorted(df_full["產業別"].unique())
            selected_industry = st.selectbox("選擇產業", industries)
            filtered_df = df_full[df_full["產業別"] == selected_industry]
            filtered_codes = filtered_df["公司代號"].unique().tolist()
        elif filter_mode == "自訂":
            unique_companies = df_full[['公司代號', '公司名稱']].drop_duplicates().sort_values('公司代號')
            unique_companies['display'] = unique_companies['公司代號'].astype(str) + " - " + unique_companies['公司名稱']
            selected = st.multiselect("選擇公司", unique_companies['display'].tolist())
            filtered_codes = [int(x.split(" - ")[0]) for x in selected]
        else:
            filtered_codes = df_full["公司代號"].unique().tolist()
        
        unique_companies = df_full[['公司代號', '公司名稱']].drop_duplicates().sort_values('公司代號')
        unique_companies['display'] = unique_companies['公司代號'].astype(str) + " - " + unique_companies['公司名稱']
        default_options = unique_companies[unique_companies["公司代號"].isin(filtered_codes)]["display"].tolist()
        selected_companies = st.multiselect("目前選擇的公司", unique_companies['display'].tolist(), default=default_options)
        try:
            filtered_codes = [int(x.split(" - ")[0].strip()) for x in selected_companies if x.strip()]
        except:
            st.error("請確保輸入格式正確")
        df_filtered = df_full[df_full["公司代號"].isin(filtered_codes)]
        
        df_full_sorted = df_full.sort_values(['年','月'])
        available_periods = df_full_sorted[['年','月']].drop_duplicates()
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
        df_display = df_filtered[df_filtered.apply(lambda row: (row['年'], row['月']) >= start_tuple and (row['年'], row['月']) <= end_tuple, axis=1)].copy()
        
        st.write("排序結果 (月營收)")
        st.dataframe(df_display)
    else:
        is_monthly = False
        df_full = quarterly_df.copy()
        filter_mode = st.selectbox("選擇篩選模式", ("全選", "自訂"))
        if filter_mode == "自訂":
            unique_companies = df_full[['公司代號', '公司名稱']].drop_duplicates().sort_values('公司代號')
            unique_companies['display'] = unique_companies['公司代號'].astype(str) + " - " + unique_companies['公司名稱']
            selected = st.multiselect("選擇公司", unique_companies['display'].tolist())
            filtered_codes = [int(x.split(" - ")[0]) for x in selected]
        else:
            filtered_codes = df_full["公司代號"].unique().tolist()
        unique_companies = df_full[['公司代號', '公司名稱']].drop_duplicates().sort_values('公司代號')
        unique_companies['display'] = unique_companies['公司代號'].astype(str) + " - " + unique_companies['公司名稱']
        default_options = unique_companies[unique_companies["公司代號"].isin(filtered_codes)]["display"].tolist()
        selected_companies = st.multiselect("目前選擇的公司", unique_companies['display'].tolist(), default=default_options)
        try:
            filtered_codes = [int(x.split(" - ")[0].strip()) for x in selected_companies if x.strip()]
        except:
            st.error("請確保輸入格式正確")
        df_filtered = df_full[df_full["公司代號"].isin(filtered_codes)]
        
        df_full_sorted = df_full.sort_values(['年','季'])
        available_quarters = df_full_sorted[['年','季']].drop_duplicates()
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
        df_display = df_filtered[df_filtered.apply(lambda row: (row['年'], row['季']) >= start_q_tuple and (row['年'], row['季']) <= end_q_tuple, axis=1)].copy()
        
        st.write("排序結果 (季財報)")
        st.dataframe(df_display)
