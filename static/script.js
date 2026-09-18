console.log("BUTTERFLY AI SCRIPT LOADED");


// ============================================================
// CURRENT MODE
// ============================================================

let currentMode = "normal";


// ============================================================
// SELECT ELEMENTS
// ============================================================

const particles =
    document.getElementById("particles");

const fileInput =
    document.getElementById("fileInput");

const imageInput =
    document.getElementById("imageInput");

const filePreview =
    document.getElementById("filePreview");

const userInput =
    document.getElementById("userInput");

const chatBox =
    document.getElementById("chatBox");


// ============================================================
// SELECTED FILES
// ============================================================

let selectedFiles = [];


// ============================================================
// FIRELY PARTICLES
// ============================================================

if (particles) {

    for (let i = 0; i < 50; i++) {

        let dot =
            document.createElement("span");

        dot.classList.add("firefly");

        dot.style.left =
            Math.random() * 100 + "vw";

        dot.style.top =
            Math.random() * 100 + "vh";

        dot.style.animationDuration =
            (5 + Math.random() * 8) + "s";

        particles.appendChild(dot);
    }
}


// ============================================================
// FILE INPUT
// ============================================================

if (fileInput) {

    fileInput.addEventListener(
        "change",
        function () {

            addSelectedFiles(
                Array.from(this.files)
            );

            this.value = "";

        }
    );
}


// ============================================================
// IMAGE INPUT
// ============================================================

if (imageInput) {

    imageInput.addEventListener(
        "change",
        function () {

            addSelectedFiles(
                Array.from(this.files)
            );

            this.value = "";

        }
    );
}


// ============================================================
// ADD FILES
// ============================================================

function addSelectedFiles(files) {

    if (!files || files.length === 0) {
        return;
    }


    files.forEach(file => {

        const alreadyExists =
            selectedFiles.some(
                existingFile =>
                    existingFile.name === file.name &&
                    existingFile.size === file.size
            );


        if (!alreadyExists) {

            selectedFiles.push(file);

        }

    });


    updateFilePreview();
}


// ============================================================
// REMOVE FILE
// ============================================================

function removeSelectedFile(index) {

    selectedFiles.splice(
        index,
        1
    );

    updateFilePreview();
}


// ============================================================
// FILE PREVIEW
// ============================================================

function updateFilePreview() {

    if (!filePreview) {
        return;
    }


    if (selectedFiles.length === 0) {

        filePreview.style.display =
            "none";

        filePreview.innerHTML = "";

        return;
    }


    filePreview.style.display =
        "block";


    filePreview.innerHTML = "";


    selectedFiles.forEach(
        (file, index) => {

            const item =
                document.createElement("div");


            item.style.display =
                "flex";

            item.style.alignItems =
                "center";

            item.style.justifyContent =
                "space-between";

            item.style.marginTop =
                "6px";

            item.style.padding =
                "7px 10px";

            item.style.borderRadius =
                "10px";

            item.style.background =
                "rgba(255,255,255,.08)";


            const name =
                document.createElement("span");

            name.innerText =
                getFileIcon(file) +
                " " +
                file.name;


            const remove =
                document.createElement("button");

            remove.type =
                "button";

            remove.innerText =
                "✕";

            remove.style.marginLeft =
                "10px";

            remove.style.padding =
                "3px 8px";

            remove.style.minWidth =
                "auto";

            remove.style.cursor =
                "pointer";


            remove.onclick =
                function () {

                    removeSelectedFile(index);

                };


            item.appendChild(name);

            item.appendChild(remove);

            filePreview.appendChild(item);

        }
    );
}


// ============================================================
// FILE ICON
// ============================================================

function getFileIcon(file) {

    const extension =
        file.name
            .split(".")
            .pop()
            .toLowerCase();


    if (extension === "pdf") {
        return "📄";
    }

    if (
        extension === "png" ||
        extension === "jpg" ||
        extension === "jpeg" ||
        extension === "webp"
    ) {
        return "🖼️";
    }

    if (extension === "docx") {
        return "📝";
    }

    if (
        extension === "xlsx" ||
        extension === "xls" ||
        extension === "csv"
    ) {
        return "📊";
    }

    return "📎";
}


