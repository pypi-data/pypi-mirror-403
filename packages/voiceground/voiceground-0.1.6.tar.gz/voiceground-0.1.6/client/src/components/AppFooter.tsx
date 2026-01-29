import { useAtomValue } from 'jotai';
import { Github } from 'lucide-react';
import { versionAtom } from '@/atoms';

interface AppFooterProps {
  turns: number;
}

const GITHUB_URL = 'https://github.com/poseneror/voiceground';
const GITHUB_ISSUES_URL = 'https://github.com/poseneror/voiceground/issues';

export function AppFooter({ turns }: AppFooterProps) {
  const version = useAtomValue(versionAtom);

  return (
    <footer className="flex-shrink-0 border-t border-border/50 bg-card">
      <div className="px-8">
        {/* Credits and Links */}
        <div className="py-3 flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-4">
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 hover:text-foreground transition-colors"
              aria-label="View Voiceground on GitHub"
            >
              <Github className="w-4 h-4" />
              <span>Voiceground</span>
            </a>
            {version && (
              <span className="text-muted-foreground/60">v{version}</span>
            )}
            {turns > 0 && (
              <span className="text-muted-foreground/60">• {turns} turns</span>
            )}
          </div>
          <a
            href={GITHUB_ISSUES_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-foreground transition-colors"
          >
            Report Issue
          </a>
        </div>
      </div>
    </footer>
  );
}

