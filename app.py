import base64
import os
from pathlib import Path

import streamlit as st
from google import genai
from helper import build_prompt, validate_text
from google.genai import types
from quiz_helper import build_quiz_prompt, parse_quiz

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
SAMPLE = (
    "Python là ngôn ngữ lập trình dễ học và có cú pháp rõ ràng. "
    "Python được sử dụng để phát triển website, phân tích dữ liệu và trí tuệ nhân tạo. "
    "Python có nhiều thư viện giúp xây dựng ứng dụng nhanh hơn."
)

st.set_page_config(page_title="StudyMate | Tóm tắt bài học", page_icon="📘", layout="wide")


def read_asset(name: str) -> str:
    return (ASSETS_DIR / name).read_text(encoding="utf-8")


def read_image_as_data_uri(name: str) -> str:
    image_path = ASSETS_DIR / name
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def render_header() -> str:
    return read_asset("header.html")


def get_api_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


styles = read_asset("style.css").replace(
    "__COVER_BACKGROUND__", read_image_as_data_uri("anhnenvanlang.png")
)
st.markdown(f"<style>{styles}</style>", unsafe_allow_html=True)
st.markdown(render_header(), unsafe_allow_html=True)

if "lesson" not in st.session_state:
    st.session_state.lesson = ""
if "result" not in st.session_state:
    st.session_state.result = ""
if "quiz" not in st.session_state:
    st.session_state.quiz = []

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
    for i in range(5):
        st.session_state.pop(f"quiz_answer_{i}", None)

left_space, chat_column, right_space = st.columns([1, 2, 1])
with chat_column:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    feature = st.radio(
    "Chọn chức năng",
    ["Tóm tắt bài học", "Tạo câu hỏi trắc nghiệm"],
    horizontal=True,
    key="feature"
    )
    heading = (
    "Nội dung cần tóm tắt"
    if feature == "Tóm tắt bài học"
    else "Nội dung tạo câu hỏi"
    )

    st.markdown(
        f'<div class="section-heading">{heading}</div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="section-note">Dán bài học của bạn vào đây. Nội dung càng rõ ràng thì bản tóm tắt càng dễ hiểu.</div>', unsafe_allow_html=True)

    with st.form("summary_form"):
        lesson = st.text_area(
            "Nội dung bài học",
            key="lesson",
            height=230,
            placeholder="Ví dụ: Python là một ngôn ngữ lập trình phổ biến vì có cú pháp đơn giản...",
            label_visibility="collapsed",
        )
        button_text = (
            "Tạo bản tóm tắt"
            if feature == "Tóm tắt bài học"
            else "Tạo 5 câu trắc nghiệm"
        )

        submitted = st.form_submit_button(
            button_text,
            type="primary",
            use_container_width=True
        )

    left, right = st.columns(2)
    with left:
        if st.button("Điền nội dung mẫu", use_container_width=True):
            st.session_state.lesson = SAMPLE
            st.session_state.result = ""
            st.session_state.quiz = []
            st.session_state.quiz_submitted = False
            st.rerun()
    with right:
        if st.button("Xóa nội dung", use_container_width=True):
            st.session_state.lesson = ""
            st.session_state.result = ""
            st.session_state.quiz = []
            st.session_state.quiz_submitted = False
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


