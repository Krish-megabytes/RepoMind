import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Loader2, GitBranch } from 'lucide-react';

interface Props {
  onIngested: (repoName: string) => void;
}

async function ingestRepo(repoUrl: string) {
  const res = await fetch('/api/ingest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || 'Ingestion failed');
  }
  return res.json();
}

export default function RepoInput({ onIngested }: Props) {
  const [url, setUrl] = useState('');

  const mutation = useMutation({
    mutationFn: ingestRepo,
    onSuccess: (data) => onIngested(data.repo_id),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    mutation.mutate(url.trim());
  };

  return (
    <div className="flex flex-col items-center gap-8 mt-16">
      <div className="text-center">
        <GitBranch className="w-16 h-16 mx-auto text-brand-500 mb-4" />
        <h2 className="text-2xl font-semibold">Index a GitHub Repository</h2>
        <p className="text-gray-500 mt-2 max-w-md">
          Enter a public GitHub repository URL and RepoMind will parse, chunk,
          embed, and index the codebase so you can ask questions about it.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="w-full max-w-lg flex gap-2">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/owner/repo"
          className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500"
          required
        />
        <button
          type="submit"
          disabled={mutation.isPending}
          className="bg-brand-600 hover:bg-brand-700 text-white font-medium px-6 py-2 rounded-lg disabled:opacity-50 flex items-center gap-2"
        >
          {mutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
          {mutation.isPending ? 'Indexing…' : 'Index'}
        </button>
      </form>

      {mutation.isError && (
        <p className="text-red-600 text-sm">{(mutation.error as Error).message}</p>
      )}
    </div>
  );
}
