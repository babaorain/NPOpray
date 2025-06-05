import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json
import traceback  # 用來取得完整堆疊資訊

# ----------------------------------------
# Google Sheets 設定
# ----------------------------------------
SHEET_ID = '1jhqJIoxn1X-M_fPBP2hVFwhrwv3vzUzG0uToJIFPBAA'
SHEET_NAME = '工作表1'

# ----------------------------------------
# 載入 Service Account 憑證
# ----------------------------------------
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# 這裡假設你在 Streamlit Cloud Secrets 放的是一個 dict（直接對應 service account JSON）
service_account_info = st.secrets["gcp_service_account"]

credentials = Credentials.from_service_account_info(
    service_account_info, scopes=scope
)
gc = gspread.authorize(credentials)

# ----------------------------------------
# 嘗試開啟 Google Sheet，如果失敗就把詳細錯誤都印出來
# ----------------------------------------
try:
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
except Exception as e:
    # 先把 Exception 的簡短訊息印出
    st.error(f"無法開啟 Google Sheet（open_by_key 失敗）：{e}")
    # 再把完整的 traceback 印到 Streamlit
    st.code(traceback.format_exc())
    st.stop()

# ----------------------------------------
# 如果程式執行到這裡，就代表 open_by_key 成功
# ----------------------------------------
# 確保第一列有欄位標題，否則第一次會先寫 header
all_values = worksheet.get_all_values()
if not all_values or all_values == [[]]:
    worksheet.clear()
    worksheet.append_row(["姓名", "日期", "時段"])

# ----------------------------------------
# 接下來的程式照之前調整好的邏輯繼續
# ----------------------------------------
member_list = [
    "宇謙", "姿羽", "昱菱", "映君", "子雋", "大大", "黃芩", "映萱", "毓臨", "慧玲",
    "艾鑫", "嵐翌", "Annie", "怡筠", "柏清哥"
]

st.set_page_config(
    page_title="禁食禱告小組簽到系統",
    page_icon="🙏",
    layout="centered"
)

st.title("禁食禱告小組簽到系統")
st.markdown("---")

def read_all_records():
    data = worksheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=["姓名", "日期", "時段"])
    df = pd.DataFrame(data)
    try:
        df["日期"] = pd.to_datetime(df["日期"], format="%Y-%m-%d")
    except:
        pass
    return df

def add_record(name, date_str, meal):
    worksheet.append_row([name, date_str, meal])

st.subheader("每日簽到")
with st.form("sign_in_form"):
    name = st.selectbox("請選擇您的姓名", [""] + member_list, index=0)
    date = st.date_input("選擇日期", datetime.now().date())
    meal = st.selectbox("請選擇今日進食的時段", [""] + ["早餐", "午餐", "晚餐"], index=0)
    submitted = st.form_submit_button("提交簽到")

    if submitted:
        if not name or not meal:
            st.error("請完整選擇姓名、日期與進食時段")
        else:
            df = read_all_records()
            str_date = date.strftime("%Y-%m-%d")
            already_signed = False
            if not df.empty:
                df_check = df.copy()
                try:
                    df_check["日期"] = df_check["日期"].dt.strftime("%Y-%m-%d")
                except:
                    df_check["日期"] = df_check["日期"].astype(str)
                already_signed = (
                    (df_check["姓名"] == name) & 
                    (df_check["日期"] == str_date) & 
                    (df_check["時段"] == meal)
                ).any()

            if not already_signed:
                add_record(name, str_date, meal)
                st.success(f"感謝 {name} 完成「{meal}」的簽到！")
            else:
                st.warning(f"{name} 今天的「{meal}」已經簽到過囉！")

st.markdown("---")

st.subheader("簽到紀錄")
df = read_all_records()
if not df.empty:
    if pd.api.types.is_datetime64_any_dtype(df["日期"]):
        df_display = df.copy()
        df_display["日期"] = df_display["日期"].dt.strftime("%Y-%m-%d")
    else:
        df_display = df

    names = sorted(df_display["姓名"].unique())
    selected_name = st.selectbox("選擇成員查看紀錄", ["全部"] + names)
    if selected_name != "全部":
        df_filtered = df_display[df_display["姓名"] == selected_name]
    else:
        df_filtered = df_display

    st.dataframe(df_filtered, use_container_width=True)

    csv_bytes = df_display.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 下載所有簽到資料 (CSV)",
        data=csv_bytes,
        file_name="attendance_data.csv",
        mime="text/csv"
    )

    if selected_name != "全部":
        st.subheader(f"{selected_name} 的簽到時段紀錄")
        df_plot = df_filtered.copy()
        df_plot["日期"] = pd.to_datetime(df_plot["日期"], format="%Y-%m-%d")
        df_plot = df_plot.sort_values("日期")

        fig = px.bar(
            df_plot,
            x="日期",
            color="時段",
            barmode="group",
            title=f"{selected_name} 各時段簽到紀錄",
            labels={"日期": "日期", "時段": "進食時段"}
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("尚無簽到資料，無法統計。")

st.markdown("---")
st.markdown("### 使用說明")
st.markdown(
    """
1. 選擇您的姓名  
2. 選擇簽到日期（預設為今天）  
3. 選擇今日進食的時段（早餐／午餐／晚餐）  
4. 點擊「提交簽到」完成簽到  
5. 上方可檢視所有成員簽到長條圖（需選擇單一成員）  
6. 下方可查看所有成員簽到紀錄及表格  
7. 點擊「下載所有簽到資料 (CSV)」即可匯出整份紀錄  
    """
)
