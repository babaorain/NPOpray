import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
import traceback
import plotly.graph_objects as go

# 台灣時區
taiwan_tz = pytz.timezone("Asia/Taipei")
now = datetime.now(taiwan_tz)

# Google Sheets 設定
SHEET_ID = '1jhqJIoxn1X-M_fPBP2hVFwhrwv3vzUzG0uToJIFPBAA'
SHEET_NAME = '工作表1'
SCHEDULE_SHEET_ID = '1F325FUwqpbvgkITUnIaQ_ZS3Ic77q9w8L4cdrT0iBiA'
SCHEDULE_SHEET_NAME = '工作表1'
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# 授權與連線
try:
    sa_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
except Exception:
    st.error("Google 憑證錯誤")
    st.code(traceback.format_exc())
    st.stop()

# Sheet 操作
try:
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet(SHEET_NAME)
except Exception:
    st.error("無法開啟 Google Sheet")
    st.code(traceback.format_exc())
    st.stop()

if not ws.get_all_values() or ws.get_all_values() == [[]]:
    ws.clear()
    ws.append_row(["姓名", "日期", "時段", "禱告方式"])

def read_all_records():
    data = ws.get_all_records()
    if not data:
        return pd.DataFrame(columns=["姓名", "日期", "時段", "禱告方式"])
    df = pd.DataFrame(data)
    try:
        df["日期"] = pd.to_datetime(df["日期"], format="%Y-%m-%d")
    except:
        pass
    return df

def add_record(name, date_str, meal, prayer_type):
    ws.append_row([name, date_str, meal, prayer_type])

# 時間設定
start_date = datetime.strptime("2025-06-09", "%Y-%m-%d").date()
today = now.date()
day_count = (today - start_date).days + 1
weekday = "一二三四五六日"[now.weekday()]
display_today = now.strftime("%m/%d") + f" ({weekday}) 禁食第{day_count}天"

# Streamlit UI
st.set_page_config(page_title="新世代教會禁食禱告簽到", page_icon="🙏", layout="wide")

members = [
    "宇謙", "姿羽", "昱菱", "映君", "子雋", "大大", "黃芩", "映萱", "毓臨", "慧玲",
    "艾鑫", "嵐翌", "Annie", "怡筠", "柏清哥"
]

st.markdown(f"""
<div style="text-align: center; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
    <h2 style="font-weight:700;">怡筠小組禁食禱告簽到<br>
    <span style="font-size:1em; color:#555; letter-spacing:2px;">06/09~06/29</span></h2>
</div>
""", unsafe_allow_html=True)

# 帶領表
try:
    sched_sh = gc.open_by_key(SCHEDULE_SHEET_ID)
    sched_ws = sched_sh.worksheet(SCHEDULE_SHEET_NAME)
    raw_data = sched_ws.get_all_values()
except Exception:
    st.error("無法讀取帶領表")
    st.code(traceback.format_exc())
    st.stop()

st.markdown(f"""
<div style="text-align: center; line-height: 2; font-size: 1.2em; font-weight: bold;">
    {display_today}<br>今日帶領人員
</div>
""", unsafe_allow_html=True)

date_fmt = now.strftime("%-m/%-d")  # 若在 Windows 改 "%#m/%#d"
date_header_rows = [2, 9, 16]
meal_row_offsets = {"早餐": 2, "午餐": 4, "晚餐": 6}
leader_info, found = {}, False

for idx in date_header_rows:
    if idx >= len(raw_data): continue
    row = raw_data[idx]
    if date_fmt in row:
        found = True
        col = row.index(date_fmt)
        for meal, offset in meal_row_offsets.items():
            meal_row = idx + offset
            leader = ""
            if meal_row < len(raw_data) and col < len(raw_data[meal_row]):
                leader = raw_data[meal_row][col].strip().replace('\u3000', '')
            leader_info[meal] = leader if leader else "尚未安排"
        break

if not found:
    st.warning(f"找不到今天日期 {date_fmt} 在帶領表中")
else:
    for meal in ["早餐", "午餐", "晚餐"]:
        st.markdown(f"<p style='text-align:center;'><strong>{meal}</strong>：{leader_info[meal]}</p>", unsafe_allow_html=True)
st.markdown("---")

