# main.py

import os
import pandas as pd
import shutil
import warnings
from tqdm import tqdm 
from pandas.errors import PerformanceWarning
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=PerformanceWarning)


# 從兩支檔案匯入 main() 函式
from get_balance_sheet import main as balance_sheet_main
from get_consolidated_income import main as income_statement_main

def main():
    start_year=114
    end_year=114
    year_list = [year for year in range(start_year, end_year+1)]
    season_list = [1,2,3,4]

    print("=== 開始批次爬蟲 ===")
    
    # tqdm 用法1：對「年」做外層進度條
    #   desc: 進度條前顯示的文字
    for year in tqdm(year_list, desc="Year Progress"):
        # tqdm 用法2：對「季」做內層進度條
        for season in tqdm(season_list, desc=f"Seasons in {year}", leave=False):
            print(f"處理民國 {year} 年，第 {season} 季資料...")

            # A. 資產負債表
            bs_raw_dir = "./raw_data/balance_sheets"
            bs_final_dir = "./final_data"
            bs_filename = f"balance_sheet_{year}_{season}.csv"
            balance_sheet_main(
                year=year,
                season=season,
                raw_output_dir=bs_raw_dir,
                final_output_dir=bs_final_dir,
                merged_output_file=bs_filename
            )

            # B. 綜合損益表
            inc_raw_dir = "./raw_data/incomes"
            inc_final_dir = "./final_data"
            inc_filename = f"consolidated_income_{year}_{season}.csv"
            income_statement_main(
                year=year,
                season=season,
                raw_output_dir=inc_raw_dir,
                final_output_dir=inc_final_dir,
                final_output_file=inc_filename
            )

            # C. 最終合併
            bs_path = os.path.join(bs_final_dir, bs_filename)
            inc_path = os.path.join(inc_final_dir, inc_filename)
            df_bs = pd.read_csv(bs_path, dtype=str)
            df_in = pd.read_csv(inc_path, dtype=str)

            merged_final = pd.merge(
                df_bs, df_in, how="left",
                on=["年", "季", "公司代號", "公司名稱"]
            )

            # 去重(可加可不加)
            merged_final.drop_duplicates(
                subset=["年","季","公司代號","公司名稱"],
                keep="last",
                inplace=True
            )

            # 寫出最後檔
            final_merged_dir = "./quarterly_report_processed"
            os.makedirs(final_merged_dir, exist_ok=True)
            final_merged_filename = f"final_merged_{year}_{season}.csv"
            final_merged_path = os.path.join(final_merged_dir, final_merged_filename)
            # 只輸出目標欄位
            financial_data_fields = [
                "年", "季", "公司代號", "公司名稱", "資產總計(額)", "負債總計(額)", "股本", "資本公積", 
                "保留盈餘(或累積虧損)", "其他權益", "歸屬於母公司業主之權益(合計)", "權益總計(額)", 
                "母公司暨子公司持有之母公司庫藏股股數（單位：股）", "每股參考淨值", "流動資產", 
                "非流動資產", "流動負債", "非流動負債", "基本每股盈餘（元）", "所得稅費用（利益）", 
                "營業成本", "營業收入", "營業毛利（毛損）", "營業費用", "稅前淨利（淨損）", 
                "綜合損益總額歸屬於母公司業主"
            ]
            merged_final = merged_final[financial_data_fields]
            merged_final.to_csv(final_merged_path, index=False, encoding="utf-8-sig")

            print(f"→ 完成 {final_merged_filename}")

    print("=== 全部處理完成！ ===")



if __name__ == "__main__":
    main()



financial_data_fields = [
    "年", "季", "公司代號", "公司名稱", "資產總計(額)", "負債總計(額)", "股本", "資本公積", 
    "保留盈餘(或累積虧損)", "其他權益", "歸屬於母公司業主之權益(合計)", "權益總計(額)", 
    "母公司暨子公司持有之母公司庫藏股股數（單位：股）", "每股參考淨值", "流動資產", 
    "非流動資產", "流動負債", "非流動負債", "基本每股盈餘（元）", "所得稅費用（利益）", 
    "營業成本", "營業收入", "營業毛利（毛損）", "營業費用", "稅前淨利（淨損）", 
    "綜合損益總額歸屬於母公司業主"
]
financial_data_fields_en = [
    "Year",  # 年度
    "Quarter",  # 季度
    "Company Code",  # 公司代號
    "Company Name",  # 公司名稱
    "Total Assets",  # 資產總計(額)
    "Total Liabilities",  # 負債總計(額)
    "Capital Stock",  # 股本
    "Capital Surplus",  # 資本公積
    "Retained Earnings (or Accumulated Deficit)",  # 保留盈餘(或累積虧損)
    "Other Equity",  # 其他權益
    "Equity Attributable to Owners of the Parent",  # 歸屬於母公司業主之權益(合計)
    "Total Equity",  # 權益總計(額)
    "Treasury Shares Held by Parent and Subsidiaries (Shares)",  # 母公司暨子公司持有之母公司庫藏股股數（單位：股）
    "Net Asset Value per Share",  # 每股參考淨值
    "Current Assets",  # 流動資產
    "Non-Current Assets",  # 非流動資產
    "Current Liabilities",  # 流動負債
    "Non-Current Liabilities",  # 非流動負債
    "Basic Earnings per Share (EPS)",  # 基本每股盈餘（元）
    "Income Tax Expense (Benefit)",  # 所得稅費用（利益）
    "Cost of Revenue",  # 營業成本
    "Revenue",  # 營業收入
    "Gross Profit (Loss)",  # 營業毛利（毛損）
    "Operating Expenses",  # 營業費用
    "Profit (Loss) Before Tax",  # 稅前淨利（淨損）
    "Total Comprehensive Income Attributable to Owners of the Parent"  # 綜合損益總額歸屬於母公司業主
]
