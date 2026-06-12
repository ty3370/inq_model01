import streamlit as st
import os
import time
import pandas as pd
import io
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

# 환경 변수 로드 및 초기화
load_dotenv()
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
openai_client = OpenAI(api_key=OPENAI_API_KEY)
MODEL_NAME = "gpt-5.4-mini"

# Streamlit 앱 UI 설정
st.set_page_config(
    page_title="서술형 평가 자동 채점 시스템 [GPT]",
    page_icon="📝",
    layout="wide"
)

# --- 상단 타이틀 및 인용구 (고정 배치) ---
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

# --- 세션 상태(Session State) 초기화 ---
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

# --- 왼쪽/오른쪽 2개 탭 구성 ---
tab_left, tab_right = st.tabs(["⚙️ 채점 기준 설정", "🔎 학생 답안지 업로드 및 채점"])

# --- [왼쪽 탭] 채점 기준 설정 ---

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
            # 데이터 동기화
            st.session_state["grading_criteria"].update({
                "max_score": max_score,
                "base_score": base_score,
                "score_step": score_step,
                "pages_per_student": pages_per_student,
                "criteria_text": criteria_text,
                "exception_text": exception_text
            })
            
            # 초기 시스템 프롬프트 작성
            st.session_state["system_prompt"] = (
                f"당신은 엄격하고 공정한 채점관입니다. 제시된 채점 기준과 예외 항목을 바탕으로 학생의 서술형 답안을 채점하세요. 모든 채점 결과는 철저하게 채점 기준에 근거하고, 스스로 판단하지 마세요. 마크다운을 사용하지 말고, 줄바꿈을 사용해 가독성을 높이세요.\n\n"
                f"[점수 규칙]\n"
                f"- 만점: {max_score}점 / 기본 점수: {base_score}점\n"
                f"- 점수 감점 및 부여는 반드시 급간 단위({score_step}점)로만 수행하세요.\n\n"
                f"[채점 기준]\n{criteria_text}\n\n"
                f"[정답 인정 또는 오답 처리 항목 (예외 기준)]\n{exception_text}\n\n"
                f"[출력 양식]\n"
                f"반드시 다음 3가지 항목 양식에 맞춰 응답하세요. 다른 인사말이나 불필요한 텍스트는 절대 생략합니다.\n"
                f"1. 채점 항목별 채점 결과와 세부 근거:\n"
                f"2. 총점: (기본점수와 감점 요인을 계산한 최종 점수)\n"
                f"3. 학생에게 제공할 피드백:"
            )
            st.success("✅ 채점 기준 프롬프트가 최신 상태로 생성/수정되었습니다!")

# --- 파일 업로드 및 채점 ---

with tab_right:
    st.subheader("📂 학생 답안지 채점 진행")
    
    # 설정이 먼저 완료되었는지 검증
    if not st.session_state["system_prompt"]:
        st.warning("⚠️ 먼저 왼쪽의 '⚙️ 채점 기준 설정' 탭에서 [업데이트] 버튼을 눌러 초기 설정을 진행해 주세요.")
    
    uploaded_file = st.file_uploader("학생들의 답안지 PDF 파일을 업로드하세요.", type=["pdf"])

    # 파일이 새로 업로드되면 기존 페이지 변환 기록 초기화
    if uploaded_file is not None:
        if "last_uploaded_filename" not in st.session_state or st.session_state["last_uploaded_filename"] != uploaded_file.name:
            st.session_state["pdf_pages"] = []
            st.session_state["grading_results"] = {}
            st.session_state["last_uploaded_filename"] = uploaded_file.name

        # PDF 변환 로직
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

            # --- 모든 학생 일괄 채점 시작 버튼 ---
