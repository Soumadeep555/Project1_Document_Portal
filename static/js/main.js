document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const chatBox = document.getElementById("chat-box");

    function addMessage(sender, text) {
        const div = document.createElement("div");
        div.className = `chat-message ${sender}`;
        div.textContent = text;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    if (chatForm) {
        chatForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const input = document.getElementById("chat-input");
            const message = input.value.trim();
            if (!message) return;

            addMessage("user", message);

            try {
                const response = await fetch("/chat/query", {
                    method: "POST",
                    body: new URLSearchParams({ question: message, use_session_dirs: true }),
                });
                const data = await response.json();
                addMessage("bot", data.answer || "No response.");
            } catch (err) {
                addMessage("bot", "⚠️ Error connecting to server.");
            }

            input.value = "";
        });
    }
});
