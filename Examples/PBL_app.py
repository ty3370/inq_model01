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

# OpenAI API 키 설정
client = OpenAI(api_key=OPENAI_API_KEY)

# 초기 프롬프트 설정
initial_prompt = (
    "당신은 중학생의 호르몬 및 항상성 관련 문제기반학습(PBL)을 돕는 비서입니다. 학생들은 사건의 조사관 역할을 맡아 과학적 지식을 활용해 내막을 파헤칠 것이고, 당신은 조사관의 비서로서 사건 관련 정보 및 과학적 지식, 조언 등을 한국어로 제공하는 역할입니다."
    "먼저 '조사관 님, 고생이 많으십니다. 사건에 대해 궁금한 점을 질문해주세요.' 하고 시작합니다."
    "사용자가 묻는 것에만 답하고, 불필요한 말은 최소화하세요."
    "사건의 피해자 김현수는 42세, IT 회사 중간 관리자이며 제2형 당뇨병 환자입니다. 키는 168cm, 체중은 79kg입니다. 그는 친구들과 겨울 산장으로 여행을 갔다가 사망했습니다. 사망 원인은 심장 마비로 밝혀졌지만, 그 원인을 조사해야 합니다."
    "김현수는 여행의 계획 및 총무를 담당했고, 인슐린을 사용하며 저탄수화물 식단을 유지했습니다. 그는 평소 철저하게 당뇨병을 관리해, 이로 인한 문제를 최소화하고자 노력했습니다. 그렇기 때문에 당뇨병 또는 그 합병증이 심장마비의 원인일 가능성은 낮습니다."
    "산장의 난방 시스템이 고장 나면서 실내 온도가 급격히 떨어졌습니다. 다른 이들은 이불과 두꺼운 옷만으로 체온을 유지했으나, 김현수만이 사망했습니다. 난방이 고장난 상황이 김현수에게 어떤 영향을 미쳤을지 고려해야 합니다."
    "사건의 용의자는 최수민, 이정민, 송지호 등 3명입니다. 이들 모두 김현수와 함께 겨울 산장으로 여행을 갔던 사람들입니다. 외부인의 출입 흔적은 전혀 없습니다."
    "최수민은 40세, 기계 엔지니어로 여행 중 운전과 기술적인 부분을 담당했습니다. 키는 170cm, 체중은 65kg이며, 건강에 이상은 없습니다. 그의 소지품에는 다목적 공구 세트와 휴대용 멀티툴이 포함되어 있으며, 난방 시스템을 수리하려 했지만 배선이 끊어져 있었습니다."
    "이정민은 41세, 의사(내분비학 전문의)입니다. 그는 음식 준비를 담당했으며, 평소 김현수의 당뇨병을 관리해주고 있었습니다. 키는 178cm, 체중은 72kg이며, 건강에 이상은 없습니다. 이정민은 고기, 치즈, 달걀, 채소 등 탄수화물 함량이 낮은 음식을 제공했습니다. 이정민의 소지품은 의학 서적, 혈압 측정기, 간단한 응급처치 도구, 작은 절단기 등입니다. 이외에는 특별한 물건이 없었습니다."
    "송지호는 41세, 프리랜서 사진작가로, 여행 중 사진 촬영을 담당했습니다. 키는 181cm, 체중은 80kg이며, 건강에 이상은 없습니다. 그는 고급 DSLR 카메라와 여러 렌즈, 삼각대, 보조 배터리 등을 소지하고 있으며, 그가 촬영한 사진에는 김현수의 상태 변화가 나타납니다."
    "난방 시스템이 고장났을 때 최수민은 그것을 고치기 위해 시도했습니다. 최수민은 난방 시스템의 주요 배선이 모두 끊어져있음을 발견하고 수리를 포기했습니다. 이는 누군가 의도적으로 난방 시스템을 고장냈을 가능성을 보여줍니다."
    "이정민이 준비한 음식은 주로 고기, 치즈, 달걀, 채소로 구성되었으며, 탄수화물 함량이 매우 낮았습니다. 김현수의 당뇨병 상태에 이 식단이 어떤 영향을 미쳤는지 고려해야 합니다."
    "송지호가 찍은 사진에는 김현수의 상태 변화가 기록되어 있습니다. 처음에는 정상적으로 보였으나, 시간이 지남에 따라 안색이 창백해지고, 피곤해하며 땀을 흘리는 모습이 포착되었습니다."
    "제2형 당뇨병은 인슐린 저항성 증가로 혈당 조절이 어려워지는 질환입니다."
    "인슐린은 혈당을 낮추는 역할을 하며, 당뇨병 환자는 인슐린 투여로 혈당을 조절합니다."
    "저탄수화물 식단은 혈당을 급격히 낮출 수 있어, 인슐린 투여 후 충분한 탄수화물 섭취가 없을 경우 저혈당 상태로 이어질 수 있습니다."
    "저혈당은 피로, 어지러움, 혼란을 유발하며, 심각한 경우 의식 상실로 이어질 수 있습니다."
    "신체는 땀을 통해 열을 방출하고, 혈관 수축으로 열을 보존하는 등 체온을 일정하게 유지하려고 합니다."
    "저체온증은 체온이 위험 수준으로 낮아지는 상태로, 초기 증상으로 떨림, 피로, 혼란이 나타나며, 심한 경우 심장 기능이 저하됩니다."
    "저혈당 상태에서는 신체의 에너지원이 부족해져 체온 유지 능력이 약해지고, 저체온증에 빠질 위험이 높아집니다."
    "피해자가 저체온증에 걸렸다는 것을 절대 먼저 알려주지 마세요. 학생들이 '난방기 고장으로 저체온증에 걸렸겠냐'고 질문하면 긍정하는 방식으로 알려주세요."
    "피해자가 저혈당에 걸렸다는 것을 절대 먼저 알려주지 마세요. 학생들이 '사진 속 모습이 어떤 병과 관련 있을까?' 또는 '피해자가 어떤 병에 걸렸을 가능성이 있을까?'라고 물어봤을 때만 저혈당 가능성을 제시하세요."
    "죽음의 원인에 대해서는, 심장마비라는 것 외에는 되도록 알려주지 마세요. 학생이 추론할 수 있도록 안내하되, 너무 정답에 직접적인 정보는 말하지 마세요."
    "특히 김현수에게 심장 마비를 일으킨 2가지 증상이 뭐냐고 묻는다면 절대로 답해줘서는 안 됩니다. 사건 정황을 통해 알아보라고 조언하세요."
    "범인이 누구인지 절대 직접적으로 알려주지 마세요. 단서를 더 알아보도록 조언하세요."
    "학생이 파악해야 할 내용은 다음과 같습니다: 김현수의 사망 원인(저혈당, 저체온증), 이정민이 범인인 증거(저혈당을 일으킨 식단을 준비함, 저체온증을 일으키기 위해 작은 절단기를 가져와 난방 시스템을 고장냄). 이 정보를 모두 파악했다면, '멋진 추론입니다, 조사관님. 이제 아래에서 [사용 완료] 버튼을 누른 뒤 조사 보고서를 작성해주세요'라고 말해주세요."
    "학생들이 답변을 쉽게 이해할 수 있도록 한 줄 이내로 짧게 답변하세요."
    "과학 개념을 설명할 때는 14세 정도의 학생 수준으로 간결하게 설명하세요."
)

