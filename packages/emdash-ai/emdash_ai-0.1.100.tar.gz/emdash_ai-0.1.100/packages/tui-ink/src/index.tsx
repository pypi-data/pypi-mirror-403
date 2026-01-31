#!/usr/bin/env node
import React from 'react';
import { render } from 'ink';
import * as fs from 'fs';
import * as tty from 'tty';
import { Readable } from 'stream';
import App from './App.js';
import { setMessageOutputStream } from './protocol.js';

// When running via Python bridge, stdin is piped for JSON events
// We need to use /dev/tty for keyboard input instead
const isTTY = process.stdin.isTTY;

interface RenderOptions {
  stdin?: NodeJS.ReadStream;
  exitOnCtrlC?: boolean;
}

const options: RenderOptions = {
  exitOnCtrlC: true,
};

let bridgeMode = false;
let hasInputSupport = isTTY;

if (!isTTY) {
  bridgeMode = true;
  // In bridge mode, send messages to stderr (stdout is used for Ink rendering)
  setMessageOutputStream(process.stderr);
  // Running via bridge - try to open /dev/tty for keyboard input
  try {
    const fd = fs.openSync('/dev/tty', 'r');
    const ttyStream = new tty.ReadStream(fd);
    ttyStream.setRawMode(true);
    options.stdin = ttyStream;
    hasInputSupport = true;
  } catch {
    // No TTY available (e.g., running in CI)
    // We'll render but input won't work
    hasInputSupport = false;

    // Create a dummy stdin that reports as TTY to prevent Ink from erroring
    // This is a workaround for environments without a real TTY
    const dummyStdin = new Readable({
      read() {
        // Never emit data - input is disabled
      }
    });
    // Pretend to be a TTY to satisfy Ink's checks
    (dummyStdin as any).isTTY = true;
    (dummyStdin as any).setRawMode = () => dummyStdin;
    (dummyStdin as any).ref = () => dummyStdin;
    (dummyStdin as any).unref = () => dummyStdin;
    options.stdin = dummyStdin as unknown as NodeJS.ReadStream;
  }
}

// Render the Ink app
render(<App bridgeMode={bridgeMode} hasInputSupport={hasInputSupport} />, options);
