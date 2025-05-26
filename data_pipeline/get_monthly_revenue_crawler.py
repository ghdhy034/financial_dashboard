import os
import time
import csv
import shutil
import itertools
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import random

class TWSEMonthlyRevenueDownloader:
    """
    負責從 MOPS 下載指定市場、民國年份、月份的營收報表 CSV
    並存放於 self.download_path
    """

    def __init__(self, download_path="downloads", max_net_retries=3, download_timeout=30, download_retries=3):
        """
        :param download_path: 下載資料夾路徑 (不會主動清空)
        :param max_net_retries: 若遇到瀏覽器 net::ERR_CONNECTION_RESET 等網路錯誤，最多嘗試連線次數
        :param download_timeout: 單次下載檔案的輪詢等待最長秒數
        :param download_retries: 單一 (market, year, month) 下載最多嘗試次數 (例如超時後再重試 2 次)
        """
        self.download_path = os.path.abspath(download_path)
        self.max_net_retries = max_net_retries
        self.download_timeout = download_timeout
        self.download_retries = download_retries

        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        # 設定 Edge 的選項
        options = webdriver.EdgeOptions()
        prefs = {"download.default_directory": self.download_path}
        options.add_experimental_option("prefs", prefs)

        # 無頭模式
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")

        # 啟動 Edge WebDriver
        self.driver = webdriver.Edge(options=options)

    def download_csv(self, market, year, month):
        """
        下載指定市場、年、月的營收報表 CSV
        :param market: "sii" (上市) 或 "otc" (上櫃)
        :param year: 民國年 (110 = 2021, 111 = 2022, ...)
        :param month: 1~12 (月份)
        """
        # 目標檔名 (如果已存在就略過)
        new_filename = f"monthly_revenue_{market}_{year}_{month}.csv"
        new_filepath = os.path.join(self.download_path, new_filename)

        # 若發現目標檔已存在，直接略過
        if os.path.exists(new_filepath):
            print(f"⚠️ 目標檔已存在，略過下載: {new_filename}")
            return

        # 要前往的目標網址
        url = f"https://mops.twse.com.tw/nas/t21/{market}/t21sc03_{year}_{month}_0.html"
        print(f"🔍 嘗試開啟網頁: {url}")
        sleep_time = random.uniform(1, 1.5)  # 產生 0.5~1 秒之間的隨機秒數
        time.sleep(sleep_time)
        # (A) 先嘗試連線 (driver.get) 時，做網路錯誤重試
        for attempt in range(1, self.max_net_retries + 1):
            try:
                self.driver.get(url)
                break  # 成功連線就離開迴圈
            except WebDriverException as e:
                print(f"⚠️ [網路錯誤:第 {attempt} 次] {e}")
                if attempt == self.max_net_retries:
                    print(f"❌ 無法連線至 {url}，放棄下載。")
                    return
                time.sleep(3)  # 等幾秒再重試

        # 執行「嘗試下載 CSV」的流程，若超時可再重試
        for dl_try in range(1, self.download_retries + 1):
            success = self._try_download_csv_once(market, year, month, new_filename)
            if success:
                # 成功下載就跳出
                break
            else:
                print(f"⏳ 下載失敗/超時，準備進行第 {dl_try+1} 次嘗試...")
                time.sleep(2)

        else:
            # 如果執行完 self.download_retries 次仍未成功，就放棄
            print(f"❌ 已嘗試 {self.download_retries} 次下載 ({market} {year}_{month}) 仍失敗，跳過。")

    def _try_download_csv_once(self, market, year, month, new_filename):
        """
        單次嘗試下載，若成功下載並改名回傳 True，
        若逾時或沒抓到檔案則回傳 False。
        """
        before_download = set(os.listdir(self.download_path))
        try:
            # 找到「下載 CSV」按鈕
            try:
                download_button = self.driver.find_element(By.NAME, "download")
            except NoSuchElementException:
                print(f"❌ 查無下載按鈕，可能該頁面無資料: {market} {year}_{month}")
                return False

            download_button.click()
            print(f"✅ 第一次請求下載 {market} {year}_{month} 的 CSV 檔案...")

            downloaded_file = None
            start_time = time.time()

            while True:
                after_download = set(os.listdir(self.download_path)) - before_download
                if after_download:
                    # 找出「最新修改時間」的檔案
                    candidate = max(after_download, key=lambda f: os.path.getmtime(os.path.join(self.download_path, f)))
                    candidate_path = os.path.join(self.download_path, candidate)

                    # 若副檔名是 csv，檢查檔案大小是否穩定
                    if candidate.endswith(".csv"):
                        size1 = os.path.getsize(candidate_path)
                        time.sleep(1)
                        size2 = os.path.getsize(candidate_path)
                        if size1 == size2:
                            downloaded_file = candidate
                            break

                # 若超過等待時間就視為超時
                if time.time() - start_time > self.download_timeout:
                    print(f"❌ 下載等待超時 (超過 {self.download_timeout} 秒) - {market} {year}_{month}")
                    return False

                time.sleep(1)

            old_filepath = os.path.join(self.download_path, downloaded_file)
            new_filepath = os.path.join(self.download_path, new_filename)

            # 若目標檔已存在(理論上不應該發生，除非重名)，先刪除
            if os.path.exists(new_filepath):
                os.remove(new_filepath)

            os.rename(old_filepath, new_filepath)
            print(f"📁 下載完成！\n   原檔名: {downloaded_file}\n   新檔名: {new_filename}")
            return True

        except Exception as e:
            print(f"⚠️ 單次下載失敗: {e}")
            return False

    def close(self):
        """關閉瀏覽器"""
        self.driver.quit()
        print("🛑 瀏覽器已關閉。")


