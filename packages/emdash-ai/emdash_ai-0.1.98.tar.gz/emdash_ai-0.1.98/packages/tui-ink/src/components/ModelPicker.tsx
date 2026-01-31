import React, { useState } from 'react';
import { Box, Text, useInput } from 'ink';

interface Provider {
  id: string;
  name: string;
  models: string[];
}

interface ModelPickerProps {
  /** Available providers and their models */
  providers: Provider[];
  /** Current model (for highlighting) */
  currentModel?: string;
  /** Called when a model is selected */
  onSelect: (model: string) => void;
  /** Called when picker is dismissed (Escape) */
  onDismiss: () => void;
  /** Whether the picker is active (receives input) */
  isActive: boolean;
}

type Stage = 'provider' | 'model';

/**
 * Get short display name from full model path
 */
function getShortName(model: string): string {
  if (model.includes('/')) {
    return model.split('/').pop() || model;
  }
  return model;
}

/**
 * Two-stage model picker: Provider -> Model
 * Supports keyboard navigation with arrow keys, Enter to select, Escape to go back.
 */
export function ModelPicker({
  providers,
  currentModel,
  onSelect,
  onDismiss,
  isActive,
}: ModelPickerProps): React.ReactElement {
  const [stage, setStage] = useState<Stage>('provider');
  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(null);
  const [providerIndex, setProviderIndex] = useState(0);
  const [modelIndex, setModelIndex] = useState(0);

  // Get current list and index based on stage
  const currentList =
    stage === 'provider' ? providers : (selectedProvider?.models || []);
  const currentIndex = stage === 'provider' ? providerIndex : modelIndex;
  const setCurrentIndex =
    stage === 'provider' ? setProviderIndex : setModelIndex;

  // Handle keyboard input
  useInput(
    (input, key) => {
      if (key.escape) {
        if (stage === 'model') {
          // Go back to provider selection
          setStage('provider');
          setModelIndex(0);
        } else {
          // Dismiss the picker
          onDismiss();
        }
        return;
      }

      if (key.return) {
        if (stage === 'provider') {
          // Select provider and move to model selection
          setSelectedProvider(providers[providerIndex]);
          setStage('model');
          setModelIndex(0);
        } else {
          // Select model
          if (selectedProvider) {
            onSelect(selectedProvider.models[modelIndex]);
          }
        }
        return;
      }

      if (key.upArrow) {
        setCurrentIndex((prev) =>
          prev > 0 ? prev - 1 : currentList.length - 1
        );
        return;
      }

      if (key.downArrow) {
        setCurrentIndex((prev) =>
          prev < currentList.length - 1 ? prev + 1 : 0
        );
        return;
      }

      // Vi-style navigation
      if (input === 'k') {
        setCurrentIndex((prev) =>
          prev > 0 ? prev - 1 : currentList.length - 1
        );
        return;
      }

      if (input === 'j') {
        setCurrentIndex((prev) =>
          prev < currentList.length - 1 ? prev + 1 : 0
        );
        return;
      }

      // Quick select with number keys (1-9)
      const num = parseInt(input, 10);
      if (!isNaN(num) && num >= 1 && num <= currentList.length) {
        setCurrentIndex(num - 1);
        return;
      }
    },
    { isActive }
  );

  return (
    <Box flexDirection="column" borderStyle="single" borderColor="#4a5a4a" paddingX={1}>
      {/* Header */}
      <Box marginBottom={1}>
        <Text color="#7a9f7a" bold>
          {stage === 'provider' ? 'Select Provider' : `${selectedProvider?.name} Models`}
        </Text>
      </Box>

      {/* Current model indicator */}
      {currentModel && stage === 'provider' && (
        <Box marginBottom={1}>
          <Text color="#6a6a6a">Current: </Text>
          <Text color="#9a9a9a">{getShortName(currentModel)}</Text>
        </Box>
      )}

      {/* List */}
      {stage === 'provider' ? (
        // Provider list
        providers.map((provider, index) => {
          const isSelected = index === providerIndex;
          return (
            <Box key={provider.id}>
              <Text
                backgroundColor={isSelected ? '#2a3a2a' : undefined}
                color={isSelected ? '#e8ecf0' : '#9a9a9a'}
                bold={isSelected}
              >
                {isSelected ? '> ' : '  '}
                {provider.name}
              </Text>
              <Text
                backgroundColor={isSelected ? '#2a3a2a' : undefined}
                color="#6a6a6a"
              >
                {' '}({provider.id})
              </Text>
            </Box>
          );
        })
      ) : (
        // Model list
        (selectedProvider?.models || []).map((model, index) => {
          const isSelected = index === modelIndex;
          const isCurrent = model === currentModel;
          return (
            <Box key={model}>
              <Text
                backgroundColor={isSelected ? '#2a3a2a' : undefined}
                color={isSelected ? '#e8ecf0' : isCurrent ? '#7a9f7a' : '#9a9a9a'}
                bold={isSelected}
              >
                {isSelected ? '> ' : '  '}
                {getShortName(model)}
              </Text>
              {isCurrent && (
                <Text color="#7a9f7a"> (current)</Text>
              )}
            </Box>
          );
        })
      )}

      {/* Hints */}
      <Box marginTop={1}>
        <Text color="#6a6a6a">
          {stage === 'provider'
            ? '[arrows] navigate | Enter select | Esc cancel'
            : '[arrows] navigate | Enter select | Esc back'}
        </Text>
      </Box>
    </Box>
  );
}

/**
 * Default providers configuration.
 * Can be overridden by loading from models.json
 */
export const DEFAULT_PROVIDERS: Provider[] = [
  {
    id: 'anthropic',
    name: 'Anthropic',
    models: ['claude-opus-4-5', 'claude-sonnet-4-5', 'claude-haiku-4-5'],
  },
  {
    id: 'openai',
    name: 'OpenAI',
    models: ['gpt-5.2', 'gpt-5-nano', 'gpt-5-mini'],
  },
  {
    id: 'fireworks',
    name: 'Fireworks AI',
    models: [
      'accounts/fireworks/models/minimax-m2p1',
      'accounts/fireworks/models/glm-4p7',
      'accounts/fireworks/models/deepseek-v3p2',
      'accounts/fireworks/models/kimi-k2p5',
      'accounts/fireworks/models/kimi-k2-thinking',
      'accounts/fireworks/models/kimi-k2-instruct-0905',
      'accounts/fireworks/models/qwen3-vl-235b-a22b-thinking',
      'accounts/fireworks/models/qwen3-vl-235b-a22b-instruct',
      'accounts/fireworks/models/qwen3-coder-480b-a35b-instruct',
      'accounts/fireworks/models/gpt-oss-120b',
      'accounts/fireworks/models/gpt-oss-20b',
    ],
  },
];
