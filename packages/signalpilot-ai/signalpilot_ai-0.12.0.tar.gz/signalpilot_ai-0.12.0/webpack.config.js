/**
 * Custom webpack configuration to suppress source-map warnings from node_modules
 */

const path = require('path');

module.exports = {
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'lib')
    }
  },
  // Ignore source-map warnings from third-party packages
  ignoreWarnings: [
    // Suppress source-map-loader warnings for packages without source maps
    {
      module: /node_modules\/@modelcontextprotocol\/sdk/,
      message: /Failed to parse source map/
    },
    {
      module: /node_modules\/diff2html/,
      message: /Failed to parse source map/
    },
    // Suppress invalid dependencies warnings from source-map-loader
    {
      module: /node_modules\/@modelcontextprotocol\/sdk/,
      message: /Invalid dependencies have been reported/
    },
    {
      module: /node_modules\/diff2html/,
      message: /Invalid dependencies have been reported/
    },
    // Suppress shared module version warnings
    {
      message: /No version specified and unable to automatically determine one/
    }
  ]
};
