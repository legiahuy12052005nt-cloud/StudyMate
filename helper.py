MAX_CHARACTERS = 10000


def validate_text(text: str) -> str | None:
    if not text or not text.strip():
        return "Vui lòng nhập nội dung bài học trước khi tóm tắt."
    if len(text) > MAX_CHARACTERS:
        return f"Nội dung tối đa {MAX_CHARACTERS:,} ký tự. Hãy rút ngắn bài học."
    return None


def build_prompt(text: str) -> str:
    return (
        "Bạn là trợ lý học tập. Hãy tóm tắt bài học dưới đây bằng tiếng Việt "
        "rõ ràng, đơn giản và chính xác. Nêu 3–5 ý chính bằng gạch đầu dòng. "
        "Chỉ dùng nội dung được cung cấp, không bịa thêm dữ kiện. "
        "Bài học:\n" + text
    )
