import React, { useState, useEffect, useCallback } from 'react';
import { Box, Text, useApp, useInput, useStdout } from 'ink';
import * as readline from 'readline';

import {
  Spinner,
  Message,
  Input,
  CommandMenu,
  ChoicePrompt,
  ApprovalPrompt,
  StatusBar,
  TypingIndicator,
  HelpDisplay,
  ModelPicker,
  RegistryBrowser,
  ConfigWizard,
  Welcome,
  LogView,
  TodoList,
  DEFAULT_PROVIDERS,
  type ImageAttachment,
} from './components/index.js';

import { sendMessage, parseIncomingEvent, type IncomingEvent, type Question } from './protocol.js';
import { useStore, initialState } from './store.js';
import {
  getPromptText,
  getPromptColor,
  getVisibleLog,
  getFilteredCommands,
  isInputDisabled,
} from './utils.js';
import { handleLocalCommand } from './commandHandlers.js';
import {
  handleSubmit,
  handleChoiceSelect,
  handleApprove,
  handleReject,
  handleReply,
  handleOverlayDismiss,
  handleModelSelect,
  handleRegistryInstall,
  handleRegistryDismiss,
  handleConfigDismiss,
  handleConfigAction,
} from './uiHandlers.js';
import { processEvent } from './eventHandlers.js';
import type { AppState, Action } from './store.js';

interface AppProps {
  bridgeMode?: boolean;
  hasInputSupport?: boolean;
}

export default function App({ bridgeMode = false, hasInputSupport = true }: AppProps) {
  const { exit } = useApp();
  const { stdout } = useStdout();

  // Use our centralized store
  const [state, dispatch] = useStore();
  const inputEnabled = true;

  // Ref for pending tools (need for tool_start/tool_result synchronization)
  const pendingToolsRef = React.useRef<Map<string, { args: Record<string, unknown>; logId: string; toolName: string }>>(new Map());

  // Ref to track command menu state without causing callback recreation
  const commandMenuStateRef = React.useRef({ showMenu: false, filter: '' });

  // Ref to immediately block input submission (avoids React state batching delay)
  const isSubmittingRef = React.useRef(false);

  /**
   * Handle incoming events from Python backend
   * Delegates to handler modules or handles special cases (multiuser, tool tracking)
   */
  const handleEvent = useCallback(
    async (event: IncomingEvent & { data?: unknown; _source_user_id?: string }) => {
      // Special handling for events that can't be in eventHandlers (need async context)
      // First try to process common events
      if (
        event.type === 'chat_chunk' ||
        event.type === 'chat_complete' ||
        event.type === 'chat_message' ||
        event.type === 'error' ||
        event.type === 'response' ||
        event.type === 'partial_response' ||
        event.type === 'thinking' ||
        event.type === 'assistant_text' ||
        event.type === 'set_processing' ||
        event.type === 'set_mode' ||
        event.type === 'set_model' ||
        event.type === 'update_available_models' ||
        event.type === 'request_approval' ||
        event.type === 'execution_started' ||
        event.type === 'execution_completed' ||
        event.type === 'execution_failed' ||
        event.type === 'clear_display' ||
        event.type === 'reset_session' ||
        event.type === 'registry_browse' ||
        event.type === 'skills_browse' ||
        event.type === 'rules_browse' ||
        event.type === 'hooks_browse' ||
        event.type === 'mcp_browse' ||
        event.type === 'agents_browse' ||
        event.type === 'verifiers_browse' ||
        event.type === 'subagent_start' ||
        event.type === 'subagent_end'
      ) {
        processEvent(event, state, dispatch);
        return;
      }

      if (event.type === 'start') {
        dispatch({
          type: 'SET_STATUS',
          payload: {
            mode: event.data.mode as 'code' | 'plan',
            model: event.data.model,
            availableModels: event.data.available_models || state.availableModels,
          },
        });
        return;
      }

      // Events that remain in App.tsx (async state tracking, multiuser)
      switch (event.type) {
        case 'session_started':
          dispatch({ type: 'SET_SESSION', payload: (event.data as { session_id: string }).session_id });
          break;

        case 'tool_start': {
          const toolName = event.data.name as string;
          const toolArgs = (event.data.args || {}) as Record<string, unknown>;
          // Use tool_use_id if available, otherwise generate unique key
          const toolUseId = (event.data as any).tool_use_id || `${toolName}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

          // Handle ask_choice_questions as interactive prompt, not a tool
          if (toolName === 'ask_choice_questions' || toolName === 'AskUserQuestion') {
            const questions = Array.isArray(toolArgs.questions) ? toolArgs.questions : [];
            if (questions.length > 0) {
              dispatch({ type: 'SET_QUESTION', payload: questions[0] as Question });
              dispatch({ type: 'SET_PROCESSING', payload: false });
            }
            pendingToolsRef.current.set(toolUseId, { args: toolArgs, logId: '', toolName });
            break;
          }

          const logId = `tool-${Date.now()}-${toolName}`;
          dispatch({
            type: 'ADD_LOG',
            payload: {
              id: logId,
              role: 'tool' as const,
              content: '',
              toolName: toolName,
              toolArgs: toolArgs,
              toolStatus: 'running' as const,
            },
          });
          pendingToolsRef.current.set(toolUseId, { args: toolArgs, logId, toolName });
          break;
        }

        case 'tool_result': {
          const toolName = event.data.name as string;
          const toolUseId = (event.data as any).tool_use_id;
          const lowerToolName = toolName.toLowerCase();

          if (toolName === 'ask_choice_questions' || toolName === 'AskUserQuestion') {
            // Find and delete by tool name if no tool_use_id
            for (const [key, value] of pendingToolsRef.current.entries()) {
              if ((value as any).toolName === toolName) {
                pendingToolsRef.current.delete(key);
                break;
              }
            }
            break;
          }

          // Find the pending tool - by tool_use_id or by tool name (FIFO for same-name tools)
          let pendingKey: string | null = null;
          let pending: { args: Record<string, unknown>; logId: string; toolName?: string } | null = null;

          if (toolUseId && pendingToolsRef.current.has(toolUseId)) {
            pendingKey = toolUseId;
            pending = pendingToolsRef.current.get(toolUseId)!;
          } else {
            // Find first matching tool by name (FIFO order)
            for (const [key, value] of pendingToolsRef.current.entries()) {
              if ((value as any).toolName === toolName || key.startsWith(toolName + '-')) {
                pendingKey = key;
                pending = value;
                break;
              }
            }
          }

          // Handle task/todo tool results - support multiple naming conventions
          const isCreateTodo = lowerToolName === 'taskcreate' || lowerToolName === 'write_todo' || lowerToolName === 'todowrite' || lowerToolName === 'todo_create';
          const isUpdateTodo = lowerToolName === 'taskupdate' || lowerToolName === 'update_todo' || lowerToolName === 'todoupdate' || lowerToolName === 'todo_update';
          const isListTodo = lowerToolName === 'tasklist' || lowerToolName === 'list_todos' || lowerToolName === 'todolist' || lowerToolName === 'todo_list';

          if (event.data.success && isCreateTodo) {
            const args = pending?.args || {};
            // Extract todo info from args or result
            const result = event.data.result as string || '';

            // Try to parse ID from result like "task-27d69962" or "(ID: task-27d69962)"
            const idMatch = result.match(/task-([a-z0-9]+)/i) || result.match(/ID:\s*([a-z0-9-]+)/i);
            const todoId = idMatch ? `task-${idMatch[1]}` : String(args.taskId || args.id || `task-${Date.now()}`);

            // Try to get subject from args first, then parse from result
            let subject = String(args.subject || args.title || args.task || '');

            // If no subject in args, try to extract from result like: Created todo "test 1" or 'test 1'
            if (!subject && result) {
              const subjectMatch = result.match(/todo\s+["']([^"']+)["']/i) ||
                                  result.match(/Created\s+["']([^"']+)["']/i) ||
                                  result.match(/["']([^"']+)["']/);
              if (subjectMatch) {
                subject = subjectMatch[1];
              }
            }

            if (subject) {
              dispatch({
                type: 'ADD_TODO',
                payload: {
                  id: todoId,
                  subject: subject,
                  description: args.description ? String(args.description) : undefined,
                  status: 'pending',
                  activeForm: args.activeForm ? String(args.activeForm) : undefined,
                },
              });
            }
          } else if (event.data.success && isUpdateTodo && pending?.args) {
            const args = pending.args;
            const updates: Record<string, unknown> = {};
            if (args.status) updates.status = String(args.status);
            if (args.subject || args.title) updates.subject = String(args.subject || args.title);
            if (args.description) updates.description = String(args.description);
            if (args.activeForm) updates.activeForm = String(args.activeForm);
            dispatch({
              type: 'UPDATE_TODO',
              payload: {
                id: String(args.taskId || args.id || ''),
                updates: updates as any,
              },
            });
          } else if (event.data.success && isListTodo) {
            // Parse task list from result and sync todos
            try {
              const result = event.data.result;
              if (typeof result === 'string' && result.includes('#')) {
                const todos: Array<{id: string; subject: string; status: 'pending' | 'in_progress' | 'completed'}> = [];
                const lines = result.split('\n');
                for (const line of lines) {
                  const match = line.match(/#(\d+)\s*\[(\w+)\]\s+(.+)/);
                  if (match) {
                    const [, id, status, subject] = match;
                    todos.push({
                      id,
                      subject: subject.trim(),
                      status: status as 'pending' | 'in_progress' | 'completed',
                    });
                  }
                }
                if (todos.length > 0) {
                  dispatch({ type: 'SET_TODOS', payload: todos });
                }
              }
            } catch {
              // Ignore parse errors
            }
          }

          if (pending && pending.logId) {
            dispatch({
              type: 'UPDATE_LOG',
              payload: {
                id: pending.logId,
                updates: {
                  success: event.data.success as boolean,
                  toolStatus: (event.data.success ? 'complete' : 'error') as 'complete' | 'error',
                  content: (event.data.result as string) || '',
                },
              },
            });
          }
          if (pendingKey) {
            pendingToolsRef.current.delete(pendingKey);
          }
          break;
        }

        case 'progress':
          dispatch({
            type: 'ADD_LOG',
            payload: {
              id: `progress-${Date.now()}`,
              role: 'system' as const,
              content: (event.data as { message: string }).message,
            },
          });
          break;

        case 'plan_mode_requested': {
          const reason = (event.data as { reason?: string }).reason;
          dispatch({
            type: 'ADD_LOG',
            payload: {
              id: `planmode-request-${Date.now()}`,
              role: 'system' as const,
              content: `📋 Plan mode requested${reason ? `: ${reason}` : ''}`,
            },
          });
          dispatch({ type: 'SET_APPROVAL', payload: { show: true, approvalType: 'planmode' } });
          break;
        }

        case 'plan_submitted': {
          dispatch({
            type: 'ADD_LOG',
            payload: {
              id: `plan-${Date.now()}`,
              role: 'assistant' as const,
              content: (event.data as { plan: string }).plan,
            },
          });
          dispatch({
            type: 'ADD_LOG',
            payload: {
              id: `plan-approval-request-${Date.now()}`,
              role: 'system' as const,
              content: '📋 Plan submitted for approval',
            },
          });
          dispatch({ type: 'SET_APPROVAL', payload: { show: true, approvalType: 'plan' } });
          break;
        }

        case 'ask_choice_questions':
          if ((event.data as { questions: Question[] }).questions.length > 0) {
            dispatch({ type: 'SET_QUESTION', payload: (event.data as { questions: Question[] }).questions[0] });
          }
          break;

        case 'clarification_request':
          dispatch({
            type: 'SET_QUESTION',
            payload: {
              question: (event.data as { question: string }).question,
              options: ((event.data as { options?: string[] }).options || []).map((opt) => ({ label: opt })),
            },
          });
          break;

        // Multiuser events - kept here as they need async state updates
        case 'multiuser_started':
          dispatch({
            type: 'SET_MULTIUSER',
            payload: {
              sessionId: (event.data as { session_id: string; user_id: string; server_url: string; is_owner: boolean }).session_id,
              userId: (event.data as { session_id: string; user_id: string; server_url: string; is_owner: boolean }).user_id,
              serverUrl: (event.data as { session_id: string; user_id: string; server_url: string; is_owner: boolean }).server_url,
              isOwner: (event.data as { session_id: string; user_id: string; server_url: string; is_owner: boolean }).is_owner,
            },
          });
          dispatch({
            type: 'ADD_LOG',
            payload: {
              id: `multiuser-${Date.now()}`,
              role: 'system' as const,
              content: `Joined shared session ${(event.data as { session_id: string; user_id: string; server_url: string; is_owner: boolean }).session_id.slice(0, 8)}`,
            },
          });
          break;

        case 'multiuser_stopped':
          dispatch({ type: 'CLEAR_MULTIUSER' });
          dispatch({
            type: 'ADD_LOG',
            payload: {
              id: `multiuser-stopped-${Date.now()}`,
              role: 'system' as const,
              content: 'Left shared session',
            },
          });
          break;

        case 'participant_joined':
          dispatch({
            type: 'SET_MULTIUSER',
            payload: {
              participantCount: state.multiuser.participantCount + 1,
            },
          });
          dispatch({
            type: 'ADD_LOG',
            payload: {
              id: `join-${Date.now()}`,
              role: 'system' as const,
              content: `${(event.data as { display_name: string }).display_name} joined`,
            },
          });
          break;

        case 'participant_left':
          dispatch({
            type: 'SET_MULTIUSER',
            payload: {
              participantCount: Math.max(0, state.multiuser.participantCount - 1),
            },
          });
          dispatch({
            type: 'ADD_LOG',
            payload: {
              id: `leave-${Date.now()}`,
              role: 'system' as const,
              content: `${(event.data as { display_name: string }).display_name} left`,
            },
          });
          break;

        case 'user_message': {
          const userId = (event.data as { user_id?: string; _source_user_id?: string }).user_id || (event.data as { user_id?: string; _source_user_id?: string })._source_user_id;
          // Get server timestamp for proper chronological ordering
          const timestamp = (event.data as { _timestamp?: string })._timestamp;
          const isOwnMessage = userId === state.multiuser.userId;
          const content = (event.data as { content: string }).content;

          // If this message triggers the agent (@agent/@emdash), flush any pending
          // stream response first. This prevents responses from different turns
          // from being concatenated if chat_complete events arrive out of order.
          const triggersAgent = content.toLowerCase().includes('@agent') || content.toLowerCase().includes('@emdash');
          if (triggersAgent) {
            dispatch({ type: 'STREAM_RESET' });
          }

          // Display ALL messages via SSE (including own) for consistent timestamps
          // Own messages show as "You", others show their display_name
          dispatch({
            type: 'ADD_LOG',
            payload: {
              id: `user-${userId}-${Date.now()}`,
              role: 'user' as const,
              content: content,
              name: isOwnMessage ? undefined : (event.data as { display_name: string }).display_name,
              timestamp, // Include server timestamp for ordering
            },
          });
          break;
        }

        case 'user_typing': {
          const userId = (event.data as { user_id?: string; _source_user_id?: string }).user_id || (event.data as { user_id?: string; _source_user_id?: string })._source_user_id;
          if (userId && userId !== state.multiuser.userId) {
            dispatch({
              type: 'ADD_TYPING_USER',
              payload: {
                id: userId,
                name: (event.data as { display_name: string }).display_name,
              },
            });
            setTimeout(() => {
              dispatch({ type: 'REMOVE_TYPING_USER', payload: userId });
            }, 3000);
          }
          break;
        }

        case 'user_stopped_typing': {
          const userId = (event.data as { user_id?: string; _source_user_id?: string }).user_id || (event.data as { user_id?: string; _source_user_id?: string })._source_user_id;
          if (userId) {
            dispatch({ type: 'REMOVE_TYPING_USER', payload: userId });
          }
          break;
        }

        case 'prompt_resolved':
          // Owner answered a question or approval — clear interactive overlays
          // so non-owners (and owner via SSE) aren't stuck on the prompt.
          dispatch({ type: 'SET_QUESTION', payload: null });
          dispatch({ type: 'SET_APPROVAL', payload: { show: false } });
          break;

        case 'agent_typing': {
          // Show/hide "Agent is thinking..." in the typing indicator.
          const agentTyping = (event.data as { is_typing: boolean }).is_typing;
          if (agentTyping) {
            dispatch({ type: 'ADD_TYPING_USER', payload: { id: '__agent__', name: 'Agent' } });
          } else {
            dispatch({ type: 'REMOVE_TYPING_USER', payload: '__agent__' });
          }
          break;
        }

        case 'clear':
          dispatch({ type: 'CLEAR_LOG' });
          break;

        case 'exit':
          exit();
          break;
      }
    },
    [state.multiuser.userId, state.multiuser.participantCount, exit, dispatch],
  );

  // Set up stdin listener
  useEffect(() => {
    const rl = readline.createInterface({
      input: process.stdin,
      terminal: false,
    });

    rl.on('line', (line) => {
      const event = parseIncomingEvent(line);
      if (event) {
        handleEvent(event);
      }
    });

    sendMessage({ type: 'user_input', data: { content: '__ink_ready__' } });

    return () => {
      rl.close();
    };
  }, [handleEvent]);

  // Sync submission ref with processing state
  useEffect(() => {
    if (!state.isProcessing) {
      isSubmittingRef.current = false;
    }
  }, [state.isProcessing]);

  // Handle global keyboard shortcuts
  useInput(
    (input, key) => {
      if (key.ctrl && input === 'c') {
        if (state.overlay !== 'none') {
          handleOverlayDismiss(dispatch);
        } else if (state.isProcessing) {
          sendMessage({ type: 'cancel', data: {} });
        } else {
          sendMessage({ type: 'quit', data: {} });
          exit();
        }
        return;
      }

      if (key.escape) {
        // Dismiss any overlay first
        if (state.overlay !== 'none') {
          handleOverlayDismiss(dispatch);
          return;
        }
        // Cancel current processing
        if (state.isProcessing) {
          sendMessage({ type: 'cancel', data: {} });
          dispatch({ type: 'SET_PROCESSING', payload: false });
          dispatch({
            type: 'ADD_LOG',
            payload: {
              id: `system-${Date.now()}`,
              role: 'system' as const,
              content: 'Cancelled',
            },
          });
          return;
        }
        // Clear any active question/approval prompts
        if (state.activeQuestion || state.showApproval) {
          dispatch({ type: 'SET_QUESTION', payload: null });
          dispatch({ type: 'SET_APPROVAL', payload: { show: false } });
          return;
        }
      }

      if (state.overlay === 'help' && input) {
        handleOverlayDismiss(dispatch);
        return;
      }
    },
    { isActive: inputEnabled },
  );

  // Handle user input submission
  const onSubmit = useCallback(
    async (value: string, attachments?: ImageAttachment[]) => {
      // Prevent double-submission using ref (avoids React state batching delay)
      if (isSubmittingRef.current) return;

      if (value.startsWith('/')) {
        const baseCommand = value.split(/\s+/)[0].toLowerCase();
        const handled = await handleLocalCommand(value, state, dispatch, exit);
        if (handled) return;
      }

      // Mark as submitting immediately
      isSubmittingRef.current = true;

      // Flush any pending stream response before adding new user message
      dispatch({ type: 'STREAM_RESET' });

      // Build display content with attachment indicator
      const hasAttachments = attachments && attachments.length > 0;
      const displayContent = hasAttachments
        ? `${value}${value ? ' ' : ''}[${attachments.map((_, i) => `Image ${i + 1}`).join('] [')}]`
        : value;

      // In multiuser mode, DON'T add message locally - it will come via SSE
      // with a proper timestamp for correct chronological ordering.
      // In solo mode, add it immediately for instant feedback.
      if (!state.multiuser.sessionId) {
        dispatch({
          type: 'ADD_LOG',
          payload: {
            id: `user-${Date.now()}`,
            role: 'user' as const,
            content: displayContent,
          },
        });
      }

      sendMessage({
        type: 'user_input',
        data: {
          content: value,
          attachments: hasAttachments ? attachments : undefined,
        },
      });
      dispatch({ type: 'SET_PROCESSING', payload: true });
    },
    [state, dispatch, exit],
  );

  // Handle command selection
  const handleCommandSelect = useCallback(
    async (command: string) => {
      dispatch({ type: 'SET_SHOW_COMMAND_MENU', payload: false });
      dispatch({ type: 'SET_COMMAND_FILTER', payload: '' });
      await onSubmit(command, undefined);
    },
    [dispatch, onSubmit],
  );

  // Keep ref in sync with state
  commandMenuStateRef.current.showMenu = state.showCommandMenu;
  commandMenuStateRef.current.filter = state.commandMenuFilter;

  // Handle input change - show command menu (only dispatch when state actually changes)
  const onChange = useCallback((value: string) => {
    const shouldShowMenu = value.startsWith('/');
    const ref = commandMenuStateRef.current;

    // Only dispatch if state needs to change
    if (shouldShowMenu) {
      // Only update filter if it changed
      if (ref.filter !== value) {
        dispatch({ type: 'SET_COMMAND_FILTER', payload: value });
      }
      // Only show menu if not already showing
      if (!ref.showMenu) {
        dispatch({ type: 'SET_SHOW_COMMAND_MENU', payload: true });
      }
    } else {
      // Only hide menu and clear filter if they're not already in that state
      if (ref.showMenu) {
        dispatch({ type: 'SET_SHOW_COMMAND_MENU', payload: false });
      }
      if (ref.filter !== '') {
        dispatch({ type: 'SET_COMMAND_FILTER', payload: '' });
      }
    }
  }, [dispatch]);

  // Handle typing indicator for multiuser
  const onTypingChange = useCallback((isTyping: boolean) => {
    // Only send typing indicators in multiuser mode
    if (!state.multiuser.sessionId) return;

    sendMessage({
      type: isTyping ? 'user_typing' : 'user_stopped_typing',
      data: {},
    });
  }, [state.multiuser.sessionId]);

  // Handle menu navigation
  const onMenuUp = useCallback(() => {
    const filtered = getFilteredCommands(state.commandMenuFilter);
    const maxIndex = Math.min(filtered.length, 10) - 1;
    dispatch({
      type: 'SET_COMMAND_MENU_INDEX',
      payload: state.commandMenuIndex > 0 ? state.commandMenuIndex - 1 : maxIndex,
    });
  }, [state.commandMenuFilter, state.commandMenuIndex, dispatch]);

  const onMenuDown = useCallback(() => {
    const filtered = getFilteredCommands(state.commandMenuFilter);
    const maxIndex = Math.min(filtered.length, 10) - 1;
    dispatch({
      type: 'SET_COMMAND_MENU_INDEX',
      payload: state.commandMenuIndex < maxIndex ? state.commandMenuIndex + 1 : 0,
    });
  }, [state.commandMenuFilter, state.commandMenuIndex, dispatch]);

  const onMenuSelect = useCallback((inputValue: string) => {
    const filtered = getFilteredCommands(inputValue);

    if (inputValue.includes(' ')) {
      dispatch({ type: 'SET_SHOW_COMMAND_MENU', payload: false });
      dispatch({ type: 'SET_COMMAND_FILTER', payload: '' });
      onSubmit(inputValue);
      return;
    }

    if (filtered.length > 0 && state.commandMenuIndex < filtered.length) {
      handleCommandSelect(filtered[state.commandMenuIndex].command);
      return;
    }

    dispatch({ type: 'SET_SHOW_COMMAND_MENU', payload: false });
    dispatch({ type: 'SET_COMMAND_FILTER', payload: '' });
    onSubmit(inputValue);
  }, [state.commandMenuIndex, handleCommandSelect, onSubmit, dispatch]);

  const onMenuComplete = useCallback((inputValue: string) => {
    // Tab pressed - autocomplete with selected command but don't send
    const filtered = getFilteredCommands(inputValue);
    if (filtered.length > 0 && state.commandMenuIndex < filtered.length) {
      const selectedCommand = filtered[state.commandMenuIndex].command;
      // Update the filter to the complete command (this will update the input display)
      dispatch({ type: 'SET_COMMAND_FILTER', payload: selectedCommand });
    }
  }, [state.commandMenuIndex, dispatch]);

  const onMenuDismiss = useCallback(() => {
    dispatch({ type: 'SET_SHOW_COMMAND_MENU', payload: false });
  }, [dispatch]);

  // UI Helpers
  const terminalHeight = stdout?.rows || 24;
  const terminalWidth = stdout?.columns || 80;
  const reservedLines = state.showCommandMenu ? 16 : 4;
  const maxLogLines = Math.max(5, terminalHeight - reservedLines);
  const visibleLog = getVisibleLog(state, maxLogLines);
  const promptText = getPromptText(state.showApproval, state.mode);
  const promptColor = getPromptColor(state);
  const inputDisabled = isInputDisabled(state, inputEnabled);
  // Border width accounting for paddingX={1} (2 chars total)
  const borderWidth = Math.max(1, terminalWidth - 2);

  return (
    <Box flexDirection="column" minHeight={terminalHeight}>
      {/* Help overlay */}
      {state.overlay === 'help' && (
        <Box flexDirection="column" paddingX={1}>
          <HelpDisplay />
          <Box marginTop={1}>
            <Text color="#6a6a6a">Press any key to close</Text>
          </Box>
        </Box>
      )}

      {/* Model picker overlay */}
      {state.overlay === 'model' && (
        <Box paddingX={1}>
          <ModelPicker
            providers={DEFAULT_PROVIDERS}
            currentModel={state.model}
            onSelect={(model) => handleModelSelect(model, dispatch)}
            onDismiss={() => handleOverlayDismiss(dispatch)}
            isActive={true}
          />
        </Box>
      )}

      {/* Registry browser overlay */}
      {state.overlay === 'registry' && state.registryData && (
        <Box paddingX={1}>
          <RegistryBrowser
            data={state.registryData}
            onInstall={(category, name) => handleRegistryInstall(category, name, dispatch)}
            onDismiss={() => handleRegistryDismiss(dispatch)}
            isActive={true}
          />
        </Box>
      )}

      {/* Skills wizard overlay */}
      {state.overlay === 'skills' && state.configData.skills && (
        <Box paddingX={1}>
          <ConfigWizard
            type="skills"
            data={state.configData.skills}
            onAction={(action, data) => handleConfigAction(dispatch, action, data)}
            onDismiss={() => handleConfigDismiss(dispatch)}
            isActive={true}
          />
        </Box>
      )}

      {/* Rules wizard overlay */}
      {state.overlay === 'rules' && state.configData.rules && (
        <Box paddingX={1}>
          <ConfigWizard
            type="rules"
            data={state.configData.rules as any}
            onAction={(action, data) => handleConfigAction(dispatch, action, data)}
            onDismiss={() => handleConfigDismiss(dispatch)}
            isActive={true}
          />
        </Box>
      )}

      {/* Hooks wizard overlay */}
      {state.overlay === 'hooks' && state.configData.hooks && (
        <Box paddingX={1}>
          <ConfigWizard
            type="hooks"
            data={state.configData.hooks as any}
            onAction={(action, data) => handleConfigAction(dispatch, action, data)}
            onDismiss={() => handleConfigDismiss(dispatch)}
            isActive={true}
          />
        </Box>
      )}

      {/* MCP wizard overlay */}
      {state.overlay === 'mcp' && state.configData.mcp && (
        <Box paddingX={1}>
          <ConfigWizard
            type="mcp"
            data={state.configData.mcp as any}
            onAction={(action, data) => handleConfigAction(dispatch, action, data)}
            onDismiss={() => handleConfigDismiss(dispatch)}
            isActive={true}
          />
        </Box>
      )}

      {/* Agents wizard overlay */}
      {state.overlay === 'agents' && state.configData.agents && (
        <Box paddingX={1}>
          <ConfigWizard
            type="agents"
            data={state.configData.agents}
            onAction={(action, data) => handleConfigAction(dispatch, action, data)}
            onDismiss={() => handleConfigDismiss(dispatch)}
            isActive={true}
          />
        </Box>
      )}

      {/* Verifiers wizard overlay */}
      {state.overlay === 'verifiers' && state.configData.verifiers && (
        <Box paddingX={1}>
          <ConfigWizard
            type="verifiers"
            data={state.configData.verifiers}
            onAction={(action, data) => handleConfigAction(dispatch, action, data)}
            onDismiss={() => handleConfigDismiss(dispatch)}
            isActive={true}
          />
        </Box>
      )}

      {/* Todo list - show when there are active tasks */}
      {state.overlay === 'none' && state.todos.length > 0 && (
        <Box paddingX={1}>
          <TodoList todos={state.todos} compact={true} />
        </Box>
      )}

      {/* Main log area */}
      {state.overlay === 'none' && (
        <LogView
          log={state.log}
          streamResponse={state.streamResponse}
          isProcessing={state.isProcessing}
          currentThinking={state.currentThinking}
          cwd={state.cwd}
          maxLines={maxLogLines}
        />
      )}

      {/* Typing indicator */}
      {state.typingUsers.length > 0 && state.overlay === 'none' && (
        <Box paddingX={1}>
          <TypingIndicator users={state.typingUsers} />
        </Box>
      )}

      {/* Interactive prompts */}
      {state.activeQuestion && state.overlay === 'none' && (
        <Box paddingX={1}>
          <ChoicePrompt
            question={state.activeQuestion}
            onSelect={(value, isOther, customValue) =>
              handleChoiceSelect(value, isOther, customValue, state.activeQuestion, dispatch)
            }
          />
        </Box>
      )}

      {state.showApproval && !state.activeQuestion && state.overlay === 'none' && (
        <Box paddingX={1}>
          <ApprovalPrompt
            onApprove={() => handleApprove(dispatch, state.approvalType)}
            onReject={() => handleReject(dispatch, state.approvalType)}
            onReply={(message) => handleReply(message, dispatch, state.approvalType)}
          />
        </Box>
      )}

      {/* Command menu dropdown */}
      {state.showCommandMenu && state.overlay === 'none' && (
        <Box paddingX={1}>
          <CommandMenu
            filter={state.commandMenuFilter}
            selectedIndex={state.commandMenuIndex}
          />
        </Box>
      )}

      {/* Input area */}
      <Box flexDirection="column" marginBottom={1}>
        {/* Top border - solid line */}
        <Box paddingX={1}>
          <Text color={state.mode === 'plan' || state.showApproval ? '#5a3d4a' : '#5a4a3d'}>
            {'─'.repeat(borderWidth)}
          </Text>
        </Box>

        {/* Input content */}
        <Box paddingX={2} paddingY={0}>
          <Input
            prompt={promptText}
            promptColor={promptColor}
            value={state.showCommandMenu ? state.commandMenuFilter : undefined}
            onSubmit={onSubmit}
            onChange={onChange}
            disabled={inputDisabled}
            placeholder={!inputEnabled ? '(no input support)' : state.isProcessing ? '' : 'Type a message...'}
            menuMode={state.showCommandMenu}
            onMenuUp={onMenuUp}
            onMenuDown={onMenuDown}
            onMenuSelect={onMenuSelect}
            onMenuComplete={onMenuComplete}
            onMenuDismiss={onMenuDismiss}
            mode={state.showApproval ? 'approval' : state.mode}
            onTypingChange={onTypingChange}
          />
        </Box>

        {/* Bottom border - solid line */}
        <Box paddingX={1}>
          <Text color={state.mode === 'plan' || state.showApproval ? '#5a3d4a' : '#5a4a3d'}>
            {'─'.repeat(borderWidth)}
          </Text>
        </Box>
      </Box>

      {/* Status bar */}
      <StatusBar
        model={state.model}
        mode={state.mode}
        cwd={state.cwd}
        multiuser={state.multiuser.sessionId ? { sessionId: state.multiuser.sessionId, participantCount: state.multiuser.participantCount } : null}
      />
    </Box>
  );
}