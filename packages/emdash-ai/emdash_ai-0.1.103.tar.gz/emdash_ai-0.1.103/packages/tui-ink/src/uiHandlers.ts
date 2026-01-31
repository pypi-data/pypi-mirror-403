import { sendMessage } from './protocol.js';
import { LOCAL_COMMANDS } from './constants/commands.js';
import React from 'react';
import type { Action, AppState } from './store.js';
import type { ConfigType, RegistryCategory } from './components/index.js';

/**
 * Handle user input submission
 */
export async function handleSubmit(
  value: string,
  dispatch: React.Dispatch<Action>,
  handleLocalCommand: (cmd: string) => Promise<boolean>
): Promise<void> {
  // Check if it's a slash command
  if (value.startsWith('/')) {
    const baseCommand = value.split(/\s+/)[0].toLowerCase();

    // Check if it's a local command (LOCAL_COMMANDS is imported from constants)
    if (LOCAL_COMMANDS.has(baseCommand)) {
      const handled = await handleLocalCommand(value);
      if (handled) return;
    }
  }

  // Add user message to log
  dispatch({
    type: 'ADD_LOG',
    payload: {
      id: `user-${Date.now()}`,
      role: 'user' as const,
      content: value,
    },
  });

  // Send to Python backend
  sendMessage({ type: 'user_input', data: { content: value } });
  dispatch({ type: 'SET_PROCESSING', payload: true });
}

/**
 * Handle choice selection (single or multi-select)
 */
export function handleChoiceSelect(
  value: string | string[],
  isOther: boolean,
  customValue: string | undefined,
  activeQuestion: AppState['activeQuestion'],
  dispatch: React.Dispatch<Action>
): void {
  // Add the question and options to the log so it's visible in the thread
  if (activeQuestion) {
    // Build the question content with options
    const optionsText = activeQuestion.options
      .map((opt, i) => `  ${i + 1}. ${opt.label}${opt.description ? ` - ${opt.description}` : ''}`)
      .join('\n');
    const questionContent = `**${activeQuestion.question}**\n${optionsText}`;

    dispatch({
      type: 'ADD_LOG',
      payload: {
        id: `question-${Date.now()}`,
        role: 'assistant' as const,
        content: questionContent,
      },
    });

    // Add the user's answer to the log
    const answerText = isOther
      ? customValue || value
      : Array.isArray(value)
        ? value.join(', ')
        : value;

    dispatch({
      type: 'ADD_LOG',
      payload: {
        id: `answer-${Date.now()}`,
        role: 'user' as const,
        content: String(answerText),
      },
    });
  }

  sendMessage({
    type: 'choice_answer',
    data: {
      question_id: activeQuestion?.id,
      selected: value,
      is_other: isOther,
      custom_value: customValue,
    },
  });
  dispatch({ type: 'SET_QUESTION', payload: null });
}

/**
 * Handle plan approval/rejection
 * @param approvalType - 'planmode' for plan mode entry, 'plan' for plan submission
 */
export function handleApprove(dispatch: React.Dispatch<Action>, approvalType: 'planmode' | 'plan' | null): void {
  const type = approvalType || 'planmode';
  sendMessage({ type: 'plan_approval', data: { approved: true, approvalType: type } });

  // Add visual feedback in conversation
  const message = type === 'plan'
    ? '✓ Plan approved - implementing...'
    : '✓ Plan mode approved - entering planning phase...';
  dispatch({
    type: 'ADD_LOG',
    payload: {
      id: `approval-${Date.now()}`,
      role: 'system' as const,
      content: message,
    },
  });
  dispatch({ type: 'SET_APPROVAL', payload: { show: false } });
}

export function handleReject(dispatch: React.Dispatch<Action>, approvalType: 'planmode' | 'plan' | null): void {
  const type = approvalType || 'planmode';
  sendMessage({ type: 'plan_approval', data: { approved: false, approvalType: type } });

  // Add visual feedback in conversation
  const message = type === 'plan'
    ? '✗ Plan rejected - revising...'
    : '✗ Plan mode rejected - continuing in code mode...';
  dispatch({
    type: 'ADD_LOG',
    payload: {
      id: `rejection-${Date.now()}`,
      role: 'system' as const,
      content: message,
    },
  });
  dispatch({ type: 'SET_APPROVAL', payload: { show: false } });
}

