import { useEffect, useRef, useState } from "react";
import {
  getBookAudio,
  getBookImage,
  getConversation,
  getConversations,
  getRecommendation,
} from "./api";

const examples = [
  "Vreau o carte despre libertate și control social.",
  "Ce recomanzi pentru cineva care iubește poveștile fantastice?",
  "Vreau o carte despre magie și prietenie.",
];

function QuestionComposer({ question, setQuestion, handleSubmit, loading }) {
  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <section className="search-panel">
      <form onSubmit={handleSubmit}>
        <label htmlFor="question">Ce ai vrea să citești?</label>
        <div className="input-row">
          <textarea
            id="question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Scrie următoarea întrebare despre cărți..."
            rows="3"
            maxLength="2000"
          />
          <button className="primary-button" type="submit" disabled={loading || !question.trim()}>
            {loading ? "Trimit..." : "Trimite"}
            <span aria-hidden="true">→</span>
          </button>
        </div>
      </form>
      <div className="examples">
        <span>Încearcă:</span>
        {examples.map((example) => (
          <button key={example} type="button" onClick={() => setQuestion(example)}>{example}</button>
        ))}
      </div>
    </section>
  );
}

function App() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [imageLoading, setImageLoading] = useState(false);
  const [audioLoading, setAudioLoading] = useState(false);
  const [image, setImage] = useState("");
  const [audioUrl, setAudioUrl] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [showConversations, setShowConversations] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => () => audioUrl && URL.revokeObjectURL(audioUrl), [audioUrl]);

  useEffect(() => {
    getConversations()
      .then(setConversations)
      .catch(() => setConversations([]));
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [messages]);

  function resetConversation() {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setConversationId(null);
    setConversations((items) => items);
    setMessages([]);
    setResult(null);
    setImage("");
    setAudioUrl("");
    setError("");
    setQuestion("");
    setShowConversations(false);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || loading) return;

    setLoading(true);
    setQuestion("");
    setError("");
    setImage("");
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl("");

    try {
      const response = await getRecommendation(trimmedQuestion, conversationId);
      setConversationId(response.conversation_id);
      setResult(response);
      setMessages((items) => [
        ...items,
        { role: "user", content: trimmedQuestion },
        { role: "assistant", content: response.recommendation, result: response },
      ]);
      setConversations(await getConversations());
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleLoadConversation(id) {
    if (loading || id === conversationId) return;

    setError("");
    try {
      const conversation = await getConversation(id);
      const latestResult = [...conversation.messages]
        .reverse()
        .find((message) => message.role === "assistant" && message.result)?.result;
      setConversationId(conversation.id);
      setMessages(conversation.messages);
      setResult(latestResult || null);
      setQuestion("");
      setImage("");
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      setAudioUrl("");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function handleImage() {
    if (!result || imageLoading) return;
    setImageLoading(true);
    setError("");
    try {
      const response = await getBookImage(result.title);
      setImage(response.image);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setImageLoading(false);
    }
  }

  async function handleAudio() {
    if (!result || audioLoading) return;
    setAudioLoading(true);
    setError("");
    try {
      const blob = await getBookAudio(result.recommendation, result.summary);
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      setAudioUrl(URL.createObjectURL(blob));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setAudioLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <header className="topbar">
        <div className="brand-mark">SL</div>
        <div>
          <p className="eyebrow">RAG · TOOL CALLING · OPENAI</p>
          <h1>Smart Librarian</h1>
        </div>
        <button
          className="conversations-tab"
          type="button"
          onClick={() => setShowConversations((visible) => !visible)}
          aria-expanded={showConversations}
        >
          Conversații <span>{conversations.length}</span>
        </button>
        <span className="status-pill"><span /> ONLINE</span>
      </header>

      {showConversations && (
        <section className="conversation-bar">
          <div>
            <p className="section-label">CONVERSAȚIILE TALE</p>
            <p className="conversation-note">Întrebările și recomandările sunt salvate local.</p>
          </div>
          <button className="new-conversation" type="button" onClick={resetConversation}>
            + Conversație nouă
          </button>
          {conversations.length > 0 ? (
            <div className="conversation-list">
              {conversations.map((conversation) => (
                <button
                  className={conversation.id === conversationId ? "conversation-item active" : "conversation-item"}
                  key={conversation.id}
                  type="button"
                  onClick={() => handleLoadConversation(conversation.id)}
                >
                  <strong>{conversation.title}</strong>
                  <span>{conversation.message_count} mesaje</span>
                </button>
              ))}
            </div>
          ) : (
            <p className="empty-conversations">Nu ai încă conversații salvate.</p>
          )}
        </section>
      )}

      <section className="intro-grid">
        <div className="intro-copy">
          <p className="section-label">BIBLIOTECA PERSONALĂ</p>
          <h2>Găsește următoarea carte care merită timpul tău.</h2>
          <p className="intro-text">
            Spune-mi ce vrei să citești. Caut în colecția semantică, aleg titlul potrivit
            și îți aduc rezumatul complet.
          </p>
        </div>
        <div className="book-spine" aria-hidden="true">
          <span>READ<br />WIDELY</span>
          <b>✦</b>
        </div>
      </section>

      {!result && (
        <QuestionComposer
          question={question}
          setQuestion={setQuestion}
          handleSubmit={handleSubmit}
          loading={loading}
        />
      )}

      {messages.length > 0 && (
        <section className="conversation-log" aria-label="Istoricul conversației">
          <div className="card-kicker">CHATUL TĂU CU LIBRARIANUL</div>
          {messages.map((message, index) => (
            <div className={`message ${message.role}`} key={`${message.role}-${index}`}>
              <span>{message.role === "user" ? "TU" : "LIBRARIAN"}</span>
              <div className="message-bubble">
                <p>{message.content}</p>
                {message.result?.summary && (
                  <p className="message-summary">
                    <strong>Rezumat:</strong> {message.result.summary}
                  </p>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </section>
      )}

      {error && <div className="error-message" role="alert">{error}</div>}

      {loading && <div className="loading-line"><span /> Analizez preferințele și caut în colecție...</div>}

      {result && (
        <section className="result-grid" aria-live="polite">
          <article className="recommendation-card">
            <div className="card-kicker">RECOMANDAREA TA</div>
            <div className="title-row">
              <div>
                <h2>{result.title}</h2>
                <p className="author">de {result.author}</p>
              </div>
              <div className="book-icon" aria-hidden="true">▤</div>
            </div>
            <div className="themes">
              {result.themes.map((theme) => <span key={theme}>{theme}</span>)}
            </div>
            <p className="recommendation-text">{result.recommendation}</p>
            <div className="actions">
              <button type="button" onClick={handleImage} disabled={imageLoading}>
                <span>▧</span> {imageLoading ? "Se generează..." : "Generează imagine"}
              </button>
              <button type="button" onClick={handleAudio} disabled={audioLoading}>
                <span>◉</span> {audioLoading ? "Se generează..." : "Ascultă recomandarea"}
              </button>
            </div>
            {audioUrl && <audio className="audio-player" controls src={audioUrl} />}
          </article>

          <article className="summary-card">
            <div className="card-kicker">REZUMAT COMPLET</div>
            <p>{result.summary}</p>
          </article>

          {image && (
            <figure className="image-card">
              <img src={image} alt={`Ilustrație inspirată de ${result.title}`} />
              <figcaption>O atmosferă inspirată de {result.title}</figcaption>
            </figure>
          )}
        </section>
      )}

      {result && (
        <QuestionComposer
          question={question}
          setQuestion={setQuestion}
          handleSubmit={handleSubmit}
          loading={loading}
        />
      )}

      <footer><span>SMART LIBRARIAN</span><span>Doar despre cărți. Mereu curios.</span></footer>
    </main>
  );
}

export default App;
