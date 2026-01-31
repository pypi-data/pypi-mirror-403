import React from 'react';
import { Box, Text } from 'ink';

interface ProgressBarProps {
  /** Progress value between 0 and 100 */
  percent: number;
  /** Width of the bar in characters */
  width?: number;
  /** Label to show before the bar */
  label?: string;
  /** Show percentage text */
  showPercent?: boolean;
  /** Color scheme */
  color?: 'green' | 'blue' | 'yellow' | 'cyan';
}

const COLOR_SCHEMES = {
  green: { filled: '#7a9f7a', empty: '#2a3a2a', text: '#98c379' },
  blue: { filled: '#7a9fc9', empty: '#2a2a3a', text: '#61afef' },
  yellow: { filled: '#c9a075', empty: '#3a3a2a', text: '#d19a66' },
  cyan: { filled: '#6ac9c9', empty: '#2a3a3a', text: '#56b6c2' },
};

export function ProgressBar({
  percent,
  width = 30,
  label,
  showPercent = true,
  color = 'green',
}: ProgressBarProps): React.ReactElement {
  const clampedPercent = Math.max(0, Math.min(100, percent));
  const filledWidth = Math.round((clampedPercent / 100) * width);
  const emptyWidth = width - filledWidth;
  const colors = COLOR_SCHEMES[color];

  const filled = '█'.repeat(filledWidth);
  const empty = '░'.repeat(emptyWidth);

  return (
    <Box>
      {label && (
        <>
          <Text color="#8a8a8a">{label}</Text>
          <Text> </Text>
        </>
      )}
      <Text color={colors.filled}>{filled}</Text>
      <Text color={colors.empty}>{empty}</Text>
      {showPercent && (
        <>
          <Text> </Text>
          <Text color={colors.text}>{Math.round(clampedPercent)}%</Text>
        </>
      )}
    </Box>
  );
}

interface MultiProgressProps {
  items: Array<{
    label: string;
    percent: number;
    color?: 'green' | 'blue' | 'yellow' | 'cyan';
  }>;
  width?: number;
}

export function MultiProgress({ items, width = 25 }: MultiProgressProps): React.ReactElement {
  const maxLabelLen = Math.max(...items.map((i) => i.label.length));

  return (
    <Box flexDirection="column">
      {items.map((item, index) => (
        <Box key={index}>
          <Text color="#8a8a8a">{item.label.padEnd(maxLabelLen, ' ')}</Text>
          <Text> </Text>
          <ProgressBar
            percent={item.percent}
            width={width}
            color={item.color || 'green'}
            showPercent={true}
          />
        </Box>
      ))}
    </Box>
  );
}
