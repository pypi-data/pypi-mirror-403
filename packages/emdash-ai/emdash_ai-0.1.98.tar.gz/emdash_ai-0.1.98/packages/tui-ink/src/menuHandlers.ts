import type { AppState, Action } from './store.js';

/**
 * Handle command menu navigation and selection
 */
export function handleCommandMenuKeyDown(
  key: string,
  selectedIndex: number,
  commands: Array<{ cmd: string; desc: string }>,
  filter: string,
  dispatch: React.Dispatch<Action>,
  onSubmit: (cmd: string) => void
): void {
  switch (key) {
    case 'up':
    case 'k':
      dispatch({ type: 'SET_SELECTED_INDEX', payload: Math.max(0, selectedIndex - 1) });
      break;
    case 'down':
    case 'j':
      const newIndex = Math.min(commands.length - 1, selectedIndex + 1);
      dispatch({ type: 'SET_SELECTED_INDEX', payload: newIndex });
      break;
    case 'enter':
      if (commands[selectedIndex]) {
        onSubmit(commands[selectedIndex].cmd);
      }
      break;
    default:
      break;
  }
}

export function handleCommandMenuFilter(
  value: string,
  commands: Array<{ cmd: string; desc: string }>,
  selectedIndex: number,
  dispatch: React.Dispatch<Action>
): void {
  // Just update filter
  dispatch({ type: 'SET_COMMAND_FILTER', payload: value });
  // Reset selection to 0 when filtering
  dispatch({ type: 'SET_SELECTED_INDEX', payload: 0 });
}

export function getFilteredCommands(
  commands: Array<{ cmd: string; desc: string }>,
  filter: string
): Array<{ cmd: string; desc: string }> {
  if (!filter) return commands;
  const lowerFilter = filter.toLowerCase();
  return commands.filter(
    (c) =>
      c.cmd.toLowerCase().includes(lowerFilter) ||
      c.desc.toLowerCase().includes(lowerFilter)
  );
}