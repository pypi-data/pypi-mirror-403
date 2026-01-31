import React, { useState, useEffect } from 'react';
import { Text, Box } from 'ink';
import chalk from 'chalk';

// Spinner frames for running status
const SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

// Colors for different users in multiuser mode
const USER_COLORS = [
  '#d4a574', // orange (default/first user)
  '#7a9fc9', // blue (second user)
  '#9fc97a', // green
  '#c97a9f', // pink
  '#9f7ac9', // purple
];

/**
 * Get a consistent color for a username.
 * Returns orange for "You" (local user), otherwise assigns colors based on name hash.
 */
function getUserColor(name: string | undefined): string {
  if (!name || name === 'You') {
    return USER_COLORS[0]; // orange for local user
  }
  // Simple hash to get consistent color per username
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = ((hash << 5) - hash) + name.charCodeAt(i);
    hash = hash & hash; // Convert to 32-bit integer
  }
  // Start from index 1 to skip orange (reserved for local user)
  const colorIndex = 1 + (Math.abs(hash) % (USER_COLORS.length - 1));
  return USER_COLORS[colorIndex];
}

/**
 * Apply basic syntax highlighting to code using a single-pass tokenizer.
 * This avoids corrupting ANSI codes by processing tokens in order.
 */
function highlightCode(code: string, _lang: string): string {
  // Define token patterns in priority order
  const patterns: Array<{ regex: RegExp; color: string }> = [
    // Comments first (highest priority)
    { regex: /\/\/[^\n]*/g, color: '#5c6370' },
    { regex: /\/\*[\s\S]*?\*\//g, color: '#5c6370' },
    { regex: /#[^\n{]*/g, color: '#5c6370' },
    // Strings
    { regex: /"(?:[^"\\]|\\.)*"/g, color: '#98c379' },
    { regex: /'(?:[^'\\]|\\.)*'/g, color: '#98c379' },
    { regex: /`(?:[^`\\]|\\.)*`/g, color: '#98c379' },
    // Keywords
    { regex: /\b(?:function|const|let|var|if|else|for|while|return|import|export|from|class|extends|new|this|async|await|try|catch|throw|typeof|instanceof|true|false|null|undefined|def|elif|except|finally|lambda|pass|raise|with|yield|None|True|False)\b/g, color: '#c678dd' },
    // Numbers (but not inside words)
    { regex: /(?<![a-zA-Z_])\b\d+\.?\d*\b/g, color: '#d19a66' },
  ];

  // Track which ranges are already highlighted
  const highlighted: Array<{ start: number; end: number; text: string }> = [];

  // Find all matches for each pattern
  for (const { regex, color } of patterns) {
    let match;
    const re = new RegExp(regex.source, regex.flags);
    while ((match = re.exec(code)) !== null) {
      const start = match.index;
      const end = start + match[0].length;

      // Check if this range overlaps with already highlighted ranges
      const overlaps = highlighted.some(h =>
        (start >= h.start && start < h.end) || (end > h.start && end <= h.end)
      );

      if (!overlaps) {
        highlighted.push({
          start,
          end,
          text: chalk.hex(color)(match[0]),
        });
      }
    }
  }

  // Sort by position and build result
  highlighted.sort((a, b) => a.start - b.start);

  let result = '';
  let lastEnd = 0;

  for (const h of highlighted) {
    result += code.slice(lastEnd, h.start);
    result += h.text;
    lastEnd = h.end;
  }
  result += code.slice(lastEnd);

  return result;
}

/**
 * Render markdown tables with box-drawing characters
 * Respects terminal width and truncates long content
 */
function renderTable(tableText: string): string {
  const lines = tableText.trim().split('\n');
  if (lines.length < 2) return tableText;

  // Max table width (leave room for margins)
  const maxTableWidth = 74;

  // Parse rows
  const rows: string[][] = [];
  let isSeparator = -1;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith('|') && line.endsWith('|')) {
      const cells = line.slice(1, -1).split('|').map(c => c.trim());
      // Check if this is the separator row (contains only dashes and colons)
      if (cells.every(c => /^:?-+:?$/.test(c))) {
        isSeparator = i;
      } else {
        rows.push(cells);
      }
    }
  }

  if (rows.length === 0) return tableText;

  const numCols = Math.max(...rows.map(r => r.length));

  // Calculate ideal column widths based on content
  const idealWidths: number[] = new Array(numCols).fill(0);
  for (const row of rows) {
    for (let i = 0; i < row.length; i++) {
      idealWidths[i] = Math.max(idealWidths[i], row[i].length);
    }
  }

  // Calculate available width for content (subtract borders and padding)
  // Each column has: "│ " (2) + content + " " (1), plus final "│" (1)
  const borderOverhead = numCols * 3 + 1;
  const availableWidth = maxTableWidth - borderOverhead;

  // Distribute width among columns
  const totalIdeal = idealWidths.reduce((a, b) => a + b, 0);
  const colWidths: number[] = idealWidths.map(w => {
    if (totalIdeal <= availableWidth) {
      return w; // Content fits, use ideal width
    }
    // Proportionally shrink, but keep minimum of 8 chars
    return Math.max(8, Math.floor((w / totalIdeal) * availableWidth));
  });

  // Truncate helper
  const truncate = (str: string, maxLen: number): string => {
    if (str.length <= maxLen) return str.padEnd(maxLen);
    return str.slice(0, maxLen - 1) + '…';
  };

  // Build table with box-drawing characters
  const topBorder = '┌' + colWidths.map(w => '─'.repeat(w + 2)).join('┬') + '┐';
  const headerSep = '├' + colWidths.map(w => '─'.repeat(w + 2)).join('┼') + '┤';
  const bottomBorder = '└' + colWidths.map(w => '─'.repeat(w + 2)).join('┴') + '┘';

  const formatRow = (row: string[], isHeader: boolean) => {
    const cells = row.map((cell, i) => {
      const width = colWidths[i] || 8;
      const content = truncate(cell, width);
      return isHeader ? chalk.bold(content) : content;
    });
    // Pad missing cells
    while (cells.length < numCols) {
      cells.push(' '.repeat(colWidths[cells.length] || 8));
    }
    return '│ ' + cells.join(' │ ') + ' │';
  };

  const tableLines: string[] = [chalk.dim(topBorder)];

  for (let i = 0; i < rows.length; i++) {
    tableLines.push(formatRow(rows[i], i === 0 && isSeparator === 1));
    if (i === 0 && isSeparator === 1) {
      tableLines.push(chalk.dim(headerSep));
    }
  }

  tableLines.push(chalk.dim(bottomBorder));
  return tableLines.join('\n');
}

/**
 * Simple markdown to styled terminal text converter.
 * Converts common markdown patterns to chalk-styled text.
 * Uses callback functions for proper chalk integration.
 */
function renderMarkdown(text: string): string {
  let result = text;

  // Code blocks ```language\ncode\n``` - render with syntax highlighting and box border
  result = result.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    const trimmedCode = code.trimEnd();
    const highlighted = highlightCode(trimmedCode, lang || '');
    const lines = highlighted.split('\n');

    // Calculate max line width for the box (strip ANSI codes for width calculation)
    const stripAnsi = (str: string) => str.replace(/\x1b\[[0-9;]*m/g, '');
    const maxLineWidth = Math.max(40, ...lines.map((line: string) => stripAnsi(line).length));

    // Pad lines to consistent width and add borders
    const border = chalk.dim('│');
    const formattedLines = lines.map((line: string) => {
      const visibleLength = stripAnsi(line).length;
      const padding = ' '.repeat(maxLineWidth - visibleLength);
      return `  ${border} ${line}${padding} ${border}`;
    }).join('\n');

    // Add top/bottom borders with closing characters
    const topBorder = chalk.dim('  ┌' + '─'.repeat(maxLineWidth + 2) + '┐');
    const bottomBorder = chalk.dim('  └' + '─'.repeat(maxLineWidth + 2) + '┘');

    return '\n' + topBorder + '\n' + formattedLines + '\n' + bottomBorder + '\n';
  });

  // Tables - detect and render markdown tables
  result = result.replace(/((?:^\|.+\|$\n?)+)/gm, (match) => {
    return renderTable(match);
  });

  // Headers - make them bold and colored (use callbacks)
  result = result.replace(/^### (.+)$/gm, (_, h) => chalk.bold.cyan(h));
  result = result.replace(/^## (.+)$/gm, (_, h) => chalk.bold.cyan(h));
  result = result.replace(/^# (.+)$/gm, (_, h) => chalk.bold.cyan(h));

  // Bold text **text** or __text__ (use callbacks)
  result = result.replace(/\*\*(.+?)\*\*/g, (_, t) => chalk.bold(t));
  result = result.replace(/__(.+?)__/g, (_, t) => chalk.bold(t));

  // Italic text *text* or _text_ (but not in middle of words)
  result = result.replace(/(?<!\w)\*([^*]+?)\*(?!\w)/g, (_, t) => chalk.italic(t));
  result = result.replace(/(?<!\w)_([^_]+?)_(?!\w)/g, (_, t) => chalk.italic(t));

  // Inline code `code` (use callback)
  result = result.replace(/`([^`]+)`/g, (_, c) => chalk.hex('#e5c07b')(c));

  // List items - convert * and - at line start to bullets
  result = result.replace(/^[\*\-] (.+)$/gm, '  • $1');

  // Numbered lists - keep numbers but clean up
  result = result.replace(/^(\d+)\. (.+)$/gm, '  $1. $2');

  // Links [text](url) - show text with dimmed URL (use callback)
  result = result.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, text, url) =>
    text + ' ' + chalk.dim('(' + url + ')')
  );

  // Horizontal rules
  result = result.replace(/^[-*_]{3,}$/gm, () => chalk.dim('─'.repeat(40)));

  // Clean up multiple blank lines
  result = result.replace(/\n{3,}/g, '\n\n');

  return result.trim();
}

