import React, { useState, useMemo } from 'react';
import { Box, Text, useInput, useStdout } from 'ink';

interface TextViewerProps {
  /** The text content to display */
  content: string;
  /** Title for the viewer header */
  title?: string;
  /** Called when the viewer is closed */
  onClose: () => void;
  /** Whether the viewer is active (receives input) */
  isActive: boolean;
}

/**
 * Full-height text viewer overlay.
 * Supports scrolling with arrow keys and Page Up/Down.
 * Close with Escape or 'q'.
 *
 * Key advantage: Native text selection works because Ink renders to terminal!
 */
export function TextViewer({
  content,
  title = 'View',
  onClose,
  isActive,
}: TextViewerProps): React.ReactElement {
  const { stdout } = useStdout();
  const terminalHeight = stdout?.rows || 24;

  // Reserve 4 lines for header and footer
  const viewportHeight = terminalHeight - 4;

  const [scrollOffset, setScrollOffset] = useState(0);

  // Split content into lines
  const lines = useMemo(() => content.split('\n'), [content]);
  const totalLines = lines.length;
  const maxScroll = Math.max(0, totalLines - viewportHeight);

  // Get visible lines
  const visibleLines = useMemo(() => {
    return lines.slice(scrollOffset, scrollOffset + viewportHeight);
  }, [lines, scrollOffset, viewportHeight]);

  // Handle keyboard input
  useInput(
    (input, key) => {
      if (key.escape || input === 'q') {
        onClose();
        return;
      }

      // Scroll up
      if (key.upArrow || input === 'k') {
        setScrollOffset((prev) => Math.max(0, prev - 1));
        return;
      }

      // Scroll down
      if (key.downArrow || input === 'j') {
        setScrollOffset((prev) => Math.min(maxScroll, prev + 1));
        return;
      }

      // Page up
      if (key.pageUp || input === 'b') {
        setScrollOffset((prev) => Math.max(0, prev - viewportHeight));
        return;
      }

      // Page down
      if (key.pageDown || input === 'f' || input === ' ') {
        setScrollOffset((prev) => Math.min(maxScroll, prev + viewportHeight));
        return;
      }

      // Home (go to top)
      if (input === 'g') {
        setScrollOffset(0);
        return;
      }

      // End (go to bottom)
      if (input === 'G') {
        setScrollOffset(maxScroll);
        return;
      }
    },
    { isActive }
  );

  // Calculate scroll percentage
  const scrollPercent = maxScroll > 0
    ? Math.round((scrollOffset / maxScroll) * 100)
    : 100;

  return (
    <Box flexDirection="column" height={terminalHeight}>
      {/* Header */}
      <Box
        borderStyle="single"
        borderColor="#4a5a4a"
        borderBottom
        borderTop={false}
        borderLeft={false}
        borderRight={false}
        paddingX={1}
      >
        <Text color="#7a9f7a" bold>
          {title}
        </Text>
        <Text color="#6a6a6a">
          {' '}- {totalLines} lines
        </Text>
        {maxScroll > 0 && (
          <Text color="#6a6a6a">
            {' '}({scrollPercent}%)
          </Text>
        )}
      </Box>

      {/* Content */}
      <Box flexDirection="column" flexGrow={1} paddingX={1}>
        {visibleLines.map((line, index) => (
          <Text key={scrollOffset + index} wrap="truncate">
            {line || ' '}
          </Text>
        ))}
      </Box>

      {/* Footer with scroll indicator */}
      <Box
        borderStyle="single"
        borderColor="#4a5a4a"
        borderTop
        borderBottom={false}
        borderLeft={false}
        borderRight={false}
        paddingX={1}
        justifyContent="space-between"
      >
        <Text color="#6a6a6a">
          [arrows/jk] scroll | [PgUp/PgDn/bf] page | [g/G] top/bottom | [q/Esc] close
        </Text>
        {maxScroll > 0 && (
          <Text color="#6a6a6a">
            {scrollOffset + 1}-{Math.min(scrollOffset + viewportHeight, totalLines)}/{totalLines}
          </Text>
        )}
      </Box>
    </Box>
  );
}
