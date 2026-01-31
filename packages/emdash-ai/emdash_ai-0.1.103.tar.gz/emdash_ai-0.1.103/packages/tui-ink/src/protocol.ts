/**
 * Protocol types for communication between Python backend and Ink TUI
 * Communication is via JSON over stdin (Python → Ink) and stdout (Ink → Python)
 */

// ============================================================================
// Core Event Types from Python SSE
// ============================================================================

export interface ThinkingEvent {
  type: 'thinking';
  data: {
    // Backend sends 'message', but some places might send 'content'
    message?: string;
    content?: string;
  };
}

export interface ResponseEvent {
  type: 'response';
  data: {
    content: string;
  };
}

export interface PartialResponseEvent {
  type: 'partial_response';
  data: {
    content: string;
  };
}

export interface ErrorEvent {
  type: 'error';
  data: {
    message: string;
  };
}

export interface SessionStartEvent {
  type: 'session_start';
  data: {
    session_id: string;
  };
}

export interface SessionStartedEvent {
  type: 'session_started';
  data: {
    session_id: string;
  };
}

// ============================================================================
// Tool Execution Events
// ============================================================================

export interface ToolStartEvent {
  type: 'tool_start';
  data: {
    name: string;
    args: Record<string, unknown>;
  };
}

export interface ToolResultEvent {
  type: 'tool_result';
  data: {
    name: string;
    success: boolean;
    result?: string;
  };
}

// ============================================================================
// Progress & Status Events
// ============================================================================

export interface ProgressEvent {
  type: 'progress';
  data: {
    message: string;
    percent?: number;
  };
}

export interface AssistantTextEvent {
  type: 'assistant_text';
  data: {
    text: string;
    complete?: boolean;
  };
}

// ============================================================================
// Subagent Events
// ============================================================================

export interface SubagentStartEvent {
  type: 'subagent_start';
  data: {
    agent_type: string;
    prompt: string;
  };
}

export interface SubagentEndEvent {
  type: 'subagent_end';
  data: {
    agent_type: string;
    success: boolean;
  };
}

// ============================================================================
// Plan Mode Events
// ============================================================================

export interface PlanModeRequestedEvent {
  type: 'plan_mode_requested';
  data: {
    reason: string;
  };
}

export interface PlanSubmittedEvent {
  type: 'plan_submitted';
  data: {
    plan: string;
  };
}

// ============================================================================
// Interactive Prompt Events
// ============================================================================

export interface QuestionOption {
  label: string;
  description?: string;
}

export interface Question {
  id?: string;
  question: string;
  options: QuestionOption[];
  multiSelect?: boolean;
}

export interface AskChoiceQuestionsEvent {
  type: 'ask_choice_questions';
  data: {
    questions: Question[];
  };
}

export interface ClarificationRequestEvent {
  type: 'clarification_request';
  data: {
    question: string;
    options?: string[];
  };
}

// ============================================================================
// Multiuser Session Events
// ============================================================================

export interface MultiuserStartedEvent {
  type: 'multiuser_started';
  data: {
    session_id: string;
    user_id: string;
    server_url: string;
    is_owner: boolean;
  };
}

export interface MultiuserStoppedEvent {
  type: 'multiuser_stopped';
  data: Record<string, never>;
}

export interface ParticipantJoinedEvent {
  type: 'participant_joined';
  data: {
    display_name: string;
    user_id?: string;
  };
}

export interface ParticipantLeftEvent {
  type: 'participant_left';
  data: {
    display_name: string;
    user_id?: string;
  };
}

export interface UserMessageEvent {
  type: 'user_message';
  data: {
    user_id: string;
    display_name: string;
    content: string;
    _source_user_id?: string;
  };
}

export interface UserTypingEvent {
  type: 'user_typing';
  data: {
    user_id: string;
    display_name: string;
  };
}

export interface UserStoppedTypingEvent {
  type: 'user_stopped_typing';
  data: {
    user_id: string;
  };
}

export interface PromptResolvedEvent {
  type: 'prompt_resolved';
  data: {
    prompt_id?: string;
    response?: string;
  };
}

export interface AgentTypingEvent {
  type: 'agent_typing';
  data: {
    is_typing: boolean;
  };
}

export interface AgentResponseEvent {
  type: 'agent_response';
  data: {
    response_content: string;
  };
}

export interface ProcessMessageRequestEvent {
  type: 'process_message_request';
  data: {
    user_id: string;
    content: string;
    display_name: string;
  };
}

// ============================================================================
// Registry Events
// ============================================================================

export interface RegistryComponent {
  name: string;
  description: string;
  author?: string;
  version?: string;
  url?: string;
}

