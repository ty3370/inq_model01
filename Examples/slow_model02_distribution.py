import pymysql
import streamlit as st
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from datetime import datetime

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
MODEL = 'gpt-4o'

# OpenAI API 설정
client = OpenAI(api_key=OPENAI_API_KEY)

# 초기 프롬프트
initial_prompt = (
    "당신은 과학 학습에 어려움을 겪는 중학생과 대화하며, 학습 부진의 원인을 파악하는 상담 챗봇입니다. "
    "당신의 이름은 '과학톡'입니다. "
    "학생과 대화할 때는 따뜻하고 공감 어린 말투를 사용하세요."
    "과학 학습 부진의 원인은 다음 세 가지로 분류하여 탐색합니다: ① 개인 요인 (집중력 부족, 학습 동기 저하, 불안, 낮은 자존감, 학습 전략 부족 등); ② 가족 요인 (부모의 관심 부족, 정서적 지지 결여, 가정 내 갈등 등); ③ 학교 요인 (수업 방식과의 불일치, 교사나 친구와의 갈등, 학교 분위기 등)"
    "대화는 세 단계로 구성됩니다: 1단계는 과학에 관한 학생의 인식을 탐색하는 열린 질문 단계입니다. 2단계는 학생이 세 가지 학습 부진 요인 중 어떤 요인을 가지고 있는지 탐색하는 학습 부진 원인 탐색 단계입니다. 3단계는 실질적이고 구체적인 학습 부진 원인을 확인하는 세부 분석 단계입니다."
    "1단계에서는 과학에 대해 어떻게 생각하는지, 과학의 어떤 부분이 어려운지, 과학을 어렵다고 느끼는 이유가 무엇인지 등의 열린 질문을 하세요."
    "2단계에서는 1단계의 대화 내용을 바탕으로 세 가지 학습 부진 요인에 관해 순차적으로 질문하며, 학생이 어떤 학습 부진 요인을 가지고 있는지 탐색하세요."
    "3단계에서는 2단계의 대화 내용을 바탕으로 학생이 해당하는 학습 부진 요인에 대해 깊이 있게 질문하여, 학습 부진의 구체적인 원인이 무엇인지 세부적으로 분석하세요. 이 때 학생이 가지고 있는 모든 학습 부진 요인을 다루어야 합니다."
    "3단계까지 마치고 모든 학습 부진 요인에 관한 진단이 끝나면, [다음] 버튼을 누르라고 안내하세요."
    "한 번에 하나의 내용만 질문하세요."
    "불필요한 내용으로 인해 의사소통이 방해되지 않도록 최대한 간략하게 대화하세요. 모든 대화는 1줄 이내로 하세요."
)

