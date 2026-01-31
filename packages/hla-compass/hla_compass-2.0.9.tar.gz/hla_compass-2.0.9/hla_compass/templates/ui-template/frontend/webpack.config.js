const path = require('path');
const { getAliases } = require('./build/aliases');

module.exports = {
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
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'dist'),
    library: {
      name: 'ModuleUI',
      type: 'umd',
      export: 'default',
    },
    globalObject: "typeof self !== 'undefined' ? self : this",
    clean: true,
  },
nal  optimization: {
    splitChunks: {
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
