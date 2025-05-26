import os
import csv
import requests
import pandas as pd
from bs4 import BeautifulSoup
from collections import defaultdict



# ========== (A) 定義最終欄位順序 + 欄位對照表 ==========

# 1. 最終輸出欄位順序 (含「年」與「季」)
chinese_list = [
    "年",
    "季",
    "公司代號",
    "公司名稱",
    "現金及約當現金",
    "存放央行及拆借(金融)同業",
    "透過損益按公允價值衡量之金融資產",
    "透過其他綜合損益按公允價值衡量之金融資產",
    "按攤銷後成本衡量之債務工具投資",
    "避險之衍生金融資產(含淨額)",
    "附賣回票券及債券投資(含淨額)",
    "應收款項(含淨額)",
    "當期(本期)所得稅資產",
    "待出售資產(含淨額)",
    "待分配予業主之資產(含淨額)",
    "貼現及放款(含淨額)",
    "再保險合約資產(含淨額)",
    "採用權益法之投資(含淨額)",
    "受限制資產(含淨額)",
    "其他金融資產(含淨額)",
    "投資性不動產(含淨額)",
    "不動產及設備(含淨額)",
    "使用權資產(含淨額)",
    "無形資產(含淨額)",
    "遞延所得稅資產",
    "其他資產(含淨額)",
    "資產總計(額)",
    "央行及金融同業存款",
    "央行及同業融資",
    "透過損益按公允價值衡量之金融負債",
    "避險之衍生金融負債(含淨額)",
    "附買回票券及債券負債",
    "應付商業本票(含淨額)",
    "應付款項",
    "當期(本期)所得稅負債",
    "與待出售資產直接相關之負債",
    "存款及匯款",
    "應付金融債券",
    "應付公司債",
    "其他借款",
    "特別股負債",
    "負債準備",
    "其他金融負債",
    "租賃負債",
    "遞延所得稅負債",
    "其他負債",
    "負債總計(額)",
    "股本",
    "資本公積",
    "保留盈餘(或累積虧損)",
    "其他權益",
    "庫藏股票",
    "共同控制下前手權益",
    "歸屬於母公司業主之權益(合計)",
    "非控制權益",
    "權益總計(額)",
    "權益─具證券性質之虛擬通貨",
    "待註銷股本股數（單位：股）",
    "預收股款（權益項下）之約當發行股數（單位：股）",
    "母公司暨子公司持有之母公司庫藏股股數（單位：股）",
    "每股參考淨值",
    "投資",
    "分離帳戶保險商品資產",
    "短期債務",
    "保險負債",
    "具金融商品性質之保險契約準備",
    "外匯價格變動準備",
    "分離帳戶保險商品負債",
    "合併前非屬共同控制股權",
    "流動資產",
    "非流動資產",
    "流動負債",
    "非流動負債",
]

