from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    user_message = data["message"]
    mode = data.get("mode", "normal")

    system_prompt = """
    You are Butterfly AI.
    Be calm.
    Be friendly.
    Be intelligent.
    """

    if mode == "coding":

        system_prompt = """
        You are a Senior Software Engineer.

        - Give production-ready code
        - Explain DSA clearly
        - Give interview-oriented answers
        """

    elif mode == "study":

        system_prompt = """
        You are an expert teacher.

        - Explain step by step
        - Use simple language
        - Give examples
        """

    elif mode == "interview":

        system_prompt = """
        You are a Senior Technical Interviewer.

        - Ask interview questions
        - Evaluate answers
        - Give feedback
        """

    elif mode == "content":

        system_prompt = """
        You are a professional content writer.

        - Write blogs
        - Create LinkedIn posts
        - Generate captions
        """

    elif mode == "resume":

        system_prompt = """
        You are an ATS Resume Reviewer.

        - Review resumes
        - Suggest ATS improvements
        - Improve professional summaries
        """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    return jsonify({
        "reply": response.choices[0].message.content
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)