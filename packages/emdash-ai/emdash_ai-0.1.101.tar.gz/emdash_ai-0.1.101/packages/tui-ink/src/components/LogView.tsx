import React from 'react';
import { Box, Text } from 'ink';
import { Message } from './Message.js';
import { Welcome } from './Welcome.js';
import { Spinner } from './Spinner.js';
import type { LogEntry } from '../store.js';

interface LogViewProps {
  log: LogEntry[];
  streamResponse: string;
  isProcessing: boolean;
  currentThinking: string;
  cwd: string;
  maxLines: number;
}

function LogViewComponent({
  log,
  streamResponse,
  isProcessing,
  currentThinking,
  cwd,
  maxLines,
}: LogViewProps): React.ReactElement {
  // Show last N entries
  const visibleLog = log.slice(-maxLines);

  return (
    <Box flexDirection="column" flexGrow={1} paddingX={1} overflowY="hidden">
      {/* Welcome screen */}
      {visibleLog.length === 0 && !streamResponse && !isProcessing && (
        <Welcome cwd={cwd} />
      )}

      {/* Hidden messages indicator */}
      {log.length > maxLines && (
        <Box marginBottom={1}>
          <Text color="#4a4a4a">
            ↑ {log.length - maxLines} earlier messages
          </Text>
        </Box>
      )}

      {/* Visible log entries */}
      {visibleLog.map((entry) => (
        <Message
          key={entry.id}
          role={entry.role}
          content={entry.content}
          name={entry.name}
          toolName={entry.toolName}
          toolArgs={entry.toolArgs}
          success={entry.success}
          toolStatus={entry.toolStatus}
          indentLevel={entry.indentLevel}
        />
      ))}

      {/* Streaming response */}
      {streamResponse && (
        <Message role="assistant" content={streamResponse} />
      )}

      {/* Loading spinner */}
      {isProcessing && !streamResponse && (
        <Box>
          <Spinner text={currentThinking ? 'thinking' : 'processing'} />
        </Box>
      )}
    </Box>
  );
}

// Memoize to prevent re-renders when typing in command menu
export const LogView = React.memo(LogViewComponent);
