import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import json
import traceback

# ----------------------------------------
# 1. Google Sheets 設定
# ----------------------------------------
SHEET_ID = '1jhqJIoxn1X-M_fPBP2hVFwhrwv3vzUzG0uToJIFPBAA'  # 你的 Sheet ID
SHEET_NAME = '工作表1'    # 試算表裡的工作表名稱

# ----------------------------------------
# 2. 載入 Service Account 憑證（來自 Streamlit Secrets）
#    假設你已在 Streamlit Cloud Secrets 中放置：
#    [gcp_service_account]
#    type = "service_account"
#    project_id = "..."
#    private_key_id = "..."
#    private_key = """
#    -----BEGIN PRIVATE KEY-----
#    ...
#    -----END PRIVATE KEY-----
#    """
#    client_email = "xxx@xxx.iam.gserviceaccount.com"
#    client_id = "..."
#    ...
# ----------------------------------------
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

try:
    service_account_info = st.secrets["gcp_service_account"]
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scope)
    gc = gspread.authorize(credentials)
except Exception as e:
    st.error("無法載入 Google Service Account 憑證，請檢查 Secrets 設定。")
    st.code(traceback.format_exc())
    st.stop()

# ----------------------------------------
# 3. 嘗試開啟 Google Sheet，若失敗顯示錯誤並停止
# ----------------------------------------
try:
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
except Exception as e:
    st.error(f"無法開啟 Google Sheet（open_by_key 失敗）：{e}")
    st.code(traceback.format_exc())
    st.stop()

# ----------------------------------------
# 4. 確保工作表第一列有欄位名稱，否則第一次寫入時先加上標題
# ----------------------------------------
all_values = worksheet.get_all_values()
if not all_values or all_values == [[]]:
    # 如果是空的，就先寫入 header
    worksheet.clear()
    worksheet.append_row(["姓名", "日期", "時段"])

# ----------------------------------------
# 5. 定義讀取與新增資料的函式
# ----------------------------------------
def read_all_records():
    """
    從 Google Sheet 取得全部紀錄，回傳 DataFrame，
    並嘗試把 '日期' 轉成 datetime 以利後續排序與統計。
    """
    data = worksheet.get_all_records()
    if not data:
        # 回傳一個空的 DataFrame，包含固定欄位
        return pd.DataFrame(columns=["姓名", "日期", "時段"])
    df = pd.DataFrame(data)
    try:
        df["日期"] = pd.to_datetime(df["日期"], format="%Y-%m-%d")
    except Exception:
        # 若無法轉，就維持原字串
        pass
    return df

def add_record(name, date_str, meal, prayer_type):
    """
    在 Google Sheet 新增一列：[姓名, 日期, 時段, 禱告方式]
    """
    worksheet.append_row([date_str, name, meal, prayer_type])

# ----------------------------------------
# 6. 頁面設定與固定成員名單
# ----------------------------------------
st.set_page_config(
    page_title= "新世代教會禁食禱告簽到",
    page_icon="🙏",
    layout="wide"
)

member_list = [
    "宇謙", "姿羽", "昱菱", "映君", "子雋", "大大", "黃芩", "映萱", "毓臨", "慧玲",
    "艾鑫", "嵐翌", "Annie", "怡筠", "柏清哥"
]

# 大標題
st.markdown(
    "<h2 style='text-align: center;'>怡筠小組禁食禱告簽到<br><span style='font-size:1em;'>06/09~06/29</span></h3>",
    unsafe_allow_html=True
)
# 設定起始日
start_date = datetime.strptime("2024-06-09", "%Y-%m-%d").date()
today_date = datetime.now().date()

# 計算第幾天
day_count = (today_date - start_date).days + 1

# 星期中文顯示
weekday_dict = {0:"一", 1:"二", 2:"三", 3:"四", 4:"五", 5:"六", 6:"日"}
weekday_str = weekday_dict[today_date.weekday()]

# 顯示格式 
display_today = today_date.strftime("%m/%d") + f"({weekday_str}) 第{day_count}天"

