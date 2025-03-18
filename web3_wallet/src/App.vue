<template>
  <div>
    <!-- <h1>{{ string }}</h1> -->
    <!-- <van-button type="primary">主要按钮</van-button> -->
    <!-- <Web3Api /> -->
    <Account />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Web3 from 'web3'
// import { Buffer } from 'buffer'
import Web3Api from './components/Web3Api.vue'
import Account from './components/account.vue'

// 确保 Buffer 在全局范围内可用
// window.Buffer = Buffer

const string = ref('hello web3')

// web3实例化
const web3 = new Web3(Web3.givenProvider || "wss://sepolia.infura.io/ws/v3/86fa8d2d26f7440aa9ca5504cbc7e095")
console.log(web3)

// 创建账号
</script>

<style lang="less">
h1 {
  color: rgb(153, 66, 66);
}
</style>