# 簽到表單
st.subheader("每日簽到")
with st.form("sign_in_form"):
    date = st.date_input("選擇日期", today)
    name = st.selectbox("請選擇您的姓名", [""] + members)
    meal = st.selectbox("請選擇今日禁食的時段", ["", "早餐", "午餐", "晚餐"])
    prayer_type = st.selectbox("請選擇禱告方式", ["", "自我禱告", "線上禱告"])
    submitted = st.form_submit_button("提交簽到")
    if submitted:
        if not name or not meal or not prayer_type:
            st.error("請完整選擇姓名、日期、禁食時段與禱告方式")
        else:
            df = read_all_records()
            str_date = date.strftime("%Y-%m-%d")
            already = False
            if not df.empty:
                check = df.copy()
                try:
                    check["日期"] = check["日期"].dt.strftime("%Y-%m-%d")
                except:
                    check["日期"] = check["日期"].astype(str)
                already = (
                    (check["姓名"] == name) &
                    (check["日期"] == str_date) &
                    (check["時段"] == meal) &
                    (check.get("禱告方式", None) == prayer_type)
                ).any()
            if not already:
                add_record(name, str_date, meal, prayer_type)
                st.success(f"感謝 {name} 完成「{meal}」簽到，禱告方式：{prayer_type}！")
            else:
                st.warning(f"{name} 今天的「{meal}」「{prayer_type}」已簽到過")

st.markdown("---")

# 自訂顏色，可依 member 順序自行加長
color_list = [
    "#3498db", "#e67e22", "#9b59b6", "#2ecc71", "#e74c3c", "#1abc9c", "#f1c40f",
    "#34495e", "#95a5a6", "#16a085", "#7f8c8d", "#d35400", "#2980b9", "#c0392b", "#27ae60"
]
color_map = {name: color_list[i % len(color_list)] for i, name in enumerate(members)}

# 取對應顏色序列
bar_colors = [color_map[name] for name in count_df["姓名"]]

# 累積簽到長條圖
st.subheader("小組員累積簽到次數")
df_all = read_all_records()
if not df_all.empty:
    df_plot = df_all.copy()
    if pd.api.types.is_datetime64_any_dtype(df_plot["日期"]):
        df_plot["日期"] = df_plot["日期"].dt.strftime("%Y-%m-%d")
    count_df = df_plot.groupby("姓名").size().reset_index(name="出席次數")
    count_df = count_df.set_index("姓名").reindex(members, fill_value=0).reset_index()
    fig = go.Figure(
    data=[go.Bar(
        x=count_df["姓名"],
        y=count_df["出席次數"],
        marker_color=bar_colors,
        width=[0.7]*len(count_df),  # 每個 bar 寬度設為 0.7（0~1，1是滿格寬）
    )]
    )
    fig.update_layout(
    yaxis_title="簽到次數",
    xaxis_title="姓名",
    title="小組員累積簽到次數",
    bargap=0.3  # bar 間距（可視覺微調）
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("尚無簽到資料")

# 簽到紀錄表格與個人時段圖
st.markdown("---")
st.subheader("簽到紀錄")
if not df_all.empty:
    df_disp = df_all.copy()
    if pd.api.types.is_datetime64_any_dtype(df_disp["日期"]):
        df_disp["日期"] = df_disp["日期"].dt.strftime("%Y-%m-%d")
    display_cols = ["日期", "姓名", "時段", "禱告方式"]
    for col in display_cols:
        if col not in df_disp.columns:
            df_disp[col] = ""
    df_disp = df_disp[display_cols]
    names = sorted(df_disp["姓名"].unique())
    selected = st.selectbox("選擇成員查看紀錄", ["全部"] + names)
    df_view = df_disp[df_disp["姓名"] == selected] if selected != "全部" else df_disp
    st.dataframe(df_view, use_container_width=True)
    if selected != "全部":
        st.subheader(f"{selected} 的簽到時段紀錄")
        df_p = df_view.copy()
        df_p["date_dt"] = pd.to_datetime(df_p["日期"], format="%Y-%m-%d")
        df_p = df_p.sort_values("date_dt")
        fig2 = px.bar(df_p, x="date_dt", color="時段", barmode="group",
                      title=f"{selected} 各時段簽到紀錄",
                      labels={"date_dt": "日期", "時段": "進食時段"})
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("目前尚無簽到紀錄")

# 使用說明
st.markdown("---")
st.markdown("""
### 使用說明
1. 選擇姓名與簽到日期  
2. 選擇今日禁食的時段  
3. 選擇禱告方式  
4. 點擊「提交簽到」  
5. 可查詢累積出席圖與簽到表  
6. 完整記錄請見 [Google Sheets](https://reurl.cc/AMrZ3Z)
""")
