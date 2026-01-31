import React from 'react';
import type { IncomingEvent } from './protocol.js';
import type { RegistryData, ConfigType } from './components/index.js';

// ============================================================================
// State Types
// ============================================================================

type ToolStatus = 'running' | 'complete' | 'error';

export interface TodoItem {
  id: string;
  subject: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed';
  activeForm?: string;
}

interface LogEntry {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'thinking' | 'tool';
  content: string;
  name?: string;
  toolName?: string;
  toolArgs?: Record<string, unknown>;
  success?: boolean;
  /** Tool execution status for animated display */
  toolStatus?: ToolStatus;
  /** Indentation level for subagent tool calls */
  indentLevel?: number;
  /** Server timestamp for proper chronological ordering in multiuser mode */
  timestamp?: string;
}

interface TypingUser {
  id: string;
  name: string;
}

type OverlayType = 'none' | 'help' | 'model' | 'commandMenu' | 'registry' | 'skills' | 'rules' | 'hooks' | 'mcp' | 'agents' | 'verifiers';

interface ConfigData {
  skills?: { skills: Array<{ name: string; description?: string }> };
  rules?: { rules: Array<{ name: string; description?: string }> };
  hooks?: { hooks: Array<{ name: string; trigger?: string }>; events: string[] };
  mcp?: { servers: Array<{ name: string; command?: string }> };
  agents?: { agents: Array<{ name: string; description?: string }> };
  verifiers?: { verifiers: Array<{ name: string; description?: string }> };
}

interface AppState {
  version: string;
  model: string;
  mode: 'code' | 'plan';
  cwd: string;
  sessionId?: string;
  isProcessing: boolean;
  log: LogEntry[];
  currentThinking: string;
  currentResponse: string;
  streamResponse: string; // Buffer for streaming response
  hadStreaming: boolean; // Track if streaming happened (to avoid duplicate response content)
  typingUsers: TypingUser[];
  activeQuestion: {
    question: string;
    options: Array<{
      label: string;
      description?: string;
    }>;
    id?: string;
  } | null;
  showApproval: boolean;
  approvalType: 'planmode' | 'plan' | null;  // Which type of approval is needed
  overlay: OverlayType;
  commandMenuFilter: string;
  commandMenuIndex: number;
  selectedIndex: number; // For command menu selection
  showCommandMenu: boolean;
  registryData: RegistryData | null;
  configData: ConfigData;
  availableModels: string[]; // Available models from backend
  todos: TodoItem[]; // Task todos from agent
  /** Track pending tool calls to merge args with results */
  pendingTools: Map<string, { args: Record<string, unknown>; logId: string }>;
  multiuser: {
    sessionId?: string;
    userId?: string;
    serverUrl?: string;
    isOwner: boolean;
    participantCount: number;
  };
  /** Current subagent nesting depth for indentation */
  subagentDepth: number;
}

