import os
import glob
import csv
import requests
import pandas as pd
from bs4 import BeautifulSoup


class ConsolidatedIncomeStatementHandler:
    """
    用於抓取並輸出「彙整綜合損益表 (t163sb04)」資料至 CSV。
    """
    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 "
                "Safari/537.36"
            )
        }
        self.url = "https://mops.twse.com.tw/mops/web/t163sb04"

    def fetch_profit_loss_data(self, type_k, year, season, output_dir):
        """
        抓取指定市場別(type_k)、民國年(year) 與季別(season)的綜合損益表，
        並將結果輸出為多個 CSV 檔 (每個 <table> 產生一個 CSV)。
        
        若市場為：
         - sii：只輸出第 14 ~ 19 個 <table>
         - otc：只輸出第 14 ~ 15 個 <table>
         
        :param type_k: 'sii'(上市)、'otc'(上櫃)、'rotc'(興櫃)、'pub'(公開發行)
        :param year  : 民國年(字串)，例如 "112"
        :param season: '01','02','03','04' 分別代表第1~4季
        :param output_dir : CSV 輸出目錄路徑
        """
        try:
            payload = {
                "step": "1",
                "firstin": "true",
                "off": "1",
                "isQuery": "Y",
                "TYPEK": type_k,
                "year": year,
                "season": season,
            }
            print(f"[綜合損益表] 抓取市場別={type_k}, 年={year}, 季={season}...")
            response = requests.post(self.url, data=payload, headers=self.headers)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch data: {response.status_code}")

            soup = BeautifulSoup(response.text, "html.parser")
            tables = soup.find_all("table")

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 根據市場別決定要輸出的表格編號範圍
            if type_k == "sii":
                valid_range = range(14, 20)  # 14~19
            elif type_k == "otc":
                valid_range = range(14, 16)  # 14~15
            else:
                valid_range = range(1, len(tables) + 1)  # 其他市場全部輸出

            for i, table in enumerate(tables, start=1):
                # 檢查目前 table 是否在有效範圍內
                if i not in valid_range:
                    continue

                filename = os.path.join(output_dir, f"consolidated_income_{type_k}_{year}_{season}_{i}.csv")
                rows = table.find_all("tr")
                with open(filename, "w", encoding="utf-8", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    for row in rows:
                        cells = row.find_all(["th", "td"])
                        row_data = [cell.get_text(strip=True) for cell in cells]
                        writer.writerow(row_data)
                print(f"已輸出檔案: {filename}")

            return tables

        except Exception as e:
            print(f"抓取或輸出 CSV 過程發生錯誤: {e}")
            return None


class CSVCombiner:
    """
    用於合併 CSV 檔案，並依照定義的 mapping 轉換欄位。
    """
    def __init__(self, folder_path, key_columns, output_file,year ,season):
        self.folder_path = folder_path
        self.key_columns = key_columns
        self.output_file = output_file
        self.all_columns = set(key_columns)  # 先加入主要欄位
        self.dfs = []
        self.year=year
        self.season=season
        # 定義最終輸出欄位順序 (chinese_list)
        self.chinese_list = [
            "公司代號",
            "公司名稱",
            "保險負債準備淨變動",
            "停業單位損益",
            "其他收益及費損淨額",
            "其他綜合損益（稅後淨額）",
            "利息以外淨損益",
            "利息淨收益",
            "原始認列生物資產及農產品之利益（損失）",
            "合併前非屬共同控制股權損益",
            "合併前非屬共同控制股權綜合損益淨額",
            "呆帳費用、承諾及保證責任準備提存",
            "基本每股盈餘（元）",
            "已實現銷貨（損）益",
            "所得稅費用（利益）",
            "支出及費用",
            "收入及收益",
            "未實現銷貨（損）益",
            "本期稅後淨利（淨損）",
            "本期綜合損益總額（稅後）",
            "淨利歸屬於共同控制權益",
            "淨利歸屬於母公司業主",
            "淨利歸屬於非控制權益",
            "營業利益",
            "營業外損益",
            "營業成本",
            "營業收入",
            "營業毛利（毛損）",
            "營業費用",
            "生物資產當期公允價值減出售成本之變動利益（損失）",
            "稅前淨利（淨損）",
            "綜合損益總額歸屬於共同控制下前手權益",
            "綜合損益總額歸屬於母公司業主",
            "綜合損益總額歸屬於非控制權益",
            "繼續營業單位本期稅後淨利（淨損）",
            "繼續營業單位稅前淨利（淨損）"
        ]
        # 定義 mapping：最終欄位對應來源可能的欄位名稱列表
        self.mapping = {
            "保險負債準備淨變動": ["保險負債準備淨變動"],
            "停業單位損益": ["停業單位損益"],
            "公司代號": ["公司代號"],
            "公司名稱": ["公司名稱"],
            "其他收益及費損淨額": ["其他收益及費損淨額"],
            "其他綜合損益（稅後淨額）": ["其他綜合損益（稅後淨額）", "本期其他綜合損益（稅後淨額）", "其他綜合損益（稅後）", "其他綜合損益", "其他綜合損益（淨額）"],
            "利息以外淨損益": ["利息以外淨損益", "利息以外淨收益"],
            "利息淨收益": ["利息淨收益"],
            "原始認列生物資產及農產品之利益（損失）": ["原始認列生物資產及農產品之利益（損失）"],
            "合併前非屬共同控制股權損益": ["合併前非屬共同控制股權損益"],
            "合併前非屬共同控制股權綜合損益淨額": ["合併前非屬共同控制股權綜合損益淨額"],
            "呆帳費用、承諾及保證責任準備提存": ["呆帳費用、承諾及保證責任準備提存"],
            "基本每股盈餘（元）": ["基本每股盈餘（元）"],
            "已實現銷貨（損）益": ["已實現銷貨（損）益"],
            "所得稅費用（利益）": ["所得稅費用（利益）", "所得稅（費用）利益"],
            "支出及費用": ["支出及費用", "支出"],
            "收入及收益": ["收入及收益", "收入", "收益"],
            "未實現銷貨（損）益": ["未實現銷貨（損）益"],
            "本期稅後淨利（淨損）": ["本期稅後淨利（淨損）", "本期淨利（淨損）"],
            "本期綜合損益總額（稅後）": ["本期綜合損益總額（稅後）", "本期綜合損益總額"],
            "淨利歸屬於共同控制權益": ["淨利歸屬於共同控制權益", "淨利（損）歸屬於共同控制下前手權益", "淨利（淨損）歸屬於共同控制下前手權益"],
            "淨利歸屬於母公司業主": ["淨利歸屬於母公司業主", "淨利（損）歸屬於母公司業主", "淨利（淨損）歸屬於母公司業主"],
            "淨利歸屬於非控制權益": ["淨利歸屬於非控制權益", "淨利（損）歸屬於非控制權益", "淨利（淨損）歸屬於非控制權益"],
            "營業利益": ["營業利益", "營業利益（損失）"],
            "營業外損益": ["營業外損益", "營業外收入及支出"],
            "營業成本": ["營業成本"],
            "營業收入": ["營業收入"],
            "營業毛利（毛損）": ["營業毛利（毛損）", "營業毛利（毛損）淨額"],
            "營業費用": ["營業費用"],
            "生物資產當期公允價值減出售成本之變動利益（損失）": ["生物資產當期公允價值減出售成本之變動利益（損失）"],
            "稅前淨利（淨損）": ["稅前淨利（淨損）"],
            "綜合損益總額歸屬於共同控制下前手權益": ["綜合損益總額歸屬於共同控制下前手權益"],
            "綜合損益總額歸屬於母公司業主": ["綜合損益總額歸屬於母公司業主"],
            "綜合損益總額歸屬於非控制權益": ["綜合損益總額歸屬於非控制權益"],
            "繼續營業單位本期稅後淨利（淨損）": ["繼續營業單位本期稅後淨利（淨損）", "繼續營業單位本期淨利（淨損）", "繼續營業單位本期純益（純損）"],
            "繼續營業單位稅前淨利（淨損）": ["繼續營業單位稅前淨利（淨損）", "繼續營業單位稅前損益", "繼續營業單位稅前純益（純損）"]
        }

    def load_csv_files(self):
        """
        讀取資料夾內所有 CSV 檔，僅處理包含 key_columns 的檔案
        """
        csv_files = [os.path.join(self.folder_path, f) for f in os.listdir(self.folder_path) if f.endswith('.csv')]
        if not csv_files:
            print("❌ 沒有找到任何 CSV 檔案")
            return
        valid_files = 0
        for file in csv_files:
            df = pd.read_csv(file, dtype=str)
            if all(col in df.columns for col in self.key_columns):
                self.all_columns.update(df.columns)
                self.dfs.append(df)
                valid_files += 1
            else:
                print(f"⚠️ {file} 未包含必要欄位 {self.key_columns}，已跳過")
        if valid_files > 0:
            print(f"✅ 已讀取 {valid_files} 個符合條件的 CSV 檔案，共有 {len(self.all_columns)} 個欄位")
        else:
            print("⚠️ 沒有任何 CSV 符合條件，無法合併")

    def clean_data(self, df):
        """
        清理數據：保留數字，移除純文字 (針對非 key_columns)
        """
        def is_valid_number(value):
            if pd.isna(value) or value == "":
                return False
            value = value.replace(",", "")
            return value.replace(".", "", 1).replace("-", "", 1).isdigit()
        for col in df.columns:
            if col not in self.key_columns:
                df[col] = df[col].apply(lambda x: x.replace(",", "") if is_valid_number(x) else "")
        return df

    def merge_data(self):
        """
        合併所有符合條件的 CSV 檔案
        """
        if not self.dfs:
            print("⚠️ 無資料可合併")
            return None
        merged_df = pd.DataFrame(columns=sorted(self.all_columns))
        for df in self.dfs:
            cleaned_df = self.clean_data(df)
            merged_df = pd.concat([merged_df, cleaned_df], ignore_index=True)
        print("✅ CSV 檔案合併與清理完成！")
        return merged_df

    def transform_columns(self, df,year,season):
        """
        根據 mapping 將原始欄位合併轉換成最終欄位，
        並依照 chinese_list 的順序建立新 DataFrame。
        """
        new_df = pd.DataFrame()
        
        # 直接填入查詢時使用的年與季
        new_df['年'] = year
        new_df['季'] = season
        
        for final_col in self.chinese_list:
            candidates = self.mapping.get(final_col, [final_col])
            def get_value(row):
                for cand in candidates:
                    if cand in df.columns:
                        value = row.get(cand, "")
                        if value != "":
                            return value
                return ""
            new_df[final_col] = df.apply(get_value, axis=1)
        return new_df

    def save_to_csv(self, df,year,season):
        """
        將轉換後的 DataFrame 存成 CSV，欄位順序按照 chinese_list，並包含 '年' 和 '季'
        """
        if df is None or df.empty:
            print("⚠️ 無法儲存，因為 DataFrame 為空")
            return
        
        # 確保 '年' 和 '季' 在最前面
        column_order = ['年', '季'] + self.chinese_list
        df = df[column_order]
        df['年']=year
        df['季']=season
        df.to_csv(self.output_file, index=False, encoding='utf-8-sig')
        print(f"✅ 成功儲存合併轉換後的 CSV 到 {self.output_file}")


def main(
    year="112",
    season="01",
    raw_output_dir="./raw_data/incomes",        # 存放爬蟲+拆分的 CSV
    final_output_dir="./final_data",            # 存放合併後的 CSV
    final_output_file="income_statement_merged.csv"
):
    """
    彙整綜合損益表的主流程。
    :param year: 民國年
    :param season: 季別
    :param raw_output_dir:   放「原始爬下、拆分」的資料夾
    :param final_output_dir: 放「最終合併檔案」的資料夾
    :param final_output_file: 產生的最終合併檔名
    """
    os.makedirs(raw_output_dir, exist_ok=True)
    os.makedirs(final_output_dir, exist_ok=True)

    # 先抓取各市場
    handler = ConsolidatedIncomeStatementHandler()
    for t in ["sii", "otc"]:
        handler.fetch_profit_loss_data(type_k=t, year=str(year), season=str(season), output_dir=raw_output_dir)

    # 合併
    key_columns = ["公司代號", "公司名稱"]
    output_file_path = os.path.join(final_output_dir, final_output_file)

    combiner = CSVCombiner(
        folder_path=raw_output_dir,
        key_columns=key_columns,
        output_file=output_file_path,
        year=str(year),
        season=str(season)
    )
    combiner.load_csv_files()
    merged_df = combiner.merge_data()

    if merged_df is not None and not merged_df.empty:
        final_df = combiner.transform_columns(merged_df, str(year), str(season))

        # (可選) 去除重複
        final_df.drop_duplicates(
            subset=["年", "季", "公司代號", "公司名稱"],
            keep="last",
            inplace=True
        )

        combiner.save_to_csv(final_df, str(year), str(season))

if __name__ == "__main__":
    main()

