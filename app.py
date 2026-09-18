from flask import Flask, render_template, request, jsonify, url_for
from openai import OpenAI
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from pypdf import PdfReader
from docx import Document
from openpyxl import load_workbook, Workbook
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

import os
import base64
import uuid
import json
import re
import fitz


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

app = Flask(__name__)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# ============================================================
# MODELS
# ============================================================

CHAT_MODEL = os.getenv(
    "OPENAI_CHAT_MODEL",
    "gpt-4o-mini"
)

IMAGE_MODEL = os.getenv(
    "OPENAI_IMAGE_MODEL",
    "gpt-image-2"
)


# ============================================================
# FOLDERS
# ============================================================

UPLOAD_FOLDER = os.path.join(
    "static",
    "uploads"
)

GENERATED_FOLDER = os.path.join(
    "static",
    "generated"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    GENERATED_FOLDER,
    exist_ok=True
)


# ============================================================
# FILE LIMIT
# ============================================================

app.config[
    "MAX_CONTENT_LENGTH"
] = 25 * 1024 * 1024


# ============================================================
# ALLOWED FILES
# ============================================================

ALLOWED_EXTENSIONS = {
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "webp",
    "docx",
    "xlsx",
    "xls",
    "txt",
    "csv"
}


# ============================================================
# BASIC HELPERS
# ============================================================

def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


def get_extension(filename):

    return filename.rsplit(
        ".",
        1
    )[1].lower()


def clean_text(text):

    if not text:
        return ""

    return text.strip()


# ============================================================
# IMAGE -> DATA URL
# ============================================================

def image_to_data_url(filepath):

    extension = get_extension(
        filepath
    )

    mime_types = {

        "jpg": "image/jpeg",

        "jpeg": "image/jpeg",

        "png": "image/png",

        "webp": "image/webp"
    }

    mime_type = mime_types.get(
        extension,
        "image/png"
    )

    with open(
        filepath,
        "rb"
    ) as file:

        encoded = base64.b64encode(
            file.read()
        ).decode("utf-8")

    return (
        f"data:{mime_type};"
        f"base64,{encoded}"
    )


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(filepath):

    text_parts = []

    try:

        reader = PdfReader(filepath)

        for index, page in enumerate(
            reader.pages
        ):

            try:

                page_text = (
                    page.extract_text()
                    or ""
                )

                if page_text.strip():

                    text_parts.append(
                        f"\n--- PAGE {index + 1} ---\n"
                    )

                    text_parts.append(
                        page_text
                    )

            except Exception as error:

                print(
                    "PDF page error:",
                    error
                )

    except Exception as error:

        print(
            "PDF extraction error:",
            error
        )

    return "\n".join(
        text_parts
    )


# ============================================================
# PDF PAGE IMAGES
# ============================================================

def extract_pdf_images(
    filepath,
    max_pages=12
):

    images = []

    try:

        pdf = fitz.open(
            filepath
        )

        page_count = min(
            len(pdf),
            max_pages
        )

        for index in range(
            page_count
        ):

            page = pdf.load_page(
                index
            )

            matrix = fitz.Matrix(
                1.4,
                1.4
            )

            pix = page.get_pixmap(
                matrix=matrix,
                alpha=False
            )

            image_bytes = pix.tobytes(
                "png"
            )

            encoded = base64.b64encode(
                image_bytes
            ).decode("utf-8")

            images.append({
                "page": index + 1,
                "data_url":
                    "data:image/png;base64,"
                    + encoded
            })

        pdf.close()

    except Exception as error:

        print(
            "PDF image error:",
            error
        )

    return images


# ============================================================
# DOCX
# ============================================================

def extract_docx_text(filepath):

    content = []

    try:

        document = Document(
            filepath
        )

        for paragraph in (
            document.paragraphs
        ):

            text = paragraph.text.strip()

            if text:

                content.append(
                    text
                )


        for table_index, table in enumerate(
            document.tables
        ):

            content.append(
                f"\n--- TABLE "
                f"{table_index + 1} ---"
            )

            for row in table.rows:

                row_values = []

                for cell in row.cells:

                    row_values.append(
                        cell.text.strip()
                    )

                content.append(
                    " | ".join(
                        row_values
                    )
                )

    except Exception as error:

        print(
            "DOCX extraction error:",
            error
        )

    return "\n".join(
        content
    )


