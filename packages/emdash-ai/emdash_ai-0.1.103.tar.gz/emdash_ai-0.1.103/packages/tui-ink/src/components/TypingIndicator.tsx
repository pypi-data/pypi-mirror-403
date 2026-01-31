import React from 'react';
import { Text, Box } from 'ink';

interface TypingIndicatorProps {
  users: Array<{ id: string; name: string }>;
}

export function TypingIndicator({ users }: TypingIndicatorProps): React.ReactElement | null {
  if (users.length === 0) {
    return null;
  }

  // Separate agent from human users — agent "thinks", humans "type"
  const agent = users.find((u) => u.id === '__agent__');
  const humans = users.filter((u) => u.id !== '__agent__');

  const parts: string[] = [];

  if (agent) {
    parts.push('Agent is thinking...');
  }

  if (humans.length === 1) {
    parts.push(`${humans[0].name} is typing...`);
  } else if (humans.length === 2) {
    parts.push(`${humans[0].name} and ${humans[1].name} are typing...`);
  } else if (humans.length > 2) {
    const names = humans.map((u) => u.name);
    parts.push(`${names.slice(0, -1).join(', ')}, and ${names[names.length - 1]} are typing...`);
  }

  const text = parts.join('  ');

  return (
    <Box>
      <Text color="#6a6a6a" italic>
        {text}
      </Text>
    </Box>
  );
}
