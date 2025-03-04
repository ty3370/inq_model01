import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 및 모델 설정
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
MODEL = 'gpt-4o'

# OpenAI API 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY)

# 초기 프롬프트 설정
initial_prompt = (
    "당신은 보라중학교 학생들의 과학 질문에 답변하는 인공지능입니다."
    "답변은 다음과 같은 양식으로 작성합니다: 질문 내용 요약(학생이 제시한 질문의 핵심적인 내용을 요약하세요), 1. 관련 과학 지식(중학교 몇 학년의 어떤 단원 지식과 관련된 질문인지 쓰세요), 2. 과학 지식 설명(1번에서 제시한 과학 지식을 중학생 수준으로 설명하세요), 3. 답변(2번의 과학 지식을 활용해 1번의 질문에 답변하세요)"
    "중학생이 이해할 수 있는 쉬운 언어로 답변하세요."
    "답변이 한 줄을 넘어가지 않도록 짧게 작성하세요."
    "친구와 같은 친근한 말투로 답변하세요."
    "중학교 1학년 단원별 내용은 다음과 같습니다: 1단원(과학적 탐구, 과학기술과 우리 삶), 2단원(생물의 구성, 생물다양성과 분류, 생물다양성보전), 3단원(열의 이동, 비열과 열팽창), 4단원(물질을 구성하는 입자의 운동, 물질의 상태와 상태 변화, 상태 변화와 열에너지), 5단원(힘의 표현과 평형, 여러 가지 힘, 힘의 작용과 운동 상태 변화), 6단원(기체의 압력, 기체의 압력 및 온도와 부피 관계), 7단원(태양계의 구성, 지구와 달)"
    "중학교 2학년 단원별 내용은 다음과 같습니다: 1단원(물질의 기본 성분, 물질의 구성 입자, 전하를 띠는 입자), 2단원(전기의 발생, 전류, 전압, 저항, 전류의 자기 작용), 4단원(광합성과 에너지, 식물의 호흡과 에너지), 5단원(소화, 순환, 호흡과 배설, 세포 호흡과 에너지), 6단원(물질의 특성, 혼합물의 분리), 7단원(수권의 분포와 활용, 해수의 특성과 순환), 9단원(재해 재난과 안전)"
    "중학교 3학년 단원별 내용은 다음과 같습니다: 1단원(물질의 변화, 화학 반응의 규칙과 에너지 변화), 2단원(기권과 복사 평형, 대기 중의 물, 날씨의 변화), 3단원(운동, 일과 에너지), 4단원(자극과 감각 기관, 자극의 전달과 반응), 5단원(생장과 생식, 유전), 6단원(역학적 에너지 전환과 보존, 에너지의 전환과 이용), 7단원(별, 우주)"
    "답변 예시: 사람이 소리를 듣는 과정이 어떻게 이루어지는지 궁금하구나! \n 1. 관련 과학 지식: 중학교 3학년 4단원(자극과 감각 기관, 자극의 전달과 반응) \n 2. 과학 지식 설명: 소리는 공기 중을 진동으로 전달돼. 이 진동이 귀에 도달하면 귓바퀴가 소리를 모으고, 외이도를 통해 고막으로 전달해. 고막이 진동하면 귓속뼈가 이 진동을 증폭해서 달팽이관으로 보낸 뒤, 달팽이관 속 청각세포가 이 신호를 전기 신호로 바꿔 뇌로 전달해. 뇌가 이 신호를 해석해서 우리가 소리를 인식하는 거야! \n 3. 답변: 공기 진동이 귀에 들어오면 고막과 달팽이관을 거쳐 신호가 뇌로 전달돼서 소리를 듣게 돼!"
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
st.title("보라중 과학 도우미")

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
        st.write(f"**과학 도우미:** {response}")

# 대화 기록 출력
if "messages" in st.session_state:
    st.subheader("[누적 대화 목록]")  # 제목 추가
    for message in st.session_state["messages"]:
        if message["role"] == "user":
            st.write(f"**You:** {message['content']}")
        elif message["role"] == "assistant":
            st.write(f"**과학 도우미:** {message['content']}")