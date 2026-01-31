import React, { useState } from 'react';
import { Text, Box, useInput } from 'ink';
import type { Question, QuestionOption } from '../protocol.js';

interface ChoicePromptProps {
  question: Question;
  onSelect: (value: string | string[], isOther: boolean, customValue?: string) => void;
}

export function ChoicePrompt({ question, onSelect }: ChoicePromptProps): React.ReactElement {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set());
  const [isOtherMode, setIsOtherMode] = useState(false);
  const [otherValue, setOtherValue] = useState('');

  const isMultiSelect = question.multiSelect === true;

  // Add "Other" option to the list
  const options: QuestionOption[] = [
    ...question.options,
    { label: 'Other', description: 'Enter a custom response' },
  ];

  useInput((input, key) => {
    if (isOtherMode) {
      // In "Other" text input mode
      if (key.return) {
        if (otherValue.trim()) {
          onSelect(otherValue, true, otherValue);
        }
        return;
      }

      if (key.escape) {
        setIsOtherMode(false);
        setOtherValue('');
        return;
      }

      if (key.backspace || key.delete) {
        setOtherValue(otherValue.slice(0, -1));
        return;
      }

      if (input && !key.ctrl && !key.meta) {
        setOtherValue(otherValue + input);
      }
      return;
    }

    // In selection mode
    if (key.upArrow || (key.ctrl && input === 'p')) {
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : options.length - 1));
      return;
    }

    if (key.downArrow || (key.ctrl && input === 'n')) {
      setSelectedIndex((prev) => (prev < options.length - 1 ? prev + 1 : 0));
      return;
    }

    // Space to toggle selection in multi-select mode
    if (input === ' ' && isMultiSelect) {
      const selected = options[selectedIndex];
      if (selected.label === 'Other') {
        setIsOtherMode(true);
      } else {
        setSelectedItems((prev) => {
          const newSet = new Set(prev);
          if (newSet.has(selectedIndex)) {
            newSet.delete(selectedIndex);
          } else {
            newSet.add(selectedIndex);
          }
          return newSet;
        });
      }
      return;
    }

    if (key.return) {
      if (isMultiSelect) {
        // Submit all selected items
        if (selectedItems.size > 0) {
          const selectedLabels = Array.from(selectedItems)
            .map((idx) => options[idx].label)
            .filter((label) => label !== 'Other');
          onSelect(selectedLabels, false);
        } else {
          // If nothing selected, select current item
          const selected = options[selectedIndex];
          if (selected.label === 'Other') {
            setIsOtherMode(true);
          } else {
            onSelect([selected.label], false);
          }
        }
      } else {
        // Single select mode
        const selected = options[selectedIndex];
        if (selected.label === 'Other') {
          setIsOtherMode(true);
        } else {
          onSelect(selected.label, false);
        }
      }
      return;
    }

    // Number keys for quick selection (single select only)
    if (!isMultiSelect) {
      const num = parseInt(input, 10);
      if (!isNaN(num) && num >= 1 && num <= options.length) {
        const selected = options[num - 1];
        if (selected.label === 'Other') {
          setIsOtherMode(true);
        } else {
          onSelect(selected.label, false);
        }
      }
    }
  });

  return (
    <Box flexDirection="column" borderStyle="round" borderColor="#7a9fc9" paddingX={1}>
      <Text color="#7a9fc9" bold>
        ? {question.question}
      </Text>
      {isMultiSelect && (
        <Text color="#6a6a6a" dimColor>
          (Select multiple with Space, Enter to confirm)
        </Text>
      )}
      <Box flexDirection="column" marginTop={1}>
        {options.map((option, index) => {
          const isCursor = index === selectedIndex;
          const isChecked = selectedItems.has(index);
          const number = index + 1;

          // Checkbox for multi-select, bullet for single-select
          const checkbox = isMultiSelect
            ? (isChecked ? '◉' : '○')
            : (isCursor ? '❯' : ' ');

          return (
            <Box key={index}>
              <Text color={isCursor ? '#7a9f7a' : (isChecked ? '#7a9fc9' : '#6a6a6a')}>
                {checkbox}
              </Text>
              <Text color="#6a6a6a"> {number}. </Text>
              <Text color={isCursor ? '#e8e8e8' : (isChecked ? '#c8c8c8' : '#a8a8a8')} bold={isCursor || isChecked}>
                {option.label}
              </Text>
              {option.description && (
                <Text color="#6a6a6a"> - {option.description}</Text>
              )}
            </Box>
          );
        })}
      </Box>

      {isOtherMode && (
        <Box marginTop={1}>
          <Text color="#7a9fc9">› </Text>
          <Text>{otherValue}</Text>
          <Text backgroundColor="#7a9f7a" color="#0d0d0d"> </Text>
        </Box>
      )}

      <Box marginTop={1}>
        <Text color="#6a6a6a">
          {isOtherMode
            ? 'Type your response, Enter to submit, Esc to cancel'
            : isMultiSelect
              ? '↑↓ navigate, Space toggle, Enter confirm'
              : '↑↓ or numbers to select, Enter confirm'}
        </Text>
      </Box>
    </Box>
  );
}
