import { useState } from 'react';
import RepoInput from './components/RepoInput';
import ChatView from './components/ChatView';
import Header from './components/Header';

type Screen = 'input' | 'chat';

export default function App() {
  const [screen, setScreen] = useState<Screen>('input');
  const [repoName, setRepoName] = useState('');

  const handleIngested = (name: string) => {
    setRepoName(name);
    setScreen('chat');
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-8">
        {screen === 'input' && <RepoInput onIngested={handleIngested} />}
        {screen === 'chat' && (
          <ChatView
            repoName={repoName}
            onBack={() => setScreen('input')}
          />
        )}
      </main>
    </div>
  );
}