// ============================================================
// SET MODE
// ============================================================

function setMode(mode) {

    currentMode = mode;


    const modeIndicator =
        document.getElementById(
            "modeIndicator"
        );


    if (modeIndicator) {

        modeIndicator.innerHTML =
            "Current Mode: <b>" +
            mode.toUpperCase() +
            "</b>";

    }


    console.log(
        "Selected Mode:",
        currentMode
    );
}


// ============================================================
// HANDLE ENTER
// ============================================================

function handleKey(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();

    }
}


// ============================================================
// UPLOAD FILES
// ============================================================

async function uploadFiles() {

    if (
        !selectedFiles ||
        selectedFiles.length === 0
    ) {

        return [];

    }


    const formData =
        new FormData();


    selectedFiles.forEach(
        file => {

            formData.append(
                "files",
                file
            );

        }
    );


    const response =
        await fetch(
            "/upload",
            {
                method: "POST",
                body: formData
            }
        );


    if (!response.ok) {

        let errorMessage =
            "File upload failed.";

        try {

            const errorData =
                await response.json();

            if (errorData.error) {
                errorMessage =
                    errorData.error;
            }

        } catch (error) {

            console.error(error);

        }

        throw new Error(
            errorMessage
        );

    }


    const data =
        await response.json();


    if (!data.success) {

        throw new Error(
            data.error ||
            "File upload failed."
        );

    }


    return data.files || [];
}


// ============================================================
// SEND MESSAGE
// ============================================================

async function sendMessage() {

    const text =
        userInput.value.trim();


    // Don't send if nothing exists
    if (
        !text &&
        selectedFiles.length === 0
    ) {

        return;

    }


    // ========================================================
    // USER MESSAGE
    // ========================================================

    const user =
        document.createElement("div");

    user.className =
        "user-message";


    // Show user text
    if (text) {

        user.innerText =
            text;

    } else {

        user.innerText =
            "Please analyse the attached file(s).";

    }


    // Show attachment names
    if (
        selectedFiles.length > 0
    ) {

        const filesText =
            selectedFiles
                .map(
                    file =>
                        "\n📎 " +
                        file.name
                )
                .join("");


        user.innerText +=
            filesText;

    }


    chatBox.appendChild(user);


    // Clear input
    userInput.value = "";


    // ========================================================
    // BOT THINKING MESSAGE
    // ========================================================

    const bot =
        document.createElement("div");

    bot.className =
        "bot-message";

    bot.innerHTML =
        "🦋 Butterfly AI is thinking...";


    chatBox.appendChild(bot);


    chatBox.scrollTop =
        chatBox.scrollHeight;


    try {

        // ====================================================
        // UPLOAD FILES FIRST
        // ====================================================

        let uploadedFiles = [];


        if (
            selectedFiles.length > 0
        ) {

            bot.innerHTML =
                "📎 Uploading and analysing your file...";


            uploadedFiles =
                await uploadFiles();

        }


        // ====================================================
        // CHECK IMAGE GENERATION
        // ====================================================

        const shouldGenerateImage =
            detectImageGenerationRequest(
                text
            );


        if (
            shouldGenerateImage &&
            uploadedFiles.length === 0
        ) {

            bot.innerHTML =
                "🎨 Butterfly AI is creating your image...";


            const imageResponse =
                await fetch(
                    "/generate-image",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            prompt: text
                        })
                    }
                );


            const imageData =
                await imageResponse.json();


            if (
                !imageResponse.ok ||
                !imageData.success
            ) {

                throw new Error(
                    imageData.error ||
                    "Image generation failed."
                );

            }


            bot.innerHTML =
                `
                <div>
                    🦋 <b>Butterfly AI</b>
                </div>

                <br>

                <img
                    src="${imageData.image_url}"
                    alt="Generated by Butterfly AI"
                    style="
                        max-width:100%;
                        border-radius:16px;
                        display:block;
                        margin-top:8px;
                    "
                >
                `;


            clearSelectedFiles();

            chatBox.scrollTop =
                chatBox.scrollHeight;

            return;

        }


        // ====================================================
        // NORMAL CHAT / FILE CHAT
        // ====================================================

        bot.innerHTML =
            "🦋 Butterfly AI is thinking...";


        const response =
            await fetch(
                "/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        message:
                            text ||
                            "Analyse the uploaded file(s) and explain the important information.",

                        mode:
                            currentMode,

                        files:
                            uploadedFiles

                    })
                }
            );


        if (!response.ok) {

            let errorMessage =
                "Server Error";

            try {

                const errorData =
                    await response.json();

                if (errorData.error) {

                    errorMessage =
                        errorData.error;

                }

            } catch (error) {

                console.error(error);

            }

            throw new Error(
                errorMessage
            );

        }


        const data =
            await response.json();


        if (data.error) {

            throw new Error(
                data.error
            );

        }


        // ====================================================
        // RENDER RESPONSE
        // ====================================================

        bot.innerHTML =
            renderMarkdown(
                data.reply || ""
            );


        clearSelectedFiles();


    } catch (error) {

        console.error(
            "Butterfly AI Error:",
            error
        );


        bot.innerHTML =
            `
            ⚠️ <b>Unable to process your request.</b>
            <br><br>
            ${escapeHtml(
                error.message ||
                "Something went wrong."
            )}
            `;

    }


    chatBox.scrollTop =
        chatBox.scrollHeight;
}


