/**
 * Theme detection hook and utilities
 * Replaces MutationObserver pattern in NotebookDiffTools
 */

import { useEffect, useState } from 'react';
import { ColorSchemeType } from 'diff2html/lib/types';

/**
 * Detect the current JupyterLab theme
 * @returns ColorSchemeType.DARK or ColorSchemeType.LIGHT
 */
export function detectJupyterLabTheme(): ColorSchemeType {
  const isLightTheme = document.body.getAttribute('data-jp-theme-light');
  return isLightTheme === 'false'
    ? ColorSchemeType.DARK
    : ColorSchemeType.LIGHT;
}

/**
 * Check if the current JupyterLab theme is dark
 * @returns true if dark theme is detected
 */
export function isDarkTheme(): boolean {
  return detectJupyterLabTheme() === ColorSchemeType.DARK;
}

/**
 * React hook for detecting JupyterLab theme changes
 * Provides reactive theme state for React components
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { theme, isDark } = useThemeDetection();
 *   return <div className={isDark ? 'dark' : 'light'}>...</div>;
 * }
 * ```
 */
export function useThemeDetection() {
  const [theme, setTheme] = useState<ColorSchemeType>(() =>
    detectJupyterLabTheme()
  );
  const [isDark, setIsDark] = useState(
    () => detectJupyterLabTheme() === ColorSchemeType.DARK
  );

  useEffect(() => {
    const updateTheme = () => {
      const newTheme = detectJupyterLabTheme();
      setTheme(newTheme);
      setIsDark(newTheme === ColorSchemeType.DARK);
    };

    const observer = new MutationObserver(mutations => {
      let themeChanged = false;

      mutations.forEach(mutation => {
        if (mutation.type === 'attributes') {
          const attributeName = mutation.attributeName;
          if (
            attributeName === 'data-jp-theme-light' ||
            attributeName === 'data-jp-theme-name' ||
            attributeName === 'class'
          ) {
            themeChanged = true;
          }
        }
      });

      if (themeChanged) {
        updateTheme();
      }
    });

    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ['data-jp-theme-light', 'data-jp-theme-name', 'class']
    });

    return () => observer.disconnect();
  }, []);

  return { theme, isDark };
}

// ============================================================
// Service-style API for non-React contexts
// ============================================================

type ThemeChangeCallback = (theme: ColorSchemeType) => void;

let themeListeners: Set<ThemeChangeCallback> = new Set();
let currentTheme: ColorSchemeType = ColorSchemeType.LIGHT;
let observerInitialized = false;
let globalObserver: MutationObserver | null = null;

/**
 * Subscribe to theme changes (for non-React contexts like services)
 * @param callback Function to call when theme changes
 * @returns Unsubscribe function
 *
 * @example
 * ```ts
 * const unsubscribe = subscribeToTheme((theme) => {
 *   console.log('Theme changed:', theme);
 * });
 * // Later: unsubscribe();
 * ```
 */
export function subscribeToTheme(callback: ThemeChangeCallback): () => void {
  themeListeners.add(callback);

  if (!observerInitialized) {
    currentTheme = detectJupyterLabTheme();

    globalObserver = new MutationObserver(mutations => {
      let themeChanged = false;

      mutations.forEach(mutation => {
        if (mutation.type === 'attributes') {
          const attributeName = mutation.attributeName;
          if (
            attributeName === 'data-jp-theme-light' ||
            attributeName === 'data-jp-theme-name' ||
            attributeName === 'class'
          ) {
            themeChanged = true;
          }
        }
      });

      if (themeChanged) {
        const newTheme = detectJupyterLabTheme();
        if (newTheme !== currentTheme) {
          currentTheme = newTheme;
          themeListeners.forEach(cb => {
            try {
              cb(currentTheme);
            } catch (error) {
              console.error('Error in theme change callback:', error);
            }
          });
        }
      }
    });

    globalObserver.observe(document.body, {
      attributes: true,
      attributeFilter: ['data-jp-theme-light', 'data-jp-theme-name', 'class']
    });

    observerInitialized = true;
  }

  // Immediately call with current theme
  callback(currentTheme);

  return () => {
    themeListeners.delete(callback);

    // Cleanup observer if no more listeners
    if (themeListeners.size === 0 && globalObserver) {
      globalObserver.disconnect();
      globalObserver = null;
      observerInitialized = false;
    }
  };
}

/**
 * Get the current theme without subscribing
 * @returns Current ColorSchemeType
 */
export function getCurrentTheme(): ColorSchemeType {
  return detectJupyterLabTheme();
}

/**
 * Cleanup theme detection (call on extension deactivation)
 */
export function cleanupThemeDetection(): void {
  if (globalObserver) {
    globalObserver.disconnect();
    globalObserver = null;
  }
  themeListeners.clear();
  observerInitialized = false;
}
