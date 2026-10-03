const API = "/chat";
const SESSION_KEY = "liwin_ai_session_id";

function createSessionId() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
        return window.crypto.randomUUID();
    }
    return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

let sessionId = localStorage.getItem(SESSION_KEY) || createSessionId();
localStorage.setItem(SESSION_KEY, sessionId);

const chatBox = document.getElementById("chatBox");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("message");
const sendBtn = document.getElementById("sendBtn");
const newChatBtn = document.getElementById("newChatBtn");

document.addEventListener("DOMContentLoaded", () => {
    newChatBtn?.addEventListener("click", newConversation);
    chatForm?.addEventListener("submit", (event) => {
        event.preventDefault();
        send();
    });
    messageInput?.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            send();
        }
    });
    messageInput?.addEventListener("input", resizeComposer);
    showWelcomeMessage();
    messageInput?.focus();
});

function getTime() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function escapeHTML(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function formatAIResponse(text) {
    return escapeHTML(text)
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/^\s*[-•]\s+(.+)$/gm, "• $1")
        .replace(/\n/g, "<br>");
}

function addMessage(type, author, content, allowFormatting = false) {
    const message = document.createElement("article");
    message.className = `message ${type}`;
    message.innerHTML = `
        <div class="message-meta"><strong>${author}</strong><time>${getTime()}</time></div>
        <div class="message-content">${allowFormatting ? formatAIResponse(content) : escapeHTML(content)}</div>
    `;
    chatBox.appendChild(message);
    scrollToBottom();
}

function showWelcomeMessage() {
    if (!chatBox) return;
    chatBox.innerHTML = `
        <section class="welcome" aria-label="Suggested questions">
            <h3>Chat with LIWIN.</h3>
            <p>I am Liwin AI. Know about my computer-vision work, RAG assistant, technical skills, education, or professional experience.</p>
            <div class="suggestion-list">
                <button class="suggestion" type="button" data-suggestion="Tell me about Smart Focus.">SMART FOCUS</button>
                <button class="suggestion" type="button" data-suggestion="What are your technical skills?">TECHNICAL SKILLS</button>
                <button class="suggestion" type="button" data-suggestion="What professional experience do you have?">EXPERIENCE</button>
                <button class="suggestion" type="button" data-suggestion="How was Liwin AI built?">LIWIN AI</button>
            </div>
        </section>`;
    chatBox.querySelectorAll("[data-suggestion]").forEach((button) => {
        button.addEventListener("click", () => {
            messageInput.value = button.dataset.suggestion;
            send();
        });
    });
}

function showThinking() {
    removeThinking();
    const message = document.createElement("article");
    message.className = "message ai";
    message.id = "thinking";
    message.innerHTML = `<div class="message-meta"><strong>LIWIN AI</strong></div><div class="thinking" aria-label="Liwin AI is thinking"><i></i><i></i><i></i></div>`;
    chatBox.appendChild(message);
    scrollToBottom();
}

function removeThinking() { document.getElementById("thinking")?.remove(); }

function showError(message) { addMessage("error-message", "LIWIN AI", message); }

function scrollToBottom() {
    requestAnimationFrame(() => { chatBox.scrollTop = chatBox.scrollHeight; });
}

function resizeComposer() {
    messageInput.style.height = "auto";
    messageInput.style.height = `${Math.min(messageInput.scrollHeight, 144)}px`;
}

function setInputState(disabled) {
    messageInput.disabled = disabled;
    sendBtn.disabled = disabled;
    chatBox?.setAttribute("aria-busy", String(disabled));
}

async function send() {
    const question = messageInput?.value.trim();
    if (!question || sendBtn.disabled) return;

    addMessage("user", "YOU", question);
    messageInput.value = "";
    resizeComposer();
    setInputState(true);
    showThinking();

    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 35000);
    try {
        const response = await fetch(API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, session_id: sessionId }),
            signal: controller.signal
        });
        if (!response.ok) {
            let detail = "Liwin AI could not complete that request.";
            try { detail = (await response.json()).detail || detail; } catch { /* Non-JSON response. */ }
            throw new Error(detail);
        }
        const data = await response.json();
        if (!data || typeof data.answer !== "string" || !data.answer.trim()) {
            throw new Error("Liwin AI returned an empty response.");
        }
        removeThinking();
        addMessage("ai", "LIWIN AI", data.answer, true);
    } catch (error) {
        removeThinking();
        showError(error.name === "AbortError" ? "The request took too long. Please try again." : error.message || "Unable to connect to Liwin AI. Please try again.");
    } finally {
        window.clearTimeout(timeoutId);
        setInputState(false);
        messageInput.focus();
    }
}

async function newConversation() {
    const previousSessionId = sessionId;
    sessionId = createSessionId();
    localStorage.setItem(SESSION_KEY, sessionId);
    showWelcomeMessage();
    messageInput.value = "";
    resizeComposer();
    setInputState(false);
    messageInput.focus();
    try {
        await fetch(`${API}/${encodeURIComponent(previousSessionId)}`, { method: "DELETE" });
    } catch {
        // The new local session is usable even if the old server memory has expired.
    }
}
