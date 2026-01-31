import React from 'react';
import { Box, Text } from 'ink';

export interface DiffLine {
  type: 'context' | 'added' | 'removed' | 'header';
  content: string;
  oldLineNum?: number;
  newLineNum?: number;
}

interface DiffViewProps {
  filename: string;
  lines: DiffLine[];
  /** Show line numbers */
  showLineNumbers?: boolean;
  /** Maximum lines to show before truncating */
  maxLines?: number;
}

// Zen diff colors - soft and easy on the eyes
const COLORS = {
  added: {
    bg: '#1e3a1e',
    fg: '#98c379',
    lineNum: '#4a6a4a',
    marker: '#7a9f7a',
  },
  removed: {
    bg: '#3a1e1e',
    fg: '#e06c75',
    lineNum: '#6a4a4a',
    marker: '#9f7a7a',
  },
  context: {
    bg: undefined,
    fg: '#8a8a8a',
    lineNum: '#4a4a4a',
    marker: '#4a4a4a',
  },
  header: {
    bg: '#2a2a3a',
    fg: '#7a9fc9',
    lineNum: '#4a4a6a',
    marker: '#6a6a8a',
  },
};

function formatLineNum(num: number | undefined, width: number): string {
  if (num === undefined) return ' '.repeat(width);
  return String(num).padStart(width, ' ');
}

export function DiffView({
  filename,
  lines,
  showLineNumbers = true,
  maxLines = 50,
}: DiffViewProps): React.ReactElement {
  // Calculate line number width
  const maxLineNum = Math.max(
    ...lines.map((l) => Math.max(l.oldLineNum || 0, l.newLineNum || 0))
  );
  const lineNumWidth = Math.max(3, String(maxLineNum).length);

  // Truncate if needed
  const displayLines = lines.slice(0, maxLines);
  const truncated = lines.length > maxLines;

  // Count additions and deletions
  const additions = lines.filter((l) => l.type === 'added').length;
  const deletions = lines.filter((l) => l.type === 'removed').length;

  return (
    <Box flexDirection="column" marginY={1}>
      {/* File header */}
      <Box marginBottom={1}>
        <Text color="#6a6a8a" bold>
          {filename}
        </Text>
        <Text color="#4a4a4a"> </Text>
        <Text color="#7a9f7a">+{additions}</Text>
        <Text color="#4a4a4a"> </Text>
        <Text color="#9f7a7a">-{deletions}</Text>
      </Box>

      {/* Diff lines */}
      <Box flexDirection="column" borderStyle="round" borderColor="#3a3a3a">
        {displayLines.map((line, index) => {
          const colors = COLORS[line.type];
          const marker =
            line.type === 'added'
              ? '+'
              : line.type === 'removed'
              ? '-'
              : line.type === 'header'
              ? '@'
              : ' ';

          return (
            <Box key={index}>
              {/* Line numbers */}
              {showLineNumbers && line.type !== 'header' && (
                <>
                  <Text color={colors.lineNum}>
                    {formatLineNum(line.oldLineNum, lineNumWidth)}
                  </Text>
                  <Text color="#2a2a2a"> </Text>
                  <Text color={colors.lineNum}>
                    {formatLineNum(line.newLineNum, lineNumWidth)}
                  </Text>
                  <Text color="#2a2a2a"> │ </Text>
                </>
              )}
              {/* Header spans full width */}
              {line.type === 'header' && showLineNumbers && (
                <Text color={colors.lineNum}>
                  {' '.repeat(lineNumWidth * 2 + 4)}
                </Text>
              )}
              {/* Marker and content */}
              <Text color={colors.marker} backgroundColor={colors.bg}>{marker}</Text>
              <Text color={colors.fg} backgroundColor={colors.bg}> {line.content}</Text>
            </Box>
          );
        })}
      </Box>

      {/* Truncation notice */}
      {truncated && (
        <Box marginTop={1}>
          <Text color="#5a5a5a" dimColor>
            ... {lines.length - maxLines} more lines
          </Text>
        </Box>
      )}
    </Box>
  );
}

/**
 * Parse a unified diff string into DiffLine array
 */
export function parseDiff(diffText: string): DiffLine[] {
  const lines: DiffLine[] = [];
  let oldLineNum = 0;
  let newLineNum = 0;

  for (const line of diffText.split('\n')) {
    if (line.startsWith('@@')) {
      // Parse hunk header: @@ -start,count +start,count @@
      const match = line.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
      if (match) {
        oldLineNum = parseInt(match[1], 10);
        newLineNum = parseInt(match[2], 10);
      }
      lines.push({ type: 'header', content: line });
    } else if (line.startsWith('+') && !line.startsWith('+++')) {
      lines.push({
        type: 'added',
        content: line.slice(1),
        newLineNum: newLineNum++,
      });
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      lines.push({
        type: 'removed',
        content: line.slice(1),
        oldLineNum: oldLineNum++,
      });
    } else if (line.startsWith(' ')) {
      lines.push({
        type: 'context',
        content: line.slice(1),
        oldLineNum: oldLineNum++,
        newLineNum: newLineNum++,
      });
    } else if (line.startsWith('diff ') || line.startsWith('index ')) {
      // Skip diff/index headers
      continue;
    } else if (line.startsWith('---') || line.startsWith('+++')) {
      // Skip file headers
      continue;
    } else if (line.trim()) {
      // Other content as context
      lines.push({
        type: 'context',
        content: line,
        oldLineNum: oldLineNum++,
        newLineNum: newLineNum++,
      });
    }
  }

  return lines;
}