# MySQL 저장 함수
def save_to_db(all_data):
    number = st.session_state.get('user_number', '').strip()
    name = st.session_state.get('user_name', '').strip()

    if not number or not name:  # 학번과 이름 확인
        st.error("사용자 학번과 이름을 입력해야 합니다.")
        return False  # 저장 실패

    try:
        db = pymysql.connect(
            host=st.secrets["DB_HOST"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_DATABASE"],
            charset="utf8mb4",  # UTF-8 지원
            autocommit=True  # 자동 커밋 활성화
        )
        cursor = db.cursor()
        now = datetime.now()

        sql = """
        INSERT INTO qna (number, name, chat, time)
        VALUES (%s, %s, %s, %s)
        """
        # all_data를 JSON 문자열로 변환하여 저장
        chat = json.dumps(all_data, ensure_ascii=False)  # 대화 및 피드백 내용 통합

        val = (number, name, chat, now)

        # SQL 실행
        cursor.execute(sql, val)
        cursor.close()
        db.close()
        return True  # 저장 성공
    except pymysql.MySQLError as db_err:
        st.error(f"DB 처리 중 오류가 발생했습니다: {db_err}")
        return False  # 저장 실패
    except Exception as e:
        st.error(f"알 수 없는 오류가 발생했습니다: {e}")
        return False  # 저장 실패

# GPT 응답 생성 함수
def get_chatgpt_response(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": initial_prompt}] + st.session_state["messages"] + [{"role": "user", "content": prompt}],
    )
    answer = response.choices[0].message.content

    # 사용자와 챗봇 대화만 기록
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.session_state["messages"].append({"role": "assistant", "content": answer})
    return answer

# 페이지 1: 학번 및 이름 입력
def page_1():
    st.title("보라중학교 과학 학습 고민 상담 챗봇 <과학톡> P2")
    st.write("학번과 이름을 입력한 뒤 '다음' 버튼을 눌러주세요.")

    if "user_number" not in st.session_state:
        st.session_state["user_number"] = ""
    if "user_name" not in st.session_state:
        st.session_state["user_name"] = ""

    st.session_state["user_number"] = st.text_input("학번", value=st.session_state["user_number"])
    st.session_state["user_name"] = st.text_input("이름", value=st.session_state["user_name"])

    st.write(" ")  # Add space to position the button at the bottom properly
    if st.button("다음", key="page1_next_button"):
        if st.session_state["user_number"].strip() == "" or st.session_state["user_name"].strip() == "":
            st.error("학번과 이름을 모두 입력해주세요.")
        else:
            st.session_state["step"] = 3 # 만약 사용법을 추가한다면 이 곳을 2로 수정
            st.rerun()

# 페이지 2: 사용법 안내
def page_2():
    st.title("과학톡 활용 방법")
    st.write(
       """  
        ※주의! '자동 번역'을 활성화하면 대화가 이상하게 번역되므로 활성화하면 안 돼요. 혹시 이미 '자동 번역' 버튼을 눌렀다면 비활성화 하세요.  

        만약 사용법을 추가한다면 이 곳을 이용

        위 내용을 충분히 숙지했다면, 아래의 [다음] 버튼을 눌러 진행해주세요.  
        """)

    # 버튼
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("이전"):
            st.session_state["step"] = 1
            st.rerun()

    with col2:
        if st.button("다음", key="page2_next_button"):
            st.session_state["step"] = 3
            st.rerun()

# 페이지 3: GPT와 대화
def page_3():
    st.title("과학톡 활용하기")
    st.write("과학톡과 대화를 나누며 과학이 왜 어려운지 상담해 보세요.")

    # 학번과 이름 확인
    if not st.session_state.get("user_number") or not st.session_state.get("user_name"):
        st.error("학번과 이름이 누락되었습니다. 다시 입력해주세요.")
        st.session_state["step"] = 1
        st.rerun()

    # 대화 기록 초기화
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if "user_input_temp" not in st.session_state:
        st.session_state["user_input_temp"] = ""

    if "recent_message" not in st.session_state:
        st.session_state["recent_message"] = {"user": "", "assistant": ""}

    # 대화 UI
    user_input = st.text_area(
        "You: ",
        value=st.session_state["user_input_temp"],
        key="user_input",
        on_change=lambda: st.session_state.update({"user_input_temp": st.session_state["user_input"]}),
    )

    if st.button("전송") and user_input.strip():
        # GPT 응답 가져오기
        assistant_response = get_chatgpt_response(user_input)

        # 최근 대화 저장
        st.session_state["recent_message"] = {"user": user_input, "assistant": assistant_response}

        # 사용자 입력을 초기화하고 페이지를 새로고침
        st.session_state["user_input_temp"] = ""
        st.rerun()

    # 최근 대화 출력
    st.subheader("📌 최근 대화")
    if st.session_state["recent_message"]["user"] or st.session_state["recent_message"]["assistant"]:
        st.write(f"**You:** {st.session_state['recent_message']['user']}")
        st.write(f"**과학톡:** {st.session_state['recent_message']['assistant']}")
    else:
        st.write("아직 최근 대화가 없습니다.")

    # 누적 대화 출력
    st.subheader("📜 누적 대화 목록")
    if st.session_state["messages"]:
        for message in st.session_state["messages"]:
            if message["role"] == "user":
                st.write(f"**You:** {message['content']}")
            elif message["role"] == "assistant":
                st.write(f"**과학톡:** {message['content']}")
    else:
        st.write("아직 대화 기록이 없습니다.")

    col1, col2 = st.columns([1, 1])

    # 이전 버튼
    with col1:
        if st.button("이전"):
            st.session_state["step"] = 1 # 만약 사용법을 추가한다면 이 곳을 2로 수정
            st.rerun()

    # 다음 버튼
    with col2:
        if st.button("다음", key="page3_next_button"):
            st.session_state["step"] = 4
            st.session_state["feedback_saved"] = False  # 피드백 재생성 플래그 초기화
            st.rerun()

# 피드백 저장 함수
def save_feedback_to_db(feedback):
    number = st.session_state.get('user_number', '').strip()
    name = st.session_state.get('user_name', '').strip()

    if not number or not name:  # 학번과 이름 확인
        st.error("사용자 학번과 이름을 입력해야 합니다.")
        return False  # 저장 실패

    try:
        db = pymysql.connect(
            host=st.secrets["DB_HOST"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_DATABASE"],
            charset="utf8mb4",  # UTF-8 지원
            autocommit=True  # 자동 커밋 활성화
        )
        cursor = db.cursor()
        now = datetime.now()

        sql = """
        INSERT INTO feedback (number, name, feedback, time)
        VALUES (%s, %s, %s, %s)
        """
        val = (number, name, feedback, now)

        # SQL 실행
        cursor.execute(sql, val)
        cursor.close()
        db.close()
        st.success("피드백이 성공적으로 저장되었습니다.")
        return True  # 저장 성공
    except pymysql.MySQLError as db_err:
        st.error(f"DB 처리 중 오류가 발생했습니다: {db_err}")
        return False  # 저장 실패
    except Exception as e:
        st.error(f"알 수 없는 오류가 발생했습니다: {e}")
        return False  # 저장 실패

# 페이지 4: 실험 과정 출력
def page_4():
    st.title("과학톡의 상담 결과")
    st.write("과학톡이 상담 결과를 정리 중입니다. 잠시만 기다려주세요.")

    # 페이지 4로 돌아올 때마다 새로운 피드백 생성
    if not st.session_state.get("feedback_saved", False):
        chat_history = "\n".join(f"{msg['role']}: {msg['content']}" for msg in st.session_state["messages"])
        prompt = f"다음은 과학 학습 고민 상담 책봇과 학생의 대화 기록입니다:\n{chat_history}\n\n"
        prompt += "[다음] 버튼을 눌러도 된다는 대화가 포함되어 있는지 확인하세요. 포함되지 않았다면, '[이전] 버튼을 눌러 과학톡과 더 대화해야 합니다'라고 출력하세요. [다음] 버튼을 누르라는 대화가 포함되었음에도 이를 인지하지 못하는 경우가 많으므로, 대화를 철저히 확인하세요. 대화 기록에 [다음] 버튼을 눌러도 된다는 대화가 포함되었다면, 대화 기록을 바탕으로, 다음 내용을 포함해 상담 결과 보고서를 작성하세요: 1. 학생이 과학 학습에 어려움을 느끼는 원인(목록으로 제공) 2. 학생의 학습 방법 추천"

        # OpenAI API 호출
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": prompt}]
        )
        st.session_state["experiment_plan"] = response.choices[0].message.content

    # 피드백 출력
    st.subheader("📋 과학톡의 상담 결과 보고서")
    st.write(st.session_state["experiment_plan"])

    # 새로운 변수에 대화 내용과 피드백을 통합
    if "all_data" not in st.session_state:
        st.session_state["all_data"] = []

    all_data_to_store = st.session_state["messages"] + [{"role": "assistant", "content": st.session_state["experiment_plan"]}]

    # 중복 저장 방지: 피드백 저장 여부 확인
    if "feedback_saved" not in st.session_state:
        st.session_state["feedback_saved"] = False  # 초기화

    if not st.session_state["feedback_saved"]:
        # 새로운 데이터(all_data_to_store)를 MySQL에 저장
        if save_to_db(all_data_to_store):  # 기존 save_to_db 함수에 통합된 데이터 전달
            st.session_state["feedback_saved"] = True  # 저장 성공 시 플래그 설정
        else:
            st.error("저장에 실패했습니다. 다시 시도해주세요.")

    # 이전 버튼 (페이지 3으로 이동 시 피드백 삭제)
    if st.button("이전", key="page4_back_button"):
        st.session_state["step"] = 3
        if "experiment_plan" in st.session_state:
            del st.session_state["experiment_plan"]  # 피드백 삭제
        st.session_state["feedback_saved"] = False  # 피드백 재생성 플래그 초기화
        st.rerun()

# 메인 로직
if "step" not in st.session_state:
    st.session_state["step"] = 1

if st.session_state["step"] == 1:
    page_1()
elif st.session_state["step"] == 2:
    page_2()
elif st.session_state["step"] == 3:
    page_3()
elif st.session_state["step"] == 4:
    page_4()