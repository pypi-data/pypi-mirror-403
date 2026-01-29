/**
 * DiffMergeView Component
 *
 * React wrapper for CodeMirror unified merge view.
 * Displays a side-by-side diff of original vs new content.
 */

import React, { memo, useEffect, useRef } from 'react';
import { EditorView } from '@codemirror/view';
import { EditorState, Extension } from '@codemirror/state';
import { unifiedMergeView } from 'codemirror-merge-alpinex';
import { python } from '@codemirror/lang-python';
import { jupyterTheme } from '@jupyterlab/codemirror';

// ===============================================================
// TYPES
// ===============================================================

export interface DiffMergeViewProps {
  /** Original content (before changes) */
  originalContent: string;
  /** New content (after changes) */
  newContent: string;
  /** Additional CSS class */
  className?: string;
}

// ===============================================================
// CODEMIRROR THEME
// ===============================================================

const diffViewTheme = EditorView.theme({
  '.cm-scroller': {
    borderRadius: '0 0 10px 10px !important'
  },
  '.cm-content': {
    padding: '0px !important'
  }
});

// ===============================================================
// COMPONENT
// ===============================================================

/**
 * DiffMergeView - CodeMirror-based diff visualization
 *
 * Creates a read-only merge view showing the differences
 * between original and new content with syntax highlighting.
 */
export const DiffMergeView: React.FC<DiffMergeViewProps> = memo(
  ({ originalContent, newContent, className }) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const editorRef = useRef<EditorView | null>(null);

    useEffect(() => {
      if (!containerRef.current) return;

      // Destroy previous editor instance
      if (editorRef.current) {
        editorRef.current.destroy();
        editorRef.current = null;
      }

      // Create unified merge view extension
      const mergeExtension = unifiedMergeView({
        original: originalContent,
        gutter: false,
        mergeControls: false,
        highlightChanges: true,
        syntaxHighlightDeletions: true,
        allowInlineDiffs: true,
        collapseUnchanged: {}
      });

      // Build extensions array
      const extensions: Extension[] = [
        python(),
        jupyterTheme,
        mergeExtension,
        EditorState.readOnly.of(true),
        EditorView.editable.of(false),
        diffViewTheme
      ];

      // Create editor state
      const state = EditorState.create({
        doc: newContent,
        extensions
      });

      // Create editor view
      editorRef.current = new EditorView({
        state,
        parent: containerRef.current
      });

      // Cleanup on unmount
      return () => {
        if (editorRef.current) {
          editorRef.current.destroy();
          editorRef.current = null;
        }
      };
    }, [originalContent, newContent]);

    // Build class name
    const containerClass = [
      'sage-ai-diff-merge-view',
      !originalContent && 'code-mirror-empty-original-content',
      className
    ]
      .filter(Boolean)
      .join(' ');

    return <div ref={containerRef} className={containerClass} />;
  }
);

DiffMergeView.displayName = 'DiffMergeView';

export default DiffMergeView;