# 今日日期與第幾天顯示
st.markdown(f"<div style='text-align:center; font-size:1.2em; font-weight:bold;'>今天日 {display_today}</div>", unsafe_allow_html=True)

SCHEDULE_SHEET_ID = '1F325FUwqpbvgkITUnIaQ_ZS3Ic77q9w8L4cdrT0iBiA'
SCHEDULE_SHEET_NAME = '工作表1'

scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# 載入憑證
try:
    service_account_info = st.secrets["gcp_service_account"]
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scope)
    gc = gspread.authorize(credentials)
except Exception:
    st.error("無法載入 Google Service Account 憑證，請檢查 Secrets 設定。")
    st.code(traceback.format_exc())
    st.stop()

# 讀取帶領表原始資料
try:
    sched_sh = gc.open_by_key(SCHEDULE_SHEET_ID)
    sched_ws = sched_sh.worksheet(SCHEDULE_SHEET_NAME)
    raw_data = sched_ws.get_all_values()
except Exception as e:
    st.error(f"無法讀取帶領表資料：{e}")
    st.code(traceback.format_exc())
    st.stop()

# Streamlit 標題
display_date = datetime.now().strftime("%m/%d")  # 06/10 格式（兩位數月份）
st.markdown(f"### {display_date} 帶領人員")

today = datetime.now().strftime("%-m/%-d")  # Linux/Mac
# Windows 用：
# today = datetime.now().strftime("%#m/%#d")

# 多組日期列所在 index（以截圖判斷）
date_header_rows = [2, 9, 16]  # 第3、10、17列 index

# 早中晚列相對於日期列的偏移
meal_row_offsets = {
    "早餐": 2,  # 例如日期列2，早餐列4 (2 + 2)
    "午餐": 4,
    "晚餐": 6
}

found = False
leader_info = {}

for date_row_idx in date_header_rows:
    if date_row_idx >= len(raw_data):
        continue
    date_row = raw_data[date_row_idx]
    if today in date_row:
        found = True
        date_col_index = date_row.index(today)

        # 取三餐帶領人
        for meal, offset in meal_row_offsets.items():
            meal_row_idx = date_row_idx + offset
            if meal_row_idx < len(raw_data) and date_col_index < len(raw_data[meal_row_idx]):
                leader = raw_data[meal_row_idx][date_col_index].strip()
            else:
                leader = ""
            leader_info[meal] = leader if leader else "尚未安排"
        break

if not found:
    st.warning(f"找不到今天日期 {today} 在帶領表中")
else:
    for meal in ["早餐", "午餐", "晚餐"]:
        st.markdown(f"- **{meal}**：{leader_info[meal]}")
st.markdown("---")

# ----------------------------------------
# 7. 簽到表單區塊
# ----------------------------------------
st.subheader("每日簽到")
with st.form("sign_in_form"):
    date = st.date_input("選擇日期", datetime.now().date())
    name = st.selectbox("請選擇您的姓名", [""] + member_list, index=0)
    meal = st.selectbox("請選擇今日禁食的時段", [""] + ["早餐", "午餐", "晚餐"], index=0)
    prayer_type = st.selectbox("請選擇禱告方式", [""] + ["自我禱告", "線上禱告"], index=0)
    submitted = st.form_submit_button("提交簽到")

    if submitted:
        if not name or not meal or not prayer_type:
            st.error("請完整選擇姓名、日期、禁食時段與禱告方式")
        else:
            df_existing = read_all_records()
            str_date = date.strftime("%Y-%m-%d")

            # 檢查是否重複簽到（含禱告方式）
            already_signed = False
            if not df_existing.empty:
                df_check = df_existing.copy()
                try:
                    df_check["日期"] = df_check["日期"].dt.strftime("%Y-%m-%d")
                except Exception:
                    df_check["日期"] = df_check["日期"].astype(str)

                already_signed = (
                    (df_check["姓名"] == name) &
                    (df_check["日期"] == str_date) &
                    (df_check["時段"] == meal) &
                    (df_check.get("禱告方式", None) == prayer_type)  # 若欄位不存在會是 None
                ).any()

            if not already_signed:
                add_record(name, str_date, meal, prayer_type)
                st.success(f"感謝 {name} 完成「{meal}」的簽到，禱告方式：{prayer_type}！")
            else:
                st.warning(f"{name} 今天的「{meal}」及「{prayer_type}」已經簽到過囉！")

