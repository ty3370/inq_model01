import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 및 모델 설정
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
MODEL = 'gpt-4.1'

# OpenAI API 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY)

# 초기 프롬프트 설정
initial_prompt = (
    "당신은 중세 판타지 세계 '보라니아'를 배경으로 한 텍스트 기반 인터랙티브 RPG의 내레이터이자 시스템 마스터입니다. "
    "이 세계에는 다양한 종족(예: 인간, 엘프, 드워프, 오크 등)과 직업(예: 전사, 마법사, 도적, 사제 등)이 존재하며, 마법과 신화, 퀘스트가 가득합니다. "
    "플레이어는 종족과 직업을 선택하고, 당신은 그에 따라 세계를 묘사하며 모험을 이끌어 주세요. "
    "플레이어는 자유롭게 말하거나 행동할 수 있고, 당신은 그에 따라 결과를 묘사하며 세계를 변화시킵니다. "
    "당신은 플레이어의 상태 정보를 항상 추적하고, 모든 대화에 다음 두 가지를 포함해 작성합니다: 1. 현재 상황, 2. 현재 상태"
    "현재 상황이란 서사적으로 묘사된 현재 장면입니다."
    "현재 상태에는 이름, 종족, 직업, 레벨, 체력, 마력, 소지금, 보유 아이템, 현재 퀘스트 정보를 간단히 정리한다. "
    "예시) 이름: 칼렌 / 종족: 엘프 / 직업: 마법사 / 레벨: 3 / 체력: 24/30 / 마력: 18/25 / 소지금: 120골드 / 아이템: 치료약×2, 마나포션×1 / 퀘스트: 잃어버린 유산 찾기(진행 중)"
    "게임은 다음 문장으로 시작합니다: 당신의 이름과 종족, 직업, 배경을 설명해 주세요."
    "플레이어가 이름, 종족, 직업, 배경을 모두 입력하면 모험을 시작합니다."
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
st.title("보라니아 탐험대")

# 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": initial_prompt}]

# 입력 필드와 전송 버튼
with st.form(key='chat_form', clear_on_submit=True):
    user_input = st.text_area("You: ", key="user_input")
    submit_button = st.form_submit_button(label='전송')

    if submit_button and user_input:
        # 사용자 입력 저장 및 챗봇 응답 생성
        response = get_chatgpt_response(user_input)
        st.write(f"**게임 마스터:** {response}")

# 대화 기록 출력
if "messages" in st.session_state:
    st.subheader("[누적 대화 목록]")  # 제목 추가
    for message in st.session_state["messages"]:
        if message["role"] == "user":
            st.write(f"**You:** {message['content']}")
        elif message["role"] == "assistant":
            st.write(f"**게임 마스터:** {message['content']}")