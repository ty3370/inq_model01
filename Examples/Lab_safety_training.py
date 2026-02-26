import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
MODEL = "gpt-5-mini"

client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(
    page_title="실험실 안전 교육",
    page_icon="🧪",
)

common_prompt = (
    "어떠한 마크다운도 절대 사용하지 마세요."
    "모든 대답은 한 줄 이내로 짧게 생성하세요."
)

prompt_A = (
    "..."
    "..."
)

prompt_B = (
    "..."
    "..."
)

prompt_C = (
    "..."
    "..."
)

prompt_scene = (
    "..."
    "..."
)

PROMPT_MAP = {
    "학생 A (조장)": prompt_A,
    "학생 B": prompt_B,
    "학생 C": prompt_C,
    "사건 현장": prompt_scene
}

def get_response(agent_key, user_input):
    session_key = f"messages_{agent_key}"

    st.session_state[session_key].append(
        {"role": "user", "content": user_input}
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=st.session_state[session_key],
    )

    answer = response.choices[0].message.content

    st.session_state[session_key].append(
        {"role": "assistant", "content": answer}
    )

    return answer

def page_intro():

    col_left, col_center, col_right = st.columns([1, 3, 1])

    with col_center:

        st.markdown(
            "<h1 style='text-align: center;'>🧪 보라고등학교<br>실험실 폭발 사고 조사<br></h1>",
            unsafe_allow_html=True
        )

        st.markdown("""
        <div style="text-align:center;">
            <img src="https://i.imgur.com/8epnNuh.png"
                 style="max-width:350px; width:50%; height:auto;">
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='text-align: center;'>

        ### <br>🔍 활동 안내

        20xx년 x월 x일, 보라고등학교 실험실에서 폭발 사고가 발생했습니다.  
        빠른 대피와 교사의 적절한 조치로 인명 피해는 없었지만, 교육청에서는 사안 조사를 위해 조사관을 파견했습니다.

        당신은 보라고등학교로 파견된 **조사관**입니다.  
        조사 대상들을 심문하고 현장을 조사해 사고의 원인을 밝혀내세요.

        당신은 폭발 사고가 발생한 모둠의 학생 3명을 심문할 수 있습니다.  
        심문 대상은 학생 A(조장), 학생 B, 학생 C 입니다.  

        또한 필요하다면 사고 발생 현장 조사도 가능합니다.

        주의할 점은, 심문 대상이 거짓말을 할 수 있다는 점입니다.  
        현장 조사와 심문 내용에서 모순점을 찾아내, 거짓말을 밝혀내고 진실을 알아내세요.

        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("▶ 조사 시작하기", use_container_width=True):
            st.session_state["page"] = 2
            st.rerun()

def page_investigation():

    st.markdown("""
        <style>

        /* 탭 전체 영역 */
        div[data-testid="stTabs"] button {
            font-size: 26px !important;
            font-weight: 800 !important;
            padding: 12px 24px !important;
        }

        </style>
    """, unsafe_allow_html=True)

    st.title("🔎 실험실 폭발 사고 조사")

    if st.button("◀ 이전 화면으로 돌아가기"):
        st.session_state["page"] = 1
        st.rerun()

    tabs = st.tabs([
        "학생 A (조장)",
        "학생 B",
        "학생 C",
        "사건 현장"
    ])

    for i, agent_name in enumerate(PROMPT_MAP.keys()):
        with tabs[i]:

            session_key = f"messages_{agent_name}"

            if session_key not in st.session_state:
                st.session_state[session_key] = [
                    {"role": "system", "content": common_prompt},
                    {"role": "system", "content": PROMPT_MAP[agent_name]}
                ]

            chat_container = st.container(height=350)

            for m in st.session_state[session_key]:
                if m["role"] == "system":
                    continue

                if m["role"] == "assistant":
                    speaker = agent_name
                    role_style = "assistant"
                else:
                    speaker = "조사관"
                    role_style = "user"

                with chat_container.chat_message(role_style):
                    st.markdown(f"**{speaker}:** {m['content']}")

            user_input = st.chat_input(
                f"{agent_name}에게 질문하기",
                key=f"input_{agent_name}"
            )

            if user_input:
                get_response(agent_name, user_input)
                st.rerun()

if "page" not in st.session_state:
    st.session_state["page"] = 1

if st.session_state["page"] == 1:
    page_intro()
else:
    page_investigation()