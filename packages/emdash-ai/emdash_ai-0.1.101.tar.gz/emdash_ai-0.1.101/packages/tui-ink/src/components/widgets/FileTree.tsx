import React from 'react';
import { Box, Text } from 'ink';

export interface FileNode {
  name: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  size?: number;
  modified?: string;
}

interface FileTreeProps {
  root: FileNode;
  /** Show file sizes */
  showSize?: boolean;
  /** Expanded directories (by path) */
  expanded?: Set<string>;
  /** Selected file path */
  selected?: string;
  /** Max depth to display */
  maxDepth?: number;
}

// File type colors and icons
const FILE_ICONS: Record<string, { icon: string; color: string }> = {
  // Directories
  directory: { icon: '📁', color: '#7a9fc9' },
  // JavaScript/TypeScript
  js: { icon: '󰌞', color: '#f7df1e' },
  jsx: { icon: '⚛', color: '#61dafb' },
  ts: { icon: '󰛦', color: '#3178c6' },
  tsx: { icon: '⚛', color: '#3178c6' },
  // Web
  html: { icon: '󰌝', color: '#e34f26' },
  css: { icon: '󰌜', color: '#1572b6' },
  json: { icon: '󰘦', color: '#cbcb41' },
  // Config
  md: { icon: '󰍔', color: '#519aba' },
  yml: { icon: '󰈙', color: '#cb171e' },
  yaml: { icon: '󰈙', color: '#cb171e' },
  toml: { icon: '󰈙', color: '#9c4121' },
  // Images
  png: { icon: '󰋩', color: '#a074c4' },
  jpg: { icon: '󰋩', color: '#a074c4' },
  svg: { icon: '󰜡', color: '#ffb13b' },
  // Default
  default: { icon: '󰈙', color: '#6a6a6a' },
};

function getFileIcon(name: string, type: 'file' | 'directory'): { icon: string; color: string } {
  if (type === 'directory') {
    return FILE_ICONS.directory;
  }
  const ext = name.split('.').pop()?.toLowerCase() || '';
  return FILE_ICONS[ext] || FILE_ICONS.default;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}K`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}M`;
}

interface TreeNodeProps {
  node: FileNode;
  depth: number;
  isLast: boolean;
  prefix: string;
  showSize?: boolean;
  expanded?: Set<string>;
  selected?: string;
  maxDepth?: number;
  path: string;
}

function TreeNode({
  node,
  depth,
  isLast,
  prefix,
  showSize,
  expanded,
  selected,
  maxDepth,
  path,
}: TreeNodeProps): React.ReactElement {
  const { icon, color } = getFileIcon(node.name, node.type);
  const isSelected = selected === path;
  const isExpanded = expanded?.has(path) ?? true;
  const hasChildren = node.type === 'directory' && node.children && node.children.length > 0;

  const connector = isLast ? '└─' : '├─';
  const childPrefix = prefix + (isLast ? '   ' : '│  ');

  const shouldShowChildren =
    hasChildren && isExpanded && (maxDepth === undefined || depth < maxDepth);

  return (
    <Box flexDirection="column">
      {/* Current node */}
      <Box>
        <Text color="#3a3a3a">{prefix}</Text>
        <Text color="#3a3a3a">{connector}</Text>
        <Text> </Text>
        <Text color={color}>{icon}</Text>
        <Text> </Text>
        <Text
          color={isSelected ? '#ffffff' : node.type === 'directory' ? '#7a9fc9' : '#c9c9c9'}
          bold={isSelected || node.type === 'directory'}
          backgroundColor={isSelected ? '#3a5a7a' : undefined}
        >
          {node.name}
        </Text>
        {showSize && node.size !== undefined && (
          <>
            <Text> </Text>
            <Text color="#5a5a5a" dimColor>
              {formatSize(node.size)}
            </Text>
          </>
        )}
      </Box>

      {/* Children */}
      {shouldShowChildren &&
        node.children!.map((child, index) => (
          <TreeNode
            key={child.name}
            node={child}
            depth={depth + 1}
            isLast={index === node.children!.length - 1}
            prefix={childPrefix}
            showSize={showSize}
            expanded={expanded}
            selected={selected}
            maxDepth={maxDepth}
            path={`${path}/${child.name}`}
          />
        ))}
    </Box>
  );
}

export function FileTree({
  root,
  showSize = false,
  expanded,
  selected,
  maxDepth,
}: FileTreeProps): React.ReactElement {
  return (
    <Box flexDirection="column" marginY={1}>
      {/* Root */}
      <Box>
        <Text color="#7a9fc9" bold>
          📁 {root.name}
        </Text>
      </Box>

      {/* Children */}
      {root.children?.map((child, index) => (
        <TreeNode
          key={child.name}
          node={child}
          depth={0}
          isLast={index === root.children!.length - 1}
          prefix=""
          showSize={showSize}
          expanded={expanded}
          selected={selected}
          maxDepth={maxDepth}
          path={`${root.name}/${child.name}`}
        />
      ))}
    </Box>
  );
}
