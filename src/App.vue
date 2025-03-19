<script setup>
import { ref, onMounted } from 'vue';
import Web3 from 'web3';
import mtcJSON from './contract/Inni.json';

const web3 = ref(null);
const account = ref('');
const isConnected = ref(false);
const contract = ref(null);
const isRequesting = ref(false);

const name = ref('');
const symbol = ref('');
const totalSupply = ref('');
const balanceOf = ref('');

const getCoinInfo = async () => {
  try {
    if (!contract.value) {
      console.error('合约未初始化');
      return;
    }
    
    name.value = await contract.value.methods.name().call();
    symbol.value = await contract.value.methods.symbol().call();
    
    // 获取总供应量并转换为Ether
    const totalSupplyWei = await contract.value.methods.totalSupply().call();
    totalSupply.value = web3.value.utils.fromWei(totalSupplyWei, 'ether');
    
    // 获取余额并转换为Ether
    const balanceWei = await contract.value.methods.balanceOf(account.value).call();
    balanceOf.value = web3.value.utils.fromWei(balanceWei, 'ether');
    
    console.log('代币信息获取成功');
  } catch (error) {
    console.error('获取代币信息失败:', error);
  }
};

const initWeb3 = async () => {
  try {
    if (isRequesting.value) {
      console.log('已有请求正在处理中，请等待...');
      return;
    }

    if (typeof window.ethereum !== 'undefined') {
      isRequesting.value = true;
      
      // 创建Web3实例
      web3.value = new Web3(window.ethereum);
      
      // 检查是否已经授权
      const accounts = await web3.value.eth.getAccounts();
      
      if (accounts.length > 0) {
        account.value = accounts[0];
        isConnected.value = true;
      } else {
        const newAccounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        account.value = newAccounts[0];
        isConnected.value = true;
      }
      
      // 初始化合约
      contract.value = new web3.value.eth.Contract(
        mtcJSON.abi,
        "0xa47e19D6992B6c78cb1b0e485ED28161e221aD6A"
      );
      
      console.log('Web3初始化成功');
      
      // 合约初始化成功后获取代币信息
      await getCoinInfo();
    } else {
      console.error('请安装MetaMask!');
    }
  } catch (error) {
    console.error('Web3初始化失败:', error);
    if (error.message.includes('wallet_requestPermissions')) {
      isRequesting.value = false;
    }
  } finally {
    isRequesting.value = false;
  }
};

// 监听账户变化
const handleAccountsChanged = async (accounts) => {
  account.value = accounts[0];
  isConnected.value = accounts.length > 0;
  if (isConnected.value) {
    await getCoinInfo();
  }
};

// 监听链变化
const handleChainChanged = (chainId) => {
  window.location.reload();
};
const toAddress=ref('');
const amount=ref('');
const transfer=()=>{
  const weiAmount=web3.value.utils.toWei(amount.value,'ether');
  contract.value.methods.transfer(toAddress.value,weiAmount).send({from:account.value}).on('receipt',(receipt)=>{
    console.log('转账成功',receipt);
  }).on('error',(error)=>{
    console.error('转账失败',error);
  });
  }
onMounted(() => {
  // 延迟初始化，等待页面完全加载
  setTimeout(() => {
    initWeb3();
  }, 1000);
  
  // 添加事件监听器
  if (window.ethereum) {
    window.ethereum.on('accountsChanged', handleAccountsChanged);
    window.ethereum.on('chainChanged', handleChainChanged);
  }
});
</script>

<template>
  <div class="web3-container">
    <h1>Web3 演示</h1>
    
    <div class="wallet-section">
      <div v-if="!isConnected">
        <button @click="initWeb3" :disabled="isRequesting">
          {{ isRequesting ? '连接中...' : '连接钱包' }}
        </button>
      </div>
      <div v-else class="wallet-info">
        <p>已连接钱包</p>
        <p>地址: {{ account }}</p>
      </div>
      
      <div v-if="isConnected" class="token-info">
        <h2>代币信息</h2>
        <p>币种名称: {{ name }}</p>
        <p>币种符号: {{ symbol }}</p>
        <p>总供应量: {{ totalSupply }} {{ symbol }}</p>
        <p>余额: {{ balanceOf }} {{ symbol }}</p>
      </div>
      <h1>转账</h1>
      <div>
        <p><input type="text" v-model="toAddress" placeholder="请输入转账地址"></p>
        <p><input type="text" v-model="amount" placeholder="请输入转账数量"></p>
        <p><button @click="transfer">转账</button></p>
      </div>
    </div>
  </div>
</template>

<style lang="less">
.web3-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
  font-size: 12px;
}

.wallet-section {
  margin: 20px 0;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

button {
  background-color: #4CAF50;
  color: white;
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  
  &:hover:not(:disabled) {
    background-color: #45a049;
  }

  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
}

.wallet-info {
  margin-top: 20px;
  
  p {
    margin: 5px 0;
    font-size: 12px;
  }
}

.token-info {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
  
  h2 {
    color: #666;
    margin-bottom: 15px;
    font-size: 14px;
  }
  
  p {
    margin: 5px 0;
    color: #333;
    font-size: 12px;
  }
}

h1 {
  color: #333;
  text-align: center;
  font-size: 16px;
  margin-bottom: 20px;
}

input {
  width: 100%;
  padding: 6px;
  margin: 5px 0;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  
  &:focus {
    outline: none;
    border-color: #4CAF50;
  }
}
</style>