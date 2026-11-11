"use strict";
// Ditado e leitura são opt-in. Nunca enviam comandos nem confirmam ações.
window.AylaVoice = (() => {
  let ui, synth, chosen = null, available = [], activeButton = null, currentUtterance = null;
  let speechGeneration = 0, speakingText = "", speechPaused = false, speechWatchdog;
  let recording = null, captureGeneration = 0, captureTimer, captureStarting = false, transcribing = null;
  let serverReady = false, allowedBrowser = false, allowedRemoteVoice = false, consentResolver = null;
  const settings = { voiceURI: "", rate: 0.98, mode: "auto" };
  function loadSettings() {
    try {
      const value = JSON.parse(localStorage.getItem("ayla.voice.settings") || "{}");
      if (typeof value.voiceURI === "string") settings.voiceURI = value.voiceURI;
      if (["auto", "local", "browser"].includes(value.mode)) settings.mode = value.mode;
      if (Number.isFinite(value.rate) && value.rate >= 0.7 && value.rate <= 1.3) settings.rate = value.rate;
    } catch { /* Armazenamento bloqueado não impede uso. */ }
  }
  function saveSettings() { try { localStorage.setItem("ayla.voice.settings", JSON.stringify(settings)); } catch {} }
  function isPortuguese(voice) { return /^pt(?:[-_]|$)/i.test(voice.lang); }
  function femaleKnown(voice) { return /\b(Maria|Francisca)\b/i.test(voice.name) && /^pt[-_]BR$/i.test(voice.lang); }
  function rank(voice) {
    return (femaleKnown(voice) ? 100 : 0) + (voice.localService ? 50 : 0) + (/^pt[-_]BR$/i.test(voice.lang) ? 20 : 0);
  }
  function voiceKey(voice) { return voice.voiceURI || voice.name; }
  function updateVoices() {
    available = synth ? synth.getVoices().filter(isPortuguese).sort((a,b) => rank(b)-rank(a)) : [];
    chosen = available.find(v => voiceKey(v) === settings.voiceURI) || available[0] || null;
    const select = document.querySelector("#voice-select");
    select.replaceChildren();
    if (!available.length) {
      const option = document.createElement("option"); option.textContent = "Nenhuma voz em português disponível"; option.value = "";
      select.append(option);
    }
    for (const voice of available) {
      const option = document.createElement("option"); option.value = voiceKey(voice);
      option.textContent = `${voice.name} · ${voice.localService ? "local" : "serviço externo"}`;
      option.selected = chosen === voice; select.append(option);
    }
    select.disabled = !available.length;
    const note = document.querySelector("#voice-note");
    note.textContent = !synth ? "Este navegador não oferece leitura em voz alta." : !chosen ?
      "Não apareceu voz em português. Instale uma voz de fala em Português (Brasil) no Windows e reabra o navegador. A presença no Narrador não garante disponibilidade no navegador." :
      `${femaleKnown(chosen) ? "Voz feminina identificada pelo nome." : "Timbre feminino não confirmado para esta voz; ouça a prévia."} ${chosen.localService ? "O navegador identifica esta voz como local." : "Esta voz usa um serviço externo. Pediremos consentimento antes de enviar o texto para leitura."}`;
    document.querySelector("#test-voice").disabled = !chosen;
  }
  function consent(message, acceptLabel) {
    return new Promise(resolve => {
      if (consentResolver) { resolve(false); return; }
      consentResolver = resolve;
      document.querySelector("#voice-consent-text").textContent = message;
      document.querySelector("#voice-consent-yes").textContent = acceptLabel;
      document.querySelector("#voice-consent").showModal();
    });
  }
  function resolveConsent(accepted) {
    const resolve = consentResolver; consentResolver = null;
    document.querySelector("#voice-consent").close();
    if (resolve) resolve(accepted);
  }
  function stopSpeech() {
    ++speechGeneration; clearTimeout(speechWatchdog);
    if (synth) synth.cancel(); currentUtterance = null;
    if (activeButton) {
      activeButton.setAttribute("aria-pressed", "false"); activeButton.title = "Ouvir resposta";
      activeButton.setAttribute("aria-label", activeButton.id === "test-voice" ? "Ouvir uma prévia" : "Ouvir resposta");
      if (activeButton.id === "test-voice") activeButton.textContent = "Ouvir uma prévia";
      else activeButton.replaceChildren(ui.icon("volume"));
    }
    activeButton = null; speechPaused = false;
    document.querySelector("#speech-player").hidden = true;
    document.querySelector("#pause-speech").textContent = "Pausar";
  }
  function splitText(text) {
    // Pequenos trechos evitam truncamento comum de falas extensas em alguns navegadores.
    const words = text.replace(/\s+/g, " ").trim().split(" "), chunks = [];
    let chunk = "";
    for (const word of words) {
      if ((chunk + " " + word).length > 220 && chunk) { chunks.push(chunk); chunk = ""; }
      chunk += (chunk ? " " : "") + word;
    }
    if (chunk) chunks.push(chunk);
    return chunks;
  }
  async function speak(text, button) {
    if (!synth) { ui.toast("Este navegador não oferece leitura em voz alta."); return; }
    if (button === activeButton) { stopSpeech(); return; }
    if (recording || captureStarting || transcribing) { ui.toast("Encerre o ditado antes de ouvir a resposta."); return; }
    updateVoices();
    if (!chosen) { document.querySelector("#voice-dialog").showModal(); return; }
    if (!chosen.localService && !allowedRemoteVoice) {
      allowedRemoteVoice = await consent("A voz selecionada é fornecida por serviço externo. O texto desta resposta poderá sair do computador para virar áudio. Autorizar leituras externas nesta página?", "Autorizar leitura externa");
      if (!allowedRemoteVoice) return;
    }
    stopSpeech(); speakingText = text;
    const generation = speechGeneration, voice = chosen;
    activeButton = button;
    if (button) { button.setAttribute("aria-pressed", "true"); button.setAttribute("aria-label", "Parar leitura"); button.title = "Parar leitura"; button.replaceChildren(ui.icon("stop")); }
    document.querySelector("#speech-player").hidden = false;
    document.querySelector("#speech-player-label").textContent = `Lendo com ${voice.name}`;
    const chunks = splitText(text);
    function next() {
      if (generation !== speechGeneration) return;
      if (!chunks.length) { stopSpeech(); return; }
      const utterance = new SpeechSynthesisUtterance(chunks.shift());
      currentUtterance = utterance; utterance.voice = voice; utterance.lang = voice.lang;
      utterance.rate = settings.rate; utterance.pitch = 1; utterance.volume = 1;
      utterance.onend = () => { clearTimeout(speechWatchdog); next(); };
      utterance.onerror = event => {
        if (generation !== speechGeneration || ["interrupted", "canceled"].includes(event.error)) return;
        stopSpeech(); ui.toast("Não consegui reproduzir a voz. Escolha outra opção em Voz e microfone.");
      };
      clearTimeout(speechWatchdog);
      speechWatchdog = setTimeout(() => {
        if (generation === speechGeneration && !speechPaused) { stopSpeech(); ui.toast("A leitura não terminou. Tente outra voz disponível."); }
      }, 60000);
      try { synth.speak(utterance); }
      catch { stopSpeech(); ui.toast("A voz selecionada não pôde ser iniciada."); }
    }
    next();
  }
  function addSpeaker(container, text) {
    const button = document.createElement("button"); button.type = "button"; button.className = "icon-button voice-play";
    button.title = "Ouvir resposta"; button.setAttribute("aria-label", "Ouvir resposta"); button.setAttribute("aria-pressed", "false");
    button.append(ui.icon("volume")); button.addEventListener("click", () => speak(text, button)); container.append(button);
    return button;
  }
  function captureState(active, message) {
    ui.captureState(active);
    const mic = document.querySelector("#microphone");
    mic.setAttribute("aria-pressed", String(active)); mic.title = active ? "Parar ditado" : "Ditar mensagem";
    mic.setAttribute("aria-label", mic.title); mic.replaceChildren(ui.icon(active ? "stop" : "mic"));
    document.querySelector("#dictation-status").textContent = message || "";
    document.querySelector("#dictation-strip").hidden = !active;
    document.querySelector("#cancel-dictation").disabled = false;
  }
  function placeTranscript(base, text) {
    const combined = [base.trim(), text.trim()].filter(Boolean).join(" ");
    if (combined.length > 1000) {
      ui.toast("O ditado ultrapassou 1.000 caracteres. Mantive o texto anterior; faça uma gravação menor."); ui.input.value = base;
    } else ui.input.value = combined;
    ui.input.dispatchEvent(new Event("input", { bubbles: true }));
  }
  function endCapture() {
    clearTimeout(captureTimer); recording = null; captureStarting = false;
    ui.input.readOnly = false; captureState(false); ui.input.focus();
  }
  function stopCapture(discard = false) {
    clearTimeout(captureTimer);
    if (captureStarting) { ++captureGeneration; captureStarting = false; endCapture(); return; }
    if (transcribing) { ++captureGeneration; transcribing.abort(); transcribing = null; endCapture(); return; }
    if (!recording) return;
    recording.discard = discard;
    if (recording.type === "browser") {
      if (discard) recording.engine.abort(); else recording.engine.stop();
    } else if (recording.engine.state !== "inactive") recording.engine.stop();
  }
  async function startBrowser() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      ui.toast("Ditado do navegador indisponível. Use o ditado local pelo atalho de instalação.");
      document.querySelector("#voice-dialog").showModal(); return;
    }
    if (!allowedBrowser) {
      allowedBrowser = await consent("O reconhecimento de voz do navegador pode enviar seu áudio a um serviço externo e depender de internet. Autorizar o ditado nesta página? Para manter o áudio local, use ATIVAR_DITADO_LOCAL_AYLA.bat e selecione Ditado local.", "Autorizar ditado do navegador");
      if (!allowedBrowser) return;
    }
    stopSpeech(); const generation = ++captureGeneration, base = ui.input.value;
    const recognition = new Recognition(); recognition.lang = "pt-BR"; recognition.interimResults = true; recognition.continuous = false; recognition.maxAlternatives = 1;
    const task = { type: "browser", engine: recognition, base, discard: false };
    recording = task; ui.input.readOnly = true; captureState(true, "Ouvindo… Toque em parar e revise antes de enviar.");
    let lastText = "", didError = false, failedService = false;
    recognition.onresult = event => {
      if (generation !== captureGeneration) return;
      lastText = Array.from(event.results).map(r => r[0].transcript).join(" ");
      placeTranscript(base, lastText);
    };
    recognition.onerror = event => {
      didError = true;
      failedService = ["network", "service-not-allowed", "language-not-supported"].includes(event.error);
      if (event.error === "aborted") return;
      const messages = {"not-allowed": "Permissão de microfone negada. Libere nas permissões do navegador.", "audio-capture": "Não encontrei um microfone disponível.", "no-speech": "Não identifiquei fala. Tente novamente.", "network": "O serviço de ditado do navegador está indisponível. Tente o modo local.", "language-not-supported": "O serviço não aceitou português brasileiro. Use o ditado local."};
      ui.toast(messages[event.error] || "O ditado não pôde continuar. Use o modo local ou digite.");
    };
    recognition.onend = () => {
      if (generation !== captureGeneration) return;
      if (task.discard) placeTranscript(base, "");
      else if (lastText && !didError) ui.toast("Ditado pronto. Revise o texto e pressione Enviar.");
      endCapture();
      if (failedService) {
        updateLocalStatus().then(() => {
          settings.mode = "local"; saveSettings();
          document.querySelector("#dictation-mode").value = "local";
          const note = document.querySelector("#dictation-note");
          note.textContent = serverReady ? "O serviço externo falhou. Selecionei o ditado local; clique no microfone novamente para gravar." : "O serviço externo falhou. Execute ATIVAR_DITADO_LOCAL_AYLA.bat, reinicie a Ayla e clique em Verificar vozes e ditado local. Não é necessário alterar o Qwen.";
          const dialog = document.querySelector("#voice-dialog"); if (!dialog.open) dialog.showModal();
        });
      }
    };
    try { recognition.start(); captureTimer = setTimeout(() => stopCapture(), 60000); }
    catch { endCapture(); ui.toast("Não consegui iniciar o ditado. Confira as permissões."); }
  }
  async function startLocal() {
    if (!serverReady) {
      ui.toast("Execute ATIVAR_DITADO_LOCAL_AYLA.bat e reinicie a Ayla para ativar o ditado local.");
      document.querySelector("#voice-dialog").showModal(); return;
    }
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) { ui.toast("Este navegador não permite gravação de áudio nesta página."); return; }
    stopSpeech(); const generation = ++captureGeneration, base = ui.input.value;
    captureStarting = true; captureState(true, "Autorize o microfone no navegador…");
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true }, video: false });
      if (generation !== captureGeneration) { stream.getTracks().forEach(t => t.stop()); return; }
      const mime = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"].find(type => MediaRecorder.isTypeSupported(type));
      if (!mime) throw new Error("Formato de gravação não suportado. Use um navegador compatível com MediaRecorder.");
      const recorder = new MediaRecorder(stream, { mimeType: mime, audioBitsPerSecond: 64000 });
      const task = { type: "local", engine: recorder, stream, base, discard: false };
      const chunks = []; let bytes = 0; recording = task; captureStarting = false;
      recorder.ondataavailable = event => {
        if (event.data.size) { bytes += event.data.size; chunks.push(event.data); }
        if (bytes > 5 * 1024 * 1024) { task.discard = true; recorder.stop(); ui.toast("Gravação muito grande. Faça um ditado menor."); }
      };
      recorder.onerror = () => { task.discard = true; if (recorder.state !== "inactive") recorder.stop(); stream.getTracks().forEach(t => t.stop()); ui.toast("Falha na gravação do microfone."); };
      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop()); clearTimeout(captureTimer);
        if (generation !== captureGeneration) return;
        recording = null;
        if (task.discard) { placeTranscript(base, ""); endCapture(); return; }
        captureState(true, "Transcrevendo neste computador… O texto não será enviado automaticamente.");
        const controller = new AbortController(); transcribing = controller;
        const timeout = setTimeout(() => controller.abort(), 180000);
        try {
          const response = await fetch("/api/voz/transcrever", { method: "POST", headers: { "Content-Type": mime, ...ui.headers() }, body: new Blob(chunks, { type: mime }), signal: controller.signal });
          const data = await response.json();
          if (!response.ok) throw new Error(data.mensagem || "Não foi possível transcrever.");
          if (generation !== captureGeneration) return;
          placeTranscript(base, data.texto); ui.toast("Ditado local pronto. Revise o texto antes de enviar.");
        } catch (error) {
          if (generation === captureGeneration) ui.toast(error.name === "AbortError" ? "Transcrição interrompida ou tempo excedido." : error.message);
        } finally {
          clearTimeout(timeout);
          if (generation === captureGeneration) { transcribing = null; endCapture(); }
        }
      };
      recorder.start(1000); ui.input.readOnly = true;
      captureState(true, "Gravando localmente… Toque em parar para transcrever. Máximo: 60 s.");
      // Margem para a duração codificada não ultrapassar o limite do servidor.
      captureTimer = setTimeout(() => stopCapture(), 58000);
    } catch (error) {
      if (stream) stream.getTracks().forEach(t => t.stop());
      if (generation !== captureGeneration) return;
      endCapture(); ui.toast(error.name === "NotAllowedError" ? "Microfone não autorizado. Confira as permissões da página." : error.message || "Não consegui acessar o microfone.");
    }
  }
  async function updateLocalStatus() {
    try { const response = await fetch("/api/voz/status", { cache: "no-store" }); serverReady = response.ok && (await response.json()).disponivel; }
    catch { serverReady = false; }
    document.querySelector("#dictation-note").textContent = serverReady ?
      "Ditado local pronto: Whisper base no processador. O áudio vai somente ao servidor desta máquina e não é salvo em arquivo." :
      "Ditado local ainda não instalado. Execute ATIVAR_DITADO_LOCAL_AYLA.bat na raiz do projeto; esse preparo usa internet. O ditado do navegador é uma alternativa com consentimento.";
  }
  function stopAll() {
    stopSpeech(); stopCapture(true);
    if (consentResolver) resolveConsent(false);
  }
  function init(options) {
    ui = options; synth = window.speechSynthesis || null; loadSettings();
    const dialog = document.querySelector("#voice-dialog");
    function show() { ui.beforeSettings?.(); updateVoices(); updateLocalStatus(); dialog.showModal(); }
    document.querySelector("#voice-settings").addEventListener("click", show);
    document.querySelector("#close-voice").addEventListener("click", () => dialog.close());
    document.querySelector("#voice-select").addEventListener("change", event => { settings.voiceURI = event.target.value; stopSpeech(); saveSettings(); updateVoices(); });
    const rate = document.querySelector("#voice-rate"); rate.value = settings.rate;
    const rateLabel = document.querySelector("#voice-rate-label"); rateLabel.textContent = `${settings.rate.toFixed(2)}×`;
    rate.addEventListener("input", () => { settings.rate = Number(rate.value); rateLabel.textContent = `${settings.rate.toFixed(2)}×`; saveSettings(); });
    document.querySelector("#test-voice").addEventListener("click", () => speak("Oi, eu sou a Ayla. Você pode falar comigo e ouvir minhas respostas. Você continua no controle.", document.querySelector("#test-voice")));
    const mode = document.querySelector("#dictation-mode"); mode.value = settings.mode;
    mode.addEventListener("change", () => { settings.mode = mode.value; saveSettings(); });
    document.querySelector("#recheck-voice").addEventListener("click", () => { updateVoices(); updateLocalStatus(); });
    document.querySelector("#microphone").addEventListener("click", async () => {
      if (recording || captureStarting || transcribing) { stopCapture(); return; }
      if (!ui.canStart()) { ui.toast("Aguarde a operação atual antes de ditar."); return; }
      await updateLocalStatus();
      if (settings.mode === "local" || (settings.mode === "auto" && serverReady)) await startLocal(); else await startBrowser();
    });
    document.querySelector("#cancel-dictation").addEventListener("click", () => stopCapture(true));
    document.querySelector("#stop-speech").addEventListener("click", stopSpeech);
    document.querySelector("#pause-speech").addEventListener("click", () => {
      if (!synth || !activeButton) return;
      speechPaused = !speechPaused;
      if (speechPaused) { synth.pause(); clearTimeout(speechWatchdog); } else { synth.resume(); speechWatchdog = setTimeout(() => { if (!speechPaused && activeButton) { stopSpeech(); ui.toast("A leitura não terminou. Tente outra voz."); } }, 60000); }
      document.querySelector("#pause-speech").textContent = speechPaused ? "Continuar" : "Pausar";
    });
    document.querySelector("#voice-consent-yes").addEventListener("click", () => resolveConsent(true));
    document.querySelector("#voice-consent-no").addEventListener("click", () => resolveConsent(false));
    document.querySelector("#voice-consent").addEventListener("cancel", event => { event.preventDefault(); resolveConsent(false); });
    if (synth) synth.addEventListener("voiceschanged", updateVoices);
    updateVoices(); updateLocalStatus(); window.addEventListener("pagehide", stopAll);
  }
  return { init, addSpeaker, stopAll, stopSpeech, splitText, rank };
})();
