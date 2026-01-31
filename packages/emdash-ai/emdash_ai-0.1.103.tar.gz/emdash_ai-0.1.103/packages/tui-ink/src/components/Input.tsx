import React, { useState, useEffect } from 'react';
import { Text, Box, useInput, useStdout } from 'ink';
import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';
import * as os from 'os';

export type InputMode = 'code' | 'plan' | 'approval';

// Image file extensions we recognize
const IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'];

// Stable empty array to avoid re-renders from default prop
const EMPTY_ATTACHMENTS: ImageAttachment[] = [];

// Try to save clipboard image to a temp file (macOS)
function saveClipboardImage(): string | null {
  if (process.platform !== 'darwin') {
    return null; // Only macOS supported for now
  }

  const tempDir = os.tmpdir();

  try {
    // Check what's in the clipboard
    const clipboardInfo = execSync('osascript -e "clipboard info"', { encoding: 'utf-8' });

    // First, check if clipboard contains a file reference (copied file from Finder)
    // This appears as "furl" or "«class furl»" in clipboard info
    if (/furl|«class furl»/.test(clipboardInfo)) {
      // Get the file path from clipboard
      const getPathScript = `
        set fileList to the clipboard as «class furl»
        return POSIX path of fileList
      `;
      try {
        const filePath = execSync(`osascript -e '${getPathScript}'`, { encoding: 'utf-8' }).trim();

        // Check if it's an image file
        const ext = path.extname(filePath).toLowerCase();
        if (IMAGE_EXTENSIONS.includes(ext)) {
          // Return the original file path - no need to copy
          if (fs.existsSync(filePath)) {
            return filePath;
          }
        }
      } catch {
        // Failed to get file path, fall through to try raw image data
      }
    }

    // Check if clipboard has raw image data (screenshot, copied image from browser, etc.)
    const hasRawImage = /PNGf|TIFF|JPEG|GIF/.test(clipboardInfo);

    if (!hasRawImage) {
      return null;
    }

    // Save clipboard image to temp file using osascript
    const tempFile = path.join(tempDir, `clipboard-${Date.now()}.png`);
    const script = `
      set theFile to (open for access POSIX file "${tempFile}" with write permission)
      set eof theFile to 0
      try
        write (the clipboard as «class PNGf») to theFile
      on error
        try
          write (the clipboard as TIFF picture) to theFile
        end try
      end try
      close access theFile
    `;
    execSync(`osascript -e '${script}'`, { encoding: 'utf-8' });

    // Verify file was created and has content
    if (fs.existsSync(tempFile) && fs.statSync(tempFile).size > 0) {
      return tempFile;
    }
  } catch {
    // Clipboard doesn't have image or save failed
  }

  return null;
}

export interface ImageAttachment {
  id: string;
  path: string;
  name: string;
}

export interface FileAttachment {
  id: string;
  path: string;
  name: string;
}

// Search for files matching a pattern
function searchFiles(query: string, cwd: string = process.cwd()): string[] {
  const results: string[] = [];
  const maxResults = 10;

  try {
    // If query is empty, list recent/common files
    if (!query) {
      const entries = fs.readdirSync(cwd, { withFileTypes: true });
      for (const entry of entries.slice(0, maxResults)) {
        if (!entry.name.startsWith('.')) {
          results.push(entry.isDirectory() ? entry.name + '/' : entry.name);
        }
      }
      return results;
    }

    // Search recursively for matching files
    const searchDir = (dir: string, depth: number = 0): void => {
      if (depth > 3 || results.length >= maxResults) return;

      try {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
          if (results.length >= maxResults) break;
          if (entry.name.startsWith('.') || entry.name === 'node_modules') continue;

          const relativePath = path.relative(cwd, path.join(dir, entry.name));
          const lowerName = entry.name.toLowerCase();
          const lowerQuery = query.toLowerCase();

          if (lowerName.includes(lowerQuery)) {
            results.push(entry.isDirectory() ? relativePath + '/' : relativePath);
          }

          if (entry.isDirectory() && depth < 3) {
            searchDir(path.join(dir, entry.name), depth + 1);
          }
        }
      } catch {
        // Permission denied or other error
      }
    };

    searchDir(cwd);
  } catch {
    // Error reading directory
  }

  return results;
}

