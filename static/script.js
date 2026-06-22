console.log("SCRIPT LOADED");
let currentMode = "normal";
const particles = document.getElementById("particles");
for(let i = 0; i < 50; i++){
    let dot = document.createElement("span");
    dot.classList.add("firefly");
    dot.style.left =Math.random() * 100 + "vw";
    dot.style.top =Math.random() * 100 + "vh";
    dot.style.animationDuration =(5 + Math.random() * 8) + "s";
    particles.appendChild(dot);
}
async function sendMessage(){
    const input =document.getElementById("userInput");
    const text =input.value.trim();
    if(!text) return;
    const chatBox =document.getElementById("chatBox");
    const user =document.createElement("div");
    user.className ="user-message";
    user.innerText =text;
    chatBox.appendChild(user);
    input.value = "";
    const bot =document.createElement("div");
    bot.className ="bot-message";
    bot.innerHTML ="🦋 Butterfly AI is thinking...";
    chatBox.appendChild(bot);
    chatBox.scrollTop =chatBox.scrollHeight;
    try{
        const response =
        await fetch("/chat",{
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
              message:text,
              mode:currentMode
})
        });
        if(!response.ok){
            throw new Error(
                "Server Error"
            );
        }
        const data =await response.json();
        bot.innerHTML =data.reply.replace(/\n/g,"<br>");
    }
    catch(error){
        console.error(error);
        bot.innerHTML ="⚠️ Unable to connect to Butterfly AI";
    }
    chatBox.scrollTop =
    chatBox.scrollHeight;
}
function handleKey(event){
    if(event.key === "Enter"){
        sendMessage();
    }
}
function setMode(mode){
    currentMode = mode;
    document.getElementById("modeIndicator")
    .innerHTML =
    "Current Mode: <b>" +
    mode.toUpperCase() +
    "</b>";
    console.log("Selected Mode:", currentMode);
}