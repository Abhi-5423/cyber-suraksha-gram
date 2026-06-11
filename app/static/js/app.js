const supportedLanguages = ["en", "hi"];
const pageLang = document.body.dataset.activeLang || "en";
const isAuthenticated = document.body.dataset.authenticated === "true";
const savedLanguage = localStorage.getItem("language");
const currentPath = `${window.location.pathname}${window.location.search}`;

if (!isAuthenticated && supportedLanguages.includes(savedLanguage) && savedLanguage !== pageLang) {
  window.location.replace(`/set-language/${savedLanguage}?next=${encodeURIComponent(currentPath)}`);
}

const langSelect = document.getElementById("languageSelect");
if (langSelect) {
  localStorage.setItem("language", langSelect.value);
  langSelect.addEventListener("change", (event) => {
    const nextLang = event.target.value;
    if (!supportedLanguages.includes(nextLang)) return;
    localStorage.setItem("language", nextLang);
    window.location.href = `/set-language/${nextLang}?next=${encodeURIComponent(currentPath)}`;
  });
}

const darkToggle = document.getElementById("darkToggle");
const savedTheme = localStorage.getItem("theme");
if (savedTheme === "dark") document.body.classList.add("dark");
if (darkToggle) {
  darkToggle.addEventListener("click", () => {
    document.body.classList.toggle("dark");
    localStorage.setItem("theme", document.body.classList.contains("dark") ? "dark" : "light");
  });
}

document.querySelectorAll("[data-count]").forEach((element) => {
  const target = Number(element.dataset.count || 0);
  let value = 0;
  const step = Math.max(1, Math.ceil(target / 40));
  const tick = () => {
    value = Math.min(target, value + step);
    element.textContent = value;
    if (value < target) requestAnimationFrame(tick);
  };
  tick();
});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/service-worker.js").catch(() => {});
}

const voiceStart = document.getElementById("voiceStart");
if (voiceStart) {
  voiceStart.addEventListener("click", () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert(pageLang === "hi" ? "इस ब्राउज़र में speech recognition उपलब्ध नहीं है." : "Speech recognition is not available in this browser.");
      return;
    }
    const recognizer = new SpeechRecognition();
    recognizer.lang = document.documentElement.lang === "hi" ? "hi-IN" : "en-IN";
    recognizer.onresult = (event) => {
      const field = document.querySelector("textarea[name='message']");
      if (field) field.value = event.results[0][0].transcript;
    };
    recognizer.start();
  });
}

const speakReply = document.getElementById("speakReply");
if (speakReply) {
  speakReply.addEventListener("click", () => {
    const text = document.getElementById("assistantReply")?.innerText;
    if (!text) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = document.documentElement.lang === "hi" ? "hi-IN" : "en-IN";
    speechSynthesis.speak(utterance);
  });
}

const serverSpeakReply = document.getElementById("serverSpeakReply");
if (serverSpeakReply) {
  serverSpeakReply.addEventListener("click", async () => {
    const text = document.getElementById("assistantReply")?.innerText;
    if (!text) return;
    const response = await fetch("/api/voice/speak", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({text}),
    });
    if (!response.ok) {
      alert(pageLang === "hi" ? "Server voice अभी उपलब्ध नहीं है." : "Server voice is unavailable right now.");
      return;
    }
    const blob = await response.blob();
    const player = document.getElementById("serverVoicePlayer");
    player.src = URL.createObjectURL(blob);
    player.hidden = false;
    player.play();
  });
}

const scoreChart = document.getElementById("scoreChart");
if (scoreChart && window.Chart) {
  const scores = JSON.parse(scoreChart.dataset.scores || "[]");
  new Chart(scoreChart, {
    type: "line",
    data: {
      labels: scores.map((_, index) => `${index + 1}`),
      datasets: [{
        label: pageLang === "hi" ? "क्विज स्कोर" : "Quiz Score",
        data: scores,
        borderColor: "#0f766e",
        backgroundColor: "rgba(15, 118, 110, 0.16)",
        fill: true,
        tension: 0.35,
      }],
    },
    options: {responsive: true, scales: {y: {beginAtZero: true, max: 100}}},
  });
}
