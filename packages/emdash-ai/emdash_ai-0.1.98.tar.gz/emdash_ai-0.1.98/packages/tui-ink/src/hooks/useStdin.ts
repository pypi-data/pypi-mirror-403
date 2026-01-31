import { useState, useEffect, useCallback } from 'react';
import * as readline from 'readline';
import { parseIncomingEvent, type IncomingEvent } from '../protocol.js';

/**
 * Hook to read JSON events from stdin (sent by Python backend)
 */
export function useStdin(): {
  events: IncomingEvent[];
  latestEvent: IncomingEvent | null;
} {
  const [events, setEvents] = useState<IncomingEvent[]>([]);
  const [latestEvent, setLatestEvent] = useState<IncomingEvent | null>(null);

  useEffect(() => {
    const rl = readline.createInterface({
      input: process.stdin,
      terminal: false,
    });

    rl.on('line', (line) => {
      const event = parseIncomingEvent(line);
      if (event) {
        setLatestEvent(event);
        setEvents((prev) => [...prev, event]);
      }
    });

    return () => {
      rl.close();
    };
  }, []);

  return { events, latestEvent };
}
