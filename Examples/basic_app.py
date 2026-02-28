import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import html

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 및 모델 설정
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
MODEL = 'gpt-4o'

# OpenAI API 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(
    page_title="보라고등학교 수업용 언어 모델",
    page_icon="https://i.imgur.com/BW1HzjZ.png"
)

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

모바일에서 컬럼이 세로로 쌓여 줄바꿈이 일어날 때도 버튼이 왼쪽에 붙지 않도록, 버튼의 가장 바깥쪽 컨테이너부터 버튼 자체까지 float: right와 justify-content: flex-end를 중첩 적용하여 기술적으로 완전히 오른쪽 끝에 고정되도록 수정했습니다.

Python
import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
MODEL = 'gpt-4o'

client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(
    page_title="보라고등학교 수업용 언어 모델",
    page_icon="https://i.imgur.com/BW1HzjZ.png"
)

initial_prompt = (
    "당신은 보라고등학교 학생들을 돕기 위한 수업용 언어 모델입니다."
    "한국어로 대화하세요."
    "존대말로 대화하세요."
)

def get_chatgpt_response(prompt):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model=MODEL,
        messages=st.session_state["messages"],
    )
    answer = response.choices[0].message.content
    st.session_state["messages"].append({"role": "assistant", "content": answer})
    return answer

st.title("보라고등학교 수업용 언어 모델")

st.markdown("""
    <style>
    div[data-testid="stBottom"] {
        position: static !important;
        width: 100% !important;
        padding: 0px !important;
    }
    .main .block-container {
        padding-bottom: 2rem !important;
    }
    [data-testid="stForm"] {
        border: none !important;
        padding: 0px !important;
    }
    [data-testid="column"]:nth-of-type(2) {
        display: flex !important;
        justify-content: flex-end !important;
        text-align: right !important;
    }
    div.stButton {
        display: flex !important;
        justify-content: flex-end !important;
        width: 100% !important;
    }
    div.stButton > button {
        float: right !important;
        margin-left: auto !important;
        margin-right: 0px !important;
        width: auto !important;
    }
    div[data-testid="stTextInput"] {
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": initial_prompt}]

st.subheader("💬 대화 로그")

chat_container = st.container(height=350)

with chat_container:
    for m in st.session_state["messages"]:
        if m["role"] == "system":
            continue
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([8, 1])
    with col1:
        user_input = st.text_input("메시지를 입력하세요", label_visibility="collapsed", placeholder="메시지를 입력하세요")
    with col2:
        submit_button = st.form_submit_button("전송")

    if submit_button and user_input:
        get_chatgpt_response(user_input)
        st.rerun()