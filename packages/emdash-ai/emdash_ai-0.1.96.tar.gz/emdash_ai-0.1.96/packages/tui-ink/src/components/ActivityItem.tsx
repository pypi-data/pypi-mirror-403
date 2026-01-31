import React, { useState, useEffect } from 'react';
import { Text, Box } from 'ink';

export type ActivityStatus = 'running' | 'complete' | 'error' | 'pending';
export type ActivityType = 'text' | 'read' | 'write' | 'edit' | 'bash' | 'search' | 'tool' | 'thinking';

interface ActivityItemProps {
  /** Type of activity for icon/color selection */
  type: ActivityType;
  /** Main label text (e.g., "Read 2 files", "Bash(npm run build)") */
  label: string;
  /** Current status */
  status: ActivityStatus;
  /** Optional detail/summary shown inline (e.g., "(ctrl+o to expand)") */
  hint?: string;
  /** Optional metadata shown on right (e.g., "timeout: 1m 0s") */
  metadata?: string;
  /** Content to show expanded (code diff, output, etc.) */
  content?: string;
  /** Whether content is initially expanded */
  defaultExpanded?: boolean;
  /** Number of nested items (shows as indented) */
  indent?: number;
  /** For edit activities, show diff-style content */
  isDiff?: boolean;
  /** Optional: lines added */
  linesAdded?: number;
  /** Optional: lines removed */
  linesRemoved?: number;
}

// Spinner frames for running status
const SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

// Colors for different activity types
const TYPE_COLORS: Record<ActivityType, string> = {
  text: '#7a9f7a',      // Green
  read: '#7a9f7a',      // Green
  write: '#c9a075',     // Orange
  edit: '#c9a075',      // Orange
  bash: '#7a9fc9',      // Blue
  search: '#9f7a9f',    // Purple
  tool: '#7a9f7a',      // Green
  thinking: '#8a8aaa',  // Gray-purple
};

// Status colors
const STATUS_COLORS: Record<ActivityStatus, string> = {
  running: '#c9c97a',   // Yellow
  complete: '#7a9f7a',  // Green
  error: '#d47a7a',     // Red
  pending: '#6a6a6a',   // Gray
};

/**
 * Render diff-style content with syntax highlighting
 */
function renderDiffContent(content: string): React.ReactElement {
  const lines = content.split('\n');

  return (
    <Box flexDirection="column" marginLeft={2} marginTop={0}>
      {lines.map((line, i) => {
        let color = '#b0b0b0';  // Default gray
        let prefix = ' ';

        if (line.startsWith('+')) {
          color = '#7a9f7a';  // Green for additions
          prefix = '';
        } else if (line.startsWith('-')) {
          color = '#d47a7a';  // Red for deletions
          prefix = '';
        } else if (line.match(/^\d+\s/)) {
          // Line number
          color = '#6a6a6a';
          prefix = '';
        }

        return (
          <Text key={i} color={color}>
            {prefix}{line}
          </Text>
        );
      })}
    </Box>
  );
}

/**
 * Render code/output content
 */
function renderContent(content: string, isDiff?: boolean): React.ReactElement {
  if (isDiff) {
    return renderDiffContent(content);
  }

  const lines = content.split('\n');
  return (
    <Box flexDirection="column" marginLeft={2}>
      {lines.slice(0, 10).map((line, i) => (
        <Text key={i} color="#a0a0a0">
          {line}
        </Text>
      ))}
      {lines.length > 10 && (
        <Text color="#6a6a6a" dimColor>
          ... {lines.length - 10} more lines
        </Text>
      )}
    </Box>
  );
}

