import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# ----------------------------------------
# 1. Google Sheets 設定
# ----------------------------------------
SHEET_ID = '1jhqJIoxn1X-M_fPBP2hVFwhrwv3vzUzG0uToJIFPBAA'
SHEET_NAME = '工作表1'

# ----------------------------------------
# 2. 載入 Service Account 憑證
#    假設你在 Streamlit Cloud Secrets 裡面這樣放：
#
#    [gcp_service_account]
#    type = "service_account"
#    project_id = "your-project-id"
#    private_key_id = "..."
#    private_key = """-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"""
#    client_email = "xxx@xxx.iam.gserviceaccount.com"
#    client_id = "..."
#    ...
#
#    如果你是把整個 JSON 字串塞到 st.secrets["gcp_service_account"]["creds"] 的話，
#    請改成： service_account_info = json.loads(st.secrets["gcp_service_account"]["creds"])
# ----------------------------------------

scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# 如果 st.secrets["gcp_service_account"] 本身就是一個 dict（而不是字串），直接用它：
#    service_account_info = st.secrets["gcp_service_account"]
#
# 如果你是把 JSON 字串放在 creds 底下，請把下一行改成：
#    service_account_info = json.loads(st.secrets["gcp_service_account"]["creds"])
service_account_info = st.secrets["gcp_service_account"]

credentials = Credentials.from_service_account_info(
    service_account_info,
    scopes=scope
)
gc = gspread.authorize(credentials)

# ----------------------------------------
# 3. 開啟或建立工作表，並且檢查是否已有 header
# ----------------------------------------
try:
    sh = gc.open_by_key(SHEET_ID)
except Exception as e:
    st.error(f"無法開啟 Google Sheet：{e}")
    st.stop()

# 如果你要確保 header 行存在，可以先去讀第一列，如果沒東西就寫 header
worksheet = sh.worksheet(SHEET_NAME)
all_values = worksheet.get_all_values()

if not all_values or all_values == [[]]:
    # 如果第一列是空的或索引不到，就先寫入欄位標題
    worksheet.clear()
    worksheet.append_row(["姓名", "日期", "時段"])

# ----------------------------------------
# 4. 應用程式標題與固定設定
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

# ----------------------------------------
# 5. 定義讀取與新增資料的函式
# ----------------------------------------
def read_all_records():
    """讀全部紀錄並回傳 DataFrame，順便把 '日期' 轉成 datetime"""
    data = worksheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=["姓名", "日期", "時段"])

    df = pd.DataFrame(data)
    # 把「日期」從字串轉成 datetime，以利之後排序或畫圖
    try:
        df["日期"] = pd.to_datetime(df["日期"], format="%Y-%m-%d")
    except Exception:
        # 如果格式不對就跳過
        pass
    return df

def add_record(name, date_str, meal):
    """加一筆新資料到 Google Sheet"""
    # date_str 已經是 'YYYY-MM-DD' 格式
    worksheet.append_row([name, date_str, meal])

# ----------------------------------------
# 6. 簽到表單
# ----------------------------------------
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

            # 檢查今天這個人、這個時段是否已簽到
            already_signed = False
            if not df.empty:
                # 因為我們把 df["日期"] 轉成 datetime，所以要比較 to_datetime
                df_check = df.copy()
                try:
                    df_check["日期"] = df_check["日期"].dt.strftime("%Y-%m-%d")
                except Exception:
                    # 如果原本就沒轉，直接當字串比
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

# ----------------------------------------
# 7. 顯示簽到紀錄
# ----------------------------------------
st.subheader("簽到紀錄")
df = read_all_records()

if not df.empty:
    # 如果日期欄是 datetime，要換回字串顯示
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

    # 直接顯示下載按鈕，下載 CSV（UTF-8 BOM）
    csv_bytes = df_display.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 下載所有簽到資料 (CSV)",
        data=csv_bytes,
        file_name="attendance_data.csv",
        mime="text/csv"
    )

    # 如果使用者選擇了單一成員，就額外畫長條圖
    if selected_name != "全部":
        st.subheader(f"{selected_name} 的簽到時段紀錄")
        # 先把 "日期" 重新轉回 datetime，方便畫圖時自動排序
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

# ----------------------------------------
# 8. 使用說明
# ----------------------------------------
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
