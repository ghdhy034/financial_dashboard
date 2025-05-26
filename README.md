# Financial Dashboard

## 專案簡介

本專案為一套以 Streamlit 為前端的財務數據分析儀表板。資料來源整理、更新及寫入都集中在 `data_pipeline` 資料夾下。前端會讀取本地 `financial_data.db`，並結合各種分析模組，提供單一或多家公司財報視覺化與比對功能。
https://financialdashboard-gn4mai6agt5prjdfay69rq.streamlit.app/


## 安裝與執行方式

1. **安裝 Python 依賴套件**
    ```bash
    pip install -r requirements.txt
    ```

2. **更新資料庫**
    進入 `data_pipeline` 資料夾，根據需求執行對應的資料處理腳本。例如：
    ```bash
    python data_pipeline/script1.py
    ```
    > 實際腳本名稱請依你的檔名替換。

3. **啟動前端**
    ```bash
    streamlit run main.py
    ```

---

## 主要功能說明

- **多公司橫向財報分析**  
  `multi_company_analysis.py`  
  對多家上市公司進行同時比較。

- **個股深度分析**  
  `individual_analysis.py`  
  針對單一公司進行詳細財報與指標檢視。

- **自訂財報評分與綜合排序**  
  `overall_sorting.py`, `metrics.py`  
  多指標評分，便於排序與篩選。

- **資料存取層**  
  `data_access.py`  
  對 `financial_data.db` 的存取操作。

- **資料前處理/更新腳本**  
  `data_pipeline/`  
  包含資料擷取、清洗、寫入資料庫等。

---


## ⚠️ 注意事項

- 每次欲分析新數據，請務必先執行 `data_pipeline` 目錄下腳本，確保資料庫內容為最新。
- **（重要）由於公開資訊觀測站（[https://mops.twse.com.tw/mops/](https://mops.twse.com.tw/mops/)）已於 2025 年 5 月大幅改版，現有爬蟲腳本已無法自動抓取新資料。若需更新數據，請另行調整爬蟲或手動補充資料庫。**
- `financial_data.db` 為系統分析依據，請勿隨意手動修改。
- 本專案以本地執行為主，資料不會自動上傳雲端。




