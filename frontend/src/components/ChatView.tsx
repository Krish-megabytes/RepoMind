import { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Send, ArrowLeft, FileCode, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Props {
  repoName: string;
  onBack: () => void;
}

interface Citation {
  file: string;
  start_line: number;
  end_line: number;
  language: string;
  content: string;
}

interface Message {
  role: 'user' | 'assistant';
  text: string;
  citations?: Citation[];
}

async function queryRepo(repository: string, question: string) {
  const res = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository, question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || 'Query failed');
  }
  return res.json();
}

export default function ChatView({ repoName, onBack }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [expandedCitation, setExpandedCitation] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const mutation = useMutation({
    mutationFn: (question: string) => queryRepo(repoName, question),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: data.answer, citations: data.citations },
      ]);
    },
    onError: (err: Error) => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: `Error: ${err.message}` },
      ]);
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || mutation.isPending) return;
    const q = input.trim();
    setMessages((prev) => [...prev, { role: 'user', text: q }]);
    setInput('');
    mutation.mutate(q);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-120px)]">
      {/* Top bar */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <button onClick={onBack} className="text-gray-500 hover:text-gray-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <span className="font-semibold text-lg">{repoName}</span>
        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
          Indexed
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-center text-gray-400 mt-12">
            Ask a question about <strong>{repoName}</strong>
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-brand-600 text-white'
                  : 'bg-white border shadow-sm'
              }`}
            >
              <ReactMarkdown className="prose prose-sm max-w-none">
                {msg.text}
              </ReactMarkdown>

              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 space-y-2">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Sources
                  </p>
                  {msg.citations.map((c, ci) => (
                    <button
                      key={ci}
                      onClick={() =>
                        setExpandedCitation(expandedCitation === ci ? null : ci)
                      }
                      className="flex items-center gap-2 text-xs text-brand-600 hover:underline w-full text-left"
                    >
                      <FileCode className="w-3.5 h-3.5" />
                      {c.file} (L{c.start_line}–{c.end_line})
                    </button>
                  ))}
                  {expandedCitation !== null && msg.citations[expandedCitation] && (
                    <pre className="text-xs bg-gray-900 text-green-300 p-3 rounded-md overflow-x-auto mt-1">
                      {msg.citations[expandedCitation].content?.slice(0, 1000)}
                    </pre>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        {mutation.isPending && (
          <div className="flex justify-start">
            <div className="bg-white border shadow-sm rounded-xl px-4 py-3 flex items-center gap-2 text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" /> Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSend}
        className="flex gap-2 pt-4 border-t"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about the codebase…"
          className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <button
          type="submit"
          disabled={mutation.isPending || !input.trim()}
          className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
}
