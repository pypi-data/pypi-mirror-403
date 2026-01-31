import React from 'react';
import { Text } from 'ink';

const SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

interface SpinnerProps {
  text?: string;
  color?: string;
}

export function Spinner({ text = 'thinking', color = '#7a9f7a' }: SpinnerProps): React.ReactElement {
  const [frame, setFrame] = React.useState(0);

  React.useEffect(() => {
    const timer = setInterval(() => {
      setFrame((prev) => (prev + 1) % SPINNER_FRAMES.length);
    }, 80);
    return () => clearInterval(timer);
  }, []);

  return (
    <Text>
      <Text color={color}>{SPINNER_FRAMES[frame]}</Text>
      <Text color="#8a8aaa"> {text}...</Text>
    </Text>
  );
}
