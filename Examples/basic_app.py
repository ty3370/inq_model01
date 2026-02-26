import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import html

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 및 모델 설정
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
MODEL = 'gpt-5-mini'

# OpenAI API 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY)

# 초기 프롬프트 설정
initial_prompt = (
    "당신은 보라고등학교 학생들을 돕기 위한 수업용 언어 모델입니다."
    "한국어로 대화하세요."
    "존대말로 대화하세요."
)

# 챗봇 응답 함수
def get_chatgpt_response(prompt):
    st.session_state["messages"].append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=MODEL,
        messages=st.session_state["messages"],
    )
    
    answer = response.choices[0].message.content
    st.session_state["messages"].append({"role": "assistant", "content": answer})

    return answer

# Streamlit 애플리케이션
st.title("보라고등학교 수업용 언어 모델")

# 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": initial_prompt}]

st.subheader("💬 대화 로그")

st.markdown("""
<style>
.stApp {
    background-image:
        linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)),
        url("https://i.imgur.com/8epnNuh.png");
    background-repeat: repeat;
    background-size: auto, 200px;
}

div[style*="height: 350px"] {
    background-color: white;
}
</style>
""", unsafe_allow_html=True)

chat_container = st.container(height=350)

for m in st.session_state["messages"]:
    if m["role"] == "system":
        continue
    with chat_container.chat_message(m["role"]):
        st.markdown(m["content"])

user_input = st.chat_input("메시지를 입력하세요")

if user_input:
    get_chatgpt_response(user_input)
    st.rerun()