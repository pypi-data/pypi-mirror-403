import { useEffect, useState, useRef } from 'react';
import { useStdin } from 'ink';
import type { Key } from 'ink';

type InputHandler = (input: string, key: Key) => void;

interface UseSafeInputOptions {
  isActive?: boolean;
}

/**
 * Parse key from raw input buffer.
 * This is a simplified version of Ink's input parsing.
 */
function parseKey(data: string): { input: string; key: Key } {
  const key: Key = {
    upArrow: false,
    downArrow: false,
    leftArrow: false,
    rightArrow: false,
    pageDown: false,
    pageUp: false,
    return: false,
    escape: false,
    ctrl: false,
    shift: false,
    tab: false,
    backspace: false,
    delete: false,
    meta: false,
  };

  let input = '';

  // Check for escape sequences
  if (data === '\x1B[A') {
    key.upArrow = true;
  } else if (data === '\x1B[B') {
    key.downArrow = true;
  } else if (data === '\x1B[C') {
    key.rightArrow = true;
  } else if (data === '\x1B[D') {
    key.leftArrow = true;
  } else if (data === '\x1B[5~') {
    key.pageUp = true;
  } else if (data === '\x1B[6~') {
    key.pageDown = true;
  } else if (data === '\x1B') {
    key.escape = true;
  } else if (data === '\r' || data === '\n') {
    key.return = true;
  } else if (data === '\t') {
    key.tab = true;
  } else if (data === '\x7F' || data === '\b') {
    key.backspace = true;
  } else if (data === '\x1B[3~') {
    key.delete = true;
  } else if (data.length === 1) {
    const code = data.charCodeAt(0);
    if (code <= 26 && code > 0) {
      // Ctrl+letter
      key.ctrl = true;
      input = String.fromCharCode(code + 96); // Convert to letter
    } else {
      input = data;
    }
  }

  return { input, key };
}

/**
 * A safe input hook that handles raw mode gracefully.
 * Falls back to reading from stdin directly when available.
 */
export function useSafeInput(handler: InputHandler, options: UseSafeInputOptions = {}): void {
  const { isActive = true } = options;
  const { stdin, setRawMode, isRawModeSupported } = useStdin();
  const handlerRef = useRef(handler);

  // Keep handler ref updated
  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  useEffect(() => {
    if (!isActive || !stdin) {
      return;
    }

    // Try to enable raw mode if supported
    if (isRawModeSupported) {
      try {
        setRawMode(true);
      } catch {
        // Raw mode not available, continue without it
      }
    }

    const handleData = (data: Buffer) => {
      const str = data.toString('utf-8');
      const { input, key } = parseKey(str);
      handlerRef.current(input, key);
    };

    stdin.on('data', handleData);

    return () => {
      stdin.off('data', handleData);
      if (isRawModeSupported) {
        try {
          setRawMode(false);
        } catch {
          // Ignore errors when disabling raw mode
        }
      }
    };
  }, [isActive, stdin, isRawModeSupported, setRawMode]);
}