export type ToolStatus = 'running' | 'complete' | 'error';

interface MessageProps {
  role: 'user' | 'assistant' | 'system' | 'thinking' | 'tool';
  content: string;
  name?: string;
  toolName?: string;
  toolArgs?: Record<string, unknown>;
  success?: boolean;
  /** Tool execution status for activity-style display */
  toolStatus?: ToolStatus;
  /** Indentation level for sub-agent messages (0 = root, 1+ = nested) */
  indentLevel?: number;
}

/**
 * Format tool call label based on tool type
 */
function formatToolLabel(toolName: string, args?: Record<string, unknown>): { label: string; detail?: string } {
  if (!args) {
    return { label: toolName };
  }

  const name = toolName.toLowerCase();

  switch (name) {
    case 'read':
    case 'read_file': {
      const path = args.file_path || args.path;
      if (path) {
        const pathStr = String(path);
        const shortPath = pathStr.length > 60 ? '...' + pathStr.slice(-57) : pathStr;
        return { label: `Read`, detail: shortPath };
      }
      return { label: 'Read file' };
    }

    case 'write':
    case 'write_file': {
      const path = args.file_path || args.path;
      if (path) {
        const pathStr = String(path);
        const shortPath = pathStr.length > 60 ? '...' + pathStr.slice(-57) : pathStr;
        return { label: `Write`, detail: shortPath };
      }
      return { label: 'Write file' };
    }

    case 'edit': {
      const path = args.file_path || args.path;
      if (path) {
        const pathStr = String(path);
        const shortPath = pathStr.length > 50 ? '...' + pathStr.slice(-47) : pathStr;
        return { label: `Update`, detail: shortPath };
      }
      return { label: 'Edit file' };
    }

    case 'bash':
    case 'execute_command': {
      const cmd = args.command ? String(args.command) : '';
      const shortCmd = cmd.length > 80 ? cmd.slice(0, 77) + '...' : cmd;
      return { label: `Bash`, detail: shortCmd };
    }

    case 'glob': {
      const pattern = args.pattern ? String(args.pattern) : '';
      return { label: 'Glob', detail: pattern };
    }

    case 'grep': {
      const pattern = args.pattern ? String(args.pattern) : '';
      return { label: 'Grep', detail: pattern };
    }

    case 'task': {
      const desc = args.description ? String(args.description) : '';
      return { label: 'Task', detail: desc };
    }

    // Todo/Task tools
    case 'taskcreate': {
      const subject = args.subject ? String(args.subject) : '';
      return { label: 'Create Task', detail: subject };
    }

    case 'taskupdate': {
      const taskId = args.taskId ? String(args.taskId) : '';
      const status = args.status ? String(args.status) : '';
      const detail = status ? `#${taskId} → ${status}` : `#${taskId}`;
      return { label: 'Update Task', detail };
    }

    case 'tasklist': {
      return { label: 'List Tasks', detail: '' };
    }

    case 'taskget': {
      const taskId = args.taskId ? String(args.taskId) : '';
      return { label: 'Get Task', detail: `#${taskId}` };
    }

    // Diff tools
    case 'apply_diff':
    case 'applydiff': {
      const path = args.file_path || args.path || '';
      const pathStr = String(path);
      const shortPath = pathStr.length > 50 ? '...' + pathStr.slice(-47) : pathStr;
      return { label: 'Apply Diff', detail: shortPath };
    }

    case 'list_files':
    case 'listfiles': {
      const path = args.path || args.directory || '.';
      return { label: 'List Files', detail: String(path) };
    }

    default:
      return { label: toolName };
  }
}

