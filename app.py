import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

# 设置页面配置
st.set_page_config(
    page_title="禁食祷告小组签到系统",
    page_icon="🙏",
    layout="wide"
)

# 初始化 session state
if 'attendance_data' not in st.session_state:
    st.session_state.attendance_data = []

# 保存数据到文件
def save_data():
    with open('attendance.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.attendance_data, f, ensure_ascii=False)

# 加载数据
def load_data():
    if os.path.exists('attendance.json'):
        with open('attendance.json', 'r', encoding='utf-8') as f:
            st.session_state.attendance_data = json.load(f)

# 加载已有数据
load_data()

# 标题
st.title("禁食祷告小组签到系统")
st.markdown("---")

# 签到表单
with st.form("sign_in_form"):
    st.subheader("每日签到")
    name = st.text_input("请输入您的姓名")
    date = st.date_input("选择日期", datetime.now())
    notes = st.text_area("祷告心得（选填）")
    
    submitted = st.form_submit_button("提交签到")
    
    if submitted and name:
        attendance_record = {
            "name": name,
            "date": date.strftime("%Y-%m-%d"),
            "notes": notes
        }
        st.session_state.attendance_data.append(attendance_record)
        save_data()
        st.success(f"感谢 {name} 的签到！")
    elif submitted and not name:
        st.error("请输入您的姓名")

# 显示签到记录
st.markdown("---")
st.subheader("签到记录")

# 转换为 DataFrame
if st.session_state.attendance_data:
    df = pd.DataFrame(st.session_state.attendance_data)
    
    # 按姓名筛选
    names = sorted(df['name'].unique())
    selected_name = st.selectbox("选择成员查看记录", ["全部"] + list(names))
    
    if selected_name != "全部":
        df_filtered = df[df['name'] == selected_name]
    else:
        df_filtered = df
    
    # 显示数据表格
    st.dataframe(df_filtered, use_container_width=True)
    
    # 导出数据
    if st.button("导出数据为 CSV"):
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "下载 CSV 文件",
            csv,
            "attendance_data.csv",
            "text/csv",
            key='download-csv'
        )
    
    # 可视化
    if selected_name != "全部":
        st.subheader(f"{selected_name} 的签到统计")
        
        # 创建柱状图
        fig = px.bar(
            df_filtered,
            x='date',
            title=f"{selected_name} 的签到记录",
            labels={'date': '日期', 'name': '姓名'}
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("暂无签到记录")

# 页脚
st.markdown("---")
st.markdown("### 使用说明")
st.markdown("""
1. 在签到表单中输入您的姓名
2. 选择签到日期（默认为今天）
3. 可选填写祷告心得
4. 点击提交完成签到
5. 在下方可以查看所有成员的签到记录
6. 可以选择特定成员查看其签到统计
""") 