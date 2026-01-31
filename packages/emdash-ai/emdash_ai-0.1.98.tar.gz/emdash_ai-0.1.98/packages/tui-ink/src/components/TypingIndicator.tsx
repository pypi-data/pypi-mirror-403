import React from 'react';
import { Text, Box } from 'ink';

interface TypingIndicatorProps {
  users: Array<{ id: string; name: string }>;
}

export function TypingIndicator({ users }: TypingIndicatorProps): React.ReactElement | null {
  if (users.length === 0) {
    return null;
  }

  const names = users.map((u) => u.name);
  let text: string;

  if (names.length === 1) {
    text = `${names[0]} is typing...`;
  } else if (names.length === 2) {
    text = `${names[0]} and ${names[1]} are typing...`;
  } else {
    text = `${names.slice(0, -1).join(', ')}, and ${names[names.length - 1]} are typing...`;
  }

  return (
    <Box>
      <Text color="#6a6a6a" italic>
        {text}
      </Text>
    </Box>
  );
}