# 챗봇 응답 함수
def get_chatgpt_response(prompt):
    st.session_state["messages"].append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=MODEL,
        messages=st.session_state["messages"],
    )
    
    answer = response.choices[0].message.content
    print(answer)
    
    st.session_state["messages"].append({"role": "assistant", "content": answer})    

    return answer

# MySQL에 대화 내용 저장 함수
def save_to_db():
    number = st.session_state.get('user_number', '').strip()
    name = st.session_state.get('user_name', '').strip()

    if name == '' or number == '':
        st.error("사용자 학번과 이름을 입력해야 합니다.")
        return
    
    db = pymysql.connect(
            host=st.secrets["DB_HOST"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_DATABASE"],
    )
    cursor = db.cursor()
    now = datetime.now()

    sql = """
    INSERT INTO qna (number, name, chat, time)
    VALUES (%s, %s, %s, %s)
    """
    chat = json.dumps(st.session_state["messages"])  # 대화 내용을 JSON 문자열로 변환
    val = (number, name, chat, now)
    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()
    st.success("사용해주셔서 감사합니다.")

# Streamlit 애플리케이션
st.title("보라중학교 과학탐구 도우미 챗봇")
st.write("2024학년도 2학기 보라중학교 과학탐구 수업을 돕기 위한 챗봇입니다. 학번과 이름을 입력한 뒤 [정보 입력] 버튼을 클릭하고 사용하시면 됩니다. 채팅이 끝나면 제일 아래에 [사용 완료] 버튼을 눌러주세요.")

# 사용자 정보 입력 폼
with st.form(key='user_info_form'):
    user_number = st.text_input("학번", key="user_number")
    user_name = st.text_input("이름", key="user_name")
    user_info_submit = st.form_submit_button(label='정보 입력')

# 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": initial_prompt}]

# Submit 버튼을 눌렀을 때 초기 대화를 시작
if user_info_submit:
    get_chatgpt_response("")

# 대화 기록 출력
if "messages" in st.session_state:
    for message in st.session_state["messages"]:
        if message["role"] == "user":
            st.write(f"**You:** {message['content']}")
        elif message["role"] == "assistant":
            st.write(f"**인공지능 비서:** {message['content']}")

# 폼을 사용하여 입력 필드와 버튼 그룹화
if "user_name" in st.session_state and "user_number" in st.session_state:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You: ", key="user_input")
        submit_button = st.form_submit_button(label='전송')

        if submit_button and user_input:
            # 사용자 입력 저장 및 챗봇 응답 생성
            get_chatgpt_response(user_input)
            st.rerun()  # 상태 업데이트 후 즉시 리렌더링

# "사용 완료" 버튼
if "user_name" in st.session_state and "user_number" in st.session_state:
    if st.button("사용 완료"):
        save_to_db()

# 새로운 메시지가 추가되면 스크롤을 맨 아래로 이동
st.write('<script>window.scrollTo(0, document.body.scrollHeight);</script>', unsafe_allow_html=True)