# ============================================================
# EXCEL
# ============================================================

def extract_excel_text(filepath):

    content = []

    try:

        workbook = load_workbook(
            filepath,
            read_only=True,
            data_only=True
        )

        for sheet in workbook.worksheets:

            content.append(
                f"\n--- SHEET: "
                f"{sheet.title} ---"
            )

            for row in sheet.iter_rows(
                values_only=True
            ):

                values = []

                for value in row:

                    if value is None:

                        values.append("")

                    else:

                        values.append(
                            str(value)
                        )

                content.append(
                    " | ".join(values)
                )

    except Exception as error:

        print(
            "Excel extraction error:",
            error
        )

    return "\n".join(
        content
    )


# ============================================================
# TEXT / CSV
# ============================================================

def extract_plain_text(filepath):

    try:

        with open(
            filepath,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:

            return file.read()

    except Exception as error:

        print(
            "Text file error:",
            error
        )

        return ""


# ============================================================
# PROCESS ONE FILE
# ============================================================

def process_file(
    filepath,
    original_filename
):

    extension = get_extension(
        original_filename
    )

    result = {

        "filename":
            original_filename,

        "type":
            extension,

        "text":
            "",

        "images":
            []
    }


    # PDF

    if extension == "pdf":

        result["text"] = (
            extract_pdf_text(
                filepath
            )
        )

        result["images"] = (
            extract_pdf_images(
                filepath
            )
        )


    # IMAGE

    elif extension in {
        "jpg",
        "jpeg",
        "png",
        "webp"
    }:

        result["images"] = [

            {
                "page": 1,

                "data_url":
                    image_to_data_url(
                        filepath
                    )
            }

        ]


    # DOCX

    elif extension == "docx":

        result["text"] = (
            extract_docx_text(
                filepath
            )
        )


    # EXCEL

    elif extension in {
        "xlsx",
        "xls"
    }:

        result["text"] = (
            extract_excel_text(
                filepath
            )
        )


    # TXT / CSV

    elif extension in {
        "txt",
        "csv"
    }:

        result["text"] = (
            extract_plain_text(
                filepath
            )
        )


    return result


# ============================================================
# UPLOAD
# ============================================================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload():

    try:

        if "files" not in request.files:

            return jsonify({
                "success": False,
                "error":
                    "No files received."
            }), 400


        incoming_files = (
            request.files.getlist(
                "files"
            )
        )


        processed = []


        for uploaded in incoming_files:

            if not uploaded.filename:

                continue


            original_name = (
                uploaded.filename
            )


            if not allowed_file(
                original_name
            ):

                return jsonify({
                    "success": False,
                    "error":
                        "Unsupported file: "
                        + original_name
                }), 400


            safe_name = secure_filename(
                original_name
            )


            unique_name = (
                uuid.uuid4().hex
                + "_"
                + safe_name
            )


            filepath = os.path.join(
                UPLOAD_FOLDER,
                unique_name
            )


            uploaded.save(
                filepath
            )


            file_data = process_file(
                filepath,
                original_name
            )


            processed.append(
                file_data
            )


        return jsonify({
            "success": True,
            "files": processed
        })


    except Exception as error:

        print(
            "UPLOAD ERROR:",
            repr(error)
        )

        return jsonify({
            "success": False,
            "error":
                str(error)
        }), 500


# ============================================================
# MODE PROMPTS
# ============================================================

def get_mode_prompt(mode):

    if mode == "interview":

        return """
You are Butterfly AI in Interview Mode.

Act as a professional interviewer.

Ask relevant questions.
Evaluate answers.
Give constructive feedback.
Explain mistakes.
Ask follow-up questions.
Adjust difficulty according to the user's answers.

If the user uploads a resume or document,
use it as interview context.
"""


    if mode == "resume":

        return """
You are Butterfly AI in Resume Mode.

Act as an ATS-focused professional resume reviewer.

Review resumes carefully.
Improve professional summaries.
Improve bullet points.
Improve wording.
Suggest ATS-friendly improvements.
Identify weak sections.
Keep all claims truthful.

If a resume file is uploaded,
analyse its actual content.
"""


    return """
You are Butterfly AI in Normal Mode.

You are a highly capable general-purpose AI assistant.

You can help with:

- General questions
- Coding
- Mathematics
- Study
- Research
- Writing
- Documents
- PDFs
- Images
- Data
- Excel
- Analysis
- Summaries
- Explanations
- Creative tasks

When files are attached, carefully understand them
before answering.

Use uploaded files as the primary source when
the user's question is about those files.

Never invent information that is not supported
by the available material.

Give clear, useful and accurate answers.
"""


# ============================================================
# BUILD FILE CONTEXT
# ============================================================

def build_file_context(files):

    context = []

    for file in files:

        context.append(
            "\n\n========== "
            + file["filename"]
            + " ==========\n"
        )

        context.append(
            "TYPE: "
            + file["type"].upper()
            + "\n"
        )


        if file.get("text"):

            # Avoid gigantic requests.
            text = file["text"]

            if len(text) > 120000:

                text = text[
                    :120000
                ]

                text += (
                    "\n\n[Content truncated "
                    "for request size.]"
                )


            context.append(
                "\nDOCUMENT CONTENT:\n"
            )

            context.append(
                text
            )


    return "\n".join(
        context
    )


# ============================================================
# CREATE MULTIMODAL CONTENT
# ============================================================

def build_multimodal_content(
    message,
    files
):

    content = [

        {
            "type":
                "text",

            "text":
                message
        }

    ]


    file_context = (
        build_file_context(
            files
        )
    )


    if file_context:

        content.append({

            "type":
                "text",

            "text":
                "\n\nFILE CONTEXT:\n"
                + file_context
        })


    image_count = 0


    for file in files:

        for image in file.get(
            "images",
            []
        ):

            if image_count >= 12:

                break


            content.append({

                "type":
                    "image_url",

                "image_url": {

                    "url":
                        image[
                            "data_url"
                        ]
                }

            })


            image_count += 1


    return content


# ============================================================
# AI INTENT DETECTION
# ============================================================

def detect_intent(
    message,
    files
):

    classifier_prompt = """
You are the routing brain of Butterfly AI.

Classify the user's request into exactly ONE category:

chat
image
pdf
docx
xlsx

Rules:

image =
The user wants an image, poster, diagram, illustration,
photo, artwork, visual, infographic, generated picture,
or wants an uploaded image/document transformed into a visual.

pdf =
The user explicitly wants a PDF/document exported as PDF,
such as "make a PDF", "create PDF", "give me PDF".

docx =
The user explicitly wants a Word document.

xlsx =
The user explicitly wants an Excel/spreadsheet file.

chat =
Everything else, including reading/analyzing PDFs,
answering questions from documents, summaries, explanations,
coding, study, general conversation, etc.

Return ONLY JSON:

{
  "intent": "chat|image|pdf|docx|xlsx"
}
"""


    file_names = [
        file["filename"]
        for file in files
    ]


    user_content = (
        classifier_prompt
        + "\n\nUSER MESSAGE:\n"
        + message
        + "\n\nFILES:\n"
        + json.dumps(file_names)
    )


    try:

        response = client.chat.completions.create(

            model=CHAT_MODEL,

            messages=[

                {
                    "role":
                        "system",

                    "content":
                        "Return valid JSON only."
                },

                {
                    "role":
                        "user",

                    "content":
                        user_content
                }

            ],

            response_format={
                "type":
                    "json_object"
            },

            temperature=0
        )


        result = json.loads(
            response.choices[
                0
            ].message.content
        )


        intent = result.get(
            "intent",
            "chat"
        )


        if intent not in {
            "chat",
            "image",
            "pdf",
            "docx",
            "xlsx"
        }:

            return "chat"


        return intent


    except Exception as error:

        print(
            "Intent error:",
            error
        )

        return "chat"


# ============================================================
# GENERATE IMAGE PROMPT FROM USER REQUEST + FILE
# ============================================================

def create_image_prompt(
    message,
    files
):

    context = build_file_context(
        files
    )


    prompt = f"""
You are preparing a prompt for an advanced
AI image generation model.

Create ONE detailed visual prompt based on
the user's request.

User request:
{message}

Available file/document context:
{context}

If the user refers to information in a PDF,
document, image or spreadsheet, use that information.

If the request is a diagram, infographic,
poster, educational visual or flowchart,
make the prompt visually precise.

If the request is a normal creative image,
make it visually rich.

Do not discuss the prompt.
Return ONLY the final image-generation prompt.
"""


    try:

        response = client.chat.completions.create(

            model=CHAT_MODEL,

            messages=[

                {
                    "role":
                        "system",

                    "content":
                        "Create image prompts only."
                },

                {
                    "role":
                        "user",

                    "content":
                        prompt
                }

            ],

            temperature=0.7
        )


        return (
            response
            .choices[0]
            .message.content
            .strip()
        )


    except Exception as error:

        print(
            "Image prompt error:",
            error
        )

        return message


# ============================================================
# IMAGE GENERATION
# ============================================================

def generate_image(
    message,
    files
):

    image_prompt = (
        create_image_prompt(
            message,
            files
        )
    )


    response = client.images.generate(

        model=IMAGE_MODEL,

        prompt=image_prompt,

        size="1024x1024"
    )


    image_base64 = (
        response
        .data[0]
        .b64_json
    )


    image_bytes = (
        base64.b64decode(
            image_base64
        )
    )


    filename = (
        "butterfly_"
        + uuid.uuid4().hex
        + ".png"
    )


    filepath = os.path.join(
        GENERATED_FOLDER,
        filename
    )


    with open(
        filepath,
        "wb"
    ) as file:

        file.write(
            image_bytes
        )


    return url_for(
        "static",
        filename=
            "generated/"
            + filename
    )


# ============================================================
# GENERATE TEXT
# ============================================================

def generate_answer(
    message,
    mode,
    files
):

    system_prompt = (
        get_mode_prompt(
            mode
        )
    )


    content = (
        build_multimodal_content(
            message,
            files
        )
    )


    response = client.chat.completions.create(

        model=CHAT_MODEL,

        messages=[

            {
                "role":
                    "system",

                "content":
                    system_prompt
            },

            {
                "role":
                    "user",

                "content":
                    content
            }

        ],

        temperature=0.5
    )


    return (
        response
        .choices[0]
        .message.content
    )


# ============================================================
# GENERATE PDF
# ============================================================

def create_pdf(
    title,
    content
):

    filename = (
        "butterfly_"
        + uuid.uuid4().hex
        + ".pdf"
    )


    filepath = os.path.join(
        GENERATED_FOLDER,
        filename
    )


    styles = (
        getSampleStyleSheet()
    )


    normal_style = ParagraphStyle(

        "ButterflyNormal",

        parent=styles["BodyText"],

        fontSize=10,

        leading=15,

        alignment=TA_LEFT,

        spaceAfter=8
    )


    title_style = ParagraphStyle(

        "ButterflyTitle",

        parent=styles["Title"],

        fontSize=20,

        leading=25,

        spaceAfter=15
    )


    document = SimpleDocTemplate(

        filepath,

        pagesize=A4,

        rightMargin=40,

        leftMargin=40,

        topMargin=40,

        bottomMargin=40
    )


    story = []


    story.append(
        Paragraph(
            title,
            title_style
        )
    )


    for line in content.splitlines():

        line = line.strip()

        if not line:

            story.append(
                Spacer(
                    1,
                    8
                )
            )

            continue


        safe_line = (
            line
            .replace(
                "&",
                "&amp;"
            )
            .replace(
                "<",
                "&lt;"
            )
            .replace(
                ">",
                "&gt;"
            )
        )


        story.append(
            Paragraph(
                safe_line,
                normal_style
            )
        )


    document.build(
        story
    )


    return url_for(
        "static",
        filename=
            "generated/"
            + filename
    )


# ============================================================
# GENERATE DOCX
# ============================================================

def create_docx(
    title,
    content
):

    filename = (
        "butterfly_"
        + uuid.uuid4().hex
        + ".docx"
    )


    filepath = os.path.join(
        GENERATED_FOLDER,
        filename
    )


    document = Document()


    document.add_heading(
        title,
        level=1
    )


    for line in content.splitlines():

        if line.strip():

            document.add_paragraph(
                line
            )


    document.save(
        filepath
    )


    return url_for(
        "static",
        filename=
            "generated/"
            + filename
    )


# ============================================================
# GENERATE XLSX
# ============================================================

def create_xlsx(
    title,
    content
):

    filename = (
        "butterfly_"
        + uuid.uuid4().hex
        + ".xlsx"
    )


    filepath = os.path.join(
        GENERATED_FOLDER,
        filename
    )


    workbook = Workbook()

    sheet = workbook.active

    sheet.title = "Butterfly AI"


    sheet["A1"] = title


    row = 3


    for line in content.splitlines():

        if line.strip():

            sheet.cell(
                row=row,
                column=1,
                value=line
            )

            row += 1


    workbook.save(
        filepath
    )


    return url_for(
        "static",
        filename=
            "generated/"
            + filename
    )


# ============================================================
# CHAT ROUTE
# ============================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "error":
                    "Invalid request."
            }), 400


        message = (
            data.get(
                "message",
                ""
            )
            .strip()
        )


        mode = (
            data.get(
                "mode",
                "normal"
            )
            .lower()
        )


        files = data.get(
            "files",
            []
        )


        if not message and not files:

            return jsonify({
                "success": False,
                "error":
                    "Please enter a message or attach a file."
            }), 400


        if mode not in {
            "normal",
            "interview",
            "resume"
        }:

            mode = "normal"


        if not message:

            message = (
                "Analyse the uploaded file(s) "
                "and explain the important information."
            )


        # ====================================================
        # INTENT
        # ====================================================

        intent = detect_intent(
            message,
            files
        )


        print(
            "Butterfly intent:",
            intent
        )


        # ====================================================
        # IMAGE
        # ====================================================

        if intent == "image":

            image_url = generate_image(
                message,
                files
            )


            return jsonify({

                "success":
                    True,

                "type":
                    "image",

                "image_url":
                    image_url,

                "reply":
                    "🦋 Your image is ready."
            })


        # ====================================================
        # PDF
        # ====================================================

        if intent == "pdf":

            content = generate_answer(
                message,
                mode,
                files
            )


            pdf_url = create_pdf(
                "Butterfly AI",
                content
            )


            return jsonify({

                "success":
                    True,

                "type":
                    "file",

                "file_url":
                    pdf_url,

                "filename":
                    "Butterfly_AI.pdf",

                "reply":
                    content
            })


        # ====================================================
        # DOCX
        # ====================================================

        if intent == "docx":

            content = generate_answer(
                message,
                mode,
                files
            )


            docx_url = create_docx(
                "Butterfly AI",
                content
            )


            return jsonify({

                "success":
                    True,

                "type":
                    "file",

                "file_url":
                    docx_url,

                "filename":
                    "Butterfly_AI.docx",

                "reply":
                    content
            })


        # ====================================================
        # XLSX
        # ====================================================

        if intent == "xlsx":

            content = generate_answer(
                message,
                mode,
                files
            )


            xlsx_url = create_xlsx(
                "Butterfly AI",
                content
            )


            return jsonify({

                "success":
                    True,

                "type":
                    "file",

                "file_url":
                    xlsx_url,

                "filename":
                    "Butterfly_AI.xlsx",

                "reply":
                    content
            })


        # ====================================================
        # NORMAL CHAT
        # ====================================================

        answer = generate_answer(
            message,
            mode,
            files
        )


        return jsonify({

            "success":
                True,

            "type":
                "chat",

            "reply":
                answer
        })


    except Exception as error:

        print(
            "\nBUTTERFLY ERROR:"
        )

        print(
            repr(error)
        )


        return jsonify({

            "success":
                False,

            "error":
                "Butterfly AI could not process your request.",

            "details":
                str(error)
        }), 500


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/health"
)
def health():

    return jsonify({

        "status":
            "online",

        "service":
            "Butterfly AI",

        "chat_model":
            CHAT_MODEL,

        "image_model":
            IMAGE_MODEL
    })


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            8080
        )
    )


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False
    )