st.markdown("---")

# ----------------------------------------
# 8. 繪製「各成員累積簽到次數長條圖」
# ----------------------------------------
st.subheader("小組員累積簽到次數")
df_all = read_all_records()

if not df_all.empty:
    # 如果讀到的 DataFrame 中“日期”欄是 datetime 型別，先把它轉回字串，以免後續 groupby 出錯
    if pd.api.types.is_datetime64_any_dtype(df_all["日期"]):
        df_plot = df_all.copy()
        df_plot["日期"] = df_plot["日期"].dt.strftime("%Y-%m-%d")
    else:
        df_plot = df_all.copy()

    # 計算每位成員的累積簽到次數
    count_df = df_plot.groupby("姓名").size().reset_index(name="出席次數")

    # 針對 member_list 補齊零次者
    count_df = count_df.set_index("姓名").reindex(member_list, fill_value=0).reset_index()

    fig_total = px.bar(
        count_df,
        x="姓名",
        y="出席次數",
        color="姓名",             # 每個人不同顏色
        labels={"姓名": "姓名", "出席次數": "簽到次數"}
    )
    fig_total.update_traces(width=0.5)
    st.plotly_chart(fig_total, use_container_width=True)
else:
    st.info("尚無簽到資料，無法顯示累積簽到長條圖。")

# ----------------------------------------
# 9. 顯示「簽到紀錄」表格與「單人成員簽到時段長條圖」
# ----------------------------------------
st.markdown("---")
st.subheader("簽到紀錄")

if not df_all.empty:
    if pd.api.types.is_datetime64_any_dtype(df_all["日期"]):
        df_display = df_all.copy()
        df_display["日期"] = df_display["日期"].dt.strftime("%Y-%m-%d")
    else:
        df_display = df_all.copy()

    
    # 只顯示這四欄，且順序為你指定
    display_cols = ["日期", "姓名", "時段", "禱告方式"]
    for col in display_cols:
        if col not in df_display.columns:
            df_display[col] = ""
    df_display = df_display[display_cols]

    names = sorted(df_display["姓名"].unique())
    selected_name = st.selectbox("選擇成員查看紀錄", ["全部"] + names)

    if selected_name != "全部":
        df_filtered = df_display[df_display["姓名"] == selected_name]
    else:
        df_filtered = df_display

    st.dataframe(df_filtered, use_container_width=True)


    # 若選擇單一成員，就顯示該人各時段累積長條圖
    if selected_name != "全部":
        st.subheader(f"{selected_name} 的簽到時段紀錄")
        # 再將「日期」轉回 datetime 以便畫圖時自動按時間排序
        df_person = df_filtered.copy()
        df_person["date_dt"] = pd.to_datetime(df_person["日期"], format="%Y-%m-%d")
        df_person = df_person.sort_values("date_dt")

        fig_person = px.bar(
            df_person,
            x="date_dt",
            color="時段",
            barmode="group",
            title=f"{selected_name} 各時段簽到紀錄",
            labels={"date_dt": "日期", "時段": "進食時段"}
        )
        st.plotly_chart(fig_person, use_container_width=True)
else:
    st.info("目前尚無簽到紀錄")

# ----------------------------------------
# 10. 使用說明
# ----------------------------------------
st.markdown("---")
st.markdown("### 使用說明")
st.markdown("""
1. 選擇您的姓名  
2. 選擇簽到日期（預設為今天）  
3. 選擇今日禁食的時段（早餐／午餐／晚餐）  
4. 點擊「提交簽到」完成簽到  
5. 上方可檢視「各成員累積簽到次數長條圖」  
6. 下方可查看所有簽到紀錄與單人成員「各時段簽到紀錄長條圖」  
7. 點擊下方連結可看GooleSheets完整紀錄  
https://reurl.cc/AMrZ3Z
""")
