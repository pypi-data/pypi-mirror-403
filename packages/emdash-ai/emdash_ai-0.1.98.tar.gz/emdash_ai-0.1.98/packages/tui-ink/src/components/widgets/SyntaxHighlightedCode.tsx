import React from 'react';
import { Box, Text } from 'ink';
import chalk from 'chalk';

interface CodeBlockProps {
  code: string;
  language?: string;
  showLineNumbers?: boolean;
  maxLines?: number;
  filename?: string;
}

// One Dark theme colors
const COLORS = {
  background: '#282c34',
  text: '#abb2bf',
  comment: '#5c6370',
  string: '#98c379',
  keyword: '#c678dd',
  function: '#61afef',
  number: '#d19a66',
  operator: '#56b6c2',
  variable: '#e06c75',
  lineNum: '#4a4a4a',
  border: '#3a3a3a',
};

/**
 * Apply syntax highlighting to code
 */
function highlightCode(code: string, lang: string): string {
  let result = code;

  // Strings first (to avoid conflicts)
  result = result.replace(/("(?:[^"\\]|\\.)*")/g, chalk.hex(COLORS.string)('$1'));
  result = result.replace(/('(?:[^'\\]|\\.)*')/g, chalk.hex(COLORS.string)('$1'));
  result = result.replace(/(`(?:[^`\\]|\\.)*`)/g, chalk.hex(COLORS.string)('$1'));

  // Comments
  result = result.replace(/(\/\/.*$)/gm, chalk.hex(COLORS.comment)('$1'));
  result = result.replace(/(\/\*[\s\S]*?\*\/)/g, chalk.hex(COLORS.comment)('$1'));
  result = result.replace(/(#[^{!\[].*$)/gm, chalk.hex(COLORS.comment)('$1'));

  // Keywords
  const keywords = [
    'function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return',
    'import', 'export', 'from', 'class', 'extends', 'new', 'this', 'async',
    'await', 'try', 'catch', 'throw', 'typeof', 'instanceof', 'true', 'false',
    'null', 'undefined', 'def', 'elif', 'except', 'finally', 'lambda', 'pass',
    'raise', 'with', 'yield', 'None', 'True', 'False', 'self', 'cls',
  ];
  const keywordRegex = new RegExp(`\\b(${keywords.join('|')})\\b`, 'g');
  result = result.replace(keywordRegex, chalk.hex(COLORS.keyword)('$1'));

  // Function calls
  result = result.replace(/\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(/g, chalk.hex(COLORS.function)('$1') + '(');

  // Numbers
  result = result.replace(/\b(\d+\.?\d*)\b/g, chalk.hex(COLORS.number)('$1'));

  return result;
}

export function CodeBlock({
  code,
  language,
  showLineNumbers = true,
  maxLines,
  filename,
}: CodeBlockProps): React.ReactElement {
  const lines = code.trimEnd().split('\n');
  const displayLines = maxLines ? lines.slice(0, maxLines) : lines;
  const truncated = maxLines && lines.length > maxLines;
  const lineNumWidth = String(lines.length).length;

  const bg = chalk.bgHex(COLORS.background);

  return (
    <Box flexDirection="column" marginY={1}>
      {/* Header with filename/language */}
      {(filename || language) && (
        <Box>
          <Text backgroundColor={COLORS.background} color={COLORS.text}>
            {' '}
            {filename && <Text color="#7a9fc9">{filename}</Text>}
            {filename && language && <Text color="#4a4a4a"> · </Text>}
            {language && <Text color="#5a5a5a">{language}</Text>}
            {' '}
          </Text>
        </Box>
      )}

      {/* Code content */}
      <Box flexDirection="column" borderStyle="round" borderColor={COLORS.border}>
        {displayLines.map((line, index) => {
          const highlighted = highlightCode(line, language || '');
          const lineNum = index + 1;

          return (
            <Box key={index}>
              <Text>
                {bg(
                  (showLineNumbers
                    ? chalk.hex(COLORS.lineNum)(String(lineNum).padStart(lineNumWidth, ' ')) + ' │ '
                    : '  ') +
                  highlighted +
                  '  '
                )}
              </Text>
            </Box>
          );
        })}
      </Box>

      {/* Truncation notice */}
      {truncated && (
        <Box>
          <Text color="#5a5a5a" dimColor>
            ... {lines.length - maxLines!} more lines
          </Text>
        </Box>
      )}
    </Box>
  );
}
