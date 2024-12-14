import streamlit as st
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
import pymysql

load_dotenv()  # .env 파일 로드

# 환경 변수 설정
OPENAI_API_KEY = st.secrets('OPENAI_API_KEY')

# MySQL에서 데이터 불러오기 함수
def fetch_records():
    db = pymysql.connect(
        host=st.secrets("DB_HOST"),
        user=st.secrets("DB_USER"),
        password=st.secrets("DB_PASSWORD"),
        database=st.secrets("DB_DATABASE"),
        charset='utf8mb4'  # 문자 집합 설정
    )
    cursor = db.cursor()
    
    # SQL 쿼리에서 number 범위에 따른 정렬
    query = """
    SELECT id, number, name, time 
    FROM qna
    ORDER BY
      CASE WHEN number >= 10300 AND number < 10400 THEN 0 ELSE 1 END,
      number
    """
    
    cursor.execute(query)
    records = cursor.fetchall()
    cursor.close()
    db.close()
    return records

# MySQL에서 특정 레코드 불러오기 함수
def fetch_record_by_id(record_id):
    db = pymysql.connect(
        host=st.secrets("DB_HOST"),
        user=st.secrets("DB_USER"),
        password=st.secrets("DB_PASSWORD"),
        database=st.secrets("DB_DATABASE"),
        charset='utf8mb4'  # 문자 집합 설정
    )
    cursor = db.cursor()
    cursor.execute("SELECT chat FROM qna WHERE id = %s", (record_id,))
    record = cursor.fetchone()
    cursor.close()
    db.close()
    return record

# Streamlit 애플리케이션
st.title("학생의 인공지능 사용 내역(교사용)")

# 비밀번호 입력
password = st.text_input("비밀번호를 입력하세요", type="password")

if password == st.secrets('PASSWORD'):  # 환경 변수에 저장된 비밀번호와 비교
    # 저장된 레코드 불러오기
    records = fetch_records()

    # 레코드 선택
    record_options = [f"{record[1]} ({record[2]}) - {record[3]}" for record in records]
    selected_record = st.selectbox("내역을 선택하세요:", record_options)

    # 선택된 레코드 ID 추출
    selected_record_id = records[record_options.index(selected_record)][0]

    # 선택된 학생의 대화 기록 불러오기
    record = fetch_record_by_id(selected_record_id)
    if record:
        chat = json.loads(record[0])
        st.write("### 학생의 대화 기록")
        for message in chat:
            if message["role"] == "user":
                st.write(f"**You:** {message['content']}")
            elif message["role"] == "assistant":
                st.write(f"**과학탐구 도우미:** {message['content']}")
else:
    st.error("비밀번호가 틀렸습니다.")
