/**
 * Cross-platform clipboard utility for copying text to system clipboard.
 * Uses native commands: pbcopy (macOS), xclip/xsel (Linux), clip (Windows)
 */

import { spawn } from 'child_process';
import { platform } from 'os';

/**
 * Copy text to the system clipboard.
 * @param text The text to copy
 * @returns Promise that resolves to true on success, false on failure
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  const os = platform();

  let command: string;
  let args: string[];

  switch (os) {
    case 'darwin':
      // macOS
      command = 'pbcopy';
      args = [];
      break;
    case 'linux':
      // Linux - try xclip first, fall back to xsel
      command = 'xclip';
      args = ['-selection', 'clipboard'];
      break;
    case 'win32':
      // Windows
      command = 'clip';
      args = [];
      break;
    default:
      return false;
  }

  return new Promise((resolve) => {
    try {
      const proc = spawn(command, args, {
        stdio: ['pipe', 'ignore', 'ignore'],
      });

      proc.on('error', async (err) => {
        // On Linux, if xclip fails, try xsel
        if (os === 'linux' && command === 'xclip') {
          const xselResult = await copyWithXsel(text);
          resolve(xselResult);
        } else {
          resolve(false);
        }
      });

      proc.on('close', (code) => {
        resolve(code === 0);
      });

      // Write text to stdin
      proc.stdin?.write(text);
      proc.stdin?.end();
    } catch {
      resolve(false);
    }
  });
}

/**
 * Fallback clipboard copy using xsel on Linux
 */
async function copyWithXsel(text: string): Promise<boolean> {
  return new Promise((resolve) => {
    try {
      const proc = spawn('xsel', ['--clipboard', '--input'], {
        stdio: ['pipe', 'ignore', 'ignore'],
      });

      proc.on('error', () => {
        resolve(false);
      });

      proc.on('close', (code) => {
        resolve(code === 0);
      });

      proc.stdin?.write(text);
      proc.stdin?.end();
    } catch {
      resolve(false);
    }
  });
}
