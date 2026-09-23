import { Brain } from 'lucide-react';

export default function Header() {
  return (
    <header className="bg-brand-700 text-white shadow-md">
      <div className="max-w-4xl mx-auto flex items-center gap-3 px-4 py-4">
        <Brain className="w-8 h-8" />
        <h1 className="text-xl font-bold tracking-tight">RepoMind</h1>
        <span className="text-sm opacity-75 ml-2">GitHub Repository Intelligence</span>
      </div>
    </header>
  );
}
