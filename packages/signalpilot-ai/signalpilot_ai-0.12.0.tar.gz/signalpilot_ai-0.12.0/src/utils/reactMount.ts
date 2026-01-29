/**
 * React Mount Utilities
 *
 * Provides utilities for mounting React components into DOM containers.
 * This is useful for incrementally migrating from imperative DOM code to React
 * while keeping the existing component structure.
 */
import React from 'react';
// @ts-ignore - React 18's createRoot types may not be available in all environments
import ReactDOM from 'react-dom/client';

// Type definition for React 18's Root
interface Root {
  render(children: React.ReactNode): void;

  unmount(): void;
}

// Create root function wrapper for React 18
const createRoot = (container: HTMLElement): Root => {
  return (
    ReactDOM as { createRoot: (container: HTMLElement) => Root }
  ).createRoot(container);
};

/**
 * Interface for managing a mounted React component
 */
export interface IMountedComponent {
  /** Update the component with new props */
  update: (element: React.ReactElement) => void;
  /** Unmount the component and clean up */
  unmount: () => void;
  /** The container element */
  container: HTMLElement;
  /** The React root */
  root: Root;
}

/**
 * Mount a React component into a DOM container
 *
 * @param container - The DOM element to render into
 * @param element - The React element to render
 * @returns A handle for updating or unmounting the component
 *
 * @example
 * ```ts
 * const container = document.createElement('div');
 * const mounted = mountComponent(
 *   container,
 *   <SendButton hasContent={true} onSend={handleSend} onCancel={handleCancel} />
 * );
 *
 * // Later, update the component
 * mounted.update(<SendButton hasContent={false} onSend={handleSend} onCancel={handleCancel} />);
 *
 * // Clean up when done
 * mounted.unmount();
 * ```
 */
export function mountComponent(
  container: HTMLElement,
  element: React.ReactElement
): IMountedComponent {
  const root = createRoot(container);
  root.render(element);

  return {
    update: (newElement: React.ReactElement) => {
      root.render(newElement);
    },
    unmount: () => {
      root.unmount();
    },
    container,
    root
  };
}

/**
 * Create a container element with optional class names
 *
 * @param className - Space-separated class names
 * @param tagName - The HTML tag to create (default: 'div')
 * @returns The created element
 */
export function createContainer(
  className?: string,
  tagName: keyof HTMLElementTagNameMap = 'div'
): HTMLElement {
  const container = document.createElement(tagName);
  if (className) {
    container.className = className;
  }
  return container;
}
