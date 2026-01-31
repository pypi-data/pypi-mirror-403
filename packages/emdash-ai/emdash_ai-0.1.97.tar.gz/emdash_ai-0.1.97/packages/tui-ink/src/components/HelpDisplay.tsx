import React from 'react';
import { Box, Text } from 'ink';
import {
  CATEGORY_ORDER,
  CATEGORY_LABELS,
  CATEGORY_COLORS,
  getCommandsByCategory,
  type CommandCategory,
} from '../constants/commands.js';

interface HelpDisplayProps {
  /** Optional filter to show only specific categories */
  categories?: CommandCategory[];
}

/**
 * Displays available slash commands organized by category.
 * Each category has its own color for easy visual scanning.
 */
export function HelpDisplay({ categories }: HelpDisplayProps): React.ReactElement {
  const displayCategories = categories || CATEGORY_ORDER;

  return (
    <Box flexDirection="column" paddingX={1}>
      <Box marginBottom={1}>
        <Text color="#7a9f7a" bold>
          Available Commands
        </Text>
      </Box>

      {displayCategories.map((category) => {
        const commands = getCommandsByCategory(category);
        if (commands.length === 0) return null;

        const color = CATEGORY_COLORS[category];
        const label = CATEGORY_LABELS[category];

        return (
          <Box key={category} flexDirection="column" marginBottom={1}>
            <Box>
              <Text color={color} bold>
                {label}
              </Text>
            </Box>
            {commands.map((cmd) => (
              <Box key={cmd.command}>
                <Text color={color}>{cmd.command.padEnd(18)}</Text>
                <Text color="#6a6a6a">{cmd.description}</Text>
              </Box>
            ))}
          </Box>
        );
      })}

      <Box marginTop={1}>
        <Text color="#6a6a6a">
          Type a command or message to interact with the agent.
        </Text>
      </Box>
    </Box>
  );
}