/**
 * Render task list output in a nice format
 */
function TaskListOutput({ content }: { content: string }): React.ReactElement {
  // Guard against non-string content
  const contentStr = typeof content === 'string' ? content : String(content || '');
  const lines = contentStr.split('\n').filter(l => l.trim());
  const taskLines = lines.slice(0, 5);

  return (
    <Box marginLeft={2} flexDirection="column">
      <Box>
        <Text color="#4a5a4a">└ </Text>
        <Text color="#9a7ac9">{lines.length} task(s)</Text>
      </Box>
      {taskLines.map((line, i) => {
        // Try to parse structured format: #1 [status] subject
        const match = line.match(/#(\d+)\s*\[(\w+)\]\s+(.+)/);
        if (match) {
          const [, id, taskStatus, subject] = match;
          const statusIcon = taskStatus === 'completed' ? '●' : taskStatus === 'in_progress' ? '◐' : '○';
          const statusColor = taskStatus === 'completed' ? '#7a9f7a' : taskStatus === 'in_progress' ? '#c9a075' : '#6a6a6a';
          return (
            <Box key={i} marginLeft={2}>
              <Text color="#5a5a5a">#{id} </Text>
              <Text color={statusColor}>{statusIcon} </Text>
              <Text color={taskStatus === 'completed' ? '#5a5a5a' : '#9a9a9a'}>{subject.slice(0, 50)}{subject.length > 50 ? '...' : ''}</Text>
            </Box>
          );
        }
        // Fallback: just show the line
        return (
          <Box key={i} marginLeft={2}>
            <Text color="#8a8a8a">{line.slice(0, 60)}{line.length > 60 ? '...' : ''}</Text>
          </Box>
        );
      })}
      {lines.length > 5 && (
        <Box marginLeft={2}>
          <Text color="#5a5a5a" dimColor>... {lines.length - 5} more tasks</Text>
        </Box>
      )}
    </Box>
  );
}

/**
 * Render diff output with +/- highlighting
 */
function DiffOutput({ content, toolArgs }: { content?: string; toolArgs?: Record<string, unknown> }): React.ReactElement {
  let diffText = '';

  // For Edit/apply_diff tools, prefer getting diff from toolArgs (has actual content)
  // The result content is usually just a success message
  if (toolArgs) {
    const oldStr = toolArgs.old_string ? String(toolArgs.old_string) : '';
    const newStr = toolArgs.new_string ? String(toolArgs.new_string) : '';
    const diff = toolArgs.diff ? String(toolArgs.diff) : '';

    if (diff) {
      diffText = diff;
    } else if (oldStr || newStr) {
      // Construct a diff view from old/new strings
      const oldLines = oldStr ? oldStr.split('\n').map(l => '- ' + l) : [];
      const newLines = newStr ? newStr.split('\n').map(l => '+ ' + l) : [];
      diffText = [...oldLines, ...newLines].join('\n');
    }
  }

  // Fallback: check if content looks like a diff (has +/- lines)
  if (!diffText && content) {
    const hasAdditions = content.includes('\n+') || content.startsWith('+');
    const hasDeletions = content.includes('\n-') || content.startsWith('-');
    if (hasAdditions || hasDeletions) {
      diffText = content;
    }
  }

  // If still no diff, show a simple success message
  if (!diffText) {
    return (
      <Box marginLeft={2}>
        <Text color="#4a5a4a">└ </Text>
        <Text color="#7a9f7a">✓ Applied</Text>
      </Box>
    );
  }

  const lines = diffText.split('\n');

  // Count additions and deletions
  const added = lines.filter(l => l.startsWith('+') && !l.startsWith('+++')).length;
  const removed = lines.filter(l => l.startsWith('-') && !l.startsWith('---')).length;

  // Get first few changed lines for preview
  const changedLines = lines
    .filter(l => (l.startsWith('+') || l.startsWith('-')) && !l.startsWith('+++') && !l.startsWith('---'))
    .slice(0, 6);

  return (
    <Box marginLeft={2} flexDirection="column">
      <Box>
        <Text color="#4a5a4a">└ </Text>
        <Text color="#7a9f7a">+{added}</Text>
        <Text color="#5a5a5a"> / </Text>
        <Text color="#d47a7a">-{removed}</Text>
        <Text color="#5a5a5a"> lines</Text>
      </Box>
      {changedLines.length > 0 && (
        <Box flexDirection="column" marginLeft={2}>
          {changedLines.map((line, i) => {
            const isAdd = line.startsWith('+');
            const color = isAdd ? '#7a9f7a' : '#d47a7a';
            const displayLine = line.length > 60 ? line.slice(0, 57) + '...' : line;
            return (
              <Box key={i}>
                <Text color={color}>{displayLine}</Text>
              </Box>
            );
          })}
          {lines.filter(l => (l.startsWith('+') || l.startsWith('-')) && !l.startsWith('+++') && !l.startsWith('---')).length > 6 && (
            <Text color="#5a5a5a" dimColor>... more changes</Text>
          )}
        </Box>
      )}
    </Box>
  );
}

/**
 * Running spinner bullet component
 */
function SpinnerBullet({ color = '#c9c97a' }: { color?: string }): React.ReactElement {
  const [frame, setFrame] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setFrame((prev) => (prev + 1) % SPINNER_FRAMES.length);
    }, 80);
    return () => clearInterval(timer);
  }, []);

  return <Text color={color}>{SPINNER_FRAMES[frame]}</Text>;
}

