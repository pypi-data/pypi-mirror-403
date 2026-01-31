import React from 'react';
import { Text, Box } from 'ink';
import { highlight } from 'cli-highlight';

interface CodeBlockProps {
  code: string;
  language?: string;
  showLineNumbers?: boolean;
}

export function CodeBlock({ code, language, showLineNumbers = false }: CodeBlockProps): React.ReactElement {
  const renderCode = (): string => {
    try {
      if (language) {
        return highlight(code, { language, ignoreIllegals: true });
      }
      return highlight(code, { ignoreIllegals: true });
    } catch {
      return code;
    }
  };

  const lines = renderCode().split('\n');

  if (showLineNumbers) {
    const maxLineNum = lines.length.toString().length;
    return (
      <Box flexDirection="column" borderStyle="round" borderColor="#4a5a4a" paddingX={1}>
        {lines.map((line, i) => (
          <Text key={i}>
            <Text color="#6a6a6a">{(i + 1).toString().padStart(maxLineNum, ' ')}</Text>
            <Text color="#4a5a4a"> │ </Text>
            <Text>{line}</Text>
          </Text>
        ))}
      </Box>
    );
  }

  return (
    <Box borderStyle="round" borderColor="#4a5a4a" paddingX={1}>
      <Text>{renderCode()}</Text>
    </Box>
  );
}
