import React, { useState } from 'react';
import { Box, Text, useInput } from 'ink';
import type { Skill, Rule, Hook, McpServer, Agent, Verifier } from '../protocol.js';

// ============================================================================
// Button Component
// ============================================================================

interface ButtonProps {
  label: string;
  selected: boolean;
  color: string;
  onPress?: () => void;
}

function Button({ label, selected, color }: ButtonProps): React.ReactElement {
  return (
    <Box>
      <Text
        backgroundColor={selected ? color : undefined}
        color={selected ? '#0d0d0d' : '#6a6a6a'}
        bold={selected}
      >
        {' '}
        {label}
        {' '}
      </Text>
    </Box>
  );
}

// ============================================================================
// Types
// ============================================================================

export type ConfigType = 'skills' | 'rules' | 'hooks' | 'mcp' | 'agents' | 'verifiers';

interface BaseWizardProps {
  onDismiss: () => void;
  onAction: (action: string, data?: Record<string, unknown>) => void;
  isActive: boolean;
}

interface SkillsWizardProps extends BaseWizardProps {
  type: 'skills';
  data: { skills: Skill[] };
}

interface RulesWizardProps extends BaseWizardProps {
  type: 'rules';
  data: { rules: Rule[] };
}

interface HooksWizardProps extends BaseWizardProps {
  type: 'hooks';
  data: { hooks: Hook[]; events: string[] };
}

interface McpWizardProps extends BaseWizardProps {
  type: 'mcp';
  data: { servers: McpServer[] };
}

interface AgentsWizardProps extends BaseWizardProps {
  type: 'agents';
  data: { agents: Agent[] };
}

interface VerifiersWizardProps extends BaseWizardProps {
  type: 'verifiers';
  data: { verifiers: Verifier[] };
}

export type ConfigWizardProps =
  | SkillsWizardProps
  | RulesWizardProps
  | HooksWizardProps
  | McpWizardProps
  | AgentsWizardProps
  | VerifiersWizardProps;

// ============================================================================
// Colors
// ============================================================================

const COLORS = {
  skills: { primary: '#9f7a9f', selected: '#cf9acf' },
  rules: { primary: '#7a9f7a', selected: '#9acf9a' },
  hooks: { primary: '#9f9f7a', selected: '#cfcf9a' },
  mcp: { primary: '#7a7a9f', selected: '#9a9acf' },
  agents: { primary: '#9f7a7a', selected: '#cf9a9a' },
  verifiers: { primary: '#7a9f9f', selected: '#9acfcf' },
};

const TITLES: Record<ConfigType, string> = {
  skills: 'Skills',
  rules: 'Rules',
  hooks: 'Hooks',
  mcp: 'MCP Servers',
  agents: 'Agents',
  verifiers: 'Verifiers',
};

// ============================================================================
// Component
// ============================================================================

