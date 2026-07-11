import streamlit as st
import os
import time
import pandas as pd
import io
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY"))

openai_client = OpenAI(api_key=OPENAI_API_KEY)
gemini_client = genai.Client(api_key=GOOGLE_API_KEY)

MODEL_GPT = "gpt-5.5"
MODEL_GEMINI_PRO = "gemini-3.1-pro-preview"
MODEL_GEMINI_FLASH = "gemini-3.5-flash"

st.set_page_config(
    page_title="서술형 평가 자동 채점 시스템",
    page_icon="📝",
    layout="wide"
)

st.markdown(
    """
    <h1 style="text-align: center;">서술형 평가 자동 채점 시스템</h1>
    """, 
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="text-align: center;">
        <blockquote style="font-size: 16px; border: none; display: inline-block; padding: 10px 20px; background-color: transparent; margin: 0;">
            💫 <strong>“많은 사람을 옳은 데로 돌아오게 한 자는 별과 같이 영원토록 빛나리라”</strong> — 다니엘 12장 3절
        </blockquote>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

if "system_prompt" not in st.session_state:
    st.session_state["system_prompt"] = ""
if "grading_criteria" not in st.session_state:
    st.session_state["grading_criteria"] = {
        "max_score": 20,
        "base_score": 8,
        "score_step": 1,
        "pages_per_student": 1,
        "criteria_text": "",
        "exception_text": ""
    }
if "pdf_pages" not in st.session_state:
    st.session_state["pdf_pages"] = []
if "grading_results" not in st.session_state:
    st.session_state["grading_results"] = {}

tab_left, tab_right = st.tabs(["⚙️ 채점 기준 설정", "🔎 학생 답안지 업로드 및 채점"])

with tab_left:
    st.subheader("📋 채점 기준 설정")
    st.info("채점 기준과 감점 규정, 채점 중 발견된 예외 항목들을 관리하는 공간입니다.")
    
    with st.form(key="config_form"):
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            max_score = st.number_input("만점", value=st.session_state["grading_criteria"]["max_score"], step=1)
        with col_b:
            base_score = st.number_input("기본 점수", value=st.session_state["grading_criteria"]["base_score"], step=1)
        with col_c:
            score_step = st.number_input("점수 급간", value=st.session_state["grading_criteria"]["score_step"], step=1)
        with col_d:
            pages_per_student = st.number_input("학생 1인당 답안지 수", value=st.session_state["grading_criteria"]["pages_per_student"], step=1, min_value=1)

        criteria_text = st.text_area("채점 기준", value=st.session_state["grading_criteria"]["criteria_text"], height=150, placeholder="예: 1번 문제의 A=34.3 (1점), B=441 (1점)")
        
        exception_text = st.text_area("정답 인정 또는 오답 처리 항목 (예외 기준)", value=st.session_state["grading_criteria"]["exception_text"], height=150, placeholder="예: 1번 문제의 B를 분수로 써도 정답 인정")

        submit_config = st.form_submit_button("🔄 기준 업데이트")

        if submit_config:
            st.session_state["grading_criteria"].update({
                "max_score": max_score,
                "base_score": base_score,
                "score_step": score_step,
                "pages_per_student": pages_per_student,
                "criteria_text": criteria_text,
                "exception_text": exception_text
            })
            
            st.session_state["system_prompt"] = (
                f"당신은 엄격하고 공정한 채점관입니다. 제시된 채점 기준과 예외 항목을 바탕으로 학생의 서술형 답안을 채점하세요. 모든 채점 결과는 철저하게 채점 기준에 근거하고, 스스로 판단하지 마세요. 마크다운을 사용하지 말고, 줄바꿈을 사용해 가독성을 높이세요.\n\n"
                f"[점수 규칙]\n"
                f"- 만점: {max_score}점 / 기본 점수: {base_score}점\n"
                f"- 점수 감점 및 부여는 반드시 급간 단위({score_step}점)로만 수행하세요.\n\n"
                f"[채점 기준]\n{criteria_text}\n\n"
                f"[정답 인정 또는 오답 처리 항목 (예외 기준)]\n{exception_text}\n\n"
                f"[출력 양식]\n"
                f"반드시 다음 3가지 항목 양식에 맞춰 응답하세요. 다른 인사말이나 불필요한 텍스트는 절대 생략합니다.\n\n"
                f"1. 채점 항목별 채점 결과와 세부 근거:\n"
                f"개별 항목명) [획득점수]점 / [배점]점\n"
                f"- 채점 근거: [정답 요인 또는 감점 사유 설명]\n\n"
                f"2. 총점:\n"
                f"최종 점수: [최종 점수]점 (만점: {max_score}점 / 기본 점수: {base_score}점)\n\n"
                f"3. 학생에게 제공할 피드백:\n"
                f"- [학생이 이해한 부분과 부족한 개념을 명확하게 요약한 피드백 작성]"
            )
            st.success("✅ 채점 기준 프롬프트가 최신 상태로 생성/수정되었습니다!")

with tab_right:
    st.subheader("📂 학생 답안지 채점 진행")
    
    is_ready = bool(st.session_state["system_prompt"])
    
    if not is_ready:
        st.warning("⚠️ 먼저 왼쪽의 '⚙️ 채점 기준 설정' 탭에서 [업데이트] 버튼을 눌러 초기 설정을 진행해 주세요.")
    
    uploaded_file = st.file_uploader("학생들의 답안지 PDF 파일을 업로드하세요.", type=["pdf"], disabled=not is_ready)

    if uploaded_file is not None:
        if "last_uploaded_filename" not in st.session_state or st.session_state["last_uploaded_filename"] != uploaded_file.name:
            st.session_state["pdf_pages"] = []
            st.session_state["grading_results"] = {}
            st.session_state["last_uploaded_filename"] = uploaded_file.name
        if not st.session_state["pdf_pages"]:
            with st.spinner("PDF 파일을 페이지별 이미지로 변환하고 있습니다..."):
                try:
                    from pdf2image import convert_from_bytes
                    pdf_bytes = uploaded_file.read()
                    st.session_state["pdf_pages"] = convert_from_bytes(pdf_bytes)
                except Exception as e:
                    st.error(f"PDF 변환 실패: {e}. 시스템에 'pdf2image'와 'poppler'가 구성되어 있는지 확인하세요.")

        pages = st.session_state["pdf_pages"]
        p_per_student = st.session_state["grading_criteria"]["pages_per_student"]
        
        if pages:
            total_students = (len(pages) + p_per_student - 1) // p_per_student
            st.info(f"총 {len(pages)}쪽 분석 완료 ➡️ 학생 1인당 {p_per_student}장씩 묶어 총 {total_students}명의 학생 답안지를 배치했습니다.")
            st.markdown("---")
            st.subheader("📊 채점 결과 내보내기")
            
            excel_data = []
            
            for s_idx in range(total_students):
                student_num = s_idx + 1
                result_text = st.session_state["grading_results"].get(student_num, "")
                
                excel_data.append({
                    "학생 번호": f"학생 {student_num}",
                    "채점 결과 상세 및 피드백": result_text
                })
            
            df = pd.DataFrame(excel_data)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='채점결과')
            buffer.seek(0)
            
            st.download_button(
                label="📥 전체 채점 결과 Excel 다운로드",
                data=buffer,
                file_name="서술형_채점_결과.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="secondary",
                key="btn_excel_download"
            )
            st.markdown("---")

            for s_idx in range(total_students):
                student_num = s_idx + 1
                st.markdown(f"### 학생 {student_num} 답안지")
                
                start_page = s_idx * p_per_student
                end_page = min(start_page + p_per_student, len(pages))
                student_pages = pages[start_page:end_page]
                
                img_cols = st.columns(p_per_student)
                for i, page_img in enumerate(student_pages):
                    with img_cols[i]:
                        st.image(page_img, caption=f"학생 {student_num} - {i+1}번 페이지", width=700)

                res_col, side_col = st.columns([2, 1])
                
                with res_col:
                    col_btn1, col_btn2, col_btn3, col_btn_rest = st.columns([0.25, 0.28, 0.29, 0.18])
                    start_grading_gpt = col_btn1.button("gpt-5.5로 채점하기", key=f"btn_grade_gpt_{student_num}", use_container_width=True, help="📊 그림/그래프 인식 우수")
                    start_grading_gemini = col_btn2.button("gemini-3.1-pro로 채점하기", key=f"btn_grade_gemini_{student_num}", use_container_width=True, help="✍️ 손글씨 인식 우수")
                    start_grading_flash = col_btn3.button("gemini-3.5-flash로 채점하기", key=f"btn_grade_flash_{student_num}", use_container_width=True, help="⚡ 속도 빠름")
                    
                    if start_grading_gpt or start_grading_gemini or start_grading_flash:
                        if start_grading_gpt:
                            selected_single_model = "gpt"
                        elif start_grading_gemini:
                            selected_single_model = "gemini_pro"
                        else:
                            selected_single_model = "gemini_flash"
                            
                        with st.spinner(f"학생 {student_num}의 답안 분석 중..."):
                            try:
                                if selected_single_model == "gpt":
                                    messages_payload = [
                                        {"role": "system", "content": st.session_state['system_prompt']}
                                    ]
                                    user_contents = []
                                    for page_img in student_pages:
                                        buffered = io.BytesIO()
                                        page_img.save(buffered, format="PNG")
                                        import base64
                                        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                                        user_contents.append({
                                            "type": "image_url",
                                            "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                                        })
                                    user_contents.append({
                                        "type": "text",
                                        "text": f"위 이미지 파일들은 학생 {student_num}의 서술형 답안지입니다. 기준에 맞게 채점하세요."
                                    })
                                    messages_payload.append({"role": "user", "content": user_contents})
                                    response = openai_client.chat.completions.create(
                                        model=MODEL_GPT,
                                        messages=messages_payload
                                    )
                                    st.session_state["grading_results"][student_num] = response.choices[0].message.content
                                
                                elif selected_single_model == "gemini_pro":
                                    contents_payload = list(student_pages)
                                    contents_payload.append(
                                        f"{st.session_state['system_prompt']}\n\n위 이미지 파일들은 학생 {student_num}의 서술형 답안지입니다. 기준에 맞게 채점하세요."
                                    )
                                    response = gemini_client.models.generate_content(
                                        model=MODEL_GEMINI_PRO,
                                        contents=contents_payload
                                    )
                                    st.session_state["grading_results"][student_num] = response.text
                                    
                                elif selected_single_model == "gemini_flash":
                                    contents_payload = list(student_pages)
                                    contents_payload.append(
                                        f"{st.session_state['system_prompt']}\n\n위 이미지 파일들은 학생 {student_num}의 서술형 답안지입니다. 기준에 맞게 채점하세요."
                                    )
                                    response = gemini_client.models.generate_content(
                                        model=MODEL_GEMINI_FLASH,
                                        contents=contents_payload
                                    )
                                    st.session_state["grading_results"][student_num] = response.text
                                    
                                st.rerun()
                            except Exception as e:
                                st.error(f"API 통신 오류: {e}")

                    if student_num in st.session_state["grading_results"]:
                        st.write(f"**학생 {student_num} 채점 결과**")
                        st.info(st.session_state["grading_results"][student_num])
                
                with side_col:
                    if student_num in st.session_state["grading_results"]:
                        st.write("➕ **정답 인정/오답 처리 항목 추가**")
                        new_rule = st.text_input(
                            "새로운 정답 인정/오답 처리 규칙 입력:", 
                            placeholder="예: 충격량이 감소한다고 언급하면 오답 처리",
                            key=f"new_rule_{student_num}"
                        )
                        update_rule_btn = st.button("기준 추가 및 업데이트", key=f"btn_add_{student_num}")
                        
                        if update_rule_btn and new_rule:
                            with st.spinner("새로운 규칙을 시스템 프롬프트에 반영하는 중..."):
                                current_exceptions = st.session_state["grading_criteria"]["exception_text"]
                                updated_exceptions = (current_exceptions + f"\n- {new_rule}").strip()
                                st.session_state["grading_criteria"]["exception_text"] = updated_exceptions
                                
                                st.session_state["system_prompt"] = (
                                    f"당신은 엄격하고 공정한 채점관입니다. 제시된 채점 기준과 예외 항목을 바탕으로 학생의 서술형 답안을 채점하세요. 모든 채점 결과는 철저하게 채점 기준에 근거하고, 스스로 판단하지 마세요. 마크다운을 사용하지 말고, 줄바꿈을 사용해 가독성을 높이세요.\n\n"
                                    f"[점수 규칙]\n"
                                    f"- 만점: {st.session_state['grading_criteria']['max_score']}점 / 기본 점수: {st.session_state['grading_criteria']['base_score']}점\n"
                                    f"- 점수 감점 및 부여는 반드시 급간 단위({st.session_state['grading_criteria']['score_step']}점)로만 수행하세요.\n\n"
                                    f"[채점 기준]\n{st.session_state['grading_criteria']['criteria_text']}\n\n"
                                    f"[정답 인정 또는 오답 처리 항목 (예외 기준)]\n{updated_exceptions}\n\n"
                                    f"[출력 양식]\n"
                                    f"반드시 다음 3가지 항목 양식에 맞춰 응답하세요. 다른 인사말은 생략합니다.\n\n"
                                    f"1. 채점 항목별 채점 결과와 세부 근거:\n"
                                    f"개별 항목명) [획득점수]점 / [배점]점\n"
                                    f"- 채점 근거: [정답 요인 또는 감점 사유 설명]\n\n"
                                    f"2. 총점:\n"
                                    f"최종 점수: [최종 점수]점 (만점: {st.session_state['grading_criteria']['max_score']}점 / 기본 점수: {st.session_state['grading_criteria']['base_score']}점)\n\n"
                                    f"3. 학생에게 제공할 피드백:\n"
                                    f"- [학생이 이해한 부분과 부족한 개념을 명확하게 요약한 피드백 작성]"
                                )
                                time.sleep(0.5)
                                msg_placeholder = st.empty()
                                msg_placeholder.success("🎯 기준 업데이트 완료! 다음 채점부터 바로 적용됩니다.")
                                time.sleep(1.2)
                                msg_placeholder.empty()
                                
                            st.rerun()
                st.markdown("---")