# 2. 欄位對照表：同義或有「－淨額」差異的欄位合併成最終名稱
column_mapping = {
    # 保留原名或同義合併
    "公司代號": "公司代號",
    "公司名稱": "公司名稱",

    # 當期(本期)所得稅資產
    "當期所得稅資產": "當期(本期)所得稅資產",
    "本期所得稅資產": "當期(本期)所得稅資產",

    # 當期(本期)所得稅負債
    "當期所得稅負債": "當期(本期)所得稅負債",
    "本期所得稅負債": "當期(本期)所得稅負債",

    # 資產總計(額)
    "資產總額": "資產總計(額)",
    "資產總計": "資產總計(額)",

    # 負債總計(額)
    "負債總額": "負債總計(額)",
    "負債總計": "負債總計(額)",

    # 保留盈餘(或累積虧損)
    "保留盈餘": "保留盈餘(或累積虧損)",
    "保留盈餘（或累積虧損）": "保留盈餘(或累積虧損)",

    # 歸屬於母公司業主之權益(合計)
    "歸屬於母公司業主之權益": "歸屬於母公司業主之權益(合計)",
    "歸屬於母公司業主之權益合計": "歸屬於母公司業主之權益(合計)",
    "歸屬於母公司業主權益合計": "歸屬於母公司業主之權益(合計)",

    # 權益總計(額)
    "權益總額": "權益總計(額)",
    "權益總計": "權益總計(額)",

    # 母公司暨子公司持有之母公司庫藏股股數
    "母公司暨子公司所持有之母公司庫藏股股數（單位：股）": "母公司暨子公司持有之母公司庫藏股股數（單位：股）",
    "母公司暨子公司持有之母公司庫藏股股數（單位：股）": "母公司暨子公司持有之母公司庫藏股股數（單位：股）",

    # 存放央行及拆借(金融)同業
    "存放央行及拆借金融同業": "存放央行及拆借(金融)同業",
    "存放央行及拆借銀行同業": "存放央行及拆借(金融)同業",

    # 權益─具證券性質之虛擬通貨
    "權益─具證券性質之虛擬通貨": "權益─具證券性質之虛擬通貨",
    "權益－具證券性質之虛擬通貨": "權益─具證券性質之虛擬通貨",

    # 「淨額」合併
    "應收款項": "應收款項(含淨額)",
    "應收款項－淨額": "應收款項(含淨額)",

    "待出售資產": "待出售資產(含淨額)",
    "待出售資產－淨額": "待出售資產(含淨額)",

    "貼現及放款": "貼現及放款(含淨額)",
    "貼現及放款－淨額": "貼現及放款(含淨額)",

    "再保險合約資產": "再保險合約資產(含淨額)",
    "再保險合約資產－淨額": "再保險合約資產(含淨額)",

    "採用權益法之投資": "採用權益法之投資(含淨額)",
    "採用權益法之投資－淨額": "採用權益法之投資(含淨額)",

    "受限制資產": "受限制資產(含淨額)",
    "受限制資產－淨額": "受限制資產(含淨額)",

    "其他金融資產": "其他金融資產(含淨額)",
    "其他金融資產－淨額": "其他金融資產(含淨額)",

    "投資性不動產": "投資性不動產(含淨額)",
    "投資性不動產－淨額": "投資性不動產(含淨額)",
    "投資性不動產投資－淨額": "投資性不動產(含淨額)",

    "不動產及設備": "不動產及設備(含淨額)",
    "不動產及設備－淨額": "不動產及設備(含淨額)",

    "使用權資產": "使用權資產(含淨額)",
    "使用權資產－淨額": "使用權資產(含淨額)",

    "無形資產": "無形資產(含淨額)",
    "無形資產－淨額": "無形資產(含淨額)",

    "其他資產": "其他資產(含淨額)",
    "其他資產－淨額": "其他資產(含淨額)",

    "避險之衍生金融資產": "避險之衍生金融資產(含淨額)",
    "避險之衍生金融資產淨額": "避險之衍生金融資產(含淨額)",

    "附賣回票券及債券投資": "附賣回票券及債券投資(含淨額)",
    "附賣回票券及債券投資淨額": "附賣回票券及債券投資(含淨額)",

    "待分配予業主之資產（或處分群組）": "待分配予業主之資產(含淨額)",
    "待分配予業主之資產－淨額": "待分配予業主之資產(含淨額)",

    "應付商業本票": "應付商業本票(含淨額)",
    "應付商業本票－淨額": "應付商業本票(含淨額)",

    "避險之衍生金融負債": "避險之衍生金融負債(含淨額)",
    "避險之衍生金融負債－淨額": "避險之衍生金融負債(含淨額)",

    # 其他無需特別合併的欄位，可以默認保留原名（程式中以 get(col, col) 方式處理）
}


# ========== 1. 爬蟲 (原 test_crawler_data.py) ==========