export interface RegistryBrowseEvent {
  type: 'registry_browse';
  data: {
    skills: Record<string, RegistryComponent>;
    rules: Record<string, RegistryComponent>;
    agents: Record<string, RegistryComponent>;
    verifiers: Record<string, RegistryComponent>;
  };
}

export interface RegistryInstallResultEvent {
  type: 'registry_install_result';
  data: {
    success: boolean;
    category: string;
    name: string;
    message: string;
    path?: string;
  };
}

// ============================================================================
// Configuration Browse Events
// ============================================================================

export interface Skill {
  name: string;
  description?: string;
  scripts?: string[];
  builtin?: boolean;
}

export interface SkillsBrowseEvent {
  type: 'skills_browse';
  data: {
    skills: Skill[];
  };
}

export interface Rule {
  name: string;
  preview: string;
  path: string;
}

export interface RulesBrowseEvent {
  type: 'rules_browse';
  data: {
    rules: Rule[];
  };
}

export interface Hook {
  id?: string;
  name?: string;
  event: string;
  command: string;
  enabled: boolean;
}

export interface HooksBrowseEvent {
  type: 'hooks_browse';
  data: {
    hooks: Hook[];
    events: string[];
  };
}

export interface McpServer {
  name: string;
  command: string;
  enabled: boolean;
  args?: string[];
}

export interface McpBrowseEvent {
  type: 'mcp_browse';
  data: {
    servers: McpServer[];
  };
}

export interface Agent {
  name: string;
  description?: string;
}

export interface AgentsBrowseEvent {
  type: 'agents_browse';
  data: {
    agents: Agent[];
  };
}

export interface Verifier {
  name: string;
  type?: string;
  command?: string;
  enabled?: boolean;
}

export interface VerifiersBrowseEvent {
  type: 'verifiers_browse';
  data: {
    verifiers: Verifier[];
  };
}

// ============================================================================
// Session History Events
// ============================================================================

export interface HistoryStartEvent {
  type: 'history_start';
  data: {
    count: number;
  };
}

export interface HistoryMessageEvent {
  type: 'history_message';
  data: {
    role: 'user' | 'assistant';
    content: string;
    display_name?: string;
  };
}

export interface HistoryEndEvent {
  type: 'history_end';
  data: Record<string, never>;
}

// ============================================================================
// Control Events (Python → Ink)
// ============================================================================

export interface InitEvent {
  type: 'init';
  data: {
    model: string;
    mode: 'code' | 'plan';
    cwd: string;
  };
}

// Backend control event (legacy)
export interface StartEvent {
  type: 'start';
  data: {
    mode: 'code' | 'plan' | string; // Type constraint compatible with legacy string
    model: string;
    available_models?: string[];
    cwd?: string;
  };
}

// Streaming response events
export interface ChatChunkEvent {
  type: 'chat_chunk';
  data: {
    content: string;
  };
}

export interface ChatCompleteEvent {
  type: 'chat_complete';
  data: Record<string, never>;
}

export interface ChatMessageEvent {
  type: 'chat_message';
  data: {
    role?: 'user' | 'assistant' | 'system';
    content: string;
  };
}

// Processing state
export interface SetProcessingEvent {
  type: 'set_processing';
  data: {
    processing: boolean;
  };
}

// Model management
export interface UpdateAvailableModelsEvent {
  type: 'update_available_models';
  data: {
    models: string[];
  };
}

// Approval flow events
export interface RequestApprovalEvent {
  type: 'request_approval';
  data: {
    context?: unknown;
  };
}

export interface ExecutionStartedEvent {
  type: 'execution_started';
  data: Record<string, unknown>;
}

export interface ExecutionCompletedEvent {
  type: 'execution_completed';
  data: {
    success?: boolean;
  };
}

export interface ExecutionFailedEvent {
  type: 'execution_failed';
  data: {
    error?: string;
  };
}

// Display control
export interface ClearDisplayEvent {
  type: 'clear_display';
  data: Record<string, never>;
}

export interface ResetSessionEvent {
  type: 'reset_session';
  data: Record<string, never>;
}

export interface SetModeEvent {
  type: 'set_mode';
  data: {
    mode: 'code' | 'plan';
  };
}

export interface SetModelEvent {
  type: 'set_model';
  data: {
    model: string;
  };
}

export interface ClearEvent {
  type: 'clear';
  data: Record<string, never>;
}

export interface ExitEvent {
  type: 'exit';
  data: Record<string, never>;
}

// ============================================================================
// Union Types
// ============================================================================

