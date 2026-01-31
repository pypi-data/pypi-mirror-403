/**
 * Slash command definitions for the TUI.
 * Ported from packages/cli/emdash_cli/tui/constants.py
 */

export type CommandCategory =
  | 'local'
  | 'session'
  | 'repository'
  | 'configuration'
  | 'collaboration'
  | 'advanced'
  | 'auth';

export interface SlashCommand {
  command: string;
  description: string;
  isLocal: boolean;
  category: CommandCategory;
}

/**
 * All available slash commands.
 * isLocal: true = handled by TUI directly, false = sent to handler (which may call API)
 */
export const SLASH_COMMANDS: SlashCommand[] = [
  // Local commands (handled by TUI directly)
  { command: '/help', description: 'Show available commands', isLocal: true, category: 'local' },
  { command: '/copy', description: 'Copy last response', isLocal: true, category: 'local' },
  { command: '/copy all', description: 'Copy entire conversation', isLocal: true, category: 'local' },
  { command: '/plan', description: 'Switch to plan mode', isLocal: true, category: 'local' },
  { command: '/code', description: 'Switch to code mode', isLocal: true, category: 'local' },
  { command: '/mode', description: 'Show current mode', isLocal: true, category: 'local' },
  { command: '/model', description: 'Switch model (picker)', isLocal: true, category: 'local' },
  { command: '/reset', description: 'Reset session', isLocal: true, category: 'local' },
  { command: '/quit', description: 'Exit', isLocal: true, category: 'local' },

  // Session commands (via handler -> API)
  { command: '/stats', description: 'Token usage & cost', isLocal: false, category: 'session' },
  { command: '/todos', description: 'Agent todo list', isLocal: false, category: 'session' },
  { command: '/todo-add', description: 'Add a todo', isLocal: false, category: 'session' },
  { command: '/context', description: 'Context usage', isLocal: false, category: 'session' },
  { command: '/messages', description: 'Conversation history', isLocal: false, category: 'session' },
  { command: '/compact', description: 'Compact conversation', isLocal: false, category: 'session' },
  { command: '/session', description: 'Save/load sessions', isLocal: false, category: 'session' },

  // Repository commands
  { command: '/status', description: 'Index status', isLocal: false, category: 'repository' },
  { command: '/diff', description: 'Git diff', isLocal: false, category: 'repository' },
  { command: '/doctor', description: 'Run diagnostics', isLocal: false, category: 'repository' },
  { command: '/projectmd', description: 'Generate PROJECT.md', isLocal: false, category: 'repository' },
  { command: '/index', description: 'Manage codebase index', isLocal: false, category: 'repository' },

  // Configuration commands
  { command: '/setup', description: 'Setup wizard', isLocal: false, category: 'configuration' },
  { command: '/registry', description: 'Browse community registry', isLocal: true, category: 'configuration' },
  { command: '/skills', description: 'Manage skills', isLocal: true, category: 'configuration' },
  { command: '/agents', description: 'Manage agents', isLocal: true, category: 'configuration' },
  { command: '/rules', description: 'Manage rules', isLocal: true, category: 'configuration' },
  { command: '/hooks', description: 'Manage hooks', isLocal: true, category: 'configuration' },
  { command: '/verify', description: 'Manage verifiers', isLocal: true, category: 'configuration' },
  { command: '/mcp', description: 'Manage MCP servers', isLocal: true, category: 'configuration' },

  // Collaboration commands
  { command: '/share', description: 'Share session', isLocal: false, category: 'collaboration' },
  { command: '/join', description: 'Join session', isLocal: false, category: 'collaboration' },
  { command: '/leave', description: 'Leave session', isLocal: false, category: 'collaboration' },
  { command: '/who', description: 'Participants', isLocal: false, category: 'collaboration' },
  { command: '/invite', description: 'Show invite code', isLocal: false, category: 'collaboration' },
  { command: '/team', description: 'Manage teams', isLocal: false, category: 'collaboration' },

  // Advanced commands
  { command: '/pr', description: 'Review a PR', isLocal: false, category: 'advanced' },
  { command: '/research', description: 'Deep research', isLocal: false, category: 'advanced' },

  // Auth
  { command: '/auth', description: 'Authentication', isLocal: false, category: 'auth' },
  { command: '/telegram', description: 'Telegram integration', isLocal: false, category: 'auth' },
];

/**
 * Get commands for the autocomplete menu (command + description pairs)
 */
export const SLASH_COMMANDS_MENU: Array<{ command: string; description: string }> =
  SLASH_COMMANDS.map(({ command, description }) => ({ command, description }));

/**
 * Set of local commands (base command only, without arguments) for quick lookup
 */
export const LOCAL_COMMANDS: Set<string> = new Set(
  SLASH_COMMANDS.filter((cmd) => cmd.isLocal).map((cmd) => cmd.command.split(' ')[0])
);

/**
 * Get commands by category
 */
export function getCommandsByCategory(category: CommandCategory): SlashCommand[] {
  return SLASH_COMMANDS.filter((cmd) => cmd.category === category);
}

/**
 * Get all categories in display order
 */
export const CATEGORY_ORDER: CommandCategory[] = [
  'local',
  'session',
  'repository',
  'configuration',
  'collaboration',
  'advanced',
  'auth',
];

/**
 * Human-readable category labels
 */
export const CATEGORY_LABELS: Record<CommandCategory, string> = {
  local: 'Local',
  session: 'Session',
  repository: 'Repository',
  configuration: 'Configuration',
  collaboration: 'Collaboration',
  advanced: 'Advanced',
  auth: 'Auth',
};

/**
 * Category colors (using terminal color codes)
 */
export const CATEGORY_COLORS: Record<CommandCategory, string> = {
  local: '#7a9f7a',       // Green - local commands
  session: '#9f9f7a',     // Yellow - session commands
  repository: '#7a9f9f',  // Cyan - repository commands
  configuration: '#9f7a9f', // Magenta - config commands
  collaboration: '#7a7a9f', // Blue - collaboration commands
  advanced: '#9f7a7a',    // Red - advanced commands
  auth: '#7a7a7a',        // Gray - auth commands
};
