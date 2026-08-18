const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "Serverul nu a putut procesa cererea.");
  }

  return response;
}

export async function getRecommendation(question, conversationId = null) {
  const response = await request("/recommend", {
    method: "POST",
    body: JSON.stringify({ question, conversation_id: conversationId }),
  });
  return response.json();
}

export async function getConversations() {
  const response = await request("/conversations");
  return response.json();
}

export async function getConversation(conversationId) {
  const response = await request(`/conversations/${conversationId}`);
  return response.json();
}

export async function getBookImage(title) {
  const response = await request("/image", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
  return response.json();
}

export async function getBookAudio(recommendation, summary) {
  const response = await request("/audio", {
    method: "POST",
    body: JSON.stringify({ recommendation, summary }),
  });
  return response.blob();
}
