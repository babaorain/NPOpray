import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

# 頁面設定
st.set_page_config(
    page_title="禁食禱告小組簽到系統",
    page_icon="🙏",
    layout="wide"
)

# 小組固定成員
member_list = [
    "宇謙", "姿羽", "昱菱", "映君", "子雋", "大大", "黃芩", "映萱", "毓臨", "慧玲",
    "艾鑫", "嵐翌", "Annie", "怡筠", "柏清哥"
]

# 初始化 session state
if 'attendance_data' not in st.session_state:
    st.session_state.attendance_data = []

# 儲存資料到檔案
def save_data():
    with open('attendance.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.attendance_data, f, ensure_ascii=False)

# 載入現有資料
def load_data():
    if os.path.exists('attendance.json'):
        with open('attendance.json', 'r', encoding='utf-8') as f:
            st.session_state.attendance_data = json.load(f)

load_data()

# 標題
st.title("禁食禱告小組簽到系統")
st.markdown("---")

# 簽到表單
with st.form("sign_in_form"):
    st.subheader("每日簽到")
    name = st.selectbox("請選擇您的姓名", member_list)
    date = st.date_input("選擇日期", datetime.now())
    meal = st.selectbox("請選擇今日進食的時段", ["早餐", "午餐", "晚餐"])
    submitted = st.form_submit_button("提交簽到")
    if submitted:
        attendance_record = {
            "name": name,
            "date": date.strftime("%Y-%m-%d"),
            "meal": meal
        }
        # 防止同一人同一天同時段重複簽到
        already_signed = any(
            rec["name"] == name and rec["date"] == attendance_record["date"] and rec["meal"] == meal
            for rec in st.session_state.attendance_data
        )
        if not already_signed:
            st.session_state.attendance_data.append(attendance_record)
            save_data()
            st.success(f"感謝 {name} 完成「{meal}」的簽到！")
        else:
            st.warning(f"{name} 今天的「{meal}」已經簽到過囉！")

# 顯示簽到紀錄
st.markdown("---")
st.subheader("簽到紀錄")

if st.session_state.attendance_data:
    df = pd.DataFrame(st.session_state.attendance_data)
    names = sorted(df['name'].unique())
    selected_name = st.selectbox("選擇成員查看紀錄", ["全部"] + list(names))
    if selected_name != "全部":
        df_filtered = df[df['name'] == selected_name]
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

    # 單人成員簽到折線/長條圖
    if selected_name != "全部":
        st.subheader(f"{selected_name} 的簽到時段紀錄")
        fig = px.bar(
            df_filtered,
            x='date',
            color='meal',
            barmode='group',
            title=f"{selected_name} 各時段簽到紀錄",
            labels={'date': '日期', 'meal': '進食時段'}
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("目前尚無簽到紀錄")

# 全員累積簽到次數統計圖
st.markdown("---")
st.subheader("各成員累積簽到次數（含所有時段）")
if st.session_state.attendance_data:
    df = pd.DataFrame(st.session_state.attendance_data)
    count_df = df.groupby('name').size().reset_index(name='出席次數')
    count_df = count_df.set_index('name').reindex(member_list, fill_value=0).reset_index()
    fig2 = px.bar(
        count_df,
        x='name',
        y='出席次數',
        title="各成員累積簽到次數",
        labels={'name': '姓名', '出席次數': '簽到次數'}
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("尚無簽到資料，無法統計。")

# 使用說明
st.markdown("---")
st.markdown("### 使用說明")
st.markdown("""
1. 選擇您的姓名
2. 選擇簽到日期（預設為今天）
3. 選擇今日進食的時段（早餐／午餐／晚餐）
4. 點擊提交完成簽到
5. 下方可查看所有成員簽到紀錄及圖表
6. 可匯出資料為 CSV 檔案
""")
