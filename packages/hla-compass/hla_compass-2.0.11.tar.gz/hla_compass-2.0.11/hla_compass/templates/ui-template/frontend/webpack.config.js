const path = require('path');
const { getAliases } = require('./build/aliases');

/**
 * Webpack configuration for HLA-Compass module UI
 *
 * Supports two build modes:
 * 1. Platform mode (default): Uses externals for React/ReactDOM/antd
 *    - Small bundle size (~50KB)
 *    - Expects platform to provide globals
 *    - Used when module is loaded on platform
 *
 * 2. Standalone mode (BUILD_STANDALONE=true): Bundles everything
 *    - Larger bundle size (~800KB)
 *    - Self-contained, no external dependencies
 *    - Used for local development with `hla-compass serve`
 *
 * Usage:
 *   npm run build              # Platform bundle (with externals)
 *   npm run build:standalone   # Standalone bundle (no externals)
 */

module.exports = (env, argv) => {
  const isStandalone = process.env.BUILD_STANDALONE === 'true';
  const mode = argv.mode || 'production';

  return {
    mode,
    devtool: isStandalone ? 'source-map' : false,
    entry: './index.tsx',
    resolve: {
      extensions: ['.tsx', '.ts', '.js', '.jsx'],
      alias: {
        ...getAliases(__dirname),
      },
    },
    module: {
      rules: [
        {
          test: /\.tsx?$/,
          use: {
            loader: 'ts-loader',
            options: {
              transpileOnly: true,
            },
          },
          exclude: /node_modules/,
        },
        {
          test: /\.css$/,
          use: [
            'style-loader',
            'css-loader',
            'postcss-loader',
          ],
        },
      ],
    },
    output: {
      filename: isStandalone ? 'bundle.standalone.js' : 'bundle.js',
      path: path.resolve(__dirname, 'dist'),
      library: {
        name: 'ModuleUI',
        type: 'umd',
        export: 'default',
      },
      globalObject: "typeof self !== 'undefined' ? self : this",
      clean: false, // Don't clean so both bundles can coexist
    },
    // Platform mode: Use externals (platform provides React/ReactDOM/antd as globals)
    // Standalone mode: Bundle everything
    externals: isStandalone ? {} : {
      react: 'React',
      'react-dom': 'ReactDOM',
      antd: 'antd',
    },
    optimization: {
      splitChunks: isStandalone ? false : {
        chunks: 'all',
      },
      minimize: true,
    },
    devServer: {
      static: {
        directory: path.join(__dirname, 'dist'),
      },
      compress: true,
      port: 3000,
      hot: true,
      headers: {
        'Access-Control-Allow-Origin': '*',
      },
      proxy: {
        '/api': 'http://localhost:8080',
      },
      devMiddleware: {
        writeToDisk: true,
      },
    },
  };
};
