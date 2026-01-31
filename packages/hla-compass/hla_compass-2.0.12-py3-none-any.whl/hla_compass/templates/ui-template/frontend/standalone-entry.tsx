/**
 * Standalone entry point for `hla-compass serve`.
 *
 * In platform mode the host app loads bundle.js, grabs window.ModuleUI,
 * and renders it with props.  In standalone mode there is no host --
 * this file bootstraps the React tree so the component renders.
 */
import React from 'react';
import { createRoot } from 'react-dom/client';
import ModuleUI from './index';

const container = document.getElementById('root');
if (container) {
  createRoot(container).render(<ModuleUI />);
}
