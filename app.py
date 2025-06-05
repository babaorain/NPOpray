import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets 設定
SHEET_ID = '1jhqJIoxn1X-M_fPBP2hVFwhrwv3vzUzG0uToJIFPBAA'  # 例如 '1FXXXXXfMgHWjP4eXXXXXnmvI0cw44xw4ABCdT7hZxxxx'
SHEET_NAME = '工作表1'   # 你要存資料的工作表名稱，預設 '工作表1'

# Streamlit secrets 管理金鑰
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)
gc = gspread.authorize(credentials)
sh = gc.open_by_key(SHEET_ID)
worksheet = sh.worksheet(SHEET_NAME)

# 小組固定成員
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

# 資料讀取 function
def read_all_records():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# 新增一筆資料
def add_record(name, date, meal):
    worksheet.append_row([name, date, meal])

# 簽到表單
st.subheader("每日簽到")
with st.form("sign_in_form"):
    name = st.selectbox("請選擇您的姓名", [""] + member_list, index=0)
    date = st.date_input("選擇日期", datetime.now())
    meal = st.selectbox("請選擇今日進食的時段", [""] + ["早餐", "午餐", "晚餐"], index=0)
    submitted = st.form_submit_button("提交簽到")
    if submitted:
        if not name or not meal or not date:
            st.error("請完整選擇姓名、日期與進食時段")
        else:
            df = read_all_records()
            str_date = date.strftime("%Y-%m-%d")
            already_signed = (
                (df["姓名"] == name) & (df["日期"] == str_date) & (df["時段"] == meal)
            ).any() if not df.empty else False
            if not already_signed:
                add_record(name, str_date, meal)
                st.success(f"感謝 {name} 完成「{meal}」的簽到！")
            else:
                st.warning(f"{name} 今天的「{meal}」已經簽到過囉！")

st.markdown("---")
st.subheader("簽到紀錄")

# 讀取資料
df = read_all_records()
if not df.empty:
    names = sorted(df['姓名'].unique())
    selected_name = st.selectbox("選擇成員查看紀錄", ["全部"] + list(names))
    if selected_name != "全部":
        df_filtered = df[df['姓名'] == selected_name]
    else:
        df_filtered = df

    st.dataframe(df_filtered, use_container_width=True)

    # 匯出資料
    if st.button("匯出資料為 CSV"):
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "下載 CSV 檔案",
            csv,
            "attendance_data.csv",
            "text/csv",
            key='download-csv'
        )

    # 個人成員簽到紀錄圖
    if selected_name != "全部":
        st.subheader(f"{selected_name} 的簽到時段紀錄")
        fig = px.bar(
            df_filtered,
            x='日期',
            color='時段',
            barmode='group',
            title=f"{selected_name} 各時段簽到紀錄",
            labels={'日期': '日期', '時段': '進食時段'}
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("目前尚無
