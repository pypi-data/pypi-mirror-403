import React from 'react';
import { Text, Box } from 'ink';
import type { TodoItem } from '../store.js';

interface TodoListProps {
  todos: TodoItem[];
  compact?: boolean;
}

const STATUS_ICONS: Record<TodoItem['status'], { icon: string; color: string }> = {
  pending: { icon: '○', color: '#6a6a6a' },
  in_progress: { icon: '◐', color: '#ba9f6a' },
  completed: { icon: '●', color: '#7a9f7a' },
};

export function TodoList({ todos, compact = false }: TodoListProps): React.ReactElement | null {
  if (todos.length === 0) {
    return null;
  }

  // Filter out completed in compact mode
  const visibleTodos = compact
    ? todos.filter(t => t.status !== 'completed')
    : todos;

  if (visibleTodos.length === 0) {
    return null;
  }

  // Count by status
  const counts = {
    pending: todos.filter(t => t.status === 'pending').length,
    in_progress: todos.filter(t => t.status === 'in_progress').length,
    completed: todos.filter(t => t.status === 'completed').length,
  };

  return (
    <Box flexDirection="column" marginBottom={1}>
      {/* Header */}
      <Box marginBottom={0}>
        <Text color="#7a6a5a" bold>Tasks </Text>
        <Text color="#5a5a5a">
          ({counts.in_progress} active, {counts.pending} pending, {counts.completed} done)
        </Text>
      </Box>

      {/* Todo items */}
      {visibleTodos.map((todo) => {
        const { icon, color } = STATUS_ICONS[todo.status];
        const isActive = todo.status === 'in_progress';

        return (
          <Box key={todo.id} paddingLeft={1}>
            <Text color={color}>{icon} </Text>
            {isActive && todo.activeForm ? (
              <Text color="#ba9f6a">{todo.activeForm}...</Text>
            ) : (
              <Text color={isActive ? '#ba9f6a' : '#8a8a8a'}>
                {todo.subject}
              </Text>
            )}
            {!compact && todo.description && (
              <Text color="#5a5a5a" dimColor> - {todo.description.slice(0, 50)}</Text>
            )}
          </Box>
        );
      })}
    </Box>
  );
}
