import React from 'react';
import type { Action, AppState } from './store.js';

/**
 * Process incoming event from Python backend
 * Returns an array of actions to dispatch
 */
export function processEvent(
  event: any,
  state: AppState,
  dispatch: React.Dispatch<Action>
): void {
  // Events have 'type' property (from protocol.ts), but bridge may wrap them with 'event' property
  const eventType = event.type || event.event;
  switch (eventType) {
    case 'start': {
      dispatch({
        type: 'SET_STATUS',
        payload: {
          mode: event.data.mode,
          model: event.data.model,
          availableModels: event.data.available_models || state.availableModels,
        },
      });
      break;
    }

    case 'chat_chunk': {
      const content = event.data.content || '';
      if (content) {
        dispatch({
          type: 'STREAM_APPEND',
          payload: content,
        });
      }
      break;
    }

    case 'chat_complete': {
      dispatch({
        type: 'STREAM_COMPLETE',
        payload: null,
      });
      break;
    }

    case 'error': {
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `error-${Date.now()}`,
          role: 'system' as const,
          content: `Error: ${event.data.message}`,
        },
      });
      dispatch({ type: 'SET_PROCESSING', payload: false });
      break;
    }

    case 'response': {
      // Response from slash command or agent
      // Slash commands send content directly, agent responses are streamed via chat_chunk
      // Use HANDLE_RESPONSE_EVENT which checks hadStreaming in the reducer
      // (fixes stale closure issue where state.hadStreaming was captured at callback creation)
      const content = event.data.content || '';
      dispatch({ type: 'HANDLE_RESPONSE_EVENT', payload: { content } });
      break;
    }

    case 'partial_response': {
      // Streaming partial response - append to stream buffer
      const content = event.data.content || '';
      if (content) {
        dispatch({
          type: 'STREAM_APPEND',
          payload: content,
        });
      }
      break;
    }

    case 'thinking': {
      // Thinking indicator from agent
      const content = event.data.message || event.data.content || '';
      if (content) {
        dispatch({ type: 'SET_THINKING', payload: content });
      }
      break;
    }

    case 'assistant_text': {
      // Text from assistant - streaming or complete
      const text = event.data.text || '';
      // Get server timestamp for proper chronological ordering in multiuser
      const timestamp = event.data._timestamp as string | undefined;
      if (!event.data.complete && text) {
        // Streaming - append to buffer
        dispatch({
          type: 'STREAM_APPEND',
          payload: text,
        });
      } else if (event.data.complete && text) {
        // Complete text from multiuser broadcast - add directly to log
        // (This is how joiners receive agent responses)
        dispatch({
          type: 'ADD_LOG',
          payload: {
            id: `assistant-${Date.now()}`,
            role: 'assistant' as const,
            content: text,
            timestamp, // Include server timestamp for ordering
          },
        });
        dispatch({ type: 'SET_PROCESSING', payload: false });
      }
      break;
    }

    case 'chat_message': {
      // Only handle system messages here - assistant content comes via streaming
      const role = event.data.role || 'assistant';
      const content = event.data.content || '';
      if (role === 'system' && content) {
        dispatch({
          type: 'ADD_LOG',
          payload: {
            id: `system-${Date.now()}`,
            role: 'system' as const,
            content: content,
          },
        });
      }
      dispatch({ type: 'SET_PROCESSING', payload: false });
      break;
    }

    case 'set_processing': {
      dispatch({ type: 'SET_PROCESSING', payload: event.data.processing });
      break;
    }

    case 'set_mode': {
      dispatch({ type: 'SET_MODE', payload: event.data.mode });
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `system-${Date.now()}`,
          role: 'system' as const,
          content: `Mode set to: ${event.data.mode}`,
        },
      });
      break;
    }

    case 'set_model': {
      dispatch({ type: 'SET_MODEL', payload: event.data.model });
      break;
    }

    case 'update_available_models': {
      dispatch({ type: 'SET_AVAILABLE_MODELS', payload: event.data.models });
      break;
    }

    case 'ask_choice_questions': {
      dispatch({
        type: 'SET_QUESTION',
        payload: { ...event.data, id: `question-${Date.now()}` },
      });
      break;
    }

    case 'request_approval': {
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `approval-${Date.now()}`,
          role: 'system' as const,
          content: event.data.description,
        },
      });
      dispatch({ type: 'SET_APPROVAL', payload: { show: true, approvalType: 'planmode' } });
      dispatch({ type: 'SET_QUESTION', payload: null });
      break;
    }

    case 'plan_approval_granted':
    case 'plan_approval_denied': {
      dispatch({ type: 'SET_APPROVAL', payload: { show: false } });
      break;
    }

    case 'execution_started': {
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `exec-${Date.now()}`,
          role: 'system' as const,
          content: '🚀 Execution started',
        },
      });
      dispatch({ type: 'SET_PROCESSING', payload: true });
      break;
    }

    case 'execution_completed': {
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `exec-${Date.now()}`,
          role: 'assistant' as const,
          content: '✅ Execution completed',
        },
      });
      dispatch({ type: 'SET_PROCESSING', payload: false });
      break;
    }

    case 'execution_failed': {
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `exec-${Date.now()}`,
          role: 'system' as const,
          content: `❌ Execution failed: ${event.data.error}`,
        },
      });
      dispatch({ type: 'SET_PROCESSING', payload: false });
      break;
    }

    case 'registry_browse': {
      dispatch({
        type: 'SET_REGISTRY_DATA',
        payload: event.data,
      });
      dispatch({ type: 'SET_OVERLAY', payload: 'registry' });
      dispatch({ type: 'SET_PROCESSING', payload: false });
      break;
    }

    case 'skills_browse': {
      dispatch({
        type: 'SET_CONFIG_DATA',
        payload: {
          type: 'skills',
          data: { skills: event.data.skills || [] },
        },
      });
      dispatch({ type: 'SET_OVERLAY', payload: 'skills' });
      dispatch({ type: 'SET_PROCESSING', payload: false });
      break;
    }

    case 'rules_browse': {
      dispatch({
        type: 'SET_CONFIG_DATA',
        payload: {
          type: 'rules',
          data: { rules: event.data.rules || [] },
        },
      });
      dispatch({ type: 'SET_OVERLAY', payload: 'rules' });
      dispatch({ type: 'SET_PROCESSING', payload: false });
      break;
    }

    case 'hooks_browse': {
      dispatch({
        type: 'SET_CONFIG_DATA',
        payload: {
          type: 'hooks',
          data: { hooks: event.data.hooks || [], events: event.data.events || [] },
        },
      });
      dispatch({ type: 'SET_OVERLAY', payload: 'hooks' });
      dispatch({ type: 'SET_PROCESSING', payload: false });
      break;
    }

    case 'mcp_browse': {
      dispatch({
        type: 'SET_CONFIG_DATA',
        payload: {
          type: 'mcp',
          data: { servers: event.data.servers || [] },
        },
      });
      dispatch({ type: 'SET_OVERLAY', payload: 'mcp' });
      dispatch({ type: 'SET_PROCESSING', payload: false });
      break;
    }

    case 'agents_browse': {
      dispatch({
        type: 'SET_CONFIG_DATA',
        payload: {
          type: 'agents',
          data: { agents: event.data.agents || [] },
        },
      });
      dispatch({ type: 'SET_OVERLAY', payload: 'agents' });
      dispatch({ type: 'SET_PROCESSING', payload: false });
      break;
    }

    case 'verifiers_browse': {
      dispatch({
        type: 'SET_CONFIG_DATA',
        payload: {
          type: 'verifiers',
          data: { verifiers: event.data.verifiers || [] },
        },
      });
      dispatch({ type: 'SET_OVERLAY', payload: 'verifiers' });
      dispatch({ type: 'SET_PROCESSING', payload: false });
      break;
    }

    case 'plan_submitted': {
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `system-${Date.now()}`,
          role: 'system' as const,
          content: 'Plan submitted for approval',
        },
      });
      break;
    }

    case 'task_completed': {
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `task-${Date.now()}`,
          role: 'system' as const,
          content: event.data.summary,
        },
      });
      break;
    }

    case 'todos_sync': {
      event.data.todos?.forEach((todo: any) => {
        dispatch({
          type: 'ADD_TODO',
          payload: todo,
        });
      });
      break;
    }

    case 'skill_activated': {
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `skill-${Date.now()}`,
          role: 'system' as const,
          content: `Skill activated: ${event.data.skill}`,
        },
      });
      break;
    }

    case 'subagent_start': {
      // Add a log entry for the subagent start and increase indent
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `subagent-start-${Date.now()}`,
          role: 'system' as const,
          content: `Starting ${event.data.agent_type || 'sub'} agent...`,
        },
      });
      dispatch({ type: 'SUBAGENT_START' });
      break;
    }

    case 'subagent_end': {
      // Decrease indent and add completion log
      dispatch({ type: 'SUBAGENT_END' });
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `subagent-end-${Date.now()}`,
          role: 'system' as const,
          content: `${event.data.agent_type || 'Sub'} agent ${event.data.success ? 'completed' : 'failed'}`,
        },
      });
      break;
    }

    case 'clear_display': {
      dispatch({ type: 'CLEAR_LOG' });
      break;
    }

    case 'reset_session': {
      dispatch({ type: 'CLEAR_SESSION' });
      dispatch({ type: 'CLEAR_LOG' });
      break;
    }

    case 'exit': {
      // Graceful exit - let the main component handle cleanup
      // TODO: Add exit handling or dismiss overlay
      dispatch({ type: 'SET_OVERLAY', payload: 'none' });
      break;
    }

    default: {
      // Unknown event - log it for debugging
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `debug-${Date.now()}`,
          role: 'system' as const,
          content: `[Unknown event] ${eventType}: ${JSON.stringify(event.data)}`,
        },
      });
      break;
    }
  }
}