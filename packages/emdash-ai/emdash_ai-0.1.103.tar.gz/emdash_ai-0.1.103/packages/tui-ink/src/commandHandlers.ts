import { sendMessage } from './protocol.js';
import { copyToClipboard } from './utils/clipboard.js';
import { getLastResponse, getAllConversation } from './utils.js';
import React from 'react';
import type { Action, AppState } from './store.js';
import { LOCAL_COMMANDS } from './constants/commands.js';

/**
 * Handle local commands that don't need to go to Python backend
 * Returns true if the command was handled, false if it should be forwarded to the backend
 */
export async function handleLocalCommand(
  cmd: string,
  state: AppState,
  dispatch: React.Dispatch<Action>,
  exit: () => void
): Promise<boolean> {
  const parts = cmd.trim().split(/\s+/);
  const command = parts[0].toLowerCase();
  const args = parts.slice(1).join(' ');

  switch (command) {
    case '/help':
      dispatch({ type: 'SET_OVERLAY', payload: 'help' });
      return true;

    case '/copy': {
      const scope = args.toLowerCase() === 'all' ? 'all' : 'last';
      const textToCopy = scope === 'all' ? getAllConversation(state) : getLastResponse(state);

      if (!textToCopy) {
        dispatch({
          type: 'ADD_LOG',
          payload: {
            id: `system-${Date.now()}`,
            role: 'system' as const,
            content: scope === 'all' ? 'No conversation to copy' : 'No response to copy',
          },
        });
        return true;
      }

      const success = await copyToClipboard(textToCopy);
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `system-${Date.now()}`,
          role: 'system' as const,
          content: success
            ? `Copied ${scope === 'all' ? 'conversation' : 'last response'} to clipboard`
            : 'Failed to copy to clipboard',
        },
      });
      return true;
    }

    case '/plan':
      dispatch({ type: 'SET_MODE', payload: 'plan' });
      dispatch({ type: 'CLEAR_SESSION' });
      sendMessage({ type: 'set_mode', data: { mode: 'plan' } });
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `system-${Date.now()}`,
          role: 'system' as const,
          content: 'Switched to plan mode (session reset)',
        },
      });
      return true;

    case '/code':
      dispatch({ type: 'SET_MODE', payload: 'code' });
      dispatch({ type: 'CLEAR_SESSION' });
      sendMessage({ type: 'set_mode', data: { mode: 'code' } });
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `system-${Date.now()}`,
          role: 'system' as const,
          content: 'Switched to code mode (session reset)',
        },
      });
      return true;

    case '/mode':
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `system-${Date.now()}`,
          role: 'system' as const,
          content: `Current mode: ${state.mode}`,
        },
      });
      return true;

    case '/model':
      dispatch({ type: 'SET_OVERLAY', payload: 'model' });
      return true;

    case '/registry':
      // Request registry data from backend - it will send registry_browse event
      dispatch({ type: 'SET_PROCESSING', payload: true });
      sendMessage({ type: 'user_input', data: { content: '/registry' } });
      return true;

    case '/skills':
      // Request skills data from backend - it will send skills_browse event
      dispatch({ type: 'SET_PROCESSING', payload: true });
      sendMessage({ type: 'user_input', data: { content: '/skills' } });
      return true;

    case '/rules':
      // Request rules data from backend - it will send rules_browse event
      dispatch({ type: 'SET_PROCESSING', payload: true });
      sendMessage({ type: 'user_input', data: { content: '/rules' } });
      return true;

    case '/hooks':
      // Request hooks data from backend - it will send hooks_browse event
      dispatch({ type: 'SET_PROCESSING', payload: true });
      sendMessage({ type: 'user_input', data: { content: '/hooks' } });
      return true;

    case '/mcp':
      // Request MCP data from backend - it will send mcp_browse event
      dispatch({ type: 'SET_PROCESSING', payload: true });
      sendMessage({ type: 'user_input', data: { content: '/mcp' } });
      return true;

    case '/agents':
      // Request agents data from backend - it will send agents_browse event
      dispatch({ type: 'SET_PROCESSING', payload: true });
      sendMessage({ type: 'user_input', data: { content: '/agents' } });
      return true;

    case '/verify':
      // Request verifiers data from backend - it will send verifiers_browse event
      dispatch({ type: 'SET_PROCESSING', payload: true });
      sendMessage({ type: 'user_input', data: { content: '/verify' } });
      return true;

    case '/reset':
      dispatch({ type: 'CLEAR_SESSION' });
      dispatch({ type: 'CLEAR_LOG' });
      sendMessage({ type: 'reset_session', data: {} });
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `system-${Date.now()}`,
          role: 'system' as const,
          content: 'Session reset',
        },
      });
      return true;

    case '/quit':
    case '/exit':
    case '/q':
      sendMessage({ type: 'quit', data: {} });
      exit();
      return true;

    default:
      return false;
  }
}