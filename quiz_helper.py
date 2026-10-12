
import json


def build_quiz_prompt(lesson):
    return f"""
Dựa vào nội dung bài học sau, hãy tạo đúng 5 câu hỏi
trắc nghiệm bằng tiếng Việt.

Yêu cầu:
- Mỗi câu hỏi có 4 đáp án A, B, C, D.
- Chỉ có một đáp án đúng.
- Có giải thích ngắn gọn cho đáp án đúng.
- Câu hỏi phải dựa trên nội dung bài học.
- Trả về JSON, không thêm văn bản bên ngoài.

Cấu trúc JSON:
{{
  "questions": [
    {{
      "question": "Nội dung câu hỏi",
      "options": {{
        "A": "Đáp án A",
        "B": "Đáp án B",
        "C": "Đáp án C",
        "D": "Đáp án D"
      }},
      "correct_answer": "A",
      "explanation": "Giải thích"
    }}
  ]
}}

Nội dung bài học:
{lesson}
"""


def parse_quiz(response_text):
    data = json.loads(response_text)
    questions = data["questions"]

    if not isinstance(questions, list) or len(questions) != 5:
        raise ValueError("Gemini phải tạo đúng 5 câu hỏi.")

    for question in questions:
        if not isinstance(question, dict):
            raise ValueError("Cấu trúc câu hỏi không hợp lệ.")

        options = question["options"]

        if not isinstance(options, dict):
            raise ValueError("Đáp án không hợp lệ.")

        if set(options.keys()) != {"A", "B", "C", "D"}:
            raise ValueError("Mỗi câu phải có 4 đáp án.")

        if question["correct_answer"] not in options:
            raise ValueError("Đáp án đúng không hợp lệ.")

        if not isinstance(question["question"], str):
            raise ValueError("Nội dung câu hỏi không hợp lệ.")

        if not isinstance(question["explanation"], str):
            raise ValueError("Phần giải thích không hợp lệ.")

        if not question["question"].strip():
            raise ValueError("Câu hỏi không được để trống.")

        if not question["explanation"].strip():
            raise ValueError("Giải thích không được để trống.")

        if any(
            not isinstance(value, str) or not value.strip()
            for value in options.values()
        ):
            raise ValueError("Nội dung đáp án không hợp lệ.")

    return questions
