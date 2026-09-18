console.log("🦋 BUTTERFLY AI V2 LOADED");


// ============================================================
// MODE
// ============================================================

let currentMode = "normal";


// ============================================================
// ELEMENTS
// ============================================================

const particles =
    document.getElementById("particles");

const chatBox =
    document.getElementById("chatBox");

const userInput =
    document.getElementById("userInput");

const fileInput =
    document.getElementById("fileInput");

const imageInput =
    document.getElementById("imageInput");

const filePreview =
    document.getElementById("filePreview");


// ============================================================
// SELECTED FILES
// ============================================================

let selectedFiles = [];


// ============================================================
// PARTICLES
// ============================================================

if (particles) {

    for (
        let i = 0;
        i < 50;
        i++
    ) {

        const dot =
            document.createElement("span");

        dot.classList.add(
            "firefly"
        );

        dot.style.left =
            Math.random() * 100 +
            "vw";

        dot.style.top =
            Math.random() * 100 +
            "vh";

        dot.style.animationDuration =
            (
                5 +
                Math.random() * 8
            ) +
            "s";

        particles.appendChild(
            dot
        );
    }
}


// ============================================================
// FILE PICKER
// ============================================================

if (fileInput) {

    fileInput.addEventListener(
        "change",
        function () {

            addFiles(
                Array.from(
                    this.files
                )
            );

            this.value = "";

        }
    );
}


// ============================================================
// IMAGE PICKER
// ============================================================

if (imageInput) {

    imageInput.addEventListener(
        "change",
        function () {

            addFiles(
                Array.from(
                    this.files
                )
            );

            this.value = "";

        }
    );
}


// ============================================================
// ADD FILES
// ============================================================

function addFiles(files) {

    files.forEach(
        file => {

            const exists =
                selectedFiles.some(
                    existing =>
                        existing.name ===
                        file.name &&
                        existing.size ===
                        file.size
                );


            if (!exists) {

                selectedFiles.push(
                    file
                );

            }

        }
    );


    renderFilePreview();
}


// ============================================================
// REMOVE FILE
// ============================================================

function removeFile(index) {

    selectedFiles.splice(
        index,
        1
    );

    renderFilePreview();
}


// ============================================================
// FILE PREVIEW
// ============================================================

