// ---------- Placement predictor ----------
const form = document.getElementById("predict-form");
const btn = document.getElementById("predict-btn");
const resultBox = document.getElementById("result");
const errorBox = document.getElementById("predict-error");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorBox.hidden = true;
  const payload = Object.fromEntries(new FormData(form).entries());
  btn.disabled = true;
  btn.textContent = "Checking...";
  try {
    const res = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.error || "Prediction failed");
    showResult(data);
  } catch (err) {
    resultBox.hidden = true;
    errorBox.textContent = err.message;
    errorBox.hidden = false;
  } finally {
    btn.disabled = false;
    btn.textContent = "Check eligibility";
  }
});

function showResult(d) {
  const color = d.probability >= 70 ? "var(--good)" : d.probability >= 40 ? "var(--mid)" : "var(--bad)";
  resultBox.hidden = false;
  const fill = document.getElementById("meter-fill");
  fill.style.background = color;
  fill.style.width = d.probability + "%";
  document.getElementById("result-status").textContent = d.status;
  document.getElementById("result-status").style.color = color;
  document.getElementById("result-prob").textContent = `Placement probability: ${d.probability}%`;
  document.getElementById("result-tier").textContent = d.prediction;
}

// ---------- Policy chatbot ----------
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatLog = document.getElementById("chat-log");

function addMsg(text, cls) {
  const div = document.createElement("div");
  div.className = "msg " + cls;
  div.textContent = text;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
  return div;
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;
  addMsg(message, "user");
  chatInput.value = "";
  const typing = addMsg("Typing...", "bot typing");
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await res.json();
    typing.remove();
    addMsg(data.success ? data.response : data.error, "bot");
  } catch {
    typing.remove();
    addMsg("Could not reach the server. Check that Flask is running.", "bot");
  }
});
