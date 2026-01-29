import React, { useEffect, useRef } from 'react';
import {
  MYSQL_ICON,
  POSTGRESQL_ICON,
  SNOWFLAKE_ICON
} from '../common/databaseIcons';

export type DatabaseType = 'postgresql' | 'mysql' | 'snowflake';

export interface WelcomeCTAContentProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onSendMessage: (message: string) => void;
  onFileUpload: () => void;
  onDatabaseClick: (dbType: DatabaseType) => void;
}

// Component to render LabIcon as React element
function DatabaseIcon({ icon }: { icon: typeof POSTGRESQL_ICON }): JSX.Element {
  const containerRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.innerHTML = '';
      const el = icon.element({ tag: 'span' });
      containerRef.current.appendChild(el);
    }
  }, [icon]);

  return <span ref={containerRef} className="db-icon" />;
}

export function WelcomeCTAContent({
  isCollapsed,
  onToggleCollapse,
  onSendMessage,
  onFileUpload,
  onDatabaseClick
}: WelcomeCTAContentProps): JSX.Element {
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleInput = () => {
    const input = inputRef.current;
    if (input) {
      input.style.height = 'auto';
      const newHeight = Math.min(input.scrollHeight, 120);
      input.style.height = newHeight + 'px';
    }
  };

  const handleSend = () => {
    const input = inputRef.current;
    if (input) {
      const message = input.value.trim();
      if (message) {
        onSendMessage(message);
        input.value = '';
        input.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Stop propagation to prevent JupyterLab shortcuts
    e.stopPropagation();
    // Handle Enter key for sending
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleKeyUp = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    e.stopPropagation();
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    e.stopPropagation();
  };

  const handleCardKeyDown = (
    e: React.KeyboardEvent<HTMLDivElement>,
    action: () => void
  ) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      action();
    }
  };

  return (
    <>
      <div className="sage-ai-data-cta-content">
        <div className="sage-ai-data-cta-header">
          {/* <h3 className="sage-ai-data-cta-title">Welcome to SignalPilot!</h3> */}
          <div className="sage-ai-data-cta-subtitle">
            Let's get started by asking a question or connecting your data
          </div>
        </div>

        <div className="sage-ai-data-cta-chat-section">
          <div className="sage-ai-data-cta-chat-label">
            <svg
              className="chat-icon"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
            >
              <path
                d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span>Ask a Question</span>
          </div>
          <div className="sage-ai-data-cta-chat-wrapper">
            <textarea
              ref={inputRef}
              className="sage-ai-data-cta-input"
              placeholder="What would you like to know? Ask me anything about your data, analytics, or insights..."
              rows={1}
              onInput={handleInput}
              onKeyDown={handleKeyDown}
              onKeyUp={handleKeyUp}
              onKeyPress={handleKeyPress}
            />
            <button
              className="sage-ai-data-cta-send-btn"
              title="Send message (Enter)"
              onClick={handleSend}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path
                  d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
        </div>

        <div className="sage-ai-data-connect-section">
          <div className="sage-ai-data-section-title">
            <svg
              className="section-icon"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
            >
              <path
                d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <polyline
                points="13 2 13 9 20 9"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span>Connect Your Data</span>
          </div>

          <div className="sage-ai-data-db-section">
            <div className="sage-ai-data-db-label">Connect to Database</div>
            <div className="sage-ai-data-db-grid">
              <div
                className="sage-ai-data-db-card postgresql"
                data-db-type="postgresql"
                role="button"
                tabIndex={0}
                onClick={() => onDatabaseClick('postgresql')}
                onKeyDown={e =>
                  handleCardKeyDown(e, () => onDatabaseClick('postgresql'))
                }
              >
                <div className="db-card-header">
                  <DatabaseIcon icon={POSTGRESQL_ICON} />
                  <div className="db-name">PostgreSQL</div>
                </div>
                <div className="db-description">
                  Powerful relational database
                </div>
              </div>

              <div
                className="sage-ai-data-db-card mysql"
                data-db-type="mysql"
                role="button"
                tabIndex={0}
                onClick={() => onDatabaseClick('mysql')}
                onKeyDown={e =>
                  handleCardKeyDown(e, () => onDatabaseClick('mysql'))
                }
              >
                <div className="db-card-header">
                  <DatabaseIcon icon={MYSQL_ICON} />
                  <div className="db-name">MySQL</div>
                </div>
                <div className="db-description">Popular open-source DB</div>
              </div>

              <div
                className="sage-ai-data-db-card snowflake"
                data-db-type="snowflake"
                role="button"
                tabIndex={0}
                onClick={() => onDatabaseClick('snowflake')}
                onKeyDown={e =>
                  handleCardKeyDown(e, () => onDatabaseClick('snowflake'))
                }
              >
                <div className="db-card-header">
                  <DatabaseIcon icon={SNOWFLAKE_ICON} />
                  <div className="db-name">Snowflake</div>
                </div>
                <div className="db-description">Cloud data warehouse</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <button
        className="sage-ai-data-cta-toggle"
        title={isCollapsed ? 'Expand' : 'Collapse'}
        aria-label="Toggle CTA visibility"
        onClick={onToggleCollapse}
      >
        <svg
          className="toggle-icon"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
        >
          <path
            d="M18 15l-6-6-6 6"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
    </>
  );
}
