console.log("🦋 BUTTERFLY AI LOADED");


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
// FILES
// ============================================================

let selectedFiles = [];


// ============================================================
// PARTICLES
// ============================================================

if (particles) {

    for (let i = 0; i < 50; i++) {

        const dot =
            document.createElement("span");

        dot.classList.add("firefly");

        dot.style.left =
            Math.random() * 100 + "vw";

        dot.style.top =
            Math.random() * 100 + "vh";

        dot.style.animationDuration =
            (
                5 +
                Math.random() * 8
            ) + "s";

        particles.appendChild(dot);
    }
}


// ============================================================
// FILE PICKER
// ============================================================

fileInput.addEventListener(
    "change",
    function () {

        addFiles(
            Array.from(this.files)
        );

        this.value = "";

    }
);


// ============================================================
// IMAGE PICKER
// ============================================================

imageInput.addEventListener(
    "change",
    function () {

        addFiles(
            Array.from(this.files)
        );

        this.value = "";

    }
);


// ============================================================
// ADD FILES
// ============================================================

function addFiles(files) {

    files.forEach(
        file => {

            const exists =
                selectedFiles.some(
                    oldFile =>
                        oldFile.name ===
                        file.name &&
                        oldFile.size ===
                        file.size
                );


            if (!exists) {

                selectedFiles.push(
                    file
                );

            }

        }
    );


    showFiles();
}


// ============================================================
// SHOW FILES
// ============================================================

function showFiles() {

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

            row.style.justifyContent =
                "space-between";

            row.style.alignItems =
                "center";

            row.style.padding =
                "7px 10px";

            row.style.marginTop =
                "5px";

            row.style.borderRadius =
                "10px";

            row.style.background =
                "rgba(255,255,255,.08)";


            row.innerHTML =
                `
                <span>
                    ${fileIcon(file)}
                    ${escapeHtml(file.name)}
                </span>

                <button
                    type="button"
                    onclick="removeFile(${index})"
                    style="
                        min-width:auto;
                        padding:3px 8px;
                    "
                >
                    ✕
                </button>
                `;


            filePreview.appendChild(
                row
            );

        }
    );
}


// ============================================================
// FILE ICON
// ============================================================

function fileIcon(file) {

    const extension =
        file.name
            .split(".")
            .pop()
            .toLowerCase();


    if (extension === "pdf") {
        return "📄";
    }


    return "🖼️";
}


// ============================================================
// REMOVE
// ============================================================

function removeFile(index) {

    selectedFiles.splice(
        index,
        1
    );

    showFiles();
}


// ============================================================
// MODE
// ============================================================

function setMode(mode) {

    currentMode =
        mode;


    document.getElementById(
        "modeIndicator"
    ).innerHTML =
        "Current Mode: <b>" +
        mode.toUpperCase() +
        "</b>";


    console.log(
        "Mode:",
        currentMode
    );
}


// ============================================================
// ENTER
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

async function uploadFiles() {

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
            "Upload failed."
        );
    }


    return data.files;
}


// ============================================================
// SEND MESSAGE
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
    // USER
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


    selectedFiles.forEach(
        file => {

            user.innerText +=
                "\n📎 " +
                file.name;

        }
    );


    chatBox.appendChild(
        user
    );


    userInput.value =
        "";


    // ========================================================
    // BOT
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

        let files = [];


        if (
            selectedFiles.length > 0
        ) {

            bot.innerHTML =
                "📎 Reading your PDF/image...";


            files =
                await uploadFiles();
        }


        // ====================================================
        // CHAT
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
                            files

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
                "Butterfly AI failed."
            );
        }


        // ====================================================
        // GENERATED IMAGE
        // ====================================================

        if (
            data.type ===
            "image"
        ) {

            bot.innerHTML =
                `
                🦋 <b>Butterfly AI</b>

                <br><br>

                <img
                    src="${data.image_url}"
                    alt="Generated image"
                    style="
                        width:100%;
                        max-width:600px;
                        border-radius:18px;
                    "
                >

                <br><br>

                <a
                    href="${data.image_url}"
                    target="_blank"
                    style="color:white;"
                >
                    Open Image
                </a>
                `;

        }


        // ====================================================
        // NORMAL ANSWER
        // ====================================================

        else {

            bot.innerHTML =
                renderMarkdown(
                    data.reply
                );
        }


        // ====================================================
        // CLEAR
        // ====================================================

        selectedFiles = [];

        showFiles();


    } catch (error) {

        console.error(
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
// SIMPLE MARKDOWN
// ============================================================

function renderMarkdown(text) {

    let html =
        escapeHtml(
            text || ""
        );


    html =
        html.replace(
            /```([\s\S]*?)```/g,
            `
            <pre style="
                overflow-x:auto;
                padding:12px;
                border-radius:12px;
                background:rgba(0,0,0,.35);
            "><code>$1</code></pre>
            `
        );


    html =
        html.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );


    html =
        html.replace(
            /`([^`]+)`/g,
            "<code>$1</code>"
        );


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


    html =
        html.replace(
            /^[\-\*] (.*)$/gm,
            "• $1"
        );


    html =
        html.replace(
            /\n/g,
            "<br>"
        );


    return html;
}


// ============================================================
// ESCAPE
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