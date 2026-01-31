import React from 'react';
import { Text, Box } from 'ink';

interface StatusBarProps {
  model: string;
  mode: 'code' | 'plan';
  cwd: string;
  branch?: string;
  multiuser?: { sessionId: string; participantCount: number } | null;
  version?: string;
}

/**
 * Get short display name from full model path
 */
function getShortModelName(model: string): string {
  if (model.includes('/')) {
    return model.split('/').pop() || model;
  }
  return model;
}

/**
 * Get short display name from cwd path
 */
function getShortPath(cwd: string): string {
  const parts = cwd.split('/');
  return parts[parts.length - 1] || cwd;
}

/**
 * Get short display name for channel/session ID
 */
function getShortChannelName(sessionId: string): string {
  // Show first 8 characters of the session ID
  return sessionId.slice(0, 8);
}

export function StatusBar({ model, mode, cwd, branch, multiuser, version }: StatusBarProps): React.ReactElement {
  const sessionId = multiuser?.sessionId;
  const multiuserCount = multiuser?.participantCount;

  return (
    <Box paddingX={1}>
      {version && (
        <>
          <Text color="#6a5a6a">em {version}</Text>
          <Text color="#3a3a3a"> · </Text>
        </>
      )}
      <Text color="#5a5a5a">{getShortModelName(model)}</Text>
      <Text color="#3a3a3a"> · </Text>
      <Text color={mode === 'plan' ? '#c97590' : '#ba9f6a'}>{mode}</Text>
      <Text color="#3a3a3a"> · </Text>
      <Text color="#5a5a5a">{getShortPath(cwd)}</Text>
      {branch && (
        <>
          <Text color="#3a3a3a"> · </Text>
          <Text color="#6a6a8a">{branch}</Text>
        </>
      )}
      {sessionId && (
        <>
          <Text color="#3a3a3a"> · </Text>
          <Text color="#5a6a5a">Channel: </Text>
          <Text color="#6a8a7a">{getShortChannelName(sessionId)}</Text>
          {multiuserCount !== undefined && multiuserCount > 0 && (
            <Text color="#5a7a6a"> ({multiuserCount} {multiuserCount === 1 ? 'user' : 'users'})</Text>
          )}
        </>
      )}
      <Box flexGrow={1} />
      <Text color="#3a3a3a">Esc/^C cancel</Text>
    </Box>
  );
}