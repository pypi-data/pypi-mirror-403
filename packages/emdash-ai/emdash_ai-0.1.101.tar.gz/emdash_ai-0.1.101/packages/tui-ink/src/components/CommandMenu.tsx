import React from 'react';
import { Box, Text } from 'ink';
import { SLASH_COMMANDS, CATEGORY_COLORS } from '../constants/commands.js';

interface CommandMenuProps {
  /** Current input text (used to filter commands) */
  filter: string;
  /** Currently selected index */
  selectedIndex: number;
}

/**
 * Get filtered commands based on input.
 * Exported so App can use it for navigation logic.
 */
export function getFilteredCommands(filter: string) {
  const filterLower = filter.toLowerCase();
  return SLASH_COMMANDS.filter((cmd) =>
    cmd.command.toLowerCase().startsWith(filterLower)
  );
}

/**
 * Autocomplete dropdown menu for slash commands.
 * Display-only component - keyboard handling is done by parent/Input.
 */
function CommandMenuComponent({
  filter,
  selectedIndex,
}: CommandMenuProps): React.ReactElement | null {
  // Filter commands based on input
  const filteredCommands = getFilteredCommands(filter);

  // Limit display to 10 items
  const displayCommands = filteredCommands.slice(0, 10);

  // Don't render if no matches
  if (displayCommands.length === 0) {
    return null;
  }

  // Zen pink color palette
  const colors = {
    border: '#8a6a7a',
    selectedBg: '#3a2a32',
    selectedText: '#f0e8ec',
    commandText: '#d4a5b5',
    descText: '#9a8a8f',
    dimText: '#6a5a5f',
    hint: '#7a6a6f',
  };

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor={colors.border}
      paddingX={2}
      paddingY={1}
      minWidth={70}
    >
      {displayCommands.map((cmd, index) => {
        const isSelected = index === selectedIndex;

        return (
          <Box key={cmd.command} paddingX={1}>
            <Text
              backgroundColor={isSelected ? colors.selectedBg : undefined}
              color={isSelected ? colors.selectedText : colors.commandText}
              bold={isSelected}
            >
              {cmd.command.padEnd(20)}
            </Text>
            <Text
              backgroundColor={isSelected ? colors.selectedBg : undefined}
              color={isSelected ? colors.descText : colors.dimText}
            >
              {cmd.description.padEnd(40)}
            </Text>
          </Box>
        );
      })}
      {filteredCommands.length > 10 && (
        <Box paddingX={1}>
          <Text color={colors.dimText}>
            ... and {filteredCommands.length - 10} more
          </Text>
        </Box>
      )}
      <Box marginTop={1} paddingX={1}>
        <Text color={colors.hint}>
          <Text color={colors.border}>[</Text>↑↓<Text color={colors.border}>]</Text> navigate{'  '}
          <Text color={colors.border}>[</Text>Tab<Text color={colors.border}>]</Text> complete{'  '}
          <Text color={colors.border}>[</Text>Enter<Text color={colors.border}>]</Text> send{'  '}
          <Text color={colors.border}>[</Text>Esc<Text color={colors.border}>]</Text> dismiss
        </Text>
      </Box>
    </Box>
  );
}

// Memoize to prevent re-renders
export const CommandMenu = React.memo(CommandMenuComponent);
