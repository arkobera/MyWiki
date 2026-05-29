import { useState } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export default function Chat() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState("Ask a question about your indexed documents.");
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async (event) => {
    event.preventDefault();
    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      setStatus("Please type a query before sending.");
      return;
    }

    const userMessage = { role: "user", text: trimmedQuery };
    setMessages((current) => [...current, userMessage]);
    setQuery("");
    setStatus("Querying the retrieval pipeline...");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: trimmedQuery }),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Chat request failed.");
      }

      const assistantMessage = {
        role: "assistant",
        text: payload.answer || "No answer was returned.",
        source: payload.document_name ? `${payload.document_name} (${payload.embedding_id})` : null,
      };
      setMessages((current) => [...current, assistantMessage]);
      setStatus("Answer received.");
    } catch (error) {
      setStatus(error.message || "Unable to connect to the chat backend.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full min-h-[420px] flex-col overflow-hidden rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,_rgba(15,23,42,0.95),_rgba(2,6,23,0.96))] shadow-[0_24px_80px_rgba(2,6,23,0.45)]">
      <div className="border-b border-white/8 px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-violet-300/75">Chat</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">Retrieval assistant</h2>
        <p className="mt-2 text-sm text-slate-300">Ask a question and the backend will retrieve from the indexed document embeddings.</p>
      </div>

      <div className="flex min-h-0 flex-1 flex-col px-6 py-5">
        <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-hidden">
          <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto rounded-[24px] border border-white/8 bg-slate-950/50 p-4">
            {messages.length === 0 ? (
              <div className="flex flex-1 items-center justify-center text-sm text-slate-400">
                No chat history yet. Ask something to begin.
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={`rounded-3xl px-4 py-3 shadow-sm ${
                    message.role === "user"
                      ? "self-end bg-white/10 text-white"
                      : "self-start bg-cyan-500/10 text-slate-100"
                  }`}
                >
                  <div className="text-xs uppercase tracking-[0.25em] text-slate-400">
                    {message.role === "user" ? "You" : "Assistant"}
                  </div>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{message.text}</p>
                  {message.source ? (
                    <div className="mt-3 text-[11px] text-slate-400">Source: {message.source}</div>
                  ) : null}
                </div>
              ))
            )}
          </div>

          <div className="rounded-[24px] border border-white/10 bg-slate-950/60 p-4">
            <form onSubmit={handleSend} className="space-y-3">
              <label className="block text-sm font-medium text-slate-300" htmlFor="chat-query">
                Query
              </label>
              <textarea
                id="chat-query"
                rows={4}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="w-full rounded-2xl border border-white/10 bg-slate-900/90 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-300/70 focus:ring-2 focus:ring-cyan-300/20"
                placeholder="Ask a question about the indexed documents..."
              />
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs text-slate-500">{status}</p>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="inline-flex items-center justify-center rounded-2xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isLoading ? "Searching…" : "Send query"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
