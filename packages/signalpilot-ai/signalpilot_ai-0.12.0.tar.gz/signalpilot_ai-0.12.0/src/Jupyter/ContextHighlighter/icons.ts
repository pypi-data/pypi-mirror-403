/**
 * SVG icons for Jupyter cell UI elements
 */

export const UNDO_ICON = `
  <svg width="20px" height="20px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" stroke="var(--jp-ui-font-color3)">
    <path d="M3 7v6h6" stroke="var(--jp-ui-font-color3)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13" stroke="var(--jp-ui-font-color3)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>
`;

export const SUBMIT_ICON = `
  <svg width="20px" height="20px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" stroke="var(--jp-ui-font-color3)">
    <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
    <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g>
    <g id="SVGRepo_iconCarrier">
      <g clip-path="url(#clip0_429_11126)">
        <path d="M9 4.00018H19V18.0002C19 19.1048 18.1046 20.0002 17 20.0002H9" stroke="var(--jp-ui-font-color3)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"></path>
        <path d="M12 15.0002L15 12.0002M15 12.0002L12 9.00018M15 12.0002H5" stroke="var(--jp-ui-font-color3)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"></path>
      </g>
      <defs>
        <clipPath id="clip0_429_11126">
          <rect width="24" height="24" fill="white"></rect>
        </clipPath>
      </defs>
    </g>
  </svg>
`;

export const CANCEL_ICON = `
  <svg xmlns="http://www.w3.org/2000/svg" height="20px" width="20px" viewBox="0 0 24 24">
    <path fill="var(--jp-ui-font-color3)" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
  </svg>
`;

export const ADD_ICON = `
  <svg xmlns="http://www.w3.org/2000/svg" height="12" width="12" viewBox="0 0 24 24">
    <path fill="#1976d2" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6z"/>
  </svg>
`;

/**
 * Get keyboard shortcut label based on platform
 */
export function getKeyboardShortcutLabel(): { modifier: string; key: string } {
  const isMac = /Mac|iPod|iPhone|iPad/.test(navigator.platform);
  const cmdIcon = '\u2318'; // ⌘
  const ctrlIcon = '\u2303'; // ⌃

  return {
    modifier: isMac ? cmdIcon : ctrlIcon,
    key: 'K'
  };
}
