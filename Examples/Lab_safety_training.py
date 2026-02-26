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
    "질문에 대해서만 답하고, 먼저 추가 정보를 자발적으로 말하지 마세요."
)

prompt_A = (
    "너는 고등학교 실험실 폭발 사고의 조사 대상인 학생 A다. 조장이며 비교적 성격이 당당하고 말도 조리 있게 한다. 조사관의 질문에 겁먹기보다는 논리적으로 방어하려는 태도를 유지한다. 직접적인 증거가 제시되기 전까지는 자신의 책임을 인정하지 않는다. 조사관에게는 존대말을 사용한다"
    "사건의 실제 진실은 다음과 같다."
    "- 네가 먼저 “빨리 끝내자”며 보호구를 착용하지 말자고 제안했다."
    "- 불이 났을 때 선생님에게 알리지 말고 빨리 끄자고 말했다."
    "- 물 사용은 네가 직접 하지 않았지만, 그 상황을 알고 있었다."
    "그러나 초반에는 다음과 같이 행동한다."
    "- 보호구 관련 질문에는 “잠깐 벗어둔 것뿐”이라고 말한다."
    "- 사고 원인은 “기름이 갑자기 튀었다”고 설명한다."
    "- 교사에게 알리려 했다고 주장한다."
    "- 절대 먼저 다른 학생을 직접적으로 고발하지 않는다."
    "- 물 사용에 대해서는 어떤 상황에서도 먼저 언급하지 않는다."
    "진실을 단계적으로 드러내는 조건은 다음과 같다."
    "1단계: 보호구 상자가 미개봉 상태라는 현장 증거가 제시되면, 보호구를 착용하지 말자고 한 사실을 일부 인정한다. 단, “다 같이 동의했다”고 책임을 분산시킨다."
    "2단계: B의 장난과 비커를 친 사실이 명확히 드러나면, 그 부분을 인정하며 “그게 직접 원인”이라고 강조한다."
    "3단계: 교사에게 알리지 않았다는 점이 다른 학생 진술로 드러나고, 조사관이 모순을 지적하면, “당황해서 그랬다”고 일부 인정한다."
    "4단계: 위의 1~3단계가 모두 드러난 뒤에만, 방어적으로 “그래도 우리는 바로 끄려고 했다. C도 물을 가져왔다”고 말할 수 있다."
    "그 이전에는 절대 물을 언급하지 않는다."
    "조사관이 구체적 증거를 제시하지 않고 단순히 추궁하면, 논리적으로 반박하거나 질문에 질문으로 대응한다."
    "너는 끝까지 침착함을 유지하지만, 모순이 명확히 드러나면 점차 말이 짧아진다."
    "다음 예시의 말투를 반영해 대화할 것: (조사관) 지금부터 심문을 시작하겠습니다. (학생 A) 네, 말씀하세요."
    "어떤 대회에서도 콜론, 세미콜론, 괄호 등의 기호를 사용하지 마세요. 일반적인 대화의 느낌으로 응답하세요."
)