function MessageComponent({ role, content, name, toolName, toolArgs, success, toolStatus, indentLevel = 0 }: MessageProps): React.ReactElement | null {
  // Skip rendering empty non-tool messages
  if (role !== 'tool' && (!content || content.trim().length === 0)) {
    return null;
  }

  // Calculate left margin for sub-agent indentation (2 spaces per level)
  const marginLeft = indentLevel * 2;

  // Skip rendering interactive prompt tools - they're handled by ChoicePrompt component
  if (role === 'tool' && toolName) {
    const lowerName = toolName.toLowerCase();
    if (lowerName === 'ask_choice_questions' || lowerName === 'askuserquestion') {
      return null;
    }
  }

  // Tool messages - compact single-line style to prevent layout shifting
  if (role === 'tool' && toolName) {
    const status = toolStatus || (success === undefined ? 'running' : success ? 'complete' : 'error');
    const { label, detail } = formatToolLabel(toolName, toolArgs);

    // Get bullet based on status
    const bullet = status === 'running' ? (
      <SpinnerBullet />
    ) : status === 'error' ? (
      <Text color="#d47a7a">●</Text>
    ) : (
      <Text color="#7a9f7a">●</Text>
    );

    // Color for label based on tool type
    const isTaskTool = label.includes('Task');
    const isDiffTool = label === 'Apply Diff';
    const labelColor = status === 'error' ? '#d47a7a' :
                       (label === 'Bash' ? '#7a9fc9' :
                        (label === 'Update' || label === 'Write' || isDiffTool ? '#c9a075' :
                         (isTaskTool ? '#9a7ac9' : '#7a9f7a')));

    // Build indent prefix for nested sub-agent messages
    const indentPrefix = indentLevel > 0 ? (
      <Text color="#4a5a4a">{'  '.repeat(indentLevel)}</Text>
    ) : null;

    // Build compact result indicator
    let resultIndicator = null;
    if (status === 'complete') {
      if (label === 'Bash' && content) {
        // Show line count for bash
        const contentStr = typeof content === 'string' ? content : String(content);
        const lineCount = contentStr.split('\n').length;
        resultIndicator = <Text color="#6a6a6a"> → {lineCount} line{lineCount !== 1 ? 's' : ''}</Text>;
      } else if ((label === 'Update' || label === 'Edit') && toolArgs) {
        // Show brief diff stats
        const oldStr = toolArgs.old_string ? String(toolArgs.old_string) : '';
        const newStr = toolArgs.new_string ? String(toolArgs.new_string) : '';
        const added = newStr ? newStr.split('\n').length : 0;
        const removed = oldStr ? oldStr.split('\n').length : 0;
        if (added || removed) {
          resultIndicator = (
            <>
              <Text color="#6a6a6a"> → </Text>
              <Text color="#7a9f7a">+{added}</Text>
              <Text color="#6a6a6a">/</Text>
              <Text color="#d47a7a">-{removed}</Text>
            </>
          );
        }
      } else if (label === 'Write') {
        resultIndicator = <Text color="#7a9f7a"> ✓</Text>;
      } else if (label === 'Create Task' && toolArgs?.subject) {
        resultIndicator = <Text color="#6a6a6a"> → {String(toolArgs.subject).slice(0, 30)}{String(toolArgs.subject).length > 30 ? '...' : ''}</Text>;
      } else if (label === 'Update Task' && toolArgs?.status) {
        const taskStatus = String(toolArgs.status);
        const statusColor = taskStatus === 'completed' ? '#7a9f7a' : taskStatus === 'in_progress' ? '#c9a075' : '#6a6a6a';
        resultIndicator = <Text color={statusColor}> → {taskStatus}</Text>;
      } else if (label === 'List Tasks' && content) {
        const contentStr = typeof content === 'string' ? content : String(content);
        const taskCount = contentStr.split('\n').filter(l => l.trim()).length;
        resultIndicator = <Text color="#6a6a6a"> → {taskCount} task{taskCount !== 1 ? 's' : ''}</Text>;
      } else if (label === 'List Files' && content) {
        const contentStr = typeof content === 'string' ? content : String(content);
        const fileCount = contentStr.split('\n').filter(l => l.trim()).length;
        resultIndicator = <Text color="#6a6a6a"> → {fileCount} file{fileCount !== 1 ? 's' : ''}</Text>;
      }
    } else if (status === 'running') {
      resultIndicator = <Text color="#6a6a6a"> ...</Text>;
    }

    return (
      <Box marginBottom={0}>
        {indentPrefix}
        {bullet}
        <Text> </Text>
        <Text color={labelColor} bold>{label}</Text>
        {detail && (
          <>
            <Text color="#5a5a5a">(</Text>
            <Text color="#9a9a9a">{detail.slice(0, 50)}{detail.length > 50 ? '...' : ''}</Text>
            <Text color="#5a5a5a">)</Text>
          </>
        )}
        {resultIndicator}
      </Box>
    );
  }

  // Thinking messages - static bullet (these are historical, not in-progress)
  if (role === 'thinking') {
    return (
      <Box marginBottom={0}>
        {indentLevel > 0 && <Text color="#4a5a4a">{'  '.repeat(indentLevel)}</Text>}
        <Text color="#6a6a6a">●</Text>
        <Text> </Text>
        <Text color="#8a8aaa" dimColor>
          {content.length > 100 ? content.slice(0, 97) + '...' : content}
        </Text>
      </Box>
    );
  }

  // User messages
  if (role === 'user') {
    const displayName = name || 'You';
    const userColor = getUserColor(name);
    return (
      <Box flexDirection="column" marginBottom={1} marginLeft={indentLevel * 2}>
        <Text color={userColor} bold>{displayName}</Text>
        <Text>{content}</Text>
      </Box>
    );
  }

  // System messages with bullet
  if (role === 'system') {
    return (
      <Box marginBottom={1}>
        {indentLevel > 0 && <Text color="#4a5a4a">{'  '.repeat(indentLevel)}</Text>}
        <Text color="#c9a075">●</Text>
        <Text> </Text>
        <Text color="#c9a075">{content}</Text>
      </Box>
    );
  }

  // Assistant messages - render as styled markdown with bullet
  const rendered = renderMarkdown(content);
  return (
    <Box flexDirection="column" marginBottom={1} marginLeft={indentLevel * 2}>
      <Box>
        <Text color="#7a9f7a">●</Text>
        <Text> </Text>
        <Text>{rendered}</Text>
      </Box>
    </Box>
  );
}

// Memoize to prevent re-renders when parent state changes (e.g., input typing)
export const Message = React.memo(MessageComponent);