class BalanceSheetHandler:
    """
    用於抓取並輸出「資產負債表 (t163sb05)」資料至多個 CSV。
    """
    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 "
                "Safari/537.36"
            )
        }
        # 目標網址：資產負債表
        self.url = "https://mops.twse.com.tw/mops/web/t163sb05"

    def fetch_balance_sheet(self, type_k, year, season, output_dir):
        """
        抓取指定市場別 (type_k)、民國年 (year)、季別 (season) 的資產負債表，
        並將特定表格 (由 allowed_tables 決定) 分別輸出為 CSV 檔。
        """
        # 根據市場別決定要輸出的表格編號
        if type_k == "sii":
            # 上市：只要編號 1, 17, 18, 19
            allowed_tables = [1, 17, 18, 19]
        elif type_k == "otc":
            # 上櫃：只要編號 1
            allowed_tables = [1]
        else:
            # 其他 (例如 rotc, pub)，此處預設不輸出
            allowed_tables = []

        try:
            payload = {
                "step": "1",
                "firstin": "true",
                "off": "1",
                "isQuery": "Y",
                "TYPEK": type_k,   # 市場別
                "year": year,      # 民國年
                "season": season,  # 季別
            }

            print(f"[資產負債表] 抓取市場別={type_k}, 年={year}, 季={season}...")

            response = requests.post(self.url, data=payload, headers=self.headers)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch data: {response.status_code}")

            soup = BeautifulSoup(response.text, "html.parser")
            tables = soup.find_all("table")

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 遍歷所有表格，但只輸出 allowed_tables 裡的編號
            for i, table in enumerate(tables, start=1):
                if i not in allowed_tables:
                    continue  # 跳過不需輸出的表格

                filename = os.path.join(output_dir, f"balance_sheet_{type_k}_{i}.csv")
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


# ========== 2. CSV 拆分 (原 sort_sii_csv.py) ==========