type Action =
  | { type: 'INIT'; payload: { model: string; mode: 'code' | 'plan'; cwd: string } }
  | { type: 'SET_STATUS'; payload: { mode: 'code' | 'plan'; model: string; availableModels: string[]; version?: string } }
  | { type: 'SET_VERSION'; payload: string }
  | { type: 'SET_MODE'; payload: 'code' | 'plan' }
  | { type: 'SET_MODEL'; payload: string }
  | { type: 'SET_AVAILABLE_MODELS'; payload: string[] }
  | { type: 'SET_PROCESSING'; payload: boolean }
  | { type: 'ADD_LOG'; payload: LogEntry }
  | { type: 'HANDLE_RESPONSE_EVENT'; payload: { content: string } }
  | { type: 'CLEAR_LOG' }
  | { type: 'SET_THINKING'; payload: string }
  | { type: 'APPEND_THINKING'; payload: string }
  | { type: 'SET_RESPONSE'; payload: string }
  | { type: 'APPEND_RESPONSE'; payload: string }
  | { type: 'STREAM_APPEND'; payload: string }
  | { type: 'STREAM_COMPLETE'; payload: null }
  | { type: 'STREAM_RESET' }
  | { type: 'FLUSH_RESPONSE' }
  | { type: 'ADD_TODO'; payload: TodoItem }
  | { type: 'UPDATE_TODO'; payload: { id: string; updates: Partial<TodoItem> } }
  | { type: 'SET_TODOS'; payload: TodoItem[] }
  | { type: 'CLEAR_TODOS' }
  | { type: 'ADD_TYPING_USER'; payload: TypingUser }
  | { type: 'REMOVE_TYPING_USER'; payload: string }
  | { type: 'SET_QUESTION'; payload: AppState['activeQuestion'] }
  | { type: 'SET_APPROVAL'; payload: { show: boolean; approvalType?: 'planmode' | 'plan' | null } }
  | { type: 'SET_SESSION'; payload: string }
  | { type: 'CLEAR_SESSION' }
  | { type: 'SET_MULTIUSER'; payload: Partial<AppState['multiuser']> }
  | { type: 'CLEAR_MULTIUSER' }
  | { type: 'SET_OVERLAY'; payload: OverlayType }
  | { type: 'SET_COMMAND_FILTER'; payload: string }
  | { type: 'SET_SELECTED_INDEX'; payload: number }
  | { type: 'SET_COMMAND_MENU_INDEX'; payload: number }
  | { type: 'SET_SHOW_COMMAND_MENU'; payload: boolean }
  | { type: 'SET_REGISTRY_DATA'; payload: RegistryData | null }
  | { type: 'SET_CONFIG_DATA'; payload: { type: ConfigType; data: ConfigData[ConfigType] } }
  | { type: 'CLEAR_CONFIG_DATA' }
  | { type: 'SET_PENDING_TOOL'; payload: { name: string; args: Record<string, unknown>; logId: string } }
  | { type: 'CLEAR_PENDING_TOOL'; payload: string }
  | { type: 'UPDATE_LOG'; payload: { id: string; updates: Partial<LogEntry> } }
  | { type: 'SUBAGENT_START' }
  | { type: 'SUBAGENT_END' };

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'INIT':
      return {
        ...state,
        model: action.payload.model,
        mode: action.payload.mode,
        cwd: action.payload.cwd,
      };

    case 'SET_STATUS':
      return {
        ...state,
        mode: action.payload.mode,
        model: action.payload.model,
        availableModels: action.payload.availableModels,
        ...(action.payload.version && { version: action.payload.version }),
      };

    case 'SET_VERSION':
      return { ...state, version: action.payload };

    case 'SET_MODE':
      return { ...state, mode: action.payload };

    case 'SET_MODEL':
      return { ...state, model: action.payload };

    case 'SET_AVAILABLE_MODELS':
      return { ...state, availableModels: action.payload };

    case 'SET_PROCESSING':
      // When processing ends, clear the hadStreaming flag
      if (!action.payload) {
        return { ...state, isProcessing: action.payload, hadStreaming: false };
      }
      return { ...state, isProcessing: action.payload };

    case 'ADD_LOG': {
      // Add current subagent depth as indent level
      const newEntry = { ...action.payload, indentLevel: action.payload.indentLevel ?? state.subagentDepth };

      // If the entry has a timestamp (from multiuser SSE), insert in chronological order
      // to handle out-of-order message delivery
      if (newEntry.timestamp && state.log.length > 0) {
        const newTime = new Date(newEntry.timestamp).getTime();
        // Find the correct insertion point
        let insertIndex = state.log.length;
        for (let i = state.log.length - 1; i >= 0; i--) {
          const entry = state.log[i];
          if (entry.timestamp) {
            const entryTime = new Date(entry.timestamp).getTime();
            if (entryTime <= newTime) {
              insertIndex = i + 1;
              break;
            }
            insertIndex = i;
          } else {
            // Stop at entries without timestamps (they're in order already)
            insertIndex = i + 1;
            break;
          }
        }
        const newLog = [...state.log];
        newLog.splice(insertIndex, 0, newEntry);
        return { ...state, log: newLog };
      }

      // Default: append to end
      return {
        ...state,
        log: [...state.log, newEntry],
      };
    }

    case 'HANDLE_RESPONSE_EVENT': {
      // Handle response event with current state's hadStreaming check
      // This fixes the stale closure issue where eventHandlers.ts was checking
      // a stale state.hadStreaming value from the callback closure
      const content = action.payload.content;

      // First, flush any pending stream content as a fallback
      // (in case chat_complete was missed or arrived out of order)
      let newLog = state.log;
      if (state.streamResponse) {
        newLog = [
          ...state.log,
          {
            id: `stream-response-${Date.now()}`,
            role: 'assistant' as const,
            content: state.streamResponse,
            indentLevel: state.subagentDepth,
          },
        ];
      }

      // If no streaming happened and response has content, add it
      if (content && !state.hadStreaming && !state.streamResponse) {
        newLog = [
          ...newLog,
          {
            id: `response-${Date.now()}`,
            role: 'assistant' as const,
            content: content,
            indentLevel: state.subagentDepth,
          },
        ];
      }

      return {
        ...state,
        log: newLog,
        streamResponse: '',
        hadStreaming: false,
        isProcessing: false,
      };
    }

    case 'UPDATE_LOG':
      return {
        ...state,
        log: state.log.map((entry) =>
          entry.id === action.payload.id ? { ...entry, ...action.payload.updates } : entry
        ),
      };

    case 'CLEAR_LOG':
      return { ...state, log: [] };

    case 'SET_THINKING':
      return { ...state, currentThinking: action.payload };

    case 'APPEND_THINKING':
      return { ...state, currentThinking: state.currentThinking + action.payload };

    case 'SET_RESPONSE':
      return { ...state, currentResponse: action.payload };

    case 'APPEND_RESPONSE':
      return { ...state, currentResponse: state.currentResponse + action.payload };

    case 'STREAM_APPEND':
      return { ...state, streamResponse: state.streamResponse + action.payload, hadStreaming: true };

    case 'STREAM_COMPLETE':
      // Flush the stream response to a log entry
      if (!state.streamResponse) return state;
      return {
        ...state,
        log: [
          ...state.log,
          {
            id: `response-${Date.now()}`,
            role: 'assistant' as const,
            content: state.streamResponse,
          },
        ],
        streamResponse: '',
      };

    case 'STREAM_RESET':
      // Flush any pending stream and reset (used when new message sent)
      if (!state.streamResponse) return { ...state, streamResponse: '', hadStreaming: false };
      return {
        ...state,
        log: [
          ...state.log,
          {
            id: `response-${Date.now()}`,
            role: 'assistant' as const,
            content: state.streamResponse,
          },
        ],
        streamResponse: '',
        hadStreaming: false,
      };

    case 'FLUSH_RESPONSE':
      if (!state.currentResponse) return state;
      return {
        ...state,
        log: [
          ...state.log,
          {
            id: `response-${Date.now()}`,
            role: 'assistant' as const,
            content: state.currentResponse,
          },
        ],
        currentResponse: '',
        currentThinking: '',
      };

    case 'ADD_TYPING_USER':
      if (state.typingUsers.some((u) => u.id === action.payload.id)) {
        return state;
      }
      return { ...state, typingUsers: [...state.typingUsers, action.payload] };

    case 'REMOVE_TYPING_USER':
      return {
        ...state,
        typingUsers: state.typingUsers.filter((u) => u.id !== action.payload),
      };

    case 'SET_QUESTION':
      return { ...state, activeQuestion: action.payload };

    case 'SET_APPROVAL':
      return {
        ...state,
        showApproval: action.payload.show,
        approvalType: action.payload.show ? (action.payload.approvalType ?? state.approvalType) : null,
      };

    case 'SET_SESSION':
      return { ...state, sessionId: action.payload };

    case 'CLEAR_SESSION':
      return { ...state, sessionId: undefined };

    case 'SET_MULTIUSER':
      return { ...state, multiuser: { ...state.multiuser, ...action.payload } };

    case 'CLEAR_MULTIUSER':
      return {
        ...state,
        multiuser: { isOwner: false, participantCount: 0 },
        typingUsers: [],
      };

    case 'SET_OVERLAY':
      return { ...state, overlay: action.payload };

    case 'SET_COMMAND_FILTER':
      return { ...state, commandMenuFilter: action.payload, commandMenuIndex: 0 };

    case 'SET_COMMAND_MENU_INDEX':
    case 'SET_SELECTED_INDEX':
      return { ...state, commandMenuIndex: action.payload };

    case 'SET_SHOW_COMMAND_MENU':
      return { ...state, showCommandMenu: action.payload, commandMenuIndex: 0, selectedIndex: 0 };

    case 'SET_REGISTRY_DATA':
      return { ...state, registryData: action.payload };

    case 'SET_CONFIG_DATA':
      return {
        ...state,
        configData: {
          ...state.configData,
          [action.payload.type]: action.payload.data,
        },
      };

    case 'CLEAR_CONFIG_DATA':
      return { ...state, configData: {} };

    case 'SET_PENDING_TOOL': {
      const newPendingTools = new Map(state.pendingTools);
      newPendingTools.set(action.payload.name, { args: action.payload.args, logId: action.payload.logId });
      return { ...state, pendingTools: newPendingTools };
    }

    case 'CLEAR_PENDING_TOOL': {
      const newPendingTools = new Map(state.pendingTools);
      newPendingTools.delete(action.payload);
      return { ...state, pendingTools: newPendingTools };
    }

    case 'ADD_TODO':
      // Don't add if already exists
      if (state.todos.some(t => t.id === action.payload.id)) {
        return state;
      }
      return { ...state, todos: [...state.todos, action.payload] };

    case 'UPDATE_TODO':
      return {
        ...state,
        todos: state.todos.map(t =>
          t.id === action.payload.id ? { ...t, ...action.payload.updates } : t
        ),
      };

    case 'SET_TODOS':
      return { ...state, todos: action.payload };

    case 'CLEAR_TODOS':
      return { ...state, todos: [] };

    case 'SUBAGENT_START':
      return { ...state, subagentDepth: state.subagentDepth + 1 };

    case 'SUBAGENT_END':
      return { ...state, subagentDepth: Math.max(0, state.subagentDepth - 1) };

    default:
      return state;
  }
}

const initialState: AppState = {
  model: process.env.EMDASH_MODEL || 'claude-sonnet-4',
  mode: 'code',
  cwd: process.cwd(),
  version: '',
  isProcessing: false,
  log: [],
  currentThinking: '',
  currentResponse: '',
  streamResponse: '',
  hadStreaming: false,
  typingUsers: [],
  activeQuestion: null,
  showApproval: false,
  approvalType: null,
  overlay: 'none',
  commandMenuFilter: '',
  commandMenuIndex: 0,
  selectedIndex: 0,
  showCommandMenu: false,
  registryData: null,
  configData: {},
  availableModels: [],
  todos: [],
  pendingTools: new Map(),
  multiuser: {
    isOwner: false,
    participantCount: 0,
  },
  subagentDepth: 0,
};

/**
 * Custom hook for app state management with useReducer
 */
export function useStore(): [AppState, React.Dispatch<Action>] {
  return React.useReducer(reducer, initialState);
}

// Export for direct use in App.tsx
export { reducer, initialState };

// Export types for use in other modules
export type { AppState, Action, LogEntry, TypingUser, OverlayType, ConfigData };