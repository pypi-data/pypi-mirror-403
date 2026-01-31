import React, { useState } from 'react';
import { Text, Box, useInput } from 'ink';

interface ApprovalPromptProps {
  onApprove: () => void;
  onReject: () => void;
  onReply: (message: string) => void;
}

type Mode = 'select' | 'reply';

export function ApprovalPrompt({ onApprove, onReject, onReply }: ApprovalPromptProps): React.ReactElement {
  const [mode, setMode] = useState<Mode>('select');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [replyText, setReplyText] = useState('');

  const options = [
    { label: 'Approve', description: 'Accept and proceed with the plan', key: 'y' },
    { label: 'Reject', description: 'Decline and cancel', key: 'n' },
    { label: 'Reply', description: 'Send feedback or ask questions', key: 'r' },
  ];

  useInput((input, key) => {
    if (mode === 'reply') {
      if (key.return) {
        if (replyText.trim()) {
          onReply(replyText);
        }
        return;
      }

      if (key.escape) {
        setMode('select');
        setReplyText('');
        return;
      }

      if (key.backspace || key.delete) {
        setReplyText(replyText.slice(0, -1));
        return;
      }

      if (input && !key.ctrl && !key.meta) {
        setReplyText(replyText + input);
      }
      return;
    }

    // Selection mode
    if (key.upArrow || (key.ctrl && input === 'p')) {
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : options.length - 1));
      return;
    }

    if (key.downArrow || (key.ctrl && input === 'n')) {
      setSelectedIndex((prev) => (prev < options.length - 1 ? prev + 1 : 0));
      return;
    }

    if (key.return) {
      const selected = options[selectedIndex];
      switch (selected.label) {
        case 'Approve':
          onApprove();
          break;
        case 'Reject':
          onReject();
          break;
        case 'Reply':
          setMode('reply');
          break;
      }
      return;
    }

    // Quick keys
    const lowerInput = input.toLowerCase();
    if (lowerInput === 'y') {
      onApprove();
    } else if (lowerInput === 'n') {
      onReject();
    } else if (lowerInput === 'r') {
      setMode('reply');
    }
  });

  return (
    <Box flexDirection="column" borderStyle="round" borderColor="#c9a075" paddingX={1}>
      <Text color="#c9a075" bold>
        ? Plan approval required
      </Text>

      <Box flexDirection="column" marginTop={1}>
        {options.map((option, index) => {
          const isSelected = index === selectedIndex;

          return (
            <Box key={index}>
              <Text color={isSelected ? '#7a9f7a' : '#6a6a6a'}>
                {isSelected ? '❯' : ' '}
              </Text>
              <Text color="#6a6a6a"> [{option.key}] </Text>
              <Text color={isSelected ? '#e8e8e8' : '#a8a8a8'} bold={isSelected}>
                {option.label}
              </Text>
              <Text color="#6a6a6a"> - {option.description}</Text>
            </Box>
          );
        })}
      </Box>

      {mode === 'reply' && (
        <Box marginTop={1}>
          <Text color="#c9a075">Reply: </Text>
          <Text>{replyText}</Text>
          <Text backgroundColor="#7a9f7a" color="#0d0d0d"> </Text>
        </Box>
      )}

      <Box marginTop={1}>
        <Text color="#6a6a6a">
          {mode === 'reply'
            ? 'Type your reply, Enter to send, Esc to cancel'
            : 'Press y/n/r or use ↑↓ and Enter'}
        </Text>
      </Box>
    </Box>
  );
}
