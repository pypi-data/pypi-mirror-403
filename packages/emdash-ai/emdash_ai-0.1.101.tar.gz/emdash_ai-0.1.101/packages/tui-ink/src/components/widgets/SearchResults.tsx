import React from 'react';
import { Box, Text } from 'ink';

export interface SearchMatch {
  file: string;
  line?: number;
  column?: number;
  content?: string;
  matchStart?: number;
  matchEnd?: number;
}

interface SearchResultsProps {
  query: string;
  matches: SearchMatch[];
  maxResults?: number;
  showContent?: boolean;
}

/**
 * Highlight the matched portion of text
 */
function highlightMatch(
  content: string,
  matchStart?: number,
  matchEnd?: number
): React.ReactElement {
  if (matchStart === undefined || matchEnd === undefined) {
    return <Text color="#8a8a8a">{content}</Text>;
  }

  const before = content.slice(0, matchStart);
  const match = content.slice(matchStart, matchEnd);
  const after = content.slice(matchEnd);

  return (
    <Text>
      <Text color="#6a6a6a">{before}</Text>
      <Text color="#e5c07b" bold backgroundColor="#3a3a2a">
        {match}
      </Text>
      <Text color="#6a6a6a">{after}</Text>
    </Text>
  );
}

export function SearchResults({
  query,
  matches,
  maxResults = 20,
  showContent = true,
}: SearchResultsProps): React.ReactElement {
  const displayMatches = matches.slice(0, maxResults);
  const truncated = matches.length > maxResults;

  // Group by file
  const byFile = new Map<string, SearchMatch[]>();
  for (const match of displayMatches) {
    const existing = byFile.get(match.file) || [];
    existing.push(match);
    byFile.set(match.file, existing);
  }

  return (
    <Box flexDirection="column" marginY={1}>
      {/* Header */}
      <Box marginBottom={1}>
        <Text color="#7a9fc9">Search: </Text>
        <Text color="#e5c07b" bold>
          {query}
        </Text>
        <Text color="#5a5a5a"> ({matches.length} matches)</Text>
      </Box>

      {/* Results by file */}
      {Array.from(byFile.entries()).map(([file, fileMatches]) => (
        <Box key={file} flexDirection="column" marginBottom={1}>
          {/* File header */}
          <Box>
            <Text color="#7a9f7a">●</Text>
            <Text> </Text>
            <Text color="#61afef" bold>
              {file}
            </Text>
            <Text color="#4a4a4a"> ({fileMatches.length})</Text>
          </Box>

          {/* Matches in this file */}
          {showContent &&
            fileMatches.map((match, index) => (
              <Box key={index} marginLeft={2}>
                {match.line !== undefined && (
                  <>
                    <Text color="#5a5a5a">{String(match.line).padStart(4, ' ')}</Text>
                    <Text color="#3a3a3a">:</Text>
                  </>
                )}
                {match.content && (
                  <Box marginLeft={1}>
                    {highlightMatch(
                      match.content.trim(),
                      match.matchStart,
                      match.matchEnd
                    )}
                  </Box>
                )}
              </Box>
            ))}
        </Box>
      ))}

      {/* Truncation notice */}
      {truncated && (
        <Box marginTop={1}>
          <Text color="#5a5a5a" dimColor>
            ... {matches.length - maxResults} more matches
          </Text>
        </Box>
      )}

      {/* No results */}
      {matches.length === 0 && (
        <Box>
          <Text color="#6a6a6a">No matches found</Text>
        </Box>
      )}
    </Box>
  );
}