// Mode-based color theming - warm orange tones
const MODE_COLORS: Record<InputMode, { border: string; accent: string; cursor: string; cursorText: string }> = {
  code: {
    border: '#5a4a3d',
    accent: '#ba9f6a',
    cursor: '#ba9f6a',
    cursorText: '#0d0d0d',
  },
  plan: {
    border: '#5a3d4a',
    accent: '#c97590',
    cursor: '#c97590',
    cursorText: '#0d0d0d',
  },
  approval: {
    border: '#5a3d4a',
    accent: '#c97590',
    cursor: '#c97590',
    cursorText: '#0d0d0d',
  },
};

interface InputProps {
  prompt?: string;
  promptColor?: string;
  /** Controlled value - when provided, syncs internal state */
  value?: string;
  onSubmit: (value: string, attachments?: ImageAttachment[]) => void;
  onChange?: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  /** When true, arrow keys will call onMenuUp/onMenuDown instead of cursor movement */
  menuMode?: boolean;
  onMenuUp?: () => void;
  onMenuDown?: () => void;
  /** Called when Enter pressed in menu mode - should send the command */
  onMenuSelect?: (value: string) => void;
  /** Called when Tab pressed in menu mode - should autocomplete the input */
  onMenuComplete?: (completedValue: string) => void;
  onMenuDismiss?: () => void;
  /** Current mode for styling (code, plan, approval) */
  mode?: InputMode;
  /** Whether to show keyboard hints below input */
  showHints?: boolean;
  /** Current image attachments */
  attachments?: ImageAttachment[];
  /** Callback when attachments change */
  onAttachmentsChange?: (attachments: ImageAttachment[]) => void;
  /** Called when typing state changes (for multiuser typing indicators) */
  onTypingChange?: (isTyping: boolean) => void;
}