// ============================================================
// CLEAR SELECTED FILES
// ============================================================

function clearSelectedFiles() {

    selectedFiles = [];

    updateFilePreview();
}


// ============================================================
// IMAGE GENERATION DETECTOR
// ============================================================

function detectImageGenerationRequest(text) {

    if (!text) {
        return false;
    }


    const message =
        text.toLowerCase();


    const keywords = [

        "generate an image",
        "generate image",
        "create an image",
        "create image",
        "make an image",
        "make image",
        "draw an image",
        "draw image",
        "generate a picture",
        "create a picture",
        "make a picture",
        "generate photo",
        "create photo"

    ];


    return keywords.some(
        keyword =>
            message.includes(keyword)
    );
}


// ============================================================
// BASIC MARKDOWN RENDERER
// ============================================================

function renderMarkdown(text) {

    let html =
        escapeHtml(text);


    // Code blocks
    html =
        html.replace(
            /```([\s\S]*?)```/g,
            function(match, code) {

                return `
                    <pre style="
                        overflow-x:auto;
                        padding:12px;
                        border-radius:12px;
                        background:rgba(0,0,0,.35);
                        margin:10px 0;
                    "><code>${code.trim()}</code></pre>
                `;

            }
        );


    // Inline code
    html =
        html.replace(
            /`([^`]+)`/g,
            "<code>$1</code>"
        );


    // Bold
    html =
        html.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );


    // Italic
    html =
        html.replace(
            /\*(.*?)\*/g,
            "<em>$1</em>"
        );


    // Headings
    html =
        html.replace(
            /^### (.*)$/gm,
            "<h4>$1</h4>"
        );


    html =
        html.replace(
            /^## (.*)$/gm,
            "<h3>$1</h3>"
        );


    html =
        html.replace(
            /^# (.*)$/gm,
            "<h2>$1</h2>"
        );


    // Bullet lists
    html =
        html.replace(
            /^[\-\*] (.*)$/gm,
            "• $1"
        );


    // Numbered lists
    html =
        html.replace(
            /^\d+\. (.*)$/gm,
            "<div>$&</div>"
        );


    // New lines
    html =
        html.replace(
            /\n/g,
            "<br>"
        );


    return html;
}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHtml(text) {

    const div =
        document.createElement("div");

    div.textContent =
        text;

    return div.innerHTML;
}