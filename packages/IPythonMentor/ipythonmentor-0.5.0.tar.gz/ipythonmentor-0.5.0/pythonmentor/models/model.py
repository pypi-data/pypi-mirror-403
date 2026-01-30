from abc import ABC, abstractmethod

def build_content(question: str, answer: str, prompt: str) -> str:
    if question is None:
        question = ""
    if answer is None:
        answer = ""
    if prompt is None:
        prompt = ""

    return f"""
            Instruction:
            {prompt.strip()}

            Question:
            {question.strip()}

            Answer:
            {answer.strip()}

            Return ONLY valid JSON in the following format.
            DO NOT add explanations, markdown, or extra text.
            DO NOT wrap in ```.

            JSON schema:
            {{
              "score": number (0-100),
              "feedback": string
            }}
    """.strip()



class Model(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def evaluate(self, question: str, answer: str, prompt: str) -> str:
        pass