class CSVSplitterSii:
    def __init__(self, file_path, split_lines, output_folder):
        """
        初始化 CSVSplitter (針對 SII 資料)
        """
        self.file_path = file_path
        self.split_lines = [line.strip() for line in split_lines]
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)
    
    def split_file(self):
        """
        讀取 CSV 並依照指定的三行拆分成多個檔案 (SII 用)
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"找不到檔案: {self.file_path}")
        
        with open(self.file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        split_indices = []  # 存儲拆分的索引
        for i, line in enumerate(lines):
            if line.strip() in self.split_lines:
                split_indices.append(i)
        
        if not split_indices:
            raise ValueError("未找到指定的拆分行 (SII)")

        split_indices.append(len(lines))  # 最後一段
        for i in range(len(split_indices) - 1):
            start, end = split_indices[i], split_indices[i + 1]
            split_data = lines[start:end]
            
            output_file = os.path.join(self.output_folder, f"split_sii_part{i+1}.csv")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.writelines(split_data)
            print(f"已產生檔案 (SII): {output_file}")


# ========== 3. CSV 拆分 (原 sort_otc_csv.py) ==========

class CSVSplitterOtc:
    def __init__(self, file_path, split_lines, output_folder):
        """
        初始化 CSVSplitter (針對 OTC 資料)
        """
        self.file_path = file_path
        self.split_lines = [line.strip() for line in split_lines]
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)
    
    def split_file(self):
        """
        讀取 CSV 並依照指定的標題行拆分成多個檔案 (OTC 用)
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"找不到檔案: {self.file_path}")
        
        with open(self.file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        split_indices = []
        for i, line in enumerate(lines):
            if line.strip() in self.split_lines:
                split_indices.append(i)
        
        if not split_indices:
            raise ValueError("未找到指定的拆分行 (OTC)")

        split_indices.append(len(lines))
        for i in range(len(split_indices) - 1):
            start, end = split_indices[i], split_indices[i + 1]
            split_data = lines[start:end]
            
            output_file = os.path.join(self.output_folder, f"split_otc_part{i+1}.csv")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.writelines(split_data)
            print(f"已產生檔案 (OTC): {output_file}")


# ========== 4. 合併 CSV (原 sort_all.py) ==========

class CSVCombiner:
    def __init__(self, folder_path, key_columns, output_file, year, season):
        """
        初始化 CSVCombiner
        :param folder_path: 存放 CSV 檔案的資料夾路徑
        :param key_columns: 需要包含的欄位 (只有包含這些欄位的 CSV 才會被合併)
        :param output_file: 合併後輸出的檔案名稱
        :param year: 民國年(字串)
        :param season: 季別(字串)
        """
        self.folder_path = folder_path
        self.key_columns = key_columns
        self.output_file = output_file
        self.year = year
        self.season = season
        self.dataframes = []

    def load_csv_files(self):
        """ 讀取資料夾內所有符合條件的 CSV，並篩選符合條件的檔案 """
        if not os.path.exists(self.folder_path):
            raise FileNotFoundError(f"找不到資料夾: {self.folder_path}")

        # 取得符合條件的 CSV 檔案
        csv_files = [
            f for f in os.listdir(self.folder_path)
            if (f.endswith('.csv') and f.split('_')[-1] != '1.csv')
        ]

        if not csv_files:
            raise ValueError("沒有符合條件的 CSV 檔案")

        for file in csv_files:
            file_path = os.path.join(self.folder_path, file)
            df = pd.read_csv(file_path, encoding='utf-8')

            # 移除 Unnamed 欄位
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

            # 檢查是否包含指定的 key_columns
            if all(col in df.columns for col in self.key_columns):
                print(f"✔ 讀取成功: {file}")
                self.dataframes.append(df)
            else:
                print(f"❌ 跳過: {file}（缺少必要欄位）")

    def clean_data(self, df):
        """
        清理數據：保留數字，移除純文字 (針對非 key_columns)
        """
        def is_valid_number(value):
            """ 判斷是否為有效數字（允許負數與小數點）"""
            if pd.isna(value) or value == "":
                return False
            val = str(value).replace(",", "").strip()
            return val.replace(".", "", 1).replace("-", "", 1).isdigit()

        for col in df.columns:
            if col not in self.key_columns:
                df[col] = df[col].apply(
                    lambda x: str(x).replace(",", "").strip() if is_valid_number(x) else ""
                )
        return df

    def _unify_columns(self, df):
        """
        - 在 DataFrame 中插入「年」、「季」欄位
        - 使用 column_mapping 將欄位改名
        - 最終依照 chinese_list 順序做重排
        """
        # 1. 插入「年」、「季」欄位在最前面
        # 若原本已經有「年」「季」欄位，先刪除
        if "年" in df.columns:
            df.drop(columns=["年"], inplace=True)
        if "季" in df.columns:
            df.drop(columns=["季"], inplace=True)
        
        df.insert(0, "季", self.season)
        df.insert(0, "年", self.year)

        # 2. 逐欄位對照 mapping
        rename_dict = {}
        for col in df.columns:
            # 若有定義對照表則用之，否則保留原名
            rename_dict[col] = column_mapping.get(col, col)

        df.rename(columns=rename_dict, inplace=True)

        # 3. 只保留在 chinese_list 中、且 df 有的欄位，並照順序排列
        existing_cols = list(df.columns)
        final_cols = [c for c in chinese_list if c in existing_cols]
        df = df[final_cols]

        return df

    def merge_data(self):
        """ 合併所有符合條件的 CSV 檔案，並清理數據 + 欄位對齊 """
        if not self.dataframes:
            raise ValueError("沒有符合條件的 CSV 檔案可合併")

        merged_df = pd.concat(self.dataframes, ignore_index=True)

        # 數字清理
        merged_df = self.clean_data(merged_df)
        merged_df = merged_df.loc[:, ~merged_df.columns.str.contains("^Unnamed")]

        # 欄位整合 (含插入年季、合併同義欄位、重排順序)
        merged_df = self._unify_columns(merged_df)

        print(f"✅ 合併並清理完成，共 {len(merged_df)} 筆資料")
        return merged_df

    def save_to_csv(self, df):
        """ 儲存合併後的 DataFrame 到 CSV 檔案 """
        df.to_csv(self.output_file, index=False, encoding='utf-8-sig')
        print(f"📂 已儲存合併結果至: {self.output_file}")




def coalesce_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    針對 df 中同名的欄位 (完全相同的字串)，做 row-wise 合併。
    每列只取第一個非空值，最終僅保留一欄。
    """
    # (1) 建立 {欄位名稱 -> [索引列表]} 的對照
    col_map = defaultdict(list)
    for idx, col in enumerate(df.columns):
        col_map[col].append(idx)

    # (2) 依原欄位「出現順序」，逐一處理
    #     （用 df.columns 的順序來確保順序不亂）
    visited = set()
    new_df = pd.DataFrame()

    for col in df.columns:
        if col in visited:
            continue  # 代表這個欄位名稱已被合併過
        visited.add(col)

        # 找到同樣欄位名稱的所有索引
        dup_indexes = col_map[col]

        if len(dup_indexes) == 1:
            # 只有一個同名欄位，直接複製即可
            new_df[col] = df.iloc[:, dup_indexes[0]]
        else:
            # 有多個同名欄位 → row-wise 合併
            sub = df.iloc[:, dup_indexes].copy()

            # 將空字串視為 NaN（方便往後合併）
            sub = sub.replace("", float("nan"))

            # 利用 bfill(axis=1) 從左到右找第一個非 NaN 值
            # bfill: 將「往右」的有效值往左填補
            # 所以要搭配 iloc[:, ::-1] 或用 fillna 方法實作
            # 常見做法是先反轉再 forward fill，或直接使用 bfill(axis=1)
            # 這裡以 bfill(axis=1) 為例
            coalesced = sub.bfill(axis=1).iloc[:, 0]  # 取得合併後最左欄

            # 可能仍有 row 全部為 nan 的狀況 → 補回空字串
            coalesced = coalesced.fillna("")

            # 將合併結果放入 new_df
            new_df[col] = coalesced

    return new_df






# ========== 主流程整合執行 (示範) ==========
def main(
    year="112",
    season="01",
    raw_output_dir="./raw_data/balance_sheets",   # 存放爬下來 & 拆分的中繼檔路徑
    final_output_dir="./final_data",              # 存放最終合併結果
    merged_output_file="balance_sheet_merged.csv" # 合併檔名(預設)
):
    """
    執行整個「資產負債表」爬蟲+處理流程。
    :param year:  民國年(字串)
    :param season:季別(字串)
    :param raw_output_dir:   放「原始爬下+拆分檔案」的資料夾
    :param final_output_dir: 放「最終合併檔案」的資料夾
    :param merged_output_file: 產生的最終合併檔名
    """
    # 建立資料夾(若不存在)
    os.makedirs(raw_output_dir, exist_ok=True)
    os.makedirs(final_output_dir, exist_ok=True)

    # [1] 先進行爬蟲
    handler = BalanceSheetHandler()
    handler.fetch_balance_sheet(type_k="sii", year=year, season=season, output_dir=raw_output_dir)
    handler.fetch_balance_sheet(type_k="otc", year=year, season=season, output_dir=raw_output_dir)

    # [2] 拆分
    sii_csv_file = os.path.join(raw_output_dir, "balance_sheet_sii_1.csv")
    sii_split_lines = [
        '公司代號,公司名稱,現金及約當現金,存放央行及拆借銀行同業,透過損益按公允價值衡量之金融資產,透過其他綜合損益按公允價值衡量之金融資產,按攤銷後成本衡量之債務工具投資,避險之衍生金融資產淨額,附賣回票券及債券投資淨額,應收款項－淨額,當期所得稅資產,待出售資產－淨額,待分配予業主之資產－淨額,貼現及放款－淨額,採用權益法之投資－淨額,受限制資產－淨額,其他金融資產－淨額,不動產及設備－淨額,使用權資產－淨額,投資性不動產投資－淨額,無形資產－淨額,遞延所得稅資產,其他資產－淨額,資產總額,央行及銀行同業存款,央行及同業融資,透過損益按公允價值衡量之金融負債,避險之衍生金融負債－淨額,附買回票券及債券負債,應付款項,當期所得稅負債,與待出售資產直接相關之負債,存款及匯款,應付金融債券,應付公司債,特別股負債,其他金融負債,負債準備,租賃負債,遞延所得稅負債,其他負債,負債總額,股本,權益─具證券性質之虛擬通貨,資本公積,保留盈餘,其他權益,庫藏股票,歸屬於母公司業主之權益合計,共同控制下前手權益,合併前非屬共同控制股權,非控制權益,權益總額,待註銷股本股數（單位：股）,母公司暨子公司所持有之母公司庫藏股股數（單位：股）,預收股款（權益項下）之約當發行股數（單位：股）,每股參考淨值',
        '公司代號,公司名稱,流動資產,非流動資產,資產總計,流動負債,非流動負債,負債總計,股本,權益－具證券性質之虛擬通貨,資本公積,保留盈餘（或累積虧損）,其他權益,庫藏股票,歸屬於母公司業主權益合計,共同控制下前手權益,合併前非屬共同控制股權,非控制權益,權益總計,待註銷股本股數（單位：股）,預收股款（權益項下）之約當發行股數（單位：股）,母公司暨子公司持有之母公司庫藏股股數（單位：股）,每股參考淨值',
        '公司代號,公司名稱,流動資產,非流動資產,資產總計,流動負債,非流動負債,負債總計,股本,權益─具證券性質之虛擬通貨,資本公積,保留盈餘,其他權益,庫藏股票,歸屬於母公司業主之權益合計,共同控制下前手權益,合併前非屬共同控制股權,非控制權益,權益總計,待註銷股本股數（單位：股）,預收股款（權益項下）之約當發行股數（單位：股）,母公司暨子公司所持有之母公司庫藏股股數（單位：股）,每股參考淨值'
    ]
    splitter_sii = CSVSplitterSii(sii_csv_file, sii_split_lines, raw_output_dir)
    splitter_sii.split_file()

    otc_csv_file = os.path.join(raw_output_dir, "balance_sheet_otc_1.csv")
    otc_split_lines = [
        '公司代號,公司名稱,流動資產,非流動資產,資產總計,流動負債,非流動負債,負債總計,股本,權益－具證券性質之虛擬通貨,資本公積,保留盈餘（或累積虧損）,其他權益,庫藏股票,歸屬於母公司業主權益合計,共同控制下前手權益,合併前非屬共同控制股權,非控制權益,權益總計,待註銷股本股數（單位：股）,預收股款（權益項下）之約當發行股數（單位：股）,母公司暨子公司持有之母公司庫藏股股數（單位：股）,每股參考淨值',
        '公司代號,公司名稱,流動資產,非流動資產,資產總計,流動負債,非流動負債,負債總計,股本,權益─具證券性質之虛擬通貨,資本公積,保留盈餘,其他權益,庫藏股票,歸屬於母公司業主之權益合計,共同控制下前手權益,合併前非屬共同控制股權,非控制權益,權益總計,待註銷股本股數（單位：股）,預收股款（權益項下）之約當發行股數（單位：股）,母公司暨子公司所持有之母公司庫藏股股數（單位：股）,每股參考淨值'
    ]
    splitter_otc = CSVSplitterOtc(otc_csv_file, otc_split_lines, raw_output_dir)
    splitter_otc.split_file()

    # [3] 合併 (會抓 raw_output_dir 下符合條件的 CSV，但排除 *_1.csv)
    key_columns = ["公司代號", "公司名稱"]
    merged_output_path = os.path.join(final_output_dir, merged_output_file)

    combiner = CSVCombiner(
        folder_path=raw_output_dir,
        key_columns=key_columns,
        output_file=merged_output_path,
        year=year,
        season=season,
    )
    combiner.load_csv_files()
    merged_df = combiner.merge_data()
    merged_df = coalesce_duplicate_columns(merged_df)

    # (選擇性) 若怕重複讀取導致多筆資料，這裡可以先做去重
    merged_df.drop_duplicates(
        subset=["年", "季", "公司代號", "公司名稱"],
        keep="last",
        inplace=True
    )

    # 再次對齊欄位順序
    final_cols = [col for col in chinese_list if col in merged_df.columns]
    merged_df = merged_df[final_cols]

    # 寫出最終合併檔
    combiner.save_to_csv(merged_df)

# 保留原本的 "if __name__ == '__main__': main()" 以防獨立執行
if __name__ == "__main__":
    main()