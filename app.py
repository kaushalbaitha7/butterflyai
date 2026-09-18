
from flask import Flask, render_template, request, jsonify, url_for
from openai import OpenAI
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from pypdf import PdfReader

import os
import base64
import uuid
import json
import fitz


# ============================================================
# SETUP
# ============================================================

load_dotenv()

app = Flask(__name__)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

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

UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    GENERATED_FOLDER,
    exist_ok=True
)

app.config["MAX_CONTENT_LENGTH"] = (
    25 * 1024 * 1024
)


# ============================================================
# ONLY PDF + IMAGE FILES
# ============================================================

ALLOWED_EXTENSIONS = {
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "webp"
}


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


# ============================================================
# IMAGE TO DATA URL
# ============================================================

def image_to_data_url(filepath):

    extension = get_extension(
        filepath
    )

    mime = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp"
    }.get(
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
        f"data:{mime};base64,{encoded}"
    )


# ============================================================
# PDF TEXT
# ============================================================

def extract_pdf_text(filepath):

    text = []

    try:

        reader = PdfReader(
            filepath
        )

        for page_number, page in enumerate(
            reader.pages
        ):

            page_text = (
                page.extract_text()
                or ""
            )

            if page_text.strip():

                text.append(
                    f"\n--- PAGE "
                    f"{page_number + 1} ---\n"
                    f"{page_text}"
                )

    except Exception as error:

        print(
            "PDF TEXT ERROR:",
            error
        )

    return "\n".join(text)


# ============================================================
# PDF PAGES -> IMAGES
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

        pages = min(
            len(pdf),
            max_pages
        )

        for page_number in range(
            pages
        ):

            page = pdf.load_page(
                page_number
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

                "page":
                    page_number + 1,

                "data_url":
                    "data:image/png;base64,"
                    + encoded

            })

        pdf.close()

    except Exception as error:

        print(
            "PDF IMAGE ERROR:",
            error
        )

    return images


# ============================================================
# PROCESS UPLOADED FILE
# ============================================================

def process_file(
    filepath,
    filename
):

    extension = get_extension(
        filename
    )

    result = {

        "filename":
            filename,

        "type":
            extension,

        "text":
            "",

        "images":
            []

    }

    # -------------------------
    # PDF
    # -------------------------

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

    # -------------------------
    # IMAGE
    # -------------------------

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

                "success":
                    False,

                "error":
                    "No file selected."

            }), 400

        files = request.files.getlist(
            "files"
        )

        processed = []

        for file in files:

            if not file.filename:
                continue

            filename = file.filename

            if not allowed_file(
                filename
            ):

                return jsonify({

                    "success":
                        False,

                    "error":
                        "Only PDF and image files are supported."

                }), 400

            safe_name = secure_filename(
                filename
            )

            if not safe_name:
                safe_name = "uploaded_file"

            unique_name = (
                uuid.uuid4().hex
                + "_"
                + safe_name
            )

            filepath = os.path.join(
                UPLOAD_FOLDER,
                unique_name
            )

            file.save(
                filepath
            )

            processed.append(
                process_file(
                    filepath,
                    filename
                )
            )

        return jsonify({

            "success":
                True,

            "files":
                processed

        })

    except Exception as error:

        print(
            "UPLOAD ERROR:",
            error
        )

        return jsonify({

            "success":
                False,

            "error":
                str(error)

        }), 500


# ============================================================
# MODES
# ============================================================

def get_mode_prompt(mode):

    # -------------------------
    # INTERVIEW MODE
    # -------------------------

    if mode == "interview":

        return """

You are Butterfly AI in Interview Mode.

Act as a professional interviewer.

Ask relevant questions.

Evaluate the user's answers.

Give constructive feedback.

Ask follow-up questions.

Adjust difficulty according to the
user's level.

If a PDF or image is uploaded,
use its actual content as interview
context.

Do not invent information from
the uploaded material.

"""

    # -------------------------
    # RESUME MODE
    # -------------------------

    if mode == "resume":

        return """

You are Butterfly AI in Resume Mode.

You are an ATS-focused resume reviewer.

Analyse the uploaded resume carefully.

Improve:

- Professional summary
- Skills
- Experience
- Projects
- Bullet points
- ATS keywords
- Formatting suggestions

Never invent experience,
qualifications, projects, skills,
or achievements.

"""

    # -------------------------
    # NORMAL MODE
    # -------------------------

    return """

You are Butterfly AI in Normal Mode.

You are a highly capable
general-purpose AI assistant.

You can answer questions,
explain concepts, help with coding,
mathematics, study, research,
writing, creative work and
general conversation.

You can understand uploaded PDFs
and images.

When a PDF or image is attached,
carefully analyse its actual content.

Answer questions from the uploaded
material without inventing information.

If the user asks to create an image,
poster, diagram, illustration,
infographic, visual or other artwork,
use the image-generation system.

"""


# ============================================================
# FILE TEXT CONTEXT
# ============================================================

def build_file_context(files):

    context = []

    for file in files:

        filename = file.get(
            "filename",
            "Uploaded file"
        )

        context.append(
            "\n========== "
            + filename
            + " ==========\n"
        )

        text = file.get(
            "text",
            ""
        )

        if text:

            if len(text) > 120000:

                text = (
                    text[:120000]
                    + "\n[PDF text truncated]"
                )

            context.append(
                text
            )

    return "\n".join(
        context
    )


# ============================================================
# MULTIMODAL CONTENT
# ============================================================

def build_content(
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
                "\n\nUPLOADED FILE CONTENT:\n"
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
# AI ROUTER
# ============================================================

def detect_intent(
    message,
    files
):

    prompt = """

You are Butterfly AI's request router.

Choose exactly ONE:

chat
image

Choose IMAGE when the user wants:

- an image
- a poster
- a diagram
- an illustration
- a photo
- an infographic
- artwork
- a generated visual
- an image based on an uploaded PDF
- an image based on an uploaded image

Choose CHAT for everything else.

Return ONLY JSON:

{"intent": "chat"}

or

{"intent": "image"}

"""

    filenames = [

        file.get(
            "filename",
            ""
        )

        for file in files

    ]

    user_content = (

        prompt

        + "\n\nUSER:\n"

        + message

        + "\n\nFILES:\n"

        + json.dumps(
            filenames
        )

    )

    try:

        response = (
            client.chat.completions.create(

                model=CHAT_MODEL,

                messages=[

                    {
                        "role":
                            "system",

                        "content":
                            "Return JSON only."
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
        )

        result = json.loads(

            response
            .choices[0]
            .message.content

        )

        if (
            result.get("intent")
            == "image"
        ):

            return "image"

        return "chat"

    except Exception as error:

        print(
            "ROUTER ERROR:",
            error
        )

        return "chat"


# ============================================================
# IMAGE PROMPT
# ============================================================

def create_image_prompt(
    message,
    files
):

    context = (
        build_file_context(
            files
        )
    )

    prompt = f"""

Create a detailed prompt for an
AI image-generation model.

USER REQUEST:

{message}

UPLOADED PDF TEXT CONTEXT:

{context}

The uploaded PDF/image may also
contain visual information.

Create the image prompt so the
generated image follows the user's
request and uses relevant information
from the uploaded material.

If the user wants a poster,
make it professional and visually clear.

If the user wants an educational
diagram, make it accurate,
structured and easy to understand.

If the user wants a creative image,
make it visually rich.

Do not add unrelated information.

Return ONLY the final image prompt.

"""

    try:

        response = (
            client.chat.completions.create(

                model=CHAT_MODEL,

                messages=[

                    {
                        "role":
                            "system",

                        "content":
                            "Generate image prompts only."
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
        )

        return (
            response
            .choices[0]
            .message.content
            .strip()
        )

    except Exception as error:

        print(
            "IMAGE PROMPT ERROR:",
            error
        )

        return message


# ============================================================
# GENERATE IMAGE
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

    if (
        not response.data
        or not response.data[0].b64_json
    ):

        raise RuntimeError(
            "Image generation returned no image."
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
# CHAT ANSWER
# ============================================================

def generate_answer(
    message,
    mode,
    files
):

    response = (
        client.chat.completions.create(

            model=CHAT_MODEL,

            messages=[

                {
                    "role":
                        "system",

                    "content":
                        get_mode_prompt(
                            mode
                        )
                },

                {
                    "role":
                        "user",

                    "content":
                        build_content(
                            message,
                            files
                        )
                }

            ],

            temperature=0.5
        )
    )

    return (
        response
        .choices[0]
        .message.content
        .strip()
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

                "success":
                    False,

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

        if mode not in {

            "normal",
            "interview",
            "resume"

        }:

            mode = "normal"

        if not message:

            message = (

                "Analyse the uploaded PDF "
                "or image and explain the "
                "important information."

            )

        intent = detect_intent(

            message,
            files

        )

        print(
            "Butterfly Intent:",
            intent
        )

        # ================================================
        # IMAGE GENERATION
        # ================================================

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

        # ================================================
        # CHAT / PDF / IMAGE ANALYSIS
        # ================================================

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
            "BUTTERFLY ERROR:",
            repr(error)
        )

        return jsonify({

            "success":
                False,

            "error":
                "Butterfly AI could not process the request.",

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
# START
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