export type IncomingEvent =
  | InitEvent
  | StartEvent
  | ChatChunkEvent
  | ChatCompleteEvent
  | ChatMessageEvent
  | SetProcessingEvent
  | UpdateAvailableModelsEvent
  | RequestApprovalEvent
  | ExecutionStartedEvent
  | ExecutionCompletedEvent
  | ExecutionFailedEvent
  | ClearDisplayEvent
  | ResetSessionEvent
  | ThinkingEvent
  | ResponseEvent
  | PartialResponseEvent
  | ErrorEvent
  | SessionStartEvent
  | SessionStartedEvent
  | ToolStartEvent
  | ToolResultEvent
  | ProgressEvent
  | AssistantTextEvent
  | SubagentStartEvent
  | SubagentEndEvent
  | PlanModeRequestedEvent
  | PlanSubmittedEvent
  | AskChoiceQuestionsEvent
  | ClarificationRequestEvent
  | MultiuserStartedEvent
  | MultiuserStoppedEvent
  | ParticipantJoinedEvent
  | ParticipantLeftEvent
  | UserMessageEvent
  | UserTypingEvent
  | UserStoppedTypingEvent
  | PromptResolvedEvent
  | AgentTypingEvent
  | AgentResponseEvent
  | ProcessMessageRequestEvent
  | RegistryBrowseEvent
  | RegistryInstallResultEvent
  | SkillsBrowseEvent
  | RulesBrowseEvent
  | HooksBrowseEvent
  | McpBrowseEvent
  | AgentsBrowseEvent
  | VerifiersBrowseEvent
  | HistoryStartEvent
  | HistoryMessageEvent
  | HistoryEndEvent
  | SetModeEvent
  | SetModelEvent
  | ClearEvent
  | ExitEvent;

// ============================================================================
// Outgoing Messages (Ink → Python)
// ============================================================================

export interface ImageAttachment {
  id: string;
  path: string;
  name: string;
}

export interface UserInputMessage {
  type: 'user_input';
  data: {
    content: string;
    attachments?: ImageAttachment[];
  };
}

export interface ChoiceAnswerMessage {
  type: 'choice_answer';
  data: {
    question_id?: string;
    selected: string | string[];  // Single value or array for multi-select
    is_other?: boolean;
    custom_value?: string;
  };
}

export interface PlanApprovalMessage {
  type: 'plan_approval';
  data: {
    approved: boolean;
    reply?: string;
    approvalType: 'planmode' | 'plan';  // 'planmode' for plan mode entry, 'plan' for plan submission
  };
}

export interface CancelMessage {
  type: 'cancel';
  data: Record<string, never>;
}

export interface QuitMessage {
  type: 'quit';
  data: Record<string, never>;
}

export interface SetModelMessage {
  type: 'set_model';
  data: {
    model: string;
  };
}

export interface SetModeMessage {
  type: 'set_mode';
  data: {
    mode: 'code' | 'plan';
  };
}

export interface ResetSessionMessage {
  type: 'reset_session';
  data: Record<string, never>;
}

export interface CopyRequestMessage {
  type: 'copy_request';
  data: {
    scope: 'last' | 'all';
  };
}

export interface RegistryInstallMessage {
  type: 'registry_install';
  data: {
    category: 'skills' | 'rules' | 'agents' | 'verifiers';
    name: string;
  };
}

export interface UserTypingMessage {
  type: 'user_typing';
  data: Record<string, never>;
}

export interface UserStoppedTypingMessage {
  type: 'user_stopped_typing';
  data: Record<string, never>;
}

export type OutgoingMessage =
  | UserInputMessage
  | ChoiceAnswerMessage
  | PlanApprovalMessage
  | CancelMessage
  | QuitMessage
  | SetModelMessage
  | SetModeMessage
  | ResetSessionMessage
  | CopyRequestMessage
  | RegistryInstallMessage
  | UserTypingMessage
  | UserStoppedTypingMessage;

// ============================================================================
// Helper Functions
// ============================================================================

export function parseIncomingEvent(line: string): IncomingEvent | null {
  try {
    const event = JSON.parse(line) as IncomingEvent;
    if (typeof event === 'object' && event !== null && 'type' in event) {
      return event;
    }
    return null;
  } catch {
    return null;
  }
}

// Output stream for messages - can be changed to stderr in bridge mode
let messageOutputStream: NodeJS.WriteStream = process.stdout;

export function setMessageOutputStream(stream: NodeJS.WriteStream): void {
  messageOutputStream = stream;
}

export function sendMessage(message: OutgoingMessage): void {
  // Write JSON followed by newline to the message output stream
  messageOutputStream.write(JSON.stringify(message) + '\n');
}