class MonthlyRevenueCSVTransformer:
    """
    專門用來讀取原始 CSV，篩選/重排欄位並輸出到新的資料夾
    需求：只保留下列欄位，順序如下：
       年, 月, 公司代號, 公司名稱, 產業別, 營業收入-當月營收, 備註
    """
    def __init__(self, input_dir, output_dir="monthly_revenue_processed"):
        self.input_dir = input_dir
        self.output_dir = output_dir

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # 想要輸出的最終欄位順序
        self.target_fields = [
            "年", 
            "月", 
            "公司代號", 
            "公司名稱", 
            "產業別", 
            "營業收入-當月營收", 
            "備註"
        ]
    
    def transform_file(self, filename):
        """
        讀取 input_dir 下的指定 CSV 檔案，抽取欄位並重新命名/排序後
        輸出到 output_dir 下同名檔
        """
        input_path = os.path.join(self.input_dir, filename)
        output_path = os.path.join(self.output_dir, filename)

        with open(input_path, "r", encoding="utf-8-sig", newline="") as fin, \
             open(output_path, "w", encoding="utf-8-sig", newline="") as fout:

            reader = csv.DictReader(fin)
            writer = csv.DictWriter(fout, fieldnames=self.target_fields)
            writer.writeheader()

            for row in reader:
                data_ym = row.get("資料年月", "")
                if "/" in data_ym:
                    parts = data_ym.split("/")
                    year_str = parts[0]  # 例如 "110"
                    month_str = parts[1] # 例如 "1"
                else:
                    year_str, month_str = "", ""

                new_row = {
                    "年": year_str,
                    "月": month_str,
                    "公司代號": row.get("公司代號", ""),
                    "公司名稱": row.get("公司名稱", ""),
                    "產業別": row.get("產業別", ""),
                    "營業收入-當月營收": row.get("營業收入-當月營收", ""),
                    "備註": row.get("備註", "")
                }
                writer.writerow(new_row)

        print(f"✅ 已處理完畢: {filename} => {output_path}")


# --------------------------
# 🎯 主程式 (批量下載 + 轉檔)
# --------------------------
def main():
    download_path = "./monthly_revenue"

    # (1) 這裡不再清空資料夾，若有舊檔案則保留；若再次下載同檔就略過
    # if os.path.exists(download_path):
    #     shutil.rmtree(download_path)
    # os.makedirs(download_path, exist_ok=True)

    # (2) 要查詢的市場 / 年 / 月

    start_year=110
    end_year=113
    markets = ["sii", "otc"]
    years = [year for year in range(start_year, end_year+1)]
    months = [1,2,3,4,5,6,7,8,9,10,11,12]

    '''
    markets = ["sii", "otc"]
    years = [114]
    months = [2]
    '''

    # (3) 建立下載器 (不清空舊資料、支持下載重試)
    downloader = TWSEMonthlyRevenueDownloader(
        download_path=download_path,
        max_net_retries=2,       # 碰到連線錯誤時，最多連線嘗試3次
        download_timeout=12,     # 單次下載輪詢 30 秒
        download_retries=1       # 若超時或失敗，再點一次下載按鈕，最多 3 次
    )

    # (4) 下載執行
    for market, year, month in itertools.product(markets, years, months):
        downloader.download_csv(market, year, month)


    # (5) 關閉瀏覽器
    downloader.close()

    # (6) 建立 CSV 轉換器，將原始檔案轉成指定欄位
    transformer = MonthlyRevenueCSVTransformer(
        input_dir=download_path,
        output_dir="./monthly_revenue_processed"
    )

    # (7) 批次讀取 download_path 中所有 `monthly_revenue_*.csv` 並轉換
    for file in os.listdir(download_path):
        if file.startswith("monthly_revenue_") and file.endswith(".csv"):
            transformer.transform_file(file)

if __name__ == "__main__":
    main()
