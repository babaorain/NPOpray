import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pytz
import gspread
from google.oauth2.service_account import Credentials
import traceback

# ----------------------------------------
# 1. 台灣時區設定
# ----------------------------------------
taiwan_tz = pytz.timezone("Asia/Taipei")
now_taiwan = datetime.now(taiwan_tz)

# ----------------------------------------
# 2. Google Sheets 設定
# ----------------------------------------
SHEET_ID = '1jhqJIoxn1X-M_fPBP2hVFwhrwv3vzUzG0uToJIFPBAA'  # 你的 Sheet ID
SHEET_NAME = '工作表1'    # 試算表裡的工作表名稱

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

try:
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
except Exception as e:
    st.error(f"無法開啟 Google Sheet（open_by_key 失敗）：{e}")
    st.code(traceback.format_exc())
    st.stop()

# ----------------------------------------
# 3. 確保工作表第一列有欄位名稱，否則第一次寫入時先加上標題
# ----------------------------------------
all_values = worksheet.get_all_values()
if not all_values or all_values == [[]]:
    worksheet.clear()
    worksheet.append_row(["姓名", "日期", "時段", "禱告方式"])

# ----------------------------------------
# 4. 定義讀取與新增資料的函式
# ----------------------------------------
def read_all_records():
    data = worksheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=["姓名", "日期", "時段", "禱告方式"])
    df = pd.DataFrame(data)
    try:
        df["日期"] = pd.to_datetime(df["日期"], format="%Y-%m-%d")
    except Exception:
        pass
    return df

def add_record(name, date_str, meal, prayer_type):
    worksheet.append_row([name, date_str, meal, prayer_type])

# ----------------------------------------
# 5. 時間相關設定
# ----------------------------------------
start_date = datetime.strptime("2025-06-09", "%Y-%m-%d").date()
today_date = now_taiwan.date()
day_count = (today_date - start_date).days + 1
weekday_dict = {0:"一", 1:"二", 2:"三", 3:"四", 4:"五", 5:"六", 6:"日"}
weekday_str = weekday_dict[now_taiwan.weekday()]
display_today = now_taiwan.strftime("%m/%d") + f" ({weekday_str}) 禁食第{day_count}天"

# ----------------------------------------
# 6. Streamlit 頁面配置與 UI
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
    f"""
    <div style="text-align: center; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin-bottom: 10px;">
        <h2 style="
            font-weight: 700;
            font-size: 2.0em;
            color: #000000;
            margin-bottom: 0em;
        ">
            怡筠小組禁食禱告簽到<br>
            <span style="font-size:1em; color: #555; letter-spacing: 2px;">06/09~06/29</span>
        </h2>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------------------
# 7. 讀取帶領表資料設定（第二個 Google Sheet）
# ----------------------------------------
SCHEDULE_SHEET_ID = '1F325FUwqpbvgkITUnIaQ_ZS3Ic77q9w8L4cdrT0iBiA'
SCHEDULE_SHEET_NAME = '工作表1'

try:
    sched_sh = gc.open_by_key(SCHEDULE_SHEET_ID)
    sched_ws = sched_sh.worksheet(SCHEDULE_SHEET_NAME)
    raw_data = sched_ws.get_all_values()
except Exception as e:
    st.error(f"無法讀取帶領表資料：{e}")
    st.code(traceback.format_exc())
    st.stop()

# 顯示今日日期與帶領人
st.markdown(
    f"""
    <div style="text-align: center; line-height: 2; font-size: 1.2em; font-weight: bold; margin-bottom: 10px;">
        {display_today}<br>
        今日帶領人員
    </div>
    """,
    unsafe_allow_html=True)

# 使用台灣時區取得的日期，格式跟帶領表對應
today = now_taiwan.strftime("%-m/%-d")  # Linux/Mac，如 Windows 請改成 "%#m/%#d"

date_header_rows = [2, 9, 16]  # 帶領表日期列索引（0-based）

meal_row_offsets = {
    "早餐": 2,
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

        for meal, offset in meal_row_offsets.items():
            meal_row_idx = date_row_idx + offset
            if meal_row_idx < len(raw_data) and date_col_index < len(raw_data[meal_row_idx]):
                leader = raw_data[meal_row_idx][date_col_index].strip().replace('\u3000', '')
            else:
                leader = ""
            leader_info[meal] = leader if leader else "尚未安排"
        break

if not found:
    st.warning(f"找不到今天日期 {today} 在帶領表中")
else:
    for meal in ["早餐", "午餐", "晚餐"]:
        st.markdown(
            f"""
            <p style="text-align:center;"><strong>{meal}</strong>：{leader_info[meal]}</p>
            """,
            unsafe_allow_html=True
        )

st.markdown("---")

# ----------------------------------------
# 8. 簽到表單
# ----------------------------------------
st.subheader("每日簽到")
with st.form("sign_in_form"):
    date = st.date_input("選擇日期", now_taiwan.date())
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
                    (df_check.get("禱告方式", None) == prayer_type)
                ).any()

            if not already_signed:
                add_record(name, str_date, meal, prayer_type)
                st.success(f"感謝 {name} 完成「{meal}」的簽到，禱告方式：{prayer_type}！")
            else:
                st.warning(f"{name} 今天的「{meal}」及「{prayer_type}」已經簽到過囉！")

st.markdown("---")

# ----------------------------------------
# 9. 繪製累積簽到長條圖
# ----------------------------------------
st.subheader("小組員累積簽到次數")
df_all = read_all_records()

if not df_all.empty:
    if pd.api.types.is_datetime64_any_dtype(df_all["日期"]):
        df_plot = df_all.copy()
        df_plot["日期"] = df_plot["日期"].dt.strftime("%Y-%m-%d")
    else:
        df_plot = df_all.copy()

    count_df = df_plot.groupby("姓名").size().reset_index(name="出席次數")
    count_df = count_df.set_index("姓名").reindex(member_list, fill_value=0).reset_index()

    fig_total = px.bar(
        count_df,
        x="姓名",
        y="出席次數",
        color="姓名",
        labels={"姓名": "姓名", "出席次數": "簽到次數"}
    )
    fig_total.update_traces(width=0.5)
    st.plotly_chart(fig_total, use_container_width=True)
else:
    st.info("尚無簽到資料，無法顯示累積簽到長條圖。")

# ----------------------------------------
# 10. 顯示簽到紀錄表格與單人成員時段長條圖
# ----------------------------------------
st.markdown("---")
st.subheader("簽到紀錄")

if not df_all.empty:
    if pd.api.types.is_datetime64_any_dtype(df_all["日期"]):
        df_display = df_all.copy()
        df_display["日期"] = df_display["日期"].dt.strftime("%Y-%m-%d")
    else:
        df_display = df_all.copy()

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

    if selected_name != "全部":
        st.subheader(f"{selected_name} 的簽到時段紀錄")
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
# 11. 使用說明
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
