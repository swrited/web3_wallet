// filepath: /e:/sai/web3/wallet/web3_wallet/vue.config.js
const { defineConfig } = require('@vue/cli-service')
const { VantResolver } = require('unplugin-vue-components/resolvers');
const ComponentsPlugin = require('unplugin-vue-components/webpack').default;
const NodePolyfillWebpackPlugin = require("node-polyfill-webpack-plugin");

module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack: {
    plugins: [
      new NodePolyfillWebpackPlugin(),
      ComponentsPlugin({ resolvers: [VantResolver()]}),
    ],
    resolve: {
      fallback: {
        "assert": require.resolve("assert/"),
        "stream": require.resolve("stream-browserify"),
        // "buffer": require.resolve("buffer/")
      }
    }
  }
});