# metrics.py
import pandas as pd

def calculate_monthly_metrics(df):
    """
    計算月度資料的 YoY（同比）與 MOM（環比）
      - YoY：以去年同月比較 (periods=12)
      - MOM：以上個月比較 (periods=1)
    """
    df = df.sort_values(['公司代號', '年', '月']).copy()
    df['YoY'] = df.groupby('公司代號')['營業收入-當月營收'].pct_change(periods=12) * 100
    df['MoM'] = df.groupby('公司代號')['營業收入-當月營收'].pct_change(periods=1) * 100
    return df

def calculate_monthly_qoq(df):
    """
    計算月度資料的 QoQ（以3個月為一季比較）
      - QoQ：以前三個月比較 (periods=3)
    """
    df = df.sort_values(['公司代號', '年', '月']).copy()
    df['QOQ'] = df.groupby('公司代號')['營業收入-當月營收'].pct_change(periods=3) * 100
    return df

def calculate_quarterly_metrics(df):
    """
    計算季度資料的各項財務比率與變化：
      - 流動比率 = 流動資產 / 流動負債
      - 負債比率 = 負債總計(額) / 資產總計(額)
      - 毛利率 = (營業毛利（毛損） / 營業收入) * 100%
      - EPS = 基本每股盈餘（元）
      
    並以各公司依季度計算：
      - QoQ：前一季變化 (periods=1)
      - YOY：以去年同季度比較 (periods=4)
      - 此處 MOM 同 QoQ 以前一季計算（季度資料無月比概念）
    """
    df = df.sort_values(['公司代號', '年', '季']).copy()
    df['流動比率'] = df['流動資產'] / df['流動負債']
    df['負債比率'] = df['負債總計(額)'] / df['資產總計(額)']
    df['毛利率'] = df['營業毛利（毛損）'] / df['營業收入'] * 100
    df['EPS'] = df['基本每股盈餘（元）']
    
    df['流動比率_QoQ'] = df.groupby('公司代號')['流動比率'].pct_change(periods=1) * 100
    df['負債比率_QoQ'] = df.groupby('公司代號')['負債比率'].pct_change(periods=1) * 100
    df['毛利率_QoQ'] = df.groupby('公司代號')['毛利率'].pct_change(periods=1) * 100
    df['EPS_QoQ'] = df.groupby('公司代號')['EPS'].pct_change(periods=1) * 100
    # 以資產總計(額)為例計算 YOY
    df['YoY'] = df.groupby('公司代號')['資產總計(額)'].pct_change(periods=4) * 100
    # 將季度 MOM 亦定義為前一季變化
    df['MOM'] = df.groupby('公司代號')['資產總計(額)'].pct_change(periods=1) * 100
    return df