with chat_column:
    if submitted:
        st.session_state.result = ""
        st.session_state.quiz = []
        st.session_state.quiz_submitted = False

        error = validate_text(lesson)

        if error:
            st.warning(error)
        else:
            key = get_api_key()

            if not key:
                st.error(
                    "Chưa có GEMINI_API_KEY. "
                    "Hãy kiểm tra file secrets.toml."
                )
            else:
                try:
                    client = genai.Client(api_key=key)

                    # CHỨC NĂNG 1: TÓM TẮT BÀI HỌC
                    if feature == "Tóm tắt bài học":
                        with st.spinner("Đang tạo bản tóm tắt..."):
                            response = client.models.generate_content(
                                model=MODEL,
                                contents=build_prompt(lesson)
                            )

                        if response.text and response.text.strip():
                            st.session_state.result = response.text.strip()
                        else:
                            st.warning("Chưa nhận được bản tóm tắt.")

                    # CHỨC NĂNG 2: TẠO TRẮC NGHIỆM
                    else:
                        with st.spinner("Đang tạo 5 câu hỏi..."):
                            response = client.models.generate_content(
                                model=MODEL,
                                contents=build_quiz_prompt(lesson),
                                config=types.GenerateContentConfig(
                                    response_mime_type="application/json"
                                )
                            )

                        if response.text:
                            st.session_state.quiz = parse_quiz(
                                response.text
                            )
                            st.success("Đã tạo 5 câu hỏi trắc nghiệm!")
                        else:
                            st.warning("Chưa tạo được câu hỏi.")

                except ValueError:
                    st.error(
                        "Câu hỏi được tạo chưa đúng định dạng. "
                        "Hãy thử tạo lại."
                    )
                except Exception as exc:
                    message = str(exc).lower()

                    if "429" in message or "quota" in message:
                        st.error(
                            "Đã hết hạn mức Gemini Free Tier. "
                            "Vui lòng thử lại sau."
                        )
                    elif "404" in message or "not_found" in message:
                        st.error(
                            "Model Gemini chưa khả dụng. "
                            "Hãy kiểm tra model đang sử dụng."
                        )
                    elif any(
                        x in message
                        for x in ["401", "403", "api key", "api_key"]
                    ):
                        st.error(
                            "API key không hợp lệ hoặc chưa có quyền."
                        )
                    else:
                        st.error(
                            "Không kết nối được Gemini. "
                            "Vui lòng thử lại sau."
                        )

    # HIỂN THỊ KẾT QUẢ TÓM TẮT
    if st.session_state.result and feature == "Tóm tắt bài học":
        with st.container(key="summary_result"):
            st.markdown(
                '<div class="section-heading">Bản tóm tắt của bạn</div>',
                unsafe_allow_html=True
            )

            st.markdown(st.session_state.result)

            st.download_button(
                "Tải bản tóm tắt (.txt)",
                st.session_state.result,
                file_name="ban_tom_tat.txt",
                mime="text/plain",
                use_container_width=True
            )

    # HIỂN THỊ BÀI TRẮC NGHIỆM
    if st.session_state.quiz and feature == "Tạo câu hỏi trắc nghiệm":
        with st.container(key="quiz_result"):
            st.subheader("Bài trắc nghiệm của bạn")
            st.write("Chọn một đáp án cho mỗi câu hỏi.")

            with st.form("quiz_answer_form"):

                for i, question in enumerate(st.session_state.quiz):
                    st.markdown(
                        f"**Câu {i + 1}: {question['question']}**"
                    )

                    options = question["options"]

                    st.radio(
                        f"Chọn đáp án câu {i + 1}",
                        options=["A", "B", "C", "D"],
                        format_func=lambda x, opts=options:
                            f"{x}. {opts[x]}",
                        index=None,
                        key=f"quiz_answer_{i}"
                    )

                    st.divider()

                check_answers = st.form_submit_button(
                    "Nộp bài và xem điểm",
                    type="primary",
                    use_container_width=True
                )

            if check_answers:
                answers = [
                    st.session_state.get(f"quiz_answer_{i}")
                    for i in range(len(st.session_state.quiz))
                ]

                if any(answer is None for answer in answers):
                    st.warning("Vui lòng trả lời đủ 5 câu hỏi.")
                    st.session_state.quiz_submitted = False
                else:
                    st.session_state.quiz_submitted = True

            if st.session_state.quiz_submitted:
                score = 0

                for i, question in enumerate(st.session_state.quiz):
                    selected = st.session_state.get(
                        f"quiz_answer_{i}"
                    )

                    correct = question["correct_answer"]

                    if selected == correct:
                        score += 1

                st.success(f"Kết quả của bạn: {score}/5 câu đúng")

                st.markdown("### Đáp án và giải thích")

                for i, question in enumerate(st.session_state.quiz):
                    correct = question["correct_answer"]
                    selected = st.session_state.get(
                        f"quiz_answer_{i}"
                    )

                    if selected == correct:
                        st.write(f"✅ Câu {i + 1}: Chính xác")
                    else:
                        st.write(f"❌ Câu {i + 1}: Chưa chính xác")

                    st.write(
                        f"**Đáp án đúng:** {correct}. "
                        f"{question['options'][correct]}"
                    )

                    st.write(
                        f"**Giải thích:** {question['explanation']}"
                    )

                    st.divider()


    if st.session_state.result:
        with st.container(key="summary_result"):
            st.markdown('<div class="section-heading">Bản tóm tắt của bạn</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-note">Kết quả được rút gọn từ nội dung bạn đã nhập.</div>', unsafe_allow_html=True)
            st.markdown(st.session_state.result)
            st.download_button(
                "Tải bản tóm tắt (.txt)",
                st.session_state.result,
                file_name="ban_tom_tat.txt",
                mime="text/plain",
                use_container_width=True,
            )

st.markdown('<div class="footer-copy">StudyMate · Công cụ hỗ trợ học tập. Hãy kiểm tra lại thông tin với tài liệu gốc.</div>', unsafe_allow_html=True)