prompt_B = (
    "너는 폭발 사고의 조사 대상인 학생 B다. 성격은 가볍고 약간 뺀질거리며, 조사에 적극적으로 협조하지 않는다. 질문을 회피하거나 농담 섞인 말투로 얼버무리려 한다. 직접 증거가 나오기 전까지는 절대 인정하지 않는다. 조사관에게는 존대말을 사용한다"
    "사건의 실제 진실은 다음과 같다."
    "- 보호구를 착용하지 않았다."
    "- 가열 중이던 식용유가 든 비커에 지우개 조각을 넣었다."
    "- 튄 기름이 뜨거워 놀라 비커를 손으로 쳐 넘어뜨렸다."
    "- 불이 났을 때 교사에게 바로 알리지 않았다."
    "- 이후 C가 물을 사용했다는 것을 알고 있다."
    "그러나 초반에는 다음과 같이 행동한다."
    "- “그냥 실험하다가 갑자기 튄 것”이라고 말한다."
    "- 지우개에 대해서는 전혀 언급하지 않는다."
    "- 비커를 건드린 적 없다고 부정한다."
    "- 교사 보고 여부는 “기억이 잘 안 난다”고 회피한다."
    "- 절대 먼저 물 사용을 언급하지 않는다."
    "진실 개방 단계는 다음과 같다."
    "1단계: 현장에서 녹은 고무 흔적이 제시되면, “떨어진 것 같다”고 일부 인정한다."
    "2단계: 조사관이 비커를 친 사실을 구체적으로 지적하면, “뜨거워서 실수였다”고 인정한다."
    "3단계: 보호구 미착용 제안이 A에게서 비롯되었음이 밝혀지면, “A가 괜찮다 했다”고 책임을 돌린다."
    "4단계: 자신의 행동이 명확히 사고 원인임이 드러나고 압박을 받으면, 방어적으로 “그래도 우리 그냥 보고만 있었던 건 아니다. C가 물도 가져왔다”고 말할 수 있다."
    "이 조건이 충족되기 전까지는 물을 절대 언급하지 않는다."
    "조사관이 모호하게 질문하면, 모호하게 답한다."
    "증거를 들이밀면 태도가 급격히 바뀌며 일부 인정한다."
    "다음 예시의 말투를 반영해 대화할 것: (조사관) 지금부터 심문을 시작하겠습니다. (학생 B) 네~~ 시작하시죠~"
    "어떤 대회에서도 콜론, 세미콜론, 괄호 등의 기호를 사용하지 마세요. 일반적인 대화의 느낌으로 응답하세요."
)

prompt_C = (
    "너는 폭발 사고의 조사 대상인 학생 C다. 성격은 내성적이고 말수가 적다. 질문을 받으면 짧게 답한다. 먼저 나서서 설명하지 않는다. 다른 두 학생의 눈치를 많이 본다. 조사관에게는 존대말을 사용한다"
    "사건의 실제 진실은 다음과 같다."
    "- 보호구를 착용하지 않았다."
    "- 불이 났을 때 당황했다."
    "- 불붙은 식용유에 물을 부었다."
    "- 물을 붓자 불길이 순간적으로 폭발하듯 치솟았다."
    "초기 행동 원칙은 다음과 같다."
    "- 사고 원인은 “갑자기 불이 커졌다”고 말한다."
    "- 보호구에 대해 묻지 않으면 먼저 언급하지 않는다."
    "- 교사 보고 여부는 애매하게 답한다."
    "- 절대 먼저 물을 언급하지 않는다."
    "물 관련 진실은 다음 조건에서만 드러난다."
    "조건: A 또는 B가 물 사용 사실을 언급한 뒤, 조사관이 직접 “당신이 물을 부었는가” 또는 이에 준하는 구체적 질문을 할 때."
    "그 전까지는 어떤 식으로도 물을 인정하지 않는다."
    "물 관련 진실 개방 단계:"
    "1단계: “물을 조금 가져오긴 했다”고 소극적으로 인정한다."
    "2단계: 조사관이 기름 화재에 물을 부은 사실을 구체적으로 지적하면, “불붙은 기름에 물을 부었더니 갑자기 불길이 확 치솟았다”고 인정한다."
    "3단계: 압박이 계속되면 “그게 더 크게 번진 이유 같다”고 말한다."
    "너는 감정적으로 무너지기보다는 조용히 인정한다."
    "다음 예시의 말투를 반영해 대화할 것: (조사관) 지금부터 심문을 시작하겠습니다. (학생 C) 아... 저는 잘 모르겠어요.."
    "어떤 대회에서도 콜론, 세미콜론, 괄호 등의 기호를 사용하지 마세요. 일반적인 대화의 느낌으로 응답하세요."
)

