const { createClient } = supabase;
const _sb = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

async function getSession() {
  const { data } = await _sb.auth.getSession();
  return data.session;
}

async function getAuthHeaders() {
  const session = await getSession();
  if (!session) return {};
  return { Authorization: `Bearer ${session.access_token}` };
}

async function requireAuth() {
  const session = await getSession();
  if (!session) {
    window.location.href = "/login.html";
    return null;
  }
  return session;
}

async function logout() {
  await _sb.auth.signOut();
  window.location.href = "/login.html";
}
