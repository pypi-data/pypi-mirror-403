# PythonMentor

PythonMentor grades Python submissions and returns feedback using a Gemini model.

## Install

```bash
pip install pythonmentor
```

## Usage

```python
from pythonmentor import PythonMentor

mentor = PythonMentor(api_key="YOUR_GEMINI_API_KEY")
result = mentor.mark_submission(
    answer_path="path/to/submission.zip",
    question="Write a function that adds two numbers.",
    prompt="Be concise and focus on correctness.",
)
print(result)
```

`answer_path` can be a directory or a zip file. The submission must contain at
least one `.py` or `.ipynb` file.

## Requirements

- Python 3.9+
- `google-genai`