export function ActivityItem({
  type,
  label,
  status,
  hint,
  metadata,
  content,
  defaultExpanded = false,
  indent = 0,
  isDiff = false,
  linesAdded,
  linesRemoved,
}: ActivityItemProps): React.ReactElement {
  const [spinnerFrame, setSpinnerFrame] = useState(0);
  const [expanded, setExpanded] = useState(defaultExpanded);

  // Animate spinner when running
  useEffect(() => {
    if (status !== 'running') return;

    const timer = setInterval(() => {
      setSpinnerFrame((prev) => (prev + 1) % SPINNER_FRAMES.length);
    }, 80);

    return () => clearInterval(timer);
  }, [status]);

  // Get bullet/icon based on status
  const getBullet = (): React.ReactElement => {
    if (status === 'running') {
      return (
        <Text color={STATUS_COLORS.running}>
          {SPINNER_FRAMES[spinnerFrame]}
        </Text>
      );
    }

    const bulletColor = status === 'error' ? STATUS_COLORS.error : STATUS_COLORS.complete;
    return <Text color={bulletColor}>●</Text>;
  };

  // Build the label with syntax highlighting for tool calls
  const renderLabel = (): React.ReactElement => {
    const color = TYPE_COLORS[type] || '#b0b0b0';

    // Check if label contains parentheses (tool call style)
    const match = label.match(/^(\w+)\((.+)\)$/);
    if (match) {
      const [, toolName, args] = match;
      return (
        <Text>
          <Text color={color} bold>{toolName}</Text>
          <Text color="#6a6a6a">(</Text>
          <Text color="#b0b0b0">{args}</Text>
          <Text color="#6a6a6a">)</Text>
        </Text>
      );
    }

    return <Text color={color}>{label}</Text>;
  };

  // Build change summary for edits
  const renderChangeSummary = (): React.ReactElement | null => {
    if (linesAdded === undefined && linesRemoved === undefined) return null;

    return (
      <Box marginLeft={1}>
        {linesAdded !== undefined && linesAdded > 0 && (
          <Text color="#7a9f7a">+{linesAdded}</Text>
        )}
        {linesAdded !== undefined && linesRemoved !== undefined && (
          <Text color="#6a6a6a">/</Text>
        )}
        {linesRemoved !== undefined && linesRemoved > 0 && (
          <Text color="#d47a7a">-{linesRemoved}</Text>
        )}
      </Box>
    );
  };

  return (
    <Box flexDirection="column">
      {/* Main line */}
      <Box marginLeft={indent * 2}>
        {getBullet()}
        <Text> </Text>
        {renderLabel()}
        {hint && (
          <Text color="#6a6a6a" dimColor> {hint}</Text>
        )}
        {renderChangeSummary()}
        {metadata && (
          <Text color="#6a6a6a" dimColor> {metadata}</Text>
        )}
      </Box>

      {/* Nested content indicator for running items */}
      {status === 'running' && !content && (
        <Box marginLeft={indent * 2 + 2}>
          <Text color="#6a6a6a">└ </Text>
          <Text color="#8a8aaa">Running...</Text>
        </Box>
      )}

      {/* Expanded content */}
      {content && (expanded || status === 'running') && (
        <Box marginLeft={indent * 2}>
          {renderContent(content, isDiff)}
        </Box>
      )}
    </Box>
  );
}

/**
 * A group of related activity items (e.g., multiple file reads)
 */
interface ActivityGroupProps {
  /** Summary label (e.g., "Read 3 files") */
  label: string;
  /** Status of the group */
  status: ActivityStatus;
  /** Hint text */
  hint?: string;
  /** Child activities */
  children?: React.ReactNode;
}

export function ActivityGroup({
  label,
  status,
  hint,
  children,
}: ActivityGroupProps): React.ReactElement {
  const [spinnerFrame, setSpinnerFrame] = useState(0);

  useEffect(() => {
    if (status !== 'running') return;
    const timer = setInterval(() => {
      setSpinnerFrame((prev) => (prev + 1) % SPINNER_FRAMES.length);
    }, 80);
    return () => clearInterval(timer);
  }, [status]);

  const getBullet = (): React.ReactElement => {
    if (status === 'running') {
      return <Text color={STATUS_COLORS.running}>{SPINNER_FRAMES[spinnerFrame]}</Text>;
    }
    return <Text color={STATUS_COLORS.complete}>●</Text>;
  };

  return (
    <Box flexDirection="column">
      <Box>
        {getBullet()}
        <Text> </Text>
        <Text color="#7a9f7a">{label}</Text>
        {hint && <Text color="#6a6a6a" dimColor> {hint}</Text>}
      </Box>
      {children && (
        <Box flexDirection="column" marginLeft={2}>
          {children}
        </Box>
      )}
    </Box>
  );
}
