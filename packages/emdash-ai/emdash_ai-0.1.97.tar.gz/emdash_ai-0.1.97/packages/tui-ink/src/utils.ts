import type { AppState, LogEntry } from './store.js';

/**
 * All supported slash commands
 */
export const ALL_COMMANDS = [
  // Config management commands
  '/help', '/copy', '/plan', '/code', '/mode', '/model', '/reset', '/quit', '/exit', '/q',
  '/registry', '/skills', '/rules', '/hooks', '/mcp', '/agents', '/verify',
];

/**
 * Determine the prompt character based on current state
 */
export function getPromptText(showApproval: boolean, mode: string): string {
  if (showApproval) return '? ';
  if (mode === 'plan') return '? ';
  return '› ';
}

export function getPrompt(state: AppState): string {
  return getPromptText(state.showApproval, state.mode);
}

/**
 * Get all slash commands
 */
export function getAllCommands(): string[] {
  return ALL_COMMANDS;
}

/**
 * Get filtered commands based on filter
 */
export function getFilteredCommands(filter: string): Array<{ command: string; desc: string }> {
  const commands = [
    { command: '/help', desc: 'Show help' },
    { command: '/copy', desc: 'Copy conversation/response to clipboard' },
    { command: '/plan', desc: 'Switch to plan mode' },
    { command: '/code', desc: 'Switch to code mode' },
    { command: '/mode', desc: 'Show current mode' },
    { command: '/model', desc: 'Change model' },
    { command: '/reset', desc: 'Reset session' },
    { command: '/quit', desc: 'Quit' },
    { command: '/registry', desc: 'Browse registry' },
    { command: '/skills', desc: 'Browse skills' },
    { command: '/rules', desc: 'Browse rules' },
    { command: '/hooks', desc: 'Browse hooks' },
    { command: '/mcp', desc: 'Browse MCP servers' },
    { command: '/agents', desc: 'Browse agents' },
    { command: '/verify', desc: 'Browse verifiers' },
  ];

  if (!filter) return [];
  const lowerFilter = filter.toLowerCase();
  return commands.filter(c =>
    c.command.toLowerCase().includes(lowerFilter) ||
    c.desc.toLowerCase().includes(lowerFilter)
  ).slice(0, 10); // Limit to 10
}

/**
 * Determine the prompt color based on current state
 */
export function getPromptColor(state: AppState): string {
  if (state.showApproval || state.mode === 'plan') return '#c97590';
  return '#ba9f6a';
}

/**
 * Get the last assistant response from the log
 */
export function getLastResponse(state: AppState): string {
  for (let i = state.log.length - 1; i >= 0; i--) {
    if (state.log[i].role === 'assistant') {
      return state.log[i].content;
    }
  }
  return '';
}

/**
 * Get all conversation content (user and assistant messages)
 */
export function getAllConversation(state: AppState): string {
  return state.log
    .filter((entry) => entry.role === 'user' || entry.role === 'assistant')
    .map((entry) => {
      const prefix = entry.role === 'user' ? 'User' : 'Assistant';
      return `${prefix}: ${entry.content}`;
    })
    .join('\n\n');
}

/**
 * Determine if the current overlay should show full screen
 */
export function shouldShowFullScreenOverlay(state: AppState): boolean {
  return false;
}

/**
 * Get visible log entries filtered to fit in terminal
 */
export function getVisibleLog(state: AppState, maxLines: number): LogEntry[] {
  // Filter out entries with empty content and interactive tool prompts
  const filteredLog = state.log.filter((entry) => {
    // Filter out interactive prompt tools - they show as ChoicePrompt, not log entries
    if (entry.role === 'tool') {
      const name = entry.toolName?.toLowerCase();
      if (name === 'ask_choice_questions' || name === 'askuserquestion') {
        return false;
      }
      return true; // Other tools show toolName even without content
    }
    return entry.content && entry.content.trim().length > 0;
  });

  return filteredLog.slice(-maxLines);
}

/**
 * Filter log entries excluding empty content and interactive prompts
 */
export function filterLog(state: AppState): LogEntry[] {
  return state.log.filter((entry) => {
    // Filter out interactive prompt tools - they show as ChoicePrompt, not log entries
    if (entry.role === 'tool') {
      const name = entry.toolName?.toLowerCase();
      if (name === 'ask_choice_questions' || name === 'askuserquestion') {
        return false;
      }
      return true; // Other tools show toolName even without content
    }
    return entry.content && entry.content.trim().length > 0;
  });
}

/**
 * Check if input should be disabled
 */
export function isInputDisabled(state: AppState, hasInputSupport: boolean): boolean {
  return (
    !hasInputSupport ||
    state.isProcessing ||
    state.showApproval ||
    state.activeQuestion !== null ||
    state.overlay !== 'none'
  );
}

/**
 * Get reserved lines calculation for layout
 */
export function getReservedLines(state: AppState): number {
  // Reserve space for: status bar (1) + input box (3) + command menu (up to 12)
  return state.showCommandMenu ? 16 : 4;
}