import React from 'react';
import { Box, Text } from 'ink';

export interface TodoItem {
  id: string;
  subject: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed';
  activeForm?: string;
}

interface TodoListProps {
  todos: TodoItem[];
  title?: string;
  compact?: boolean;
}

const STATUS_ICONS: Record<TodoItem['status'], { icon: string; color: string }> = {
  pending: { icon: '○', color: '#6a6a6a' },
  in_progress: { icon: '◐', color: '#c9a075' },
  completed: { icon: '●', color: '#7a9f7a' },
};

export function TodoList({ todos, title = 'Tasks', compact = false }: TodoListProps): React.ReactElement | null {
  if (todos.length === 0) {
    return null;
  }

  const pending = todos.filter(t => t.status === 'pending').length;
  const inProgress = todos.filter(t => t.status === 'in_progress').length;
  const completed = todos.filter(t => t.status === 'completed').length;

  return (
    <Box flexDirection="column" borderStyle="round" borderColor="#3a3a3a" paddingX={1} marginY={1}>
      {/* Header */}
      <Box marginBottom={1}>
        <Text color="#7a9fc9" bold>{title}</Text>
        <Text color="#4a4a4a"> </Text>
        <Text color="#5a5a5a">
          {completed}/{todos.length} done
        </Text>
      </Box>

      {/* Todo items */}
      {todos.map((todo) => {
        const { icon, color } = STATUS_ICONS[todo.status];
        const isActive = todo.status === 'in_progress';

        return (
          <Box key={todo.id} flexDirection="column" marginBottom={compact ? 0 : 1}>
            <Box>
              <Text color={color}>{icon}</Text>
              <Text> </Text>
              <Text
                color={todo.status === 'completed' ? '#5a5a5a' : '#c9c9c9'}
                strikethrough={todo.status === 'completed'}
                bold={isActive}
              >
                {todo.subject}
              </Text>
            </Box>
            {/* Show active form when in progress */}
            {isActive && todo.activeForm && (
              <Box marginLeft={2}>
                <Text color="#8a8a6a" dimColor>
                  {todo.activeForm}...
                </Text>
              </Box>
            )}
            {/* Show description if not compact */}
            {!compact && todo.description && todo.status !== 'completed' && (
              <Box marginLeft={2}>
                <Text color="#5a5a5a" wrap="wrap">
                  {todo.description.length > 80
                    ? todo.description.slice(0, 77) + '...'
                    : todo.description}
                </Text>
              </Box>
            )}
          </Box>
        );
      })}

      {/* Summary bar */}
      <Box marginTop={1} borderStyle="single" borderTop borderBottom={false} borderLeft={false} borderRight={false} borderColor="#2a2a2a" paddingTop={1}>
        <Text color="#5a5a5a">
          <Text color="#6a6a6a">{pending} pending</Text>
          <Text color="#3a3a3a"> · </Text>
          <Text color="#c9a075">{inProgress} active</Text>
          <Text color="#3a3a3a"> · </Text>
          <Text color="#7a9f7a">{completed} done</Text>
        </Text>
      </Box>
    </Box>
  );
}