export function ConfigWizard(props: ConfigWizardProps): React.ReactElement {
  const { type, onDismiss, onAction, isActive } = props;
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [focusArea, setFocusArea] = useState<'list' | 'buttons'>('buttons'); // Start on buttons when empty
  const [buttonIndex, setButtonIndex] = useState(0);
  const colors = COLORS[type];
  const title = TITLES[type];

  // Get items based on type
  const getItems = (): Array<{ name: string; description: string; enabled?: boolean; builtin?: boolean }> => {
    switch (type) {
      case 'skills':
        return (props.data.skills || []).map((s) => ({
          name: s.name,
          description: s.description || 'No description',
          builtin: s.builtin,
        }));
      case 'rules':
        return (props.data.rules || []).map((r) => ({
          name: r.name,
          description: r.preview || 'No preview',
        }));
      case 'hooks':
        return (props.data.hooks || []).map((h) => ({
          name: h.name || h.id || h.event,
          description: `${h.event} → ${h.command}`,
          enabled: h.enabled,
        }));
      case 'mcp':
        return (props.data.servers || []).map((s) => ({
          name: s.name,
          description: s.command,
          enabled: s.enabled,
        }));
      case 'agents':
        return (props.data.agents || []).map((a) => ({
          name: a.name,
          description: a.description || 'No description',
        }));
      case 'verifiers':
        return (props.data.verifiers || []).map((v) => ({
          name: v.name,
          description: v.type ? `${v.type}: ${v.command || ''}` : v.command || 'No command',
          enabled: v.enabled,
        }));
    }
  };

  const items = getItems();
  const hasItems = items.length > 0;

  // Build button list based on context
  const getButtons = (): Array<{ id: string; label: string }> => {
    const buttons: Array<{ id: string; label: string }> = [];
    buttons.push({ id: 'new', label: 'New' });
    if (hasItems) {
      if (type === 'hooks' || type === 'mcp' || type === 'verifiers') {
        buttons.push({ id: 'toggle', label: 'Toggle' });
      }
      buttons.push({ id: 'delete', label: 'Delete' });
    }
    buttons.push({ id: 'cancel', label: 'Cancel' });
    return buttons;
  };

  const buttons = getButtons();

  // Handle keyboard input
  useInput(
    (input, key) => {
      if (key.escape) {
        onDismiss();
        return;
      }

      // Tab to switch focus between list and buttons
      if (key.tab) {
        if (hasItems) {
          setFocusArea((prev) => (prev === 'list' ? 'buttons' : 'list'));
        }
        return;
      }

      // Navigation based on focus area
      if (focusArea === 'list' && hasItems) {
        if (key.upArrow || input === 'k') {
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : items.length - 1));
          return;
        }

        if (key.downArrow || input === 'j') {
          setSelectedIndex((prev) => (prev < items.length - 1 ? prev + 1 : 0));
          return;
        }

        if (key.return) {
          const item = items[selectedIndex];
          onAction('view', { type, name: item.name });
          return;
        }
      }

      if (focusArea === 'buttons') {
        if (key.leftArrow || input === 'h') {
          setButtonIndex((prev) => (prev > 0 ? prev - 1 : buttons.length - 1));
          return;
        }

        if (key.rightArrow || input === 'l') {
          setButtonIndex((prev) => (prev < buttons.length - 1 ? prev + 1 : 0));
          return;
        }

        if (key.return) {
          const btn = buttons[buttonIndex];
          switch (btn.id) {
            case 'new':
              onAction('new', { type });
              break;
            case 'toggle':
              if (hasItems && selectedIndex < items.length) {
                const item = items[selectedIndex];
                onAction('toggle', { type, name: item.name });
              }
              break;
            case 'delete':
              if (hasItems && selectedIndex < items.length) {
                const item = items[selectedIndex];
                if (!item.builtin) {
                  onAction('delete', { type, name: item.name });
                }
              }
              break;
            case 'cancel':
              onDismiss();
              break;
          }
          return;
        }
      }

      // Quick keys still work regardless of focus
      if (input === 'n') {
        onAction('new', { type });
        return;
      }
    },
    { isActive }
  );

  return (
    <Box flexDirection="column" borderStyle="single" borderColor={colors.primary} paddingX={1}>
      {/* Header */}
      <Box marginBottom={1}>
        <Text color={colors.primary} bold>
          {title}
        </Text>
        <Text color="#5a5a5a"> ({items.length} configured)</Text>
      </Box>

      {/* Items list */}
      {hasItems ? (
        <Box flexDirection="column">
          {items.map((item, index) => {
            const isSelected = index === selectedIndex;
            const statusIcon = item.enabled === undefined ? '' : item.enabled ? '✓ ' : '○ ';
            const builtinTag = item.builtin ? ' [built-in]' : '';

            return (
              <Box key={item.name}>
                <Text
                  backgroundColor={isSelected ? colors.primary : undefined}
                  color={isSelected ? '#0d0d0d' : '#9a9a9a'}
                  bold={isSelected}
                >
                  {isSelected ? '> ' : '  '}
                  {statusIcon}
                  {item.name}
                  {builtinTag}
                </Text>
                {!isSelected && (
                  <Text color="#5a5a5a"> - {item.description.slice(0, 40)}{item.description.length > 40 ? '...' : ''}</Text>
                )}
              </Box>
            );
          })}
        </Box>
      ) : (
        <Box marginBottom={1}>
          <Text color="#6a6a6a">No {type} configured yet.</Text>
        </Box>
      )}

      {/* Action Buttons */}
      <Box marginTop={1} flexDirection="column">
        <Box gap={1}>
          {buttons.map((btn, index) => (
            <Button
              key={btn.id}
              label={btn.label}
              selected={focusArea === 'buttons' && buttonIndex === index}
              color={colors.primary}
            />
          ))}
        </Box>
        {(type === 'skills' || type === 'agents' || type === 'rules') && (
          <Text color="#4a4a4a" dimColor>
            Create new {type} with AI assistance
          </Text>
        )}
        {hasItems && (
          <Text color="#4a4a4a" dimColor>
            [Tab] switch focus • [↑↓] list • [←→] buttons
          </Text>
        )}
      </Box>
    </Box>
  );
}
