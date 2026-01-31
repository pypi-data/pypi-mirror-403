import React, { useState, useEffect } from 'react';
import { Text, Box } from 'ink';

interface WelcomeProps {
  cwd?: string;
}

// Stylized "EMDASH" ASCII art logo - all caps
const LOGO_LINES = [
  ' ████  █   █  ███    ▄▄▄   ▄▄▄  █   █',
  ' █     ██ ██  █  █  █   █ █     █   █',
  ' ███   █ █ █  █  █  █▄▄▄█ ▀▄▄▄  █▄▄▄█',
  ' █     █   █  █  █  █   █     █ █   █',
  ' ████  █   █  ███   █   █ ▄▄▄▀  █   █',
];

// Color gradient from gold to orange
const GRADIENT_COLORS = [
  '#d4a84b',
  '#c99a45',
  '#be8c3f',
  '#b37e39',
  '#a87033',
];

export function Welcome({ cwd }: WelcomeProps): React.ReactElement {
  const [visibleChars, setVisibleChars] = useState(0);
  const [showContent, setShowContent] = useState(false);

  // Get short directory name
  const dirName = cwd ? cwd.split('/').pop() || cwd : '';

  // Calculate total characters in logo
  const totalChars = LOGO_LINES.reduce((sum, line) => sum + line.length, 0);

  // Animate logo reveal
  useEffect(() => {
    if (visibleChars < totalChars) {
      const timer = setTimeout(() => {
        // Reveal multiple characters at once for faster animation
        setVisibleChars(prev => Math.min(prev + 4, totalChars));
      }, 8);
      return () => clearTimeout(timer);
    } else if (!showContent) {
      // Show content after logo animation completes
      const timer = setTimeout(() => setShowContent(true), 100);
      return () => clearTimeout(timer);
    }
  }, [visibleChars, totalChars, showContent]);

  // Render logo with animation
  const renderLogo = () => {
    let charCount = 0;

    return LOGO_LINES.map((line, lineIndex) => {
      const lineStart = charCount;
      charCount += line.length;

      // Calculate how many chars of this line to show
      const charsToShow = Math.max(0, Math.min(line.length, visibleChars - lineStart));
      const visiblePart = line.slice(0, charsToShow);

      return (
        <Text key={lineIndex} color={GRADIENT_COLORS[lineIndex]}>
          {visiblePart}
        </Text>
      );
    });
  };

  return (
    <Box flexDirection="column" paddingX={1} paddingY={1}>
      {/* Animated ASCII Art Logo */}
      <Box flexDirection="column" marginBottom={1}>
        {renderLogo()}
      </Box>

      {/* Content appears after logo animation */}
      {showContent && (
        <>
          {/* Tagline with fade effect */}
          <Box marginBottom={1}>
            <Text color="#6a6a6a">AI Team Lead</Text>
          </Box>

          {/* Context info */}
          {dirName && (
            <Box marginBottom={1}>
              <Text color="#5a5a5a">Working in </Text>
              <Text color="#ba9f6a">{dirName}</Text>
            </Box>
          )}

          {/* Quick tips */}
          <Box flexDirection="column" marginTop={1}>
            <Text color="#4a4a4a">Quick start:</Text>
            <Box marginLeft={2} flexDirection="column">
              <Text color="#5a5a5a">
                <Text color="#7a6a5a">/</Text> Browse commands
              </Text>
              <Text color="#5a5a5a">
                <Text color="#7a6a5a">/help</Text> Show all shortcuts
              </Text>
              <Text color="#5a5a5a">
                <Text color="#7a6a5a">Ctrl+C</Text> Cancel or quit
              </Text>
            </Box>
          </Box>
        </>
      )}
    </Box>
  );
}
