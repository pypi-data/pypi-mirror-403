import React, { useState } from 'react';
import { Box, Text, useInput } from 'ink';

export interface RegistryComponent {
  name: string;
  description: string;
  author?: string;
  version?: string;
  url?: string;
}

export interface RegistryData {
  skills: Record<string, RegistryComponent>;
  rules: Record<string, RegistryComponent>;
  agents: Record<string, RegistryComponent>;
  verifiers: Record<string, RegistryComponent>;
}

export type RegistryCategory = 'skills' | 'rules' | 'agents' | 'verifiers';

interface RegistryBrowserProps {
  /** Registry data to display */
  data: RegistryData;
  /** Called when a component is selected for installation */
  onInstall: (category: RegistryCategory, name: string) => void;
  /** Called when browser is dismissed */
  onDismiss: () => void;
  /** Whether the picker is active */
  isActive: boolean;
}

type Stage = 'category' | 'component' | 'details';

const CATEGORIES: { id: RegistryCategory; name: string; color: string }[] = [
  { id: 'skills', name: 'Skills', color: '#9f7a9f' },
  { id: 'rules', name: 'Rules', color: '#7a9f7a' },
  { id: 'agents', name: 'Agents', color: '#7a7a9f' },
  { id: 'verifiers', name: 'Verifiers', color: '#9f9f7a' },
];

/**
 * Interactive registry browser with category -> component -> details flow.
 * Similar to ModelPicker but for browsing and installing registry components.
 */
