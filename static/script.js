// ─── Speak Button ────────────────────────────────────────────────
document.getElementById("speak-btn").addEventListener("click", () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        showError("Speech recognition is not supported in this browser. Please use Chrome.");
        return;
    }

    const recognition = new SpeechRecognition();
    const selectedLang = document.getElementById("language").value;
    const speakBtn = document.getElementById("speak-btn");

    recognition.lang = selectedLang;
    recognition.interimResults = false;

    recognition.onstart = () => {
        speakBtn.classList.add("listening");
        setRecognizedText("🎤 Listening...", true);
    };

    recognition.onspeechend = () => {
        recognition.stop();
    };

    recognition.onend = () => {
        speakBtn.classList.remove("listening");
    };

    recognition.onresult = (event) => {
        const spokenText = event.results[0][0].transcript;
        setRecognizedText("🗣️ " + spokenText, false);
        sendToBackend(spokenText, selectedLang);
    };

    recognition.onerror = (event) => {
        speakBtn.classList.remove("listening");
        setRecognizedText("❌ Could not recognize speech. Try again.", false);
    };

    recognition.start();
});

// ─── Submit Button ────────────────────────────────────────────────
document.getElementById("submit-btn").addEventListener("click", () => {
    const typedText = document.getElementById("typed-text").value.trim();
    const selectedLang = document.getElementById("language").value;

    if (!typedText) {
        document.getElementById("typed-text").classList.add("shake");
        setTimeout(() => document.getElementById("typed-text").classList.remove("shake"), 400);
        return;
    }

    setRecognizedText("✏️ " + typedText, false);
    sendToBackend(typedText, selectedLang);
});

// ─── Core function ────────────────────────────────────────────────
function sendToBackend(text, lang) {
    setConvertedText("Translating...", true);
    clearSigns();

    fetch("/recognize_speech", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, lang }),
    })
    .then((res) => res.json())
    .then((data) => {
        if (data.error) {
            showError(data.error);
            return;
        }

        setConvertedText("🔤 " + data.translated_text, false);
        displaySigns(data.images);
    })
    .catch((err) => {
        console.error("Error:", err);
        showError("Something went wrong. Please try again.");
    });
}

// ─── UI helpers ───────────────────────────────────────────────────
function setRecognizedText(text, isPlaceholder) {
    const el = document.getElementById("recognized-text");
    el.innerText = text;
    el.className = "result-text" + (isPlaceholder ? " placeholder-text" : "");
}

function setConvertedText(text, isPlaceholder) {
    const el = document.getElementById("converted-text");
    el.innerText = text;
    el.className = "result-text" + (isPlaceholder ? " placeholder-text" : "");
}

function clearSigns() {
    const container = document.getElementById("hand-signs");
    container.innerHTML = "";
}

function displaySigns(images) {
    const container = document.getElementById("hand-signs");
    container.innerHTML = "";

    if (!images || images.length === 0) {
        container.innerHTML = `<div class="empty-state"><span class="empty-icon">🤔</span><span>No signs found</span></div>`;
        return;
    }

    let imgIndex = 0; // separate counter for animation stagger (ignore spacers)
    images.forEach((src) => {
        if (src === "__SPACE__") {
            // Word-gap spacer
            const spacer = document.createElement("div");
            spacer.className = "word-spacer";
            container.appendChild(spacer);
        } else {
            const img = document.createElement("img");
            img.src = src;
            img.alt = "Hand sign";
            img.title = "Hand sign";
            img.style.animationDelay = Math.min(imgIndex, 14) * 0.04 + "s";
            img.onerror = () => { img.style.display = "none"; };
            container.appendChild(img);
            imgIndex++;
        }
    });
}

function showError(msg) {
    setConvertedText("⚠️ " + msg, true);
}