function renderFilePreview() {

    if (!filePreview) {
        return;
    }


    if (
        selectedFiles.length === 0
    ) {

        filePreview.style.display =
            "none";

        filePreview.innerHTML =
            "";

        return;
    }


    filePreview.style.display =
        "block";


    filePreview.innerHTML =
        "";


    selectedFiles.forEach(
        (file, index) => {

            const row =
                document.createElement(
                    "div"
                );


            row.style.display =
                "flex";

            row.style.alignItems =
                "center";

            row.style.justifyContent =
                "space-between";

            row.style.padding =
                "7px 10px";

            row.style.marginTop =
                "5px";

            row.style.borderRadius =
                "10px";

            row.style.background =
                "rgba(255,255,255,.08)";


            const label =
                document.createElement(
                    "span"
                );


            label.innerText =
                getFileIcon(file) +
                " " +
                file.name;


            const remove =
                document.createElement(
                    "button"
                );


            remove.type =
                "button";

            remove.innerText =
                "✕";

            remove.style.minWidth =
                "auto";

            remove.style.padding =
                "3px 8px";

            remove.style.cursor =
                "pointer";


            remove.onclick =
                () => removeFile(index);


            row.appendChild(
                label
            );

            row.appendChild(
                remove
            );

            filePreview.appendChild(
                row
            );

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


    if (
        extension === "jpg" ||
        extension === "jpeg" ||
        extension === "png" ||
        extension === "webp"
    ) {

        return "🖼️";
    }


    if (
        extension === "pdf"
    ) {

        return "📄";
    }


    if (
        extension === "docx"
    ) {

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

    currentMode =
        mode;


    const indicator =
        document.getElementById(
            "modeIndicator"
        );


    if (indicator) {

        indicator.innerHTML =
            "Current Mode: <b>" +
            mode.toUpperCase() +
            "</b>";

    }


    console.log(
        "Butterfly Mode:",
        currentMode
    );
}


// ============================================================
// ENTER KEY
// ============================================================

function handleKey(event) {

    if (
        event.key === "Enter"
    ) {

        event.preventDefault();

        sendMessage();
    }
}


// ============================================================
// UPLOAD
// ============================================================

async function uploadSelectedFiles() {

    if (
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


    const data =
        await response.json();


    if (
        !response.ok ||
        !data.success
    ) {

        throw new Error(
            data.error ||
            "File upload failed."
        );
    }


    return data.files || [];
}


// ============================================================
// SEND
// ============================================================

async function sendMessage() {

    const text =
        userInput.value.trim();


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
        document.createElement(
            "div"
        );


    user.className =
        "user-message";


    user.innerText =
        text ||
        "Please analyse my uploaded file.";


    if (
        selectedFiles.length > 0
    ) {

        selectedFiles.forEach(
            file => {

                user.innerText +=
                    "\n📎 " +
                    file.name;

            }
        );
    }


    chatBox.appendChild(
        user
    );


    userInput.value =
        "";


    // ========================================================
    // BOT MESSAGE
    // ========================================================

    const bot =
        document.createElement(
            "div"
        );


    bot.className =
        "bot-message";


    bot.innerHTML =
        "🦋 Butterfly AI is thinking...";


    chatBox.appendChild(
        bot
    );


    chatBox.scrollTop =
        chatBox.scrollHeight;


    try {

        // ====================================================
        // UPLOAD
        // ====================================================

        let uploadedFiles = [];


        if (
            selectedFiles.length > 0
        ) {

            bot.innerHTML =
                "📎 Reading your file...";


            uploadedFiles =
                await uploadSelectedFiles();
        }


        // ====================================================
        // REQUEST
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
                            text,

                        mode:
                            currentMode,

                        files:
                            uploadedFiles

                    })
                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Butterfly AI request failed."
            );
        }


        // ====================================================
        // IMAGE
        // ====================================================

        if (
            data.type ===
            "image"
        ) {

            bot.innerHTML =
                `
                <div>
                    🦋 <b>Butterfly AI</b>
                </div>

                <br>

                <img
                    src="${data.image_url}"
                    alt="Generated image"
                    style="
                        max-width:100%;
                        display:block;
                        border-radius:18px;
                        margin-top:8px;
                    "
                >

                <br>

                <a
                    href="${data.image_url}"
                    target="_blank"
                    style="
                        color:white;
                    "
                >
                    Open generated image
                </a>
                `;

        }


        // ====================================================
        // GENERATED FILE
        // ====================================================

        else if (
            data.type ===
            "file"
        ) {

            bot.innerHTML =
                `
                ${renderMarkdown(
                    data.reply || ""
                )}

                <br><br>

                📁 <b>File generated:</b>

                <br>

                <a
                    href="${data.file_url}"
                    target="_blank"
                    download
                    style="
                        color:white;
                        font-weight:bold;
                    "
                >
                    ⬇️ Download
                    ${escapeHtml(
                        data.filename ||
                        "Butterfly_File"
                    )}
                </a>
                `;

        }


        // ====================================================
        // NORMAL CHAT
        // ====================================================

        else {

            bot.innerHTML =
                renderMarkdown(
                    data.reply || ""
                );

        }


        // ====================================================
        // CLEAR
        // ====================================================

        selectedFiles = [];

        renderFilePreview();


    } catch (error) {

        console.error(
            "Butterfly error:",
            error
        );


        bot.innerHTML =
            `
            ⚠️ <b>Butterfly AI Error</b>
            <br><br>
            ${escapeHtml(
                error.message
            )}
            `;

    }


    chatBox.scrollTop =
        chatBox.scrollHeight;
}


// ============================================================
// MARKDOWN
// ============================================================

function renderMarkdown(text) {

    let html =
        escapeHtml(text);


    // Code blocks

    html =
        html.replace(
            /```([\s\S]*?)```/g,
            function (
                match,
                code
            ) {

                return `
                <pre style="
                    overflow-x:auto;
                    padding:12px;
                    border-radius:12px;
                    background:rgba(0,0,0,.35);
                "><code>${code.trim()}</code></pre>
                `;

            }
        );


    // Bold

    html =
        html.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );


    // Inline code

    html =
        html.replace(
            /`([^`]+)`/g,
            "<code>$1</code>"
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


    // Bullets

    html =
        html.replace(
            /^[\-\*] (.*)$/gm,
            "• $1"
        );


    // Newlines

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
        document.createElement(
            "div"
        );


    div.textContent =
        text;


    return div.innerHTML;
}