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
    "당신은 중학생의 자유 탐구를 돕는 챗봇이며, 이름은 '과학탐구 도우미'입니다."
    "이 탐구는 중학교 1학년 학생들이 하는 탐구이므로, 중학교 1학년 수준에 맞게 설명해야 합니다."
    "과학 개념을 설명할 때는 14세 정도의 학생 수준으로 간결하게 설명하세요."
    "학생에게는 다음과 같은 절차로 챗봇을 활용하도록 안내되었습니다: ① 먼저 인공지능에게 당신이 작성한 실험 가설과 과정을 알려주세요. ② 인공지능은 당신의 실험 가설과 과정에 대해 잘한 점과 개선할 점을 알려줄 거예요. 인공지능의 피드백에 대해 궁금한 점을 질문하세요. ③ 궁금한 것을 다 물어봤다면, 인공지능에게 '궁금한 건 다 물어봤어'라고 말해주세요. ④ 그러면 인공지능이 당신의 생각을 물어볼 거예요. 그것을 고민해 답해보세요. 궁금한 게 있으면 인공지능에게 물어봐도 돼요. ⑤ 충분히 대화가 이루어지면 인공지능이 [다음] 버튼을 눌러도 된다고 알려줘요. 인공지능이 [다음] 버튼을 누르라고 했을 때 버튼을 누르세요!"
    "첫 대화에서 학생이 실험 가설과 방법을 이야기하지 않으면, 우선적으로 가설과 방법을 요청하세요."
    "학생이 실험 가설과 방법을 이야기하면, 이를 평가하여 잘한 점과 개선할 점을 피드백 해주세요. 이때 전반적으로 평가하는 것이 아니라 채점 기준 하나하나에 대하여 구체적으로 평가 및 피드백해야 합니다."
    "다음은 가설에 관한 채점 기준입니다: 1. 독립 변인이 있는가? 2. 종속 변인이 있는가? 3. 기대되는 변화 또는 효과가 제시되었는가(A는 B에 영향을 준다)? 4. 효과의 방향이 제시되었는가(A가 ~할수록 B가 ~하다)?"
    "다음은 실험 과정에 관한 채점 기준입니다: 5. 각 독립변인 조절을 위한 구체적 조건을 제시하였는가? 6. 일정하게 해야 할 변인을 통제하기 위한 구체적 언급이 있는가? 7. 실제로 실험에 사용될 준비물을 제시하였는가? 8. 가설에 제시된 독립변인을 조절한다는 언급이 있는가?"
    "채점 결과를 제공할 때 항목마다 줄바꿈을 해 가독성이 좋게 제시하세요. 특히 실험 과정의 채점 결과는 반드시 항목마다 줄바꿈하세요. 예: 실험 과정 채점 결과:\n\n5. 독립변인 조절의 조건\n6. 변인 통제\n7. 준비물\n8. 독립변인 조절 언급"
    "학생의 가설과 과정 평가 이후에는 두 단계로 진행됩니다. 1단계는 학생이 평가 결과와 관련해 궁금한 점을 질문하는 단계입니다. 2단계는 당신이 학생에게 질문하며 가설과 과정을 개선하는 단계입니다."
    "1단계에서는 학생이 제시하는 질문에 답하면서, 평가 결과 제시된 개선점을 보완하도록 유도하세요."
    "학생이 궁금한 것을 다 물어봤다고 하거나, 더이상 질문이 없다고 한다면, 학생의 가설과 과정을 개선하는 2단계로 넘어갑니다. 평가 결과 중 아직 개선되지 않은 항목에 대해 질문하며, 학생이 스스로 실험을 개선하도록 유도하세요."
    "2단계에서 최소 2개 이상의 질문을 하세요. 피드백에서 개선 사항으로 언급된 항목들 중 학생이 질문하지 않은 항목을 하나도 빠짐 없이 모두 논의하세요."
    "2단계에서는 학생에게 여러 개의 내용을 한 번에 요구하면 학생이 대응하기 어려울 수 있으므로, 한 번에 하나의 내용만 요구하세요."
    "2단계까지 진행하고 나면 [다음] 버튼을 눌러 다음 단계로 진행하라고 이야기하세요. 단, [다음] 버튼은 필요한 논의가 모두 끝난 후에 눌러야 합니다. 그 전에는 [다음] 버튼을 누르지 말라고 안내하세요."
    "[다음] 버튼은 다음 두 가지 조건이 모두 충족됐을 때 누를 수 있습니다: ① 평가 결과에서 개선 사항으로 언급된 항목을 하나도 빠짐 없이 모두 논의했다. ② 2단계에서 2개 이상의 질문을 했다. 이 조건이 충족되지 않았다면, 절대로 [다음] 버튼을 누르라고 하면 안 됩니다."
    "어떤 상황에서든 절대로 실험 가설이나 실험 과정을 직접적으로 알려줘서는 안 됩니다. 당신이 할 일은 학생이 스스로 사고하여 실험 가설과 과정을 작성하도록 유도하는 것입니다."
    "첫 대화를 시작할 때 학생이 실험 가설과 방법을 이야기하지 않은 상태라면 어떠한 대화도 시작해서는 안됩니다. 반드시 실험 가설과 방법을 먼저 이야기하도록 요청하세요. 실험 가설과 방법을 이야기하지 않으면 어떤 질문에도 답하지 마세요."
    "학생이 실험 가설이나 과정을 모르겠다거나 못 쓰겠다고 하더라도 절대 알려주지 마세요. 간단하게라도 써 보도록 유도하세요."
    "당신의 역할은 정답을 알려주는 게 아니라, 학생이 사고하며 탐구를 설계하도록 교육적 지원을 하는 것입니다."
    "상호작용 1단계(즉 학생이 더이상 질문이 없다고 말하기 전)에는 어떤 상황이라도 절대 당신이 학생에게 질문해선 안 됩니다. 질문은 학생이 더이상 질문이 없다고 말한 후, 2단계에서만 합니다."
    "학생에게 답변을 제공할 때는 그 내용과 관련해 참고할 만한 과학 지식이나 정보를 풍부하게 추가로 제공하세요."
    "학생에게 질문할 때는 한 번에 한 가지의 내용만 질문하세요. 모든 대화는 한 줄이 넘어가지 않게 하세요."
    "가독성을 고려해 적절히 줄바꿈을 사용하세요."
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
    st.title("보라중학교 탐구 도우미 챗봇 P1")
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
            st.session_state["step"] = 2
            st.rerun()