// Normalize a pasted path to a standard file path
function normalizePath(str: string): string {
  let normalized = str;

  // Remove bracketed paste sequences (terminals wrap pasted text with these)
  normalized = normalized.replace(/\x1b\[200~/g, '');
  normalized = normalized.replace(/\x1b\[201~/g, '');

  // Remove other common escape sequences
  normalized = normalized.replace(/\x1b\[[0-9;]*[a-zA-Z]/g, '');

  normalized = normalized.trim();

  // Remove surrounding quotes
  normalized = normalized.replace(/^["']|["']$/g, '');

  // Handle file:// URLs (macOS Finder paste)
  if (normalized.startsWith('file://')) {
    normalized = decodeURIComponent(normalized.slice(7));
  }

  // Handle shell-escaped characters (backslash before space, parens, brackets, etc.)
  // Common escapes: \ , \(, \), \[, \], \', \"
  normalized = normalized.replace(/\\(.)/g, '$1');

  // Handle tilde for home directory
  if (normalized.startsWith('~/')) {
    const home = process.env.HOME || process.env.USERPROFILE || '';
    normalized = path.join(home, normalized.slice(2));
  }

  return normalized;
}

// Check if a string looks like an image file path
function isImagePath(str: string): boolean {
  const normalized = normalizePath(str);
  if (!normalized) return false;

  // Check if it's a file path with image extension
  const ext = path.extname(normalized).toLowerCase();
  if (!IMAGE_EXTENSIONS.includes(ext)) return false;

  // Check if file exists
  try {
    const resolved = path.isAbsolute(normalized) ? normalized : path.resolve(process.cwd(), normalized);
    return fs.existsSync(resolved);
  } catch {
    return false;
  }
}

// Extract image paths from pasted text
function extractImagePaths(text: string): string[] {
  const paths: string[] = [];

  // Try the whole text first (single file paste)
  const wholePath = normalizePath(text);
  if (isImagePath(wholePath)) {
    paths.push(wholePath);
    return paths;
  }

  // Try splitting by newlines (multiple files)
  const lines = text.split(/[\n\r]+/);
  for (const line of lines) {
    const normalized = normalizePath(line);
    if (normalized && isImagePath(normalized)) {
      paths.push(normalized);
    }
  }

  return paths;
}

export function Input({
  prompt = '› ',
  promptColor,
  value: controlledValue,
  onSubmit,
  onChange,
  disabled = false,
  placeholder = '',
  menuMode = false,
  onMenuUp,
  onMenuDown,
  onMenuSelect,
  onMenuComplete,
  onMenuDismiss,
  mode = 'code',
  showHints = false,
  attachments = EMPTY_ATTACHMENTS,
  onAttachmentsChange,
  onTypingChange,
}: InputProps): React.ReactElement {
  const [internalValue, setInternalValue] = useState('');
  const [cursorOffset, setCursorOffset] = useState(0);
  const [localAttachments, setLocalAttachments] = useState<ImageAttachment[]>(attachments);

  // Typing indicator state
  const isTypingRef = React.useRef(false);
  const typingTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);
  const typingIntervalRef = React.useRef<NodeJS.Timeout | null>(null);

  // Cleanup typing timeout and interval on unmount
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      if (typingIntervalRef.current) {
        clearInterval(typingIntervalRef.current);
      }
      // Notify stopped typing on unmount
      if (isTypingRef.current && onTypingChange) {
        onTypingChange(false);
      }
    };
  }, [onTypingChange]);

  // Use controlled value when provided, otherwise use internal state
  const value = controlledValue !== undefined ? controlledValue : internalValue;

  // Helper to update value (updates internal state and notifies parent)
  const setValue = (newValue: string) => {
    setInternalValue(newValue);
  };
  const { stdout } = useStdout();
  const terminalWidth = stdout?.columns || 80;

  // File menu state
  const [showFileMenu, setShowFileMenu] = useState(false);
  const [fileMenuIndex, setFileMenuIndex] = useState(0);
  const [fileSuggestions, setFileSuggestions] = useState<string[]>([]);
  const [fileQuery, setFileQuery] = useState('');

  // Track previous value length to detect paste events
  const prevValueLenRef = React.useRef(0);

  // Ref for attachment function to use in effect
  const addAttachmentRef = React.useRef<(filePath: string) => void>();

  // Track when we just added an image via Ctrl+V to suppress subsequent pasted text
  const suppressPasteUntilRef = React.useRef(0);
  // Track paths we've already added as attachments to avoid duplicates
  const addedPathsRef = React.useRef<Set<string>>(new Set());

  // Listen for raw Ctrl+V (character code 22) directly on stdin
  useEffect(() => {
    const handleData = (data: Buffer) => {
      // Check for Ctrl+V (character code 22) anywhere in the data
      for (let i = 0; i < data.length; i++) {
        if (data[i] === 22) {
          const imagePath = saveClipboardImage();
          if (imagePath && addAttachmentRef.current) {
            addAttachmentRef.current(imagePath);
            // Track this path and suppress subsequent paste text
            addedPathsRef.current.add(imagePath);
            suppressPasteUntilRef.current = Date.now() + 500; // Suppress for 500ms
          }
          return;
        }
      }
    };

    // Use 'readable' event as backup
    const handleReadable = () => {
      let chunk;
      while ((chunk = process.stdin.read()) !== null) {
        if (Buffer.isBuffer(chunk)) {
          handleData(chunk);
        }
      }
    };

    process.stdin.on('data', handleData);
    process.stdin.on('readable', handleReadable);

    return () => {
      process.stdin.off('data', handleData);
      process.stdin.off('readable', handleReadable);
    };
  }, []);

  // Get colors based on mode
  const colors = MODE_COLORS[mode];
  const effectivePromptColor = promptColor ?? colors.accent;

  // Add image attachment
  const addAttachment = (filePath: string) => {
    const resolved = path.isAbsolute(filePath) ? filePath : path.resolve(process.cwd(), filePath);
    // Check if already attached
    if (localAttachments.some(a => a.path === resolved)) return;
    const newAttachment: ImageAttachment = {
      id: `img-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      path: resolved,
      name: path.basename(resolved),
    };
    const updated = [...localAttachments, newAttachment];
    setLocalAttachments(updated);
    onAttachmentsChange?.(updated);
  };

  // Keep ref updated for stdin listener
  addAttachmentRef.current = addAttachment;

  // Remove attachment by id
  const removeAttachment = (id: string) => {
    // Find the attachment to remove and clean up tracking
    const toRemove = localAttachments.find(a => a.id === id);
    if (toRemove) {
      addedPathsRef.current.delete(toRemove.path);
    }
    const updated = localAttachments.filter(a => a.id !== id);
    setLocalAttachments(updated);
    onAttachmentsChange?.(updated);
  };

  // Add file attachment (for @ mentions)
  const addFileAttachment = (filePath: string) => {
    const resolved = path.isAbsolute(filePath) ? filePath : path.resolve(process.cwd(), filePath);
    // Check if already attached
    if (localAttachments.some(a => a.path === resolved)) return;
    const newAttachment: ImageAttachment = {
      id: `file-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      path: resolved,
      name: path.basename(resolved),
    };
    const updated = [...localAttachments, newAttachment];
    setLocalAttachments(updated);
    onAttachmentsChange?.(updated);
  };

  // Handle file selection from menu
  const selectFile = (filePath: string) => {
    addFileAttachment(filePath);
    // Remove the @query from input
    const atIndex = value.lastIndexOf('@');
    if (atIndex !== -1) {
      const newValue = value.slice(0, atIndex);
      setValue(newValue);
      prevValueLenRef.current = newValue.length;
      onChange?.(newValue);
    }
    setShowFileMenu(false);
    setFileQuery('');
    setFileSuggestions([]);
    setFileMenuIndex(0);
  };

  // Track last check time to avoid repeated clipboard checks
  const lastClipboardCheckRef = React.useRef(0);

  // Wrapper to call onChange when value changes
  const updateValue = (newValue: string) => {
    // Check for @@ trigger to paste clipboard image
    if (newValue.endsWith('@@')) {
      const imagePath = saveClipboardImage();
      if (imagePath) {
        addAttachment(imagePath);
        addedPathsRef.current.add(imagePath);
        // Remove the @@ from input
        const cleanedValue = newValue.slice(0, -2);
        prevValueLenRef.current = cleanedValue.length;
        setValue(cleanedValue);
        onChange?.(cleanedValue);
        setShowFileMenu(false);
        return;
      }
    }

    // Early detection: Check if the value looks like a pasted image path
    // This handles Command+V pasting a file path directly
    const prevLen = prevValueLenRef.current;

    // Debug: always log what we receive
    const debugFile = '/tmp/tui-paste-debug.log';
    if (newValue.length > 10) {
      const debugLines = [
        `\n=== ${new Date().toISOString()} ===`,
        `newValue length: ${newValue.length}`,
        `newValue: ${JSON.stringify(newValue)}`,
        `starts with /: ${newValue.startsWith('/')}`,
        `trimmed starts with /: ${newValue.trim().startsWith('/')}`,
        `ends with .png: ${/\.png$/i.test(newValue)}`,
        `ends with image ext: ${/\.(png|jpg|jpeg|gif|webp|bmp|svg)$/i.test(newValue.trim())}`,
      ];
      fs.appendFileSync(debugFile, debugLines.join('\n') + '\n');
    }

    // Simple check: does it look like an image path? (starts with / or ~, ends with image extension)
    const trimmedValue = newValue.trim();
    const looksLikeImagePath = (trimmedValue.startsWith('/') || trimmedValue.startsWith('~')) &&
      /\.(png|jpg|jpeg|gif|webp|bmp|svg)$/i.test(trimmedValue);

    if (looksLikeImagePath) {
      // Debug: write to temp file
      const debugFile = '/tmp/tui-paste-debug.log';
      const debugInfo: string[] = [];
      debugInfo.push(`Time: ${new Date().toISOString()}`);
      debugInfo.push(`Raw value: ${newValue}`);
      debugInfo.push(`Trimmed: ${trimmedValue}`);

      // Use saveClipboardImage() to get the file from clipboard (same as @@)
      const imagePath = saveClipboardImage();
      debugInfo.push(`saveClipboardImage returned: ${imagePath}`);

      if (imagePath) {
        addAttachment(imagePath);
        addedPathsRef.current.add(imagePath);
        // Clear the entire input
        prevValueLenRef.current = 0;
        setValue('');
        onChange?.('');
        fs.appendFileSync(debugFile, debugInfo.join('\n') + '\nSUCCESS via saveClipboardImage\n\n');
        return;
      }

      // Fallback: try the normalized path directly
      const normalized = normalizePath(newValue);
      debugInfo.push(`Normalized: ${normalized}`);
      let resolvedPath = normalized;
      if (normalized.startsWith('~/')) {
        const home = process.env.HOME || '';
        resolvedPath = path.join(home, normalized.slice(2));
      }
      debugInfo.push(`Resolved: ${resolvedPath}`);
      debugInfo.push(`Exists: ${fs.existsSync(resolvedPath)}`);

      try {
        if (fs.existsSync(resolvedPath)) {
          addAttachment(resolvedPath);
          addedPathsRef.current.add(resolvedPath);
          prevValueLenRef.current = 0;
          setValue('');
          onChange?.('');
          fs.appendFileSync(debugFile, debugInfo.join('\n') + '\nSUCCESS via normalized path\n\n');
          return;
        }
      } catch (e) {
        debugInfo.push(`Error: ${e}`);
      }

      fs.appendFileSync(debugFile, debugInfo.join('\n') + '\nFAILED\n\n');
    }

    // Check for @ to trigger file menu
    const atIndex = newValue.lastIndexOf('@');
    if (atIndex !== -1 && atIndex === newValue.length - 1) {
      // Just typed @, show file menu with default files
      setShowFileMenu(true);
      setFileQuery('');
      setFileSuggestions(searchFiles(''));
      setFileMenuIndex(0);
    } else if (atIndex !== -1 && !newValue.slice(atIndex).includes(' ')) {
      // Typing after @, update search
      const query = newValue.slice(atIndex + 1);
      setFileQuery(query);
      setFileSuggestions(searchFiles(query));
      setFileMenuIndex(0);
      if (!showFileMenu) setShowFileMenu(true);
    } else if (showFileMenu) {
      // Space or no @ found, close menu
      setShowFileMenu(false);
      setFileQuery('');
    }

    const prevValue = value;
    const addedChars = newValue.length - prevLen;
    prevValueLenRef.current = newValue.length;

    // Only check for image paths on paste-like events (5+ chars added at once)
    // This avoids expensive fs.existsSync on every keystroke
    if (addedChars >= 5) {
      // Get only the newly pasted portion
      // Use prevLen (from ref) for consistency with addedChars calculation
      const pastedText = newValue.slice(prevLen);

      // Check if we're suppressing paste text (image was just added via Ctrl+V)
      // In this case, suppress any pasted file paths
      const now = Date.now();
      if (suppressPasteUntilRef.current > now) {
        // Check if pasted text looks like a file path
        const normalizedPaste = normalizePath(pastedText);
        const ext = path.extname(normalizedPaste).toLowerCase();
        if (IMAGE_EXTENSIONS.includes(ext) || addedPathsRef.current.has(normalizedPaste)) {
          // Suppress this paste - it's the path of an image we just added
          const textBeforePaste = newValue.slice(0, prevLen);
          prevValueLenRef.current = textBeforePaste.length;
          setValue(textBeforePaste);
          onChange?.(textBeforePaste);
          return;
        }
      }

      const imagePaths = extractImagePaths(pastedText);

      if (imagePaths.length > 0) {
        // Filter out paths we've already added
        const newPaths = imagePaths.filter(p => !addedPathsRef.current.has(p));

        if (newPaths.length > 0) {
          // Add new images as attachments
          for (const imgPath of newPaths) {
            addAttachment(imgPath);
            addedPathsRef.current.add(imgPath);
          }
        }
        // Keep only the text that was there before the paste
        const textBeforePaste = newValue.slice(0, prevLen);
        prevValueLenRef.current = textBeforePaste.length;
        setValue(textBeforePaste);
        onChange?.(textBeforePaste);
        return;
      }
    }

    // Check for bracketed paste start sequence or control chars that indicate paste attempt
    const now = Date.now();
    const pastedTextForCheck = newValue.slice(prevLen);

    // Detect various paste indicators:
    // - Bracketed paste: \x1b[200~ ... \x1b[201~
    // - Control characters
    // - Empty paste (Cmd+V with image might send nothing visible)
    const isBracketedPaste = pastedTextForCheck.includes('\x1b[200~') || pastedTextForCheck.includes('\x1b[201~');
    const hasControlChars = /[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/.test(pastedTextForCheck);
    const looksLikePasteAttempt = isBracketedPaste || hasControlChars;

    if (looksLikePasteAttempt && now - lastClipboardCheckRef.current > 300) {
      lastClipboardCheckRef.current = now;
      const imagePath = saveClipboardImage();
      if (imagePath) {
        addAttachment(imagePath);
        addedPathsRef.current.add(imagePath);
        suppressPasteUntilRef.current = Date.now() + 500; // Suppress for 500ms
        // Remove the paste artifacts from input
        const textBeforePaste = newValue.slice(0, prevLen);
        prevValueLenRef.current = textBeforePaste.length;
        setValue(textBeforePaste);
        onChange?.(textBeforePaste);
        return;
      }
    }

    setValue(newValue);
    onChange?.(newValue);

    // Typing indicator logic for multiuser
    if (onTypingChange && newValue.length > 0) {
      // User is typing - notify if not already notified
      if (!isTypingRef.current) {
        isTypingRef.current = true;
        onTypingChange(true);

        // Start periodic re-send interval (every 2.5s) to keep indicator alive
        // Receiver has 3s auto-clear, so we re-send before it expires
        if (typingIntervalRef.current) {
          clearInterval(typingIntervalRef.current);
        }
        typingIntervalRef.current = setInterval(() => {
          if (isTypingRef.current) {
            onTypingChange(true);
          }
        }, 2500);
      }

      // Clear existing timeout
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }

      // Set timeout to notify stopped typing after 2 seconds of inactivity
      typingTimeoutRef.current = setTimeout(() => {
        if (isTypingRef.current) {
          isTypingRef.current = false;
          onTypingChange(false);
          // Clear the interval when stopped typing
          if (typingIntervalRef.current) {
            clearInterval(typingIntervalRef.current);
            typingIntervalRef.current = null;
          }
        }
      }, 2000);
    } else if (onTypingChange && newValue.length === 0 && isTypingRef.current) {
      // Input cleared - stop typing
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      if (typingIntervalRef.current) {
        clearInterval(typingIntervalRef.current);
        typingIntervalRef.current = null;
      }
      isTypingRef.current = false;
      onTypingChange(false);
    }
  };

  useInput(
    (input, key) => {
      // File menu navigation (@ mentions)
      if (showFileMenu && fileSuggestions.length > 0) {
        if (key.escape) {
          setShowFileMenu(false);
          setFileQuery('');
          return;
        }
        if (key.return || key.tab) {
          // Select current file
          if (fileSuggestions[fileMenuIndex]) {
            selectFile(fileSuggestions[fileMenuIndex]);
          }
          return;
        }
        if (key.upArrow) {
          setFileMenuIndex(prev => prev > 0 ? prev - 1 : fileSuggestions.length - 1);
          return;
        }
        if (key.downArrow) {
          setFileMenuIndex(prev => prev < fileSuggestions.length - 1 ? prev + 1 : 0);
          return;
        }
        // Continue to allow typing for filtering
      }

      // In menu mode (command menu), handle navigation keys differently
      if (menuMode) {
        if (key.escape) {
          onMenuDismiss?.();
          return;
        }
        if (key.tab) {
          // Tab autocompletes the selected command without sending
          onMenuComplete?.(value);
          return;
        }
        if (key.return) {
          // Enter sends the command (will use selected command from menu)
          const currentValue = value;
          updateValue('');
          setCursorOffset(0);
          onMenuSelect?.(currentValue);
          return;
        }
        if (key.upArrow) {
          onMenuUp?.();
          return;
        }
        if (key.downArrow) {
          onMenuDown?.();
          return;
        }
      }

      // Shift+Enter or Ctrl+J - insert newline
      if ((key.shift && key.return) || (key.ctrl && input === 'j')) {
        const pos = value.length - cursorOffset;
        updateValue(value.slice(0, pos) + '\n' + value.slice(pos));
        return;
      }

      if (key.return) {
        // Double-check disabled state before submitting (handles race conditions)
        if (disabled) return;
        if (value.trim() || localAttachments.length > 0) {
          // Clear typing state on submit
          if (typingTimeoutRef.current) {
            clearTimeout(typingTimeoutRef.current);
          }
          if (isTypingRef.current && onTypingChange) {
            isTypingRef.current = false;
            onTypingChange(false);
          }
          onSubmit(value, localAttachments.length > 0 ? localAttachments : undefined);
          updateValue('');
          setCursorOffset(0);
          // Clear attachments after submit
          setLocalAttachments([]);
          onAttachmentsChange?.([]);
        }
        return;
      }

      if (key.backspace || key.delete) {
        if (cursorOffset < value.length) {
          const pos = value.length - cursorOffset;
          updateValue(value.slice(0, pos - 1) + value.slice(pos));
        }
        return;
      }

      if (key.leftArrow) {
        setCursorOffset(Math.min(cursorOffset + 1, value.length));
        return;
      }

      if (key.rightArrow) {
        setCursorOffset(Math.max(cursorOffset - 1, 0));
        return;
      }

      // Ctrl+A - move to start
      if (key.ctrl && input === 'a') {
        setCursorOffset(value.length);
        return;
      }

      // Ctrl+E - move to end
      if (key.ctrl && input === 'e') {
        setCursorOffset(0);
        return;
      }

      // Ctrl+U - clear line
      if (key.ctrl && input === 'u') {
        updateValue('');
        setCursorOffset(0);
        return;
      }

      // Ctrl+W - delete word
      if (key.ctrl && input === 'w') {
        const pos = value.length - cursorOffset;
        const beforeCursor = value.slice(0, pos);
        const afterCursor = value.slice(pos);
        // Find last word boundary
        const trimmed = beforeCursor.trimEnd();
        const lastSpace = trimmed.lastIndexOf(' ');
        const newBefore = lastSpace === -1 ? '' : trimmed.slice(0, lastSpace + 1);
        updateValue(newBefore + afterCursor);
        return;
      }

      // Ctrl+X - remove last attachment
      if (key.ctrl && input === 'x') {
        if (localAttachments.length > 0) {
          const lastAttachment = localAttachments[localAttachments.length - 1];
          removeAttachment(lastAttachment.id);
        }
        return;
      }

      // Ctrl+V - paste image from clipboard
      // Check multiple ways Ctrl+V might come through:
      // - key.ctrl + 'v'
      // - raw character code 22 (\x16)
      // - character code check
      const isCtrlV = (key.ctrl && input === 'v') ||
                      (key.meta && input === 'v') ||
                      input === '\x16' ||
                      input === '√' ||
                      (input.length === 1 && input.charCodeAt(0) === 22);
      if (isCtrlV) {
        const imagePath = saveClipboardImage();
        if (imagePath) {
          addAttachment(imagePath);
          // Track this path and suppress subsequent paste text
          addedPathsRef.current.add(imagePath);
          suppressPasteUntilRef.current = Date.now() + 500; // Suppress for 500ms
          return;
        }
        // If no image, let it fall through for normal paste
      }

      // Ctrl+C - handled by parent
      if (key.ctrl && input === 'c') {
        return;
      }

      // Regular character input
      if (input && !key.ctrl && !key.meta) {
        const pos = value.length - cursorOffset;
        updateValue(value.slice(0, pos) + input + value.slice(pos));
      }
    },
    { isActive: !disabled }
  );

  const displayValue = value || (disabled ? '' : placeholder);
  const isPlaceholder = !value && !disabled && placeholder;
  const cursorPos = value.length - cursorOffset;

  // Calculate available width for text (terminal width minus prompt and padding)
  const promptLen = prompt.length;
  const availableWidth = Math.max(20, terminalWidth - promptLen - 6); // 6 for padding/borders

  // Split text into visual lines (handling both newlines and wrapping)
  const getVisualLines = (text: string): { lines: string[]; cursorLine: number; cursorCol: number } => {
    const lines: string[] = [];
    let cursorLine = 0;
    let cursorCol = 0;
    let charIndex = 0;

    // Split by actual newlines first
    const segments = text.split('\n');

    for (let segIdx = 0; segIdx < segments.length; segIdx++) {
      const segment = segments[segIdx];

      if (segment.length === 0) {
        // Empty line (from newline character)
        if (charIndex <= cursorPos && cursorPos <= charIndex) {
          cursorLine = lines.length;
          cursorCol = 0;
        }
        lines.push('');
        charIndex++; // Account for the newline character
        continue;
      }

      // Wrap long lines
      let remaining = segment;
      let segmentCharIndex = 0;

      while (remaining.length > 0) {
        const lineText = remaining.slice(0, availableWidth);
        remaining = remaining.slice(availableWidth);

        // Check if cursor is in this visual line
        const lineStart = charIndex + segmentCharIndex;
        const lineEnd = lineStart + lineText.length;

        if (cursorPos >= lineStart && cursorPos < lineEnd) {
          cursorLine = lines.length;
          cursorCol = cursorPos - lineStart;
        } else if (cursorPos === lineEnd && remaining.length === 0 && segIdx === segments.length - 1) {
          // Cursor at very end
          cursorLine = lines.length;
          cursorCol = lineText.length;
        }

        lines.push(lineText);
        segmentCharIndex += lineText.length;
      }

      charIndex += segment.length + 1; // +1 for newline (except last segment)
    }

    // Handle cursor at very end of empty input
    if (lines.length === 0) {
      lines.push('');
      cursorLine = 0;
      cursorCol = 0;
    }

    return { lines, cursorLine, cursorCol };
  };

  // Render the text content with cursor, handling multi-line and wrapping
  const renderContent = () => {
    if (disabled) {
      return <Text color="#6a6a6a">{displayValue}</Text>;
    }

    if (isPlaceholder) {
      // Show placeholder with cursor at start
      return (
        <>
          <Text backgroundColor={colors.cursor} color={colors.cursorText}>{' '}</Text>
          <Text color="#5a5a5a" dimColor>{placeholder}</Text>
        </>
      );
    }

    const { lines, cursorLine, cursorCol } = getVisualLines(value);

    // Single line - simple rendering
    if (lines.length === 1) {
      const line = lines[0];
      const beforeCursor = line.slice(0, cursorCol);
      const cursorChar = line[cursorCol] || ' ';
      const afterCursor = line.slice(cursorCol + 1);

      return (
        <>
          <Text>{beforeCursor}</Text>
          <Text backgroundColor={colors.cursor} color={colors.cursorText}>
            {cursorChar}
          </Text>
          <Text>{afterCursor}</Text>
        </>
      );
    }

    // Multi-line rendering
    return (
      <Box flexDirection="column">
        {lines.map((line, lineIndex) => {
          if (lineIndex === cursorLine) {
            // This line has the cursor
            const beforeCursor = line.slice(0, cursorCol);
            const cursorChar = line[cursorCol] || ' ';
            const afterCursor = line.slice(cursorCol + 1);
            return (
              <Box key={lineIndex}>
                {lineIndex > 0 && <Text color={effectivePromptColor}>{'  '}</Text>}
                <Text>{beforeCursor}</Text>
                <Text backgroundColor={colors.cursor} color={colors.cursorText}>
                  {cursorChar}
                </Text>
                <Text>{afterCursor}</Text>
              </Box>
            );
          }
          // Other lines without cursor
          return (
            <Box key={lineIndex}>
              {lineIndex > 0 && <Text color={effectivePromptColor}>{'  '}</Text>}
              <Text>{line || ' '}</Text>
            </Box>
          );
        })}
      </Box>
    );
  };

  // Check if we have multiple visual lines
  const { lines } = value ? getVisualLines(value) : { lines: [''] };
  const isMultiLine = lines.length > 1;

  return (
    <Box flexDirection="column">
      {/* Attachments display */}
      {localAttachments.length > 0 && (
        <Box marginBottom={0}>
          <Text color="#5a5a5a">Attachments: </Text>
          {localAttachments.map((attachment, index) => {
            const isImage = IMAGE_EXTENSIONS.some(ext => attachment.name.toLowerCase().endsWith(ext));
            return (
              <React.Fragment key={attachment.id}>
                {index > 0 && <Text color="#4a4a4a"> </Text>}
                <Text color="#7a9fc9">[</Text>
                <Text color={isImage ? '#9ac9c9' : '#c9a075'}>
                  {attachment.name.length > 25 ? attachment.name.slice(0, 22) + '...' : attachment.name}
                </Text>
                <Text color="#7a9fc9">]</Text>
              </React.Fragment>
            );
          })}
          <Text color="#4a4a4a" dimColor> (Ctrl+X to remove)</Text>
        </Box>
      )}

      {/* File menu dropdown */}
      {showFileMenu && fileSuggestions.length > 0 && (
        <Box flexDirection="column" marginBottom={0}>
          <Text color="#5a5a5a" dimColor>Files matching @{fileQuery}:</Text>
          {fileSuggestions.slice(0, 8).map((file, index) => (
            <Box key={file}>
              <Text color={index === fileMenuIndex ? '#c9a075' : '#5a5a5a'}>
                {index === fileMenuIndex ? '› ' : '  '}
              </Text>
              <Text color={index === fileMenuIndex ? '#c9c9c9' : '#7a7a7a'}>
                {file}
              </Text>
            </Box>
          ))}
          {fileSuggestions.length > 8 && (
            <Text color="#4a4a4a" dimColor>  ... {fileSuggestions.length - 8} more</Text>
          )}
        </Box>
      )}
      <Box flexDirection={isMultiLine ? 'column' : 'row'}>
        {isMultiLine ? (
          // Multi-line: prompt on first line only
          <Box flexDirection="column">
            <Box>
              <Text color={effectivePromptColor} bold>{prompt}</Text>
              {renderContent()}
            </Box>
          </Box>
        ) : (
          // Single line: prompt inline
          <>
            <Text color={effectivePromptColor} bold>{prompt}</Text>
            {renderContent()}
          </>
        )}
      </Box>
      {showHints && !disabled && (
        <Box marginTop={0}>
          <Text color="#4a4a4a" dimColor>
            {menuMode ? '↑↓ navigate • Tab complete • Enter send • Esc cancel' : '/ commands • @ files • @@ paste image • Enter send'}
          </Text>
        </Box>
      )}
    </Box>
  );
}