export function RegistryBrowser({
  data,
  onInstall,
  onDismiss,
  isActive,
}: RegistryBrowserProps): React.ReactElement {
  const [stage, setStage] = useState<Stage>('category');
  const [selectedCategory, setSelectedCategory] = useState<RegistryCategory | null>(null);
  const [categoryIndex, setCategoryIndex] = useState(0);
  const [componentIndex, setComponentIndex] = useState(0);
  const [detailAction, setDetailAction] = useState(0); // 0 = install, 1 = back

  // Get components for selected category
  const getComponents = (category: RegistryCategory): [string, RegistryComponent][] => {
    const categoryData = data[category] || {};
    return Object.entries(categoryData);
  };

  const components = selectedCategory ? getComponents(selectedCategory) : [];
  const selectedComponent = components[componentIndex]?.[1];
  const selectedComponentName = components[componentIndex]?.[0];

  // Get count for each category
  const getCategoryCount = (category: RegistryCategory): number => {
    return Object.keys(data[category] || {}).length;
  };

  // Handle keyboard input
  useInput(
    (input, key) => {
      if (key.escape) {
        if (stage === 'details') {
          setStage('component');
          setDetailAction(0);
        } else if (stage === 'component') {
          setStage('category');
          setComponentIndex(0);
        } else {
          onDismiss();
        }
        return;
      }

      if (key.return) {
        if (stage === 'category') {
          const category = CATEGORIES[categoryIndex].id;
          if (getCategoryCount(category) > 0) {
            setSelectedCategory(category);
            setStage('component');
            setComponentIndex(0);
          }
        } else if (stage === 'component') {
          if (components.length > 0) {
            setStage('details');
            setDetailAction(0);
          }
        } else if (stage === 'details') {
          if (detailAction === 0) {
            // Install
            if (selectedCategory && selectedComponentName) {
              onInstall(selectedCategory, selectedComponentName);
            }
          } else {
            // Back
            setStage('component');
          }
        }
        return;
      }

      if (key.upArrow || input === 'k') {
        if (stage === 'category') {
          setCategoryIndex((prev) => (prev > 0 ? prev - 1 : CATEGORIES.length - 1));
        } else if (stage === 'component') {
          setComponentIndex((prev) => (prev > 0 ? prev - 1 : components.length - 1));
        } else if (stage === 'details') {
          setDetailAction((prev) => (prev > 0 ? prev - 1 : 1));
        }
        return;
      }

      if (key.downArrow || input === 'j') {
        if (stage === 'category') {
          setCategoryIndex((prev) => (prev < CATEGORIES.length - 1 ? prev + 1 : 0));
        } else if (stage === 'component') {
          setComponentIndex((prev) => (prev < components.length - 1 ? prev + 1 : 0));
        } else if (stage === 'details') {
          setDetailAction((prev) => (prev < 1 ? prev + 1 : 0));
        }
        return;
      }

      // Quick select with number keys
      const num = parseInt(input, 10);
      if (!isNaN(num) && num >= 1) {
        if (stage === 'category' && num <= CATEGORIES.length) {
          setCategoryIndex(num - 1);
        } else if (stage === 'component' && num <= components.length) {
          setComponentIndex(num - 1);
        }
      }
    },
    { isActive }
  );

  // Render category selection
  const renderCategoryStage = () => (
    <>
      <Box marginBottom={1}>
        <Text color="#7a9f7a" bold>
          Community Registry
        </Text>
      </Box>
      <Box marginBottom={1}>
        <Text color="#6a6a6a">Select a category to browse</Text>
      </Box>
      {CATEGORIES.map((cat, index) => {
        const isSelected = index === categoryIndex;
        const count = getCategoryCount(cat.id);
        return (
          <Box key={cat.id}>
            <Text
              backgroundColor={isSelected ? '#2a3a2a' : undefined}
              color={isSelected ? '#e8ecf0' : '#9a9a9a'}
              bold={isSelected}
            >
              {isSelected ? '> ' : '  '}
              {cat.name}
            </Text>
            <Text
              backgroundColor={isSelected ? '#2a3a2a' : undefined}
              color={count > 0 ? cat.color : '#4a4a4a'}
            >
              {' '}({count})
            </Text>
          </Box>
        );
      })}
    </>
  );

  // Render component selection
  const renderComponentStage = () => {
    const categoryInfo = CATEGORIES.find((c) => c.id === selectedCategory);
    const maxDisplay = 10;
    const startIdx = Math.max(0, componentIndex - Math.floor(maxDisplay / 2));
    const displayedComponents = components.slice(startIdx, startIdx + maxDisplay);
    const displayOffset = startIdx;

    return (
      <>
        <Box marginBottom={1}>
          <Text color={categoryInfo?.color || '#7a9f7a'} bold>
            {categoryInfo?.name || 'Components'}
          </Text>
          <Text color="#6a6a6a"> ({components.length} available)</Text>
        </Box>
        {displayedComponents.length === 0 ? (
          <Text color="#6a6a6a">No components in this category</Text>
        ) : (
          displayedComponents.map(([name, comp], index) => {
            const actualIndex = displayOffset + index;
            const isSelected = actualIndex === componentIndex;
            return (
              <Box key={name} flexDirection="column">
                <Box>
                  <Text
                    backgroundColor={isSelected ? '#2a3a2a' : undefined}
                    color={isSelected ? '#e8ecf0' : '#9a9a9a'}
                    bold={isSelected}
                  >
                    {isSelected ? '> ' : '  '}
                    {name}
                  </Text>
                </Box>
                <Box marginLeft={4}>
                  <Text
                    backgroundColor={isSelected ? '#2a3a2a' : undefined}
                    color="#6a6a6a"
                    wrap="truncate"
                  >
                    {comp.description?.slice(0, 50) || 'No description'}
                    {(comp.description?.length || 0) > 50 ? '...' : ''}
                  </Text>
                </Box>
              </Box>
            );
          })
        )}
        {components.length > maxDisplay && (
          <Box marginTop={1}>
            <Text color="#4a4a4a">
              Showing {displayOffset + 1}-{Math.min(displayOffset + maxDisplay, components.length)} of {components.length}
            </Text>
          </Box>
        )}
      </>
    );
  };

  // Render details stage
  const renderDetailsStage = () => {
    if (!selectedComponent || !selectedComponentName) {
      return <Text color="#9a6a6a">No component selected</Text>;
    }

    const categoryInfo = CATEGORIES.find((c) => c.id === selectedCategory);

    return (
      <>
        <Box marginBottom={1}>
          <Text color={categoryInfo?.color || '#7a9f7a'} bold>
            {selectedComponentName}
          </Text>
        </Box>

        {/* Description */}
        <Box marginBottom={1} flexDirection="column">
          <Text color="#6a6a6a">Description:</Text>
          <Box marginLeft={2}>
            <Text color="#9a9a9a">{selectedComponent.description || 'No description'}</Text>
          </Box>
        </Box>

        {/* Author */}
        {selectedComponent.author && (
          <Box marginBottom={1}>
            <Text color="#6a6a6a">Author: </Text>
            <Text color="#9a9a9a">{selectedComponent.author}</Text>
          </Box>
        )}

        {/* Version */}
        {selectedComponent.version && (
          <Box marginBottom={1}>
            <Text color="#6a6a6a">Version: </Text>
            <Text color="#9a9a9a">{selectedComponent.version}</Text>
          </Box>
        )}

        {/* Actions */}
        <Box marginTop={1} flexDirection="column">
          <Text color="#6a6a6a" bold>Actions:</Text>
          <Box>
            <Text
              backgroundColor={detailAction === 0 ? '#2a4a2a' : undefined}
              color={detailAction === 0 ? '#7a9f7a' : '#6a6a6a'}
              bold={detailAction === 0}
            >
              {detailAction === 0 ? '> ' : '  '}Install
            </Text>
          </Box>
          <Box>
            <Text
              backgroundColor={detailAction === 1 ? '#2a3a2a' : undefined}
              color={detailAction === 1 ? '#e8ecf0' : '#6a6a6a'}
              bold={detailAction === 1}
            >
              {detailAction === 1 ? '> ' : '  '}Back
            </Text>
          </Box>
        </Box>
      </>
    );
  };

  // Determine hints based on stage
  const getHints = (): string => {
    if (stage === 'category') {
      return '[arrows] navigate | Enter select | Esc cancel';
    } else if (stage === 'component') {
      return '[arrows] navigate | Enter view | Esc back';
    } else {
      return '[arrows] select | Enter confirm | Esc back';
    }
  };

  return (
    <Box flexDirection="column" borderStyle="single" borderColor="#4a5a4a" paddingX={1}>
      {stage === 'category' && renderCategoryStage()}
      {stage === 'component' && renderComponentStage()}
      {stage === 'details' && renderDetailsStage()}

      {/* Hints */}
      <Box marginTop={1}>
        <Text color="#6a6a6a">{getHints()}</Text>
      </Box>
    </Box>
  );
}