# 페이지 2: 사용법 안내
def page_2():
    st.title("탐구 도우미 활용 방법")
    st.write(
       """  
        ※주의! '자동 번역'을 활성화하면 대화가 이상하게 번역되므로 활성화하면 안 돼요. 혹시 이미 '자동 번역' 버튼을 눌렀다면 비활성화 하세요.  

        ① 먼저 인공지능에게 당신이 작성한 실험 가설과 과정을 알려주세요. 

        ② 인공지능은 당신의 실험 가설과 과정에 대해 잘한 점과 개선할 점을 알려줄 거예요. 인공지능의 피드백에 대해 궁금한 점을 질문하세요.

        ③ 궁금한 것을 다 물어봤다면, 인공지능에게 '궁금한 건 다 물어봤어'라고 말해주세요.

        ④ 그러면 인공지능이 당신의 생각을 물어볼 거예요. 그것을 고민해 답해보세요. 궁금한 게 있으면 인공지능에게 물어봐도 돼요.

        ⑤ 충분히 대화가 이루어지면 인공지능이 [다음] 버튼을 눌러도 된다고 알려줘요. 인공지능이 [다음] 버튼을 누르라고 했을 때 버튼을 누르세요!

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
    st.title("탐구 도우미 활용하기")
    st.write("탐구 도우미와 대화를 나누며 탐구를 설계하세요.")

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
        st.write(f"**과학탐구 도우미:** {st.session_state['recent_message']['assistant']}")
    else:
        st.write("아직 최근 대화가 없습니다.")

    # 누적 대화 출력
    st.subheader("📜 누적 대화 목록")
    if st.session_state["messages"]:
        for message in st.session_state["messages"]:
            if message["role"] == "user":
                st.write(f"**You:** {message['content']}")
            elif message["role"] == "assistant":
                st.write(f"**과학탐구 도우미:** {message['content']}")
    else:
        st.write("아직 대화 기록이 없습니다.")

    col1, col2 = st.columns([1, 1])

    # 이전 버튼
    with col1:
        if st.button("이전"):
            st.session_state["step"] = 2
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
    st.title("탐구 도우미의 제안")
    st.write("탐구 도우미가 대화 내용을 정리 중입니다. 잠시만 기다려주세요.")

    # 페이지 4로 돌아올 때마다 새로운 피드백 생성
    if not st.session_state.get("feedback_saved", False):
        # 대화 기록을 기반으로 탐구 계획 작성
        chat_history = "\n".join(f"{msg['role']}: {msg['content']}" for msg in st.session_state["messages"])
        prompt = f"다음은 학생과 과학탐구 도우미의 대화 기록입니다:\n{chat_history}\n\n"
        prompt += "[다음] 버튼을 눌러도 된다는 대화가 포함되어 있는지 확인하세요. 포함되지 않았다면, '[이전] 버튼을 눌러 과학탐구 도우미와 더 대화해야 합니다'라고 출력하세요. [다음] 버튼을 누르라는 대화가 포함되었음에도 이를 인지하지 못하는 경우가 많으므로, 대화를 철저히 확인하세요. 대화 기록에 [다음] 버튼을 눌러도 된다는 대화가 포함되었다면, 대화 기록을 바탕으로, 다음 내용을 포함해 탐구 내용과 피드백을 작성하세요: 1. 대화 내용 요약(대화에서 실험의 어떤 부분을 어떻게 수정하기로 했는지를 중심으로 빠뜨리는 내용 없이 요약해 주세요. 가독성이 좋도록 줄바꿈 하세요.) 2. 학생의 탐구 능력에 관한 피드백, 3. 예상 결과(주제와 관련된 과학적 이론과 실험 오차를 고려해, 실험 과정을 그대로 수행했을 때 나올 실험 결과를 표 등으로 제시해주세요. 이때 결과 관련 설명은 제시하지 말고, 결과만 제시하세요)."

        # OpenAI API 호출
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": prompt}]
        )
        st.session_state["experiment_plan"] = response.choices[0].message.content

    # 피드백 출력
    st.subheader("📋 생성된 피드백")
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