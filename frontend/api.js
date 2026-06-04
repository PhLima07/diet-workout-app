const BASE = "";

async function _parseError(res) {
  const text = await res.text();
  try { return JSON.parse(text).detail || res.statusText; } catch { return text.slice(0, 200) || res.statusText; }
}

async function apiPost(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await getAuthHeaders()) },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await _parseError(res));
  return res.json();
}

async function apiGet(path) {
  const res = await fetch(`${BASE}${path}`, {
    headers: await getAuthHeaders(),
  });
  if (!res.ok) throw new Error(await _parseError(res));
  return res.json();
}

async function apiPut(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...(await getAuthHeaders()) },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await _parseError(res));
  return res.json();
}