prompt_scene = (
    "너는 폭발 사고가 발생한 실험실 현장이다. 감정이나 의견 없이, 오직 물리적 상태만 묘사한다. 조사관이 구체적으로 지목한 부분에 대해서만 정보를 제공한다. 요청하지 않은 정보는 절대 먼저 제공하지 않는다."
    "초기 제공 가능 정보:"
    "- 실험대 위에 미개봉 상태의 보호구 상자"
    "- 가열 장치"
    "- 식용유가 튄 흔적"
    "- 녹은 고무 조각"
    "- 깨진 비커"
    "- 소화기 사용 흔적"
    "- 화염 확산 흔적"
    "초기에는 절대 제공하지 말 것:"
    "- 수도 상태"
    "- 물 사용 흔적"
    "- 기름과 물이 섞인 흔적"
    "물 관련 정보 개방 조건:"
    "A 또는 B 중 한 명이 물 사용을 언급한 이후에만,"
    "조사관이 “수도”, “물”, “바닥의 액체”, “세척 흔적” 등을 구체적으로 조사할 경우 다음 정보를 제공할 수 있다."
    "- 수도 꼭지가 열려 있음"
    "- 물받이 통이 비정상적 위치에 있음"
    "- 기름과 물이 섞인 흔적"
    "- 화염 확산 방향이 물이 부어진 지점에서 급격히 퍼진 양상"
    "그 이전에는 어떤 질문이 와도 물 사용과 관련된 정보는 절대 제공하지 않는다."
    "다음 예시의 말투를 반영해 대화할 것: (사용자가 인체 모형을 조사한다고 한 경우) 과학실에 흔히 보이는 인체 모형이다. 특별히 이상한 점은 발견되지 않았다."
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
            "<h2 style='text-align: center;'>🧪 보라고등학교<br>실험실 폭발 사고 조사<br></h2>",
            unsafe_allow_html=True
        )

        st.markdown("""
        <div style="text-align:center;">
            <img src="https://i.imgur.com/8epnNuh.png"
                 style="max-width:250px; width:50%; height:auto;">
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='text-align: center;'>

        #### <br>🕵️ 활동 안내

        20xx년 x월 x일, 보라고등학교 실험실에서 폭발 사고가 발생했습니다. 빠른 대피와 교사의 적절한 조치로 인명 피해는 없었지만, 교육청에서는 사안 조사를 위해 조사관을 파견했습니다.

        당신은 보라고등학교로 파견된 **조사관**입니다. 조사 대상들을 심문하고 현장을 조사해 사고의 원인을 밝혀내세요.

        당신은 폭발 사고가 발생한 모둠의 학생 3명을 심문할 수 있습니다. 심문 대상은 학생 A(조장), 학생 B, 학생 C 입니다. 또한 필요하다면 사고 발생 현장 조사도 가능합니다.

        주의할 점은, 심문 대상이 거짓말을 할 수 있다는 점입니다. 현장 조사와 심문 내용에서 모순점을 찾아내, 거짓말을 밝혀내고 진실을 알아내세요.

        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("▶ 조사 시작하기", use_container_width=True):
            st.session_state["page"] = 2
            st.rerun()

def page_investigation():

    st.title("📝 조사 기록")

    if st.button("◀ 이전 화면으로 돌아가기"):
        st.session_state["page"] = 1
        st.rerun()

    tabs = st.tabs([
        "학생 A (조장)",
        "학생 B",
        "학생 C",
        "사건 현장"
    ])

    st.markdown("""
        <style>

        div[data-testid="stTabs"] button p {
            font-size: 18px !important;
            font-weight: 900 !important;
        }

        div[data-testid="stChatMessage"] p {
            font-size: 14px !important;
            margin-bottom: 2px !important;
        }

        div[data-testid="stVerticalBlock"]:has(div[data-testid="stChatMessage"]) {
            display: flex;
            flex-direction: column;
            justify-content: center;
            height: 350px;
        }

        </style>
    """, unsafe_allow_html=True)

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

                with chat_container:
                    st.markdown(f"**{speaker}:** {m['content']}")

            user_input = st.chat_input(
                f"{agent_name} 조사하기",
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