export function handleReply(message: string, dispatch: React.Dispatch<Action>, approvalType: 'planmode' | 'plan' | null): void {
  const type = approvalType || 'planmode';
  sendMessage({ type: 'plan_approval', data: { approved: false, reply: message, approvalType: type } });

  // Add visual feedback in conversation with the feedback
  const statusMessage = type === 'plan'
    ? `✗ Plan rejected with feedback: "${message}"`
    : `✗ Plan mode rejected: "${message}"`;
  dispatch({
    type: 'ADD_LOG',
    payload: {
      id: `rejection-feedback-${Date.now()}`,
      role: 'system' as const,
      content: statusMessage,
    },
  });
  dispatch({ type: 'SET_APPROVAL', payload: { show: false } });
}

/**
 * Handle overlay dismissal
 */
export function handleOverlayDismiss(dispatch: React.Dispatch<Action>): void {
  dispatch({ type: 'SET_OVERLAY', payload: 'none' });
  dispatch({ type: 'SET_COMMAND_FILTER', payload: '' });
}

/**
 * Handle model selection from picker
 */
export function handleModelSelect(model: string, dispatch: React.Dispatch<Action>): void {
  dispatch({ type: 'SET_MODEL', payload: model });
  sendMessage({ type: 'set_model', data: { model } });
  dispatch({ type: 'SET_OVERLAY', payload: 'none' });
  dispatch({
    type: 'ADD_LOG',
    payload: {
      id: `system-${Date.now()}`,
      role: 'system' as const,
      content: `Model changed to: ${model}`,
    },
  });
}

/**
 * Handle registry install from browser
 */
export function handleRegistryInstall(
  category: RegistryCategory,
  name: string,
  dispatch: React.Dispatch<Action>
): void {
  dispatch({ type: 'SET_PROCESSING', payload: true });
  sendMessage({ type: 'registry_install', data: { category, name } });
}

/**
 * Handle registry browser dismiss
 */
export function handleRegistryDismiss(dispatch: React.Dispatch<Action>): void {
  dispatch({ type: 'SET_OVERLAY', payload: 'none' });
  dispatch({ type: 'SET_REGISTRY_DATA', payload: null });
}

/**
 * Handle config wizard dismiss
 */
export function handleConfigDismiss(dispatch: React.Dispatch<Action>): void {
  dispatch({ type: 'SET_OVERLAY', payload: 'none' });
  dispatch({ type: 'CLEAR_CONFIG_DATA' });
}

/**
 * Handle config wizard actions
 */
export function handleConfigAction(
  dispatch: React.Dispatch<Action>,
  action: string,
  data?: { type?: ConfigType; name?: string }
): void {
  const configType = data?.type as ConfigType;

  switch (action) {
    case 'new':
      // Close wizard and prompt for AI-assisted creation
      dispatch({ type: 'SET_OVERLAY', payload: 'none' });
      dispatch({ type: 'CLEAR_CONFIG_DATA' });
      dispatch({
        type: 'ADD_LOG',
        payload: {
          id: `system-${Date.now()}`,
          role: 'system' as const,
          content: `To create a new ${configType}, describe what you want to create and I'll help you set it up.`,
        },
      });
      break;

    case 'toggle':
      // Send toggle command to backend
      if (configType === 'hooks' || configType === 'mcp') {
        sendMessage({
          type: 'user_input',
          data: { content: `/${configType} toggle ${data?.name}` },
        });
      }
      break;

    case 'delete':
      // Send delete command to backend
      sendMessage({
        type: 'user_input',
        data: { content: `/${configType} delete ${data?.name}` },
      });
      dispatch({ type: 'SET_OVERLAY', payload: 'none' });
      dispatch({ type: 'CLEAR_CONFIG_DATA' });
      break;

    case 'view':
      // Close wizard and show item details
      dispatch({ type: 'SET_OVERLAY', payload: 'none' });
      dispatch({ type: 'CLEAR_CONFIG_DATA' });
      sendMessage({
        type: 'user_input',
        data: { content: `/${configType} view ${data?.name}` },
      });
      break;
  }
}