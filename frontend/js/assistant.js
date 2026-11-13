document.addEventListener("DOMContentLoaded", async () => {
    Auth.requireAuth();
    document.getElementById("logoutBtn")?.addEventListener("click", Auth.logout);
    const user = API.getUser() || await Auth.refreshUser();
    if (user) renderProfileChip(user);
    await loadHistory();
    const input = document.getElementById("chatInput");
    const sendBtn = document.getElementById("chatSend");
    const send = async () => {
        const msg = input.value.trim();
        if (!msg) return;
        appendMsg("user", msg);
        input.value = "";
        sendBtn.disabled = true;
        const loading = appendMsg("bot", "…");
        try {
            const res = await API.post("/api/assistant/chat", { message: msg });
            loading.querySelector(".msg-text").textContent = res.reply;
            if (res.source === "rule_based") {
                const tag = document.createElement("span");
                tag.style.cssText = "font-size:10px;color:var(--gray-500);margin-left:6px";
                tag.textContent = "(rule-based)";
                loading.appendChild(tag);
            }
        } catch (e) { loading.querySelector(".msg-text").textContent = "Error: " + e.message; }
        finally { sendBtn.disabled = false; scrollChat(); }
    };
    sendBtn.addEventListener("click", send);
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") send(); });
});
function appendMsg(role, text) {
    const host = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = "msg " + (role === "user" ? "user" : "bot");
    const span = document.createElement("span");
    span.className = "msg-text"; span.textContent = text;
    div.appendChild(span);
    host.appendChild(div);
    scrollChat();
    return div;
}
function scrollChat() {
    const h = document.getElementById("chatMessages");
    if (h) h.scrollTop = h.scrollHeight;
}
async function loadHistory() {
    try {
        const msgs = await API.get("/api/assistant/history");
        msgs.forEach(m => appendMsg(m.role === "user" ? "user" : "bot", m.message));
    } catch (e) {}
}
