import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime

# عرض صورة اللوجو والعنوان
st.image("black.jpeg", width=200)
st.title("Finger Print App")

# رفع ملف CSV
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    # قراءة الملف
    df = pd.read_csv(uploaded_file)

    # تنظيف البيانات
    df['Person ID'] = df['Person ID'].str.lstrip("'")
    df['Person ID'] = df['Person ID'].astype(int)
    df = df.drop(["Department", "Attendance Check Point", "Custom Name", "Data Source", "Handling Type", "Temperature", "Abnormal"], axis=1)

    # تقسيم التاريخ والوقت
    df[['Date', 'Time']] = df['Time'].str.split(' ', expand=True)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.time

    # ترتيب البيانات حسب الموظف والتاريخ والوقت
    df = df.sort_values(by=['Person ID', 'Date', 'Time'])

    # تجميع البيانات لكل موظف في كل يوم
    grouped = df.groupby(['Person ID', 'Name', 'Date'])['Time'].agg(list).reset_index()

    # دالة لتحديد Check In و Check Out بشكل ذكي
    def assign_check_in_out(times):
        if len(times) == 1:  # لو تسجيل واحد فقط
            if times[0] <= datetime.strptime("14:00:00", "%H:%M:%S").time():
                return times[0], None  # يعتبر Check In
            else:
                return None, times[0]  # يعتبر Check Out
        else:
            return times[0], times[-1]  # أول تسجيل Check In وآخر تسجيل Check Out

    # تطبيق الدالة على البيانات
    grouped[['Check In', 'Check Out']] = grouped['Time'].apply(lambda x: pd.Series(assign_check_in_out(x)))

    # حذف العمود الأصلي
    grouped = grouped.drop(columns=['Time'])

    # تعويض القيم الناقصة
    default_check_in = datetime.strptime("09:31:00", "%H:%M:%S").time()
    default_check_out = datetime.strptime("16:30:00", "%H:%M:%S").time()

    grouped['Check In'] = grouped['Check In'].fillna(default_check_in)
    grouped['Check Out'] = grouped['Check Out'].fillna(default_check_out)

    # عرض البيانات بعد المعالجة
    st.subheader("Processed Data")
    st.write(grouped)

    # تحويل DataFrame إلى Excel
    @st.cache_data
    def convert_df_to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        return output.getvalue()

    # زر لتحميل الملف
    st.download_button(
        label="Download Processed Excel File",
        data=convert_df_to_excel(grouped),
        file_name="processed_attendance.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