#            start_bulk_grading = st.button("🔍 모든 학생 일괄 채점 시작", key="btn_bulk_grade", type="primary")

            start_bulk_grading = False # 일괄 채점 활성화 시 이 문장을 주석처리
            
            if start_bulk_grading:
                bulk_progress = st.progress(0)
                with st.spinner("모든 학생에 대한 일괄 채점을 진행 중입니다..."):
                    for s_idx in range(total_students):
                        student_num = s_idx + 1
                        
                        start_page = s_idx * p_per_student
                        end_page = min(start_page + p_per_student, len(pages))
                        student_pages = pages[start_page:end_page]
                        
                        try:
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
                                model=MODEL_NAME,
                                messages=messages_payload
                            )
                            st.session_state["grading_results"][student_num] = response.choices[0].message.content
                        except Exception as e:
                            st.error(f"학생 {student_num} 채점 중 OpenAI API 오류 발생: {e}")
                        
                        # 진행 바 업데이트
                        bulk_progress.progress((s_idx + 1) / total_students)
                st.success("🎉 모든 학생의 일괄 채점이 완료되었습니다!")
                st.rerun()

            st.markdown("---")

            # --- 채점 결과 엑셀 다운로드 구역 ---
            st.subheader("📊 채점 결과 내보내기")
            
            excel_data = []
            
            # 전체 학생 목록을 기준으로 엑셀 행을 미리 생성합니다.
            for s_idx in range(total_students):
                student_num = s_idx + 1
                # 해당 학생의 채점 결과가 있으면 가져오고, 없으면 빈 문자열("") 처리를 합니다.
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
            
            # key 값을 지정해 주어야 다운로드 시 세션이 꼬이거나 풀리는 것을 방지할 수 있습니다.
            st.download_button(
                label="📥 전체 채점 결과 Excel 다운로드",
                data=buffer,
                file_name="서술형_채점_결과.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="secondary",
                key="btn_excel_download"  # <-- 이 부분 추가
            )
            st.markdown("---")

            # 학생 단위 루프 생성
            for s_idx in range(total_students):
                student_num = s_idx + 1
                st.markdown(f"### 학생 {student_num} 답안지")
                
                start_page = s_idx * p_per_student
                end_page = min(start_page + p_per_student, len(pages))
                student_pages = pages[start_page:end_page]
                
                img_cols = st.columns(p_per_student)
                for i, page_img in enumerate(student_pages):
                    with img_cols[i]:
                        st.image(page_img, caption=f"학생 {student_num} - {i+1}번 페이지", width=700) # 이미지 크기

                # 결과 레이아웃: 왼쪽(채점 결과) / 오른쪽(실시간 예외 기준 추가창)
                res_col, side_col = st.columns([2, 1])
                
                with res_col:
                    start_grading = st.button(f"🔍 학생 {student_num} 개별 채점", key=f"btn_grade_{student_num}")
                    
                    if start_grading:
                        with st.spinner(f"학생 {student_num}의 답안 분석 중..."):
                            try:
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
                                    model=MODEL_NAME,
                                    messages=messages_payload
                                )
                                st.session_state["grading_results"][student_num] = response.choices[0].message.content
                                st.rerun()
                            except Exception as e:
                                st.error(f"OpenAI API 통신 오류: {e}")

                    # 채점 결과 렌더링
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
                                # 1. 왼쪽 탭 데이터 업데이트
                                current_exceptions = st.session_state["grading_criteria"]["exception_text"]
                                updated_exceptions = (current_exceptions + f"\n- {new_rule}").strip()
                                st.session_state["grading_criteria"]["exception_text"] = updated_exceptions
                                
                                # 2. 내부 시스템 프롬프트 자동 동기화
                                st.session_state["system_prompt"] = (
                                    f"당신은 엄격하고 공정한 채점관입니다. 제시된 채점 기준과 예외 항목을 바탕으로 학생의 서술형 답안을 채점하세요. 모든 채점 결과는 철저하게 채점 기준에 근거하고, 스스로 판단하지 마세요. 마크다운을 사용하지 말고, 줄바꿈을 사용해 가독성을 높이세요.\n\n"
                                    f"[점수 규칙]\n"
                                    f"- 만점: {st.session_state['grading_criteria']['max_score']}점 / 기본 점수: {st.session_state['grading_criteria']['base_score']}점\n"
                                    f"- 점수 감점 및 부여는 반드시 급간 단위({st.session_state['grading_criteria']['score_step']}점)로만 수행하세요.\n\n"
                                    f"[채점 기준]\n{st.session_state['grading_criteria']['criteria_text']}\n\n"
                                    f"[정답 인정 또는 오답 처리 항목 (예외 기준)]\n{updated_exceptions}\n\n"
                                    f"[출력 양식]\n"
                                    f"반드시 다음 3가지 항목 양식에 맞춰 응답하세요. 다른 인사말은 생략합니다.\n"
                                    f"1. 채점 항목별 채점 결과와 세부 근거:\n"
                                    f"2. 총점:\n"
                                    f"3. 학생에게 제공할 피드백:"
                                )
                                time.sleep(0.5)
                                msg_placeholder = st.empty()
                                msg_placeholder.success("🎯 기준 업데이트 완료! 다음 채점부터 바로 적용됩니다.")
                                time.sleep(1.2)
                                msg_placeholder.empty()
                                
                            st.rerun() # UI 리프레시
                st.markdown("---")