/**
 * StateDisplayContainer Component (Pure React)
 *
 * Container for LLM and Plan state displays, and Demo control panel.
 * Uses the existing pure React components that are powered by Zustand stores.
 */

import React from 'react';
import { LLMStateDisplayComponent } from './StateDisplay/LLMStateContent';
import { PlanStateDisplayComponent } from './StateDisplay/PlanStateDisplay';
import { DemoControlPanel } from './StateDisplay/DemoControlPanel';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface StateDisplayContainerProps {
  /** Optional class name for styling */
  className?: string;
}

// ═══════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════

export const StateDisplayContainer: React.FC<StateDisplayContainerProps> = ({
  className = ''
}) => {
  return (
    <div className={`sage-ai-state-display-container ${className}`}>
      {/* Demo control panel - renders when demo mode is active */}
      <DemoControlPanel />
      {/* LLM state display - hidden during demo */}
      <LLMStateDisplayComponent />
      <PlanStateDisplayComponent />
    </div>
  );
};

export default StateDisplayContainer;
