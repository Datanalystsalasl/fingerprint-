import io
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

# عنوان التطبيق
st.image("black.jpeg", width=200)
st.title("Finger print app")

# رفع ملف CSV
uploaded_file = st.file_uploader("upload CSV file", type=["csv"])

if uploaded_file is not None:
    # قراءة الملف
    df = pd.read_csv(uploaded_file)

    # تنظيف البيانات وإجراء العمليات
    df['Person ID'] = df['Person ID'].str.lstrip("'")
    df['Person ID'] = df['Person ID'].astype(int)
    df = df.drop(["Department", "Attendance Check Point", "Custom Name", "Data Source", "Handling Type", "Temperature", "Abnormal"], axis=1)
    df[['Date', 'Time']] = df['Time'].str.split(' ', expand=True)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['CheckType'] = np.where(df['Time'] <= '14:00:00', 'Check In', 'Check Out')
    df = df.drop('Attendance Status', axis=1)

    df = df.pivot_table(
        index=['Person ID', 'Name', 'Date'],
        columns='CheckType',
        values='Time',
        aggfunc='last'
    ).reset_index()

    df['Check In'] = df['Check In'].fillna('9:30:00')
    df['Check Out'] = df['Check Out'].fillna('16:30:00')
    df['Check In'] = pd.to_datetime(df['Check In'], format='%H:%M:%S')
    df['Check Out'] = pd.to_datetime(df['Check Out'], format='%H:%M:%S')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    reference_time = pd.to_datetime('1900-01-01 17:00:00')

    df['Over Time'] = df['Check Out'] - reference_time
    df['Over Time'] = pd.to_timedelta(df['Over Time'])

    for index, row in df.iterrows():
        if row['Over Time'] < timedelta(0):
            df.at[index, 'Over Time'] = timedelta(0)

    df['Over Time'] = df['Over Time'].apply(
        lambda x: f"{int(x.total_seconds() // 3600)}:{int(abs(x.total_seconds() % 3600) // 60):02d}:{int(abs(x.total_seconds() % 60)):02d}"
    )

    reference_in_time = pd.to_datetime('1900-01-01 9:00:00')
    df['Delay time'] = df['Check In'] - reference_in_time
    df['Delay time'] = pd.to_timedelta(df['Delay time'])

    for index, row in df.iterrows():
        if row['Delay time'] < timedelta(0):
            df.at[index, 'Delay time'] = timedelta(0)

    df['Delay time'] = df['Delay time'].apply(
        lambda x: f"{int(x.total_seconds() // 3600)}:{int(abs(x.total_seconds() % 3600) // 60):02d}:{int(abs(x.total_seconds() % 60)):02d}"
    )

    df['Real Duration'] = df['Check Out'] - df['Check In']
    df['Real Duration'] = df['Real Duration'].apply(
        lambda x: f"{int(x.total_seconds() // 3600)}:{int(abs(x.total_seconds() % 3600) // 60):02d}:{int(abs(x.total_seconds() % 60)):02d}"
    )

    df['Check In'] = pd.to_datetime(df['Check In'], format='%H:%M:%S').dt.time
    df['Check Out'] = pd.to_datetime(df['Check Out'], format='%H:%M:%S').dt.time

    # عرض البيانات بعد التعديل
    st.subheader("Data after Processing")
    st.write(df)


    # وظيفة لتحويل DataFrame إلى ملف Excel
    @st.cache_data
    def convert_df_to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        processed_data = output.getvalue()
        return processed_data


    # زر لتنزيل الملف المعدل
    st.download_button(
        label="Download Excel file",
        data=convert_df_to_excel(df),
        file_name="data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
