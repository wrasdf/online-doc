'use client';

import React, { useEffect, useRef, useState } from 'react';
import { EditorView, basicSetup } from 'codemirror';
import { EditorState } from '@codemirror/state';
import { keymap } from '@codemirror/view';
import { defaultKeymap, historyKeymap, history } from '@codemirror/commands';

interface CodeMirrorEditorProps {
  value: string;
  onChange?: (value: string) => void;
  onSave?: () => void;
  readOnly?: boolean;
  placeholder?: string;
  className?: string;
}

export default function CodeMirrorEditor({
  value,
  onChange,
  onSave,
  readOnly = false,
  placeholder = 'Start typing...',
  className = ''
}: CodeMirrorEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize CodeMirror editor
  useEffect(() => {
    if (!editorRef.current || isInitialized) return;

    // Create custom keymap for saving
    const customKeymap = keymap.of([
      ...defaultKeymap,
      ...historyKeymap,
      {
        key: 'Ctrl-s',
        mac: 'Cmd-s',
        run: () => {
          if (onSave) {
            onSave();
          }
          return true;
        }
      }
    ]);

    // Create editor state
    const startState = EditorState.create({
      doc: value,
      extensions: [
        basicSetup,
        history(),
        customKeymap,
        EditorView.editable.of(!readOnly),
        EditorView.updateListener.of((update) => {
          if (update.docChanged && onChange && !readOnly) {
            const newValue = update.state.doc.toString();
            onChange(newValue);
          }
        }),
        EditorView.theme({
          '&': {
            height: '100%',
            fontSize: '14px'
          },
          '.cm-scroller': {
            overflow: 'auto',
            fontFamily: 'monospace'
          },
          '.cm-content': {
            minHeight: '400px',
            padding: '10px 0'
          },
          '.cm-line': {
            padding: '0 10px'
          }
        }),
        EditorView.lineWrapping,
        // Placeholder extension
        EditorView.domEventHandlers({
          focus: (event, view) => {
            if (view.state.doc.length === 0) {
              // Handle empty state
            }
          }
        })
      ]
    });

    // Create editor view
    const view = new EditorView({
      state: startState,
      parent: editorRef.current
    });

    viewRef.current = view;
    setIsInitialized(true);

    // Cleanup on unmount
    return () => {
      view.destroy();
      viewRef.current = null;
      setIsInitialized(false);
    };
  }, []); // Only run once on mount

  // Update editor content when value prop changes externally
  useEffect(() => {
    if (!viewRef.current || !isInitialized) return;

    const currentValue = viewRef.current.state.doc.toString();
    if (value !== currentValue) {
      viewRef.current.dispatch({
        changes: {
          from: 0,
          to: currentValue.length,
          insert: value
        }
      });
    }
  }, [value, isInitialized]);

  // Update read-only state
  useEffect(() => {
    if (!viewRef.current || !isInitialized) return;

    viewRef.current.dispatch({
      effects: EditorView.editable.reconfigure(EditorView.editable.of(!readOnly))
    });
  }, [readOnly, isInitialized]);

  return (
    <div className={`codemirror-editor-wrapper ${className}`}>
      <div ref={editorRef} className="codemirror-editor" />
      {!readOnly && onSave && (
        <div className="editor-hint text-muted small mt-2">
          Press <kbd>Ctrl+S</kbd> (or <kbd>Cmd+S</kbd> on Mac) to save
        </div>
      )}
      <style jsx>{`
        .codemirror-editor-wrapper {
          border: 1px solid #dee2e6;
          border-radius: 0.375rem;
          overflow: hidden;
          background: white;
        }
        .codemirror-editor {
          height: 100%;
          min-height: 400px;
        }
        .editor-hint {
          padding: 0.5rem 0.75rem;
          background: #f8f9fa;
          border-top: 1px solid #dee2e6;
        }
        kbd {
          padding: 0.2rem 0.4rem;
          font-size: 87.5%;
          color: #fff;
          background-color: #212529;
          border-radius: 0.2rem;
        }
      `}</style>
    </div>
  );
}
