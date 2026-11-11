"use strict";
const $ = selector => document.querySelector(selector);
const form = $("#command-form"), input = $("#command"), send = $("#send");
const messages = $("#messages"), welcome = $("#welcome"), activity = $("#activity");
const scroller = $("#conversation-scroll"), about = $("#about-dialog"), newDialog = $("#new-dialog");
let busy = false, capturing = false, toastTimer;
let webConsent = false, webConfigured = null, webTested = false, pendingWebForce = false;
try { webConsent = sessionStorage.getItem("ayla-web-consent-v1") === "yes"; } catch { /* Disabled storage: page-scoped consent. */ }
function saveWebConsent(value) {
  webConsent = value;
  try { if (value) sessionStorage.setItem("ayla-web-consent-v1", "yes"); else sessionStorage.removeItem("ayla-web-consent-v1"); } catch { /* No persistence. */ }
}
// Uma página = uma conversa. Não persiste após recarregar nem sincroniza entre abas.
const sessionId = crypto.randomUUID ? crypto.randomUUID() : Array.from(crypto.getRandomValues(new Uint8Array(24)), b => b.toString(16).padStart(2, "0")).join("");
function sessionHeaders() { return { "X-Ayla-Session": sessionId }; }
const pendingTokens = new Set();

function node(tag, text, className) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text; // Dados do usuário/modelo nunca são HTML.
  if (className) el.className = className;
  return el;
}
function icon(name) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  use.setAttribute("href", `/static/icons.svg#${name}`);
  svg.append(use);
  return svg;
}
function end() { scroller.scrollTop = scroller.scrollHeight; }
function toast(message) {
  clearTimeout(toastTimer);
  $("#toast").textContent = message;
  $("#toast").hidden = false;
  toastTimer = setTimeout(() => { $("#toast").hidden = true; }, 3500);
}
function setBusy(value, label = "Preparando resposta com o modelo local…") {
  busy = value;
  send.disabled = value || capturing || !input.value.trim();
  $("#new-chat").disabled = value || capturing;
  $("#microphone").disabled = value;
  form.setAttribute("aria-busy", String(value));
  activity.textContent = value ? label : "Enter para enviar · Shift + Enter para nova linha";
}
function renderAnswer(text) {
  const box = node("div", undefined, "answer-text");
  const lines = text.split("\n"); let code = null, codeLines = [];
  function flushCode() { if (code) { code.textContent = codeLines.join("\n"); const pre = node("pre"); pre.append(code); box.append(pre); code = null; codeLines = []; } }
  function inline(parent, value) {
    const parts = value.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
    for (const part of parts) {
      if (part.startsWith("**") && part.endsWith("**")) parent.append(node("strong", part.slice(2,-2)));
      else if (part.startsWith("`") && part.endsWith("`")) parent.append(node("code", part.slice(1,-1)));
      else parent.append(document.createTextNode(part));
    }
  }
  for (const line of lines) {
    if (line.startsWith("```")) { if (code) flushCode(); else { code = node("code"); codeLines = []; } continue; }
    if (code) { codeLines.push(line); continue; }
    if (!line.trim()) continue;
    const h = /^(#{1,3})\s+(.+)$/.exec(line);
    const p = node(h ? "h3" : "p"); inline(p, h ? h[2] : line); box.append(p);
  }
  flushCode(); return box;
}
function bubble(text, role = "assistant") {
  welcome.hidden = true;
  const article = node("article", undefined, `message ${role}`);
  if (role !== "user") {
    const speaker = node("div", undefined, "speaker");
    const avatar = node("span", undefined, "avatar");
    avatar.append(icon(role === "error" ? "alert" : "spark"));
    speaker.append(avatar, node("span", "Ayla"));
    article.append(speaker);
  }
  const body = node("div", undefined, "message-content");
  if (text) body.append(role === "assistant" ? renderAnswer(text) : node("p", text));
  article.append(body);
  if (role === "error") {
    const tools = node("div", undefined, "message-tools");
    AylaVoice.addSpeaker(tools, text); body.append(tools);
  }
  messages.append(article);
  end();
  return { article, body };
}
function thinking() {
  const item = bubble("", "assistant thinking");
  const dots = node("span", undefined, "thinking-dots");
  dots.setAttribute("aria-hidden", "true");
  dots.append(node("i"), node("i"), node("i"));
  item.body.append(dots, node("span", "Preparando a resposta; pesquisas podem exigir várias etapas…"));
  end();
  return item.article;
}
async function request(path, body) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 205000);
  const options = { signal: controller.signal, cache: "no-store", headers: sessionHeaders() };
  if (body !== undefined) Object.assign(options, {
    method: "POST", headers: { "Content-Type": "application/json", ...sessionHeaders() }, body: JSON.stringify(body),
  });
  try {
    const response = await fetch(path, options);
    let data;
    try { data = await response.json(); }
    catch { throw new Error("O servidor retornou uma resposta inesperada. Confira o terminal."); }
    if (!response.ok) {
      const error = new Error(data.mensagem || "Não consegui concluir a operação.");
      error.status = response.status;
      throw error;
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("A resposta demorou além do limite. Confira o Ollama e tente novamente.");
    if (error instanceof TypeError) throw new Error("Não consegui conectar ao servidor local. Confira se ele continua aberto.");
    throw error;
  } finally { clearTimeout(timeout); }
}
function displayName(list) { return list.nome_exibicao || list.nome; }
async function refreshLists() {
  const target = $("#saved-lists"), notice = $("#list-notice");
  try {
    const data = await request("/api/listas");
    const counts = new Map();
    for (const list of data.listas) {
      const name = displayName(list).toLocaleLowerCase("pt-BR");
      counts.set(name, (counts.get(name) || 0) + 1);
    }
    target.replaceChildren();
    $("#list-count").textContent = data.listas.length;
    notice.textContent = "";
    if (!data.listas.length) target.append(node("p", "Suas listas aparecem aqui depois da primeira inclusão confirmada.", "sidebar-empty"));
    for (const list of data.listas) {
      const duplicate = counts.get(displayName(list).toLocaleLowerCase("pt-BR")) > 1;
      const button = node("button", undefined, "saved-list");
      button.type = "button";
      button.title = `${list.nome} · abrir lista salva`;
      button.setAttribute("aria-label", `Abrir lista ${list.nome}${duplicate ? `, registro ${list.id}` : ""}`);
      const text = node("span", undefined, "saved-list-text");
      text.append(node("span", duplicate ? list.nome : displayName(list), "saved-list-title"),
        node("span", `${list.itens.length} ${list.itens.length === 1 ? "item" : "itens"}${duplicate ? ` · registro #${list.id}` : ""}`, "saved-list-meta"));
      const chevron = icon("chevron"); chevron.classList.add("list-chevron");
      button.append(icon("list"), text, chevron);
      button.addEventListener("click", async () => {
        if (busy || capturing) { toast("Aguarde a resposta atual para abrir uma lista."); return; }
        closeMenu();
        setBusy(true, "Abrindo sua lista salva…");
        try {
          const result = await request(`/api/listas/${list.id}`);
          showResult({ estado: "respondido", mensagem: `Aqui está sua lista “${displayName(result.lista)}”.`, lista: result.lista, origem: "Consulta direta ao banco local" });
        } catch (error) { bubble(error.message, "error"); }
        finally { setBusy(false); }
      });
      target.append(button);
    }
  } catch (error) {
    notice.textContent = "Não consegui atualizar as listas. Tente o botão de atualização.";
    throw error;
  }
}
function listCard(list, proposal = false) {
  const card = node("section", undefined, proposal ? "proposal" : "result-card");
  const title = node("div", undefined, "result-title");
  title.append(icon("list"), node("span", displayName(list)));
  const items = node("ul", undefined, "result-items");
  for (const item of list.itens) {
    const done = list.detalhes_itens?.find(record => record.texto === item)?.concluido;
    const li = node("li", undefined, done ? "item-completed" : "");
    li.append(node("span", done ? "✓" : undefined, done ? "item-check" : "item-dot"), node("span", item));
    if (done) li.append(node("span", "concluído", "item-status"));
    items.append(li);
  }
  card.append(title, items);
  if (!list.itens.length) card.append(node("p", "Nenhum item salvo nesta lista.", "proposal-note"));
  if (list.novo_nome) card.append(node("p", `Novo nome: ${list.novo_nome}`, "proposal-note"));
  if (proposal) card.append(node("p", "A proposta ainda não foi aplicada. A confirmação vale por 10 minutos.", "proposal-note"));
  return card;
}
function catalogCard(lists) {
  const card = node("section", undefined, "result-card catalog-card");
  card.setAttribute("aria-label", "Listas salvas no banco local");
  const counts = new Map();
  for (const list of lists) {
    const name = displayName(list).toLocaleLowerCase("pt-BR");
    counts.set(name, (counts.get(name) || 0) + 1);
  }
  for (const list of lists) {
    const duplicate = counts.get(displayName(list).toLocaleLowerCase("pt-BR")) > 1;
    const button = node("button", undefined, "saved-list catalog-entry");
    button.type = "button";
    button.setAttribute("aria-label", `Abrir lista ${list.nome}${duplicate ? `, registro ${list.id}` : ""}`);
    const text = node("span", undefined, "saved-list-text");
    text.append(node("span", duplicate ? list.nome : displayName(list), "saved-list-title"),
      node("span", `${list.quantidade_itens} ${list.quantidade_itens === 1 ? "item" : "itens"}${duplicate ? ` · registro #${list.id}` : ""}`, "saved-list-meta"));
    button.append(icon("list"), text, icon("chevron"));
    button.addEventListener("click", async () => {
      if (busy || capturing) { toast("Aguarde a resposta atual para abrir uma lista."); return; }
      setBusy(true, "Abrindo sua lista salva…");
      try {
        const result = await request(`/api/listas/${list.id}`);
        showResult({ estado: "respondido", mensagem: `Aqui está sua lista “${displayName(result.lista)}”.`,
          lista: result.lista, origem: "Consulta direta ao banco local" });
      } catch (error) { bubble(error.message, "error"); }
      finally { setBusy(false); end(); }
    });
    card.append(button);
  }
  card.append(node("p", "Contagem de entradas salvas; não de unidades físicas. Retrato do banco no momento da consulta.", "proposal-note"));
  return card;
}
function weatherCard(data) {
  const card = node("section", undefined, "result-card");
  const title = node("div", undefined, "result-title"); title.append(icon("sun"), node("span", data.local));
  const body = node("div", undefined, "weather-result");
  const temp = Number(data.temperatura_c).toLocaleString("pt-BR", { maximumFractionDigits: 1 });
  const feels = Number(data.sensacao_c).toLocaleString("pt-BR", { maximumFractionDigits: 1 });
  body.append(node("div", `${temp} °C`, "weather-number"), node("div", `Sensação de ${feels} °C`, "weather-meta"),
    node("div", `Referência: ${data.horario} · ${data.fuso}`, "weather-source"),
    node("div", "Fonte: Open-Meteo · dados de modelo meteorológico", "weather-source"));
  card.append(title, body); return card;
}
function responseText(data) {
  let text = data.mensagem;
  for (const list of [data.proposta, data.lista]) if (list) {
    text += `\nLista ${displayName(list)}.`;
    if (list.novo_nome) text += ` Novo nome: ${list.novo_nome}.`;
    if (list.itens.length) text += "\n" + list.itens.map(item => {
      const done = list.detalhes_itens?.find(record => record.texto === item)?.concluido;
      return item + (done ? ": concluído." : ".");
    }).join("\n");
  }
  if (data.catalogo?.length) text += "\n" + data.catalogo.map(list => `${displayName(list)}: ${list.quantidade_itens} ${list.quantidade_itens === 1 ? "item" : "itens"}.`).join("\n");
  if (data.encontrados?.length) text += "\n" + data.encontrados.map(row => `${row.item}, na lista ${row.lista}${row.concluido ? ", concluído" : ""}.`).join("\n");
  return text;
}
function showResult(data, originalQuestion = null) {
  if (data.cancelou_pendentes) {
    pendingTokens.clear();
    document.querySelectorAll(".message-content .actions").forEach(actions => {
      actions.replaceChildren(node("span", "Proposta cancelada.")); actions.className = "action-resolved";
    });
  }
  const { body } = bubble(data.mensagem);
  if (data.encontrados?.length) {
    const results = node("section", undefined, "result-card search-results");
    for (const row of data.encontrados) {
      const entry = node("div", undefined, "search-result");
      entry.append(icon("search"), node("div", `${row.item}${row.concluido ? " · concluído" : ""}\n${row.lista} · registro #${row.lista_id}`));
      results.append(entry);
    }
    body.append(results);
  }
  if (data.proposta) body.append(listCard(data.proposta, true));
  if (data.lista) body.append(listCard(data.lista));
  if (data.catalogo && data.catalogo.length) body.append(catalogCard(data.catalogo));
  if (data.clima) body.append(weatherCard(data.clima));
  const actions = node("div", undefined, "actions");
  if (data.token) pendingTokens.add(data.token);
  function action(label, path, payload, secondary = false, actionType = "confirm") {
    const button = node("button", undefined, secondary ? "secondary" : "primary");
    button.type = "button";
    if (!secondary) button.append(icon(actionType === "weather" ? "sun" : "check"));
    button.append(node("span", label));
    button.addEventListener("click", async () => {
      if (busy || capturing) { toast("Aguarde a resposta atual para continuar."); return; }
      setBusy(true, actionType === "weather" ? "Consultando o clima…" : "Concluindo sua solicitação…");
      actions.querySelectorAll("button").forEach(b => { b.disabled = true; });
      try {
        const result = await request(path, payload);
        pendingTokens.delete(data.token);
        actions.replaceChildren();
        actions.className = "action-resolved";
        actions.append(icon(actionType === "cancel" ? "close" : "check"),
          node("span", actionType === "cancel" ? "Solicitação cancelada" : actionType === "weather" ? "Localização selecionada" : "Alteração confirmada"));
        showResult(result);
        // Uma falha na atualização visual não reativa uma confirmação já consumida.
        try { await refreshLists(); } catch { toast("A operação terminou, mas as listas não atualizaram. Use Atualizar listas."); }
      } catch (error) {
        bubble(error.message, "error");
        if (error.status === 409) {
          pendingTokens.delete(data.token);
          actions.replaceChildren(node("span", "Solicitação encerrada. Faça um novo pedido."));
          actions.className = "action-resolved";
        } else { actions.querySelectorAll("button").forEach(b => { b.disabled = false; }); }
      } finally { setBusy(false); end(); }
    });
    actions.append(button);
  }
  if (data.estado === "confirmacao_necessaria") {
    action(data.rotulo_confirmar || "Confirmar inclusão", `/api/confirmar/${encodeURIComponent(data.token)}`, {});
    action("Cancelar", `/api/cancelar/${encodeURIComponent(data.token)}`, {}, true, "cancel");
  }
  if (data.estado === "escolher_cidade") {
    for (const place of data.opcoes) action(place.nome, `/api/clima/${encodeURIComponent(data.token)}`, { indice: place.indice }, false, "weather");
    action("Cancelar", `/api/cancelar/${encodeURIComponent(data.token)}`, {}, true, "cancel");
  }
  if (actions.childElementCount) body.append(actions);
  if (data.calculos?.length) {
    const card = node("section", undefined, "calculation-card");
    for (const calc of data.calculos) card.append(node("code", `${calc.expressao} = ${calc.resultado}`));
    card.append(node("small", "Resultado da calculadora local · precisão decimal limitada"));
    body.append(card);
  }
  if (data.fontes?.length) {
    const refs = node("section", undefined, "web-sources");
    refs.append(node("h3", "Fontes recuperadas"));
    for (const source of data.fontes) {
      let url; try { url = new URL(source.url); } catch { continue; }
      if (!["https:", "http:"].includes(url.protocol)) continue;
      const link = node("a", `[${source.id}] ${source.titulo}`);
      link.href = url.href; link.target = "_blank"; link.rel = "noopener noreferrer";
      const card = node("div", undefined, "source-card");
      card.append(link, node("small", `${url.hostname} · ${source.tipo} · acesso ${source.acesso.slice(0, 10)}`));
      refs.append(card);
    }
    body.append(refs);
  }
  if (data.avisos?.length) {
    const note = node("div", undefined, "response-warning");
    for (const warning of data.avisos) note.append(node("p", warning));
    body.append(note);
  }
  if (data.ferramentas?.length) {
    const trace = node("details", undefined, "trace");
    trace.append(node("summary", "Ferramentas utilizadas (não é raciocínio interno)"));
    for (const event of data.ferramentas) trace.append(node("p", event));
    body.append(trace);
  }
  if (data.interpretacao) {
    const details = node("details", undefined, "trace");
    const seconds = Number(data.latencia_total_ms / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 2 });
    details.append(node("summary", `Detalhes da interpretação${data.latencia_total_ms !== undefined ? ` · ${seconds} s` : ""}`),
      node("pre", JSON.stringify(data.interpretacao, null, 2)));
    body.append(details);
  }
  const tools = node("div", undefined, "message-tools");
  const copy = node("button", undefined, "icon-button"); copy.type = "button"; copy.title = "Copiar resposta";
  copy.setAttribute("aria-label", "Copiar resposta"); copy.append(icon("copy"));
  copy.addEventListener("click", async () => {
    const text = responseText(data) + (data.fontes?.length ? "\n\nFontes:\n" + data.fontes.map(s => `[${s.id}] ${s.titulo}: ${s.url}`).join("\n") : "");
    try { await navigator.clipboard.writeText(text); toast("Resposta copiada."); }
    catch { toast("Não foi possível copiar. Selecione o texto da resposta."); }
  });
  tools.append(copy);
  AylaVoice.addSpeaker(tools, responseText(data));
  if (data.origem) tools.append(node("span", data.origem));
  if (originalQuestion && !data.fontes?.length && !data.token && !data.interpretacao) {
    const retry = node("button", "Pesquisar esta pergunta", "research-retry");
    retry.type = "button";
    retry.addEventListener("click", () => {
      if (busy || capturing) return;
      input.value = originalQuestion; updateCount();
      if (!webConsent || !$("#web-enabled").checked) {
        pendingWebForce = true; showWebSettings();
      } else { $("#web-force").checked = true; renderWebState(); input.focus(); }
      toast("A pergunta voltou ao campo de mensagem. Revise e envie para pesquisar.");
    });
    tools.append(retry);
  }
  body.append(tools);
  end();
}
form.addEventListener("submit", async event => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text || busy || capturing) return;
  AylaVoice.stopSpeech();
  setBusy(true); input.value = ""; updateCount(); closeMenu();
  bubble(text, "user");
  const loader = thinking();
  try {
    const permission = webConsent && $("#web-enabled").checked;
    const forced = $("#web-force").checked;
    $("#web-force").checked = false; renderWebState();
    const data = await request("/api/comandos", { texto: text, permitir_web: permission, pesquisar_agora: forced });
    loader.remove(); showResult(data, text);
  } catch (error) { loader.remove(); bubble(error.message, "error"); }
  finally { setBusy(false); input.focus(); end(); }
});
input.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault(); if (!busy && !capturing) form.requestSubmit();
  }
});
function updateCount() { $("#character-count").textContent = input.value.length > 800 ? `${input.value.length}/1000` : ""; send.disabled = busy || capturing || !input.value.trim(); }
input.addEventListener("input", updateCount);
document.querySelectorAll(".suggestion").forEach(button => button.addEventListener("click", () => {
  input.value = button.dataset.example; updateCount(); input.focus();
}));
$("#refresh").addEventListener("click", async () => {
  $("#refresh").disabled = true;
  try { await refreshLists(); toast("Listas atualizadas."); } catch (error) { toast(error.message); }
  finally { $("#refresh").disabled = false; }
});
async function checkStatus() {
  const indicator = $("#model-status"), label = $("#status-text");
  indicator.className = "model-status checking"; label.textContent = "Verificando modelo";
  try {
    const data = await request("/api/status");
    const ready = data.ollama && data.instalado;
    label.textContent = ready ? "Modelo disponível" : "Verificar Ollama";
    indicator.className = ready ? "model-status ok" : "model-status bad";
    indicator.title = ready ? `Instalado: ${data.modelo}. A velocidade depende do seu computador.` : "Abra o Ollama e confira se o modelo foi baixado.";
    $("#model-name").textContent = data.modelo && data.modelo !== "substituto-de-teste" ? data.modelo : "Qwen · modelo local";
  } catch {
    label.textContent = "Servidor indisponível"; indicator.className = "model-status bad";
  }
}
function showAbout() { closeMenu(); about.showModal(); }
for (const id of ["about-sidebar", "about-header", "limits-link"]) $("#" + id).addEventListener("click", showAbout);
$("#close-about").addEventListener("click", () => about.close());
$("#recheck-model").addEventListener("click", async () => {
  $("#recheck-model").disabled = true;
  await checkStatus();
  $("#recheck-model").disabled = false;
});
$("#new-chat").addEventListener("click", () => {
  closeMenu();
  if (!messages.childElementCount) { input.focus(); return; }
  newDialog.showModal();
});
$("#cancel-new").addEventListener("click", () => newDialog.close());
$("#confirm-new").addEventListener("click", async () => {
  $("#confirm-new").disabled = true;
  let failed = false;
  for (const token of pendingTokens) {
    try { await request(`/api/cancelar/${encodeURIComponent(token)}`, {}); }
    catch (error) { if (error.status !== 409) failed = true; }
  }
  if (failed) {
    toast("Não consegui cancelar todos os pedidos. Confira o servidor e tente novamente.");
    $("#confirm-new").disabled = false;
    return;
  }
  try { await request("/api/conversa/nova", {}); }
  catch (error) { toast(error.message); $("#confirm-new").disabled = false; return; }
  AylaVoice.stopAll();
  pendingTokens.clear(); messages.replaceChildren(); welcome.hidden = false;
  input.value = ""; updateCount(); newDialog.close(); $("#confirm-new").disabled = false; input.focus();
});
function openMenu() {
  document.body.classList.add("sidebar-open"); $("#rail-backdrop").hidden = false;
  $("#open-menu").setAttribute("aria-expanded", "true");
  $("#content").inert = true;
  $("#sidebar").setAttribute("role", "dialog"); $("#sidebar").setAttribute("aria-modal", "true");
  $("#close-menu").focus();
}
function closeMenu() {
  const wasOpen = document.body.classList.contains("sidebar-open");
  document.body.classList.remove("sidebar-open"); $("#rail-backdrop").hidden = true;
  $("#content").inert = false; $("#open-menu").setAttribute("aria-expanded", "false");
  $("#sidebar").removeAttribute("role"); $("#sidebar").removeAttribute("aria-modal");
  if (wasOpen) $("#open-menu").focus();
}
$("#open-menu").addEventListener("click", openMenu);
$("#close-menu").addEventListener("click", closeMenu);
$("#rail-backdrop").addEventListener("click", closeMenu);
$("#conversation-nav").addEventListener("click", () => { closeMenu(); input.focus(); });
document.addEventListener("keydown", event => {
  if (!document.body.classList.contains("sidebar-open")) return;
  if (event.key === "Escape") { event.preventDefault(); closeMenu(); }
  if (event.key === "Tab") {
    const focusable = Array.from($("#sidebar").querySelectorAll("button:not(:disabled),a[href]")).filter(el => el.getClientRects().length);
    const first = focusable[0], last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
});
window.addEventListener("resize", () => { if (window.innerWidth > 850) closeMenu(); });
AylaVoice.init({
  toast, icon, input, beforeSettings: closeMenu, headers: sessionHeaders, canStart: () => !busy,
  captureState: active => {
    capturing = active; send.disabled = busy || active || !input.value.trim();
    $("#new-chat").disabled = busy || active;
  },
});
function renderWebState() {
  const line = $("#web-mode-state");
  if (!webConsent || !$("#web-enabled").checked) {
    line.textContent = "Web desativada · mensagens não serão pesquisadas. Autorize em Permitir pesquisa web.";
    line.className = "web-mode-state offline";
  } else if (webConfigured === false) {
    line.textContent = "Web autorizada, mas falta a chave · abra Configurar pesquisa.";
    line.className = "web-mode-state warning";
  } else {
    const mode = $("#web-force").checked ? "Pesquisa obrigatória no próximo envio" : "Web autorizada · decisão automática de pesquisa";
    line.textContent = mode + (webTested ? " · conexão testada nesta sessão" : " · conexão ainda não testada");
    line.className = "web-mode-state allowed";
  }
}
async function checkWebStatus() {
  try {
    const status = await request("/api/pesquisa/status");
    webConfigured = Boolean(status.configurada);
    if (!webConfigured) webTested = false;
    $("#web-settings").textContent = webConfigured ? "Pesquisa · configuração" : "Configurar pesquisa";
    $("#web-status-detail").textContent = webConfigured ? "Chave encontrada. Isso não comprova acesso ao serviço: use Testar conexão abaixo." : "Nenhuma chave de pesquisa configurada. A conversa e a calculadora funcionam sem ela.";
  } catch {
    webConfigured = null;
    $("#web-status-detail").textContent = "Não consegui consultar o backend. Confira o servidor.";
  }
  renderWebState();
}
function showWebSettings() { checkWebStatus(); $("#web-dialog").showModal(); }
$("#web-settings").addEventListener("click", () => { pendingWebForce = false; showWebSettings(); });
$("#close-web").addEventListener("click", () => { pendingWebForce = false; $("#web-dialog").close(); });
$("#web-dialog").addEventListener("cancel", () => { pendingWebForce = false; });
$("#recheck-web").addEventListener("click", checkWebStatus);
$("#web-enabled").checked = webConsent;
$("#web-enabled").addEventListener("change", () => {
  if ($("#web-enabled").checked && !webConsent) {
    $("#web-enabled").checked = false; pendingWebForce = false; showWebSettings();
  }
  if (!$("#web-enabled").checked) { saveWebConsent(false); $("#web-force").checked = false; }
  renderWebState();
});
$("#web-force").addEventListener("change", () => {
  if ($("#web-force").checked && (!webConsent || !$("#web-enabled").checked)) {
    pendingWebForce = true; $("#web-force").checked = false; showWebSettings();
  }
  renderWebState();
});
$("#accept-web").addEventListener("click", () => {
  saveWebConsent(true); $("#web-enabled").checked = true;
  if (pendingWebForce) $("#web-force").checked = true;
  pendingWebForce = false; renderWebState(); $("#web-dialog").close();
  toast("Pesquisa autorizada nesta aba, inclusive após atualizar a página. Desative a opção para revogar.");
});
$("#test-web-connection").addEventListener("click", async () => {
  const button = $("#test-web-connection"), result = $("#web-test-result");
  button.disabled = true; result.textContent = "Testando uma consulta pública, sem usar o Qwen nem suas mensagens…";
  try {
    const data = await request("/api/pesquisa/testar", {});
    webTested = Boolean(data.ok); result.textContent = data.mensagem;
  } catch (error) { webTested = false; result.textContent = error.message; }
  finally { button.disabled = false; renderWebState(); }
});
async function initialize() {
  updateCount();
  try { await refreshLists(); } catch { /* O painel mostra seu próprio erro. */ }
  await checkStatus();
  await checkWebStatus();
}
initialize();
