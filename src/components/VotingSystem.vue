<!-- 投票系统组件 -->
<template>
  <div class="voting-system">
    <div class="back-btn">
      <button @click="$emit('back')">返回主页</button>
    </div>
    <div class="wallet-section">
      <div v-if="!isConnected">
        <button @click="initWeb3" :disabled="isRequesting">
          {{ isRequesting ? '连接中...' : '连接钱包' }}
        </button>
      </div>
      <div v-else class="wallet-info">
        <p>已连接钱包</p>
        <p>地址: {{ account }}</p>
        <button @click="switchAccount" class="switch-btn">切换账号</button>
      </div>
    </div>

    <div v-if="isConnected" class="vote-section">
      <div class="create-vote">
        <h2>创建新投票</h2>
        <div class="input-group">
          <input 
            type="text" 
            v-model="voteName" 
            placeholder="请输入投票名称"
            class="vote-input"
          >
          <button @click="createVote" class="create-btn">创建</button>
        </div>
      </div>

      <div class="vote-list">
        <h2>投票列表</h2>
        <div v-for="vote in votes" :key="vote.index" class="vote-item">
          <div class="vote-info">
            <h3>{{ vote.name }}</h3>
            <p>赞成票: {{ vote.yesCount }}</p>
            <p>反对票: {{ vote.noCount }}</p>
            <p v-if="vote.hasVoted" class="vote-status">
              您已投票: {{ vote.userVote ? '赞成' : '反对' }}
            </p>
          </div>
          <div class="vote-actions">
            <button 
              @click="submitVote(vote.index, true)" 
              class="vote-btn yes"
              :disabled="vote.hasVoted"
            >赞成</button>
            <button 
              @click="submitVote(vote.index, false)" 
              class="vote-btn no"
              :disabled="vote.hasVoted"
            >反对</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import Web3 from 'web3';
import votingJSON from '../contract/VotingSystem.json';

const web3 = ref(null);
const account = ref('');
const isConnected = ref(false);
const contract = ref(null);
const isRequesting = ref(false);

// 投票相关状态
const voteName = ref('');
const votes = ref([]);
const voteCount = ref(0);

// 初始化Web3
const initWeb3 = async () => {
  try {
    if (isRequesting.value) {
      console.log('已有请求正在处理中，请等待...');
      return;
    }

    if (typeof window.ethereum !== 'undefined') {
      isRequesting.value = true;
      
      console.log('开始初始化Web3...');
      web3.value = new Web3(window.ethereum);
      
      // 检查是否已经授权
      console.log('检查账户授权状态...');
      const accounts = await web3.value.eth.getAccounts();
      console.log('当前账户:', accounts);
      
      if (accounts.length > 0) {
        account.value = accounts[0];
        isConnected.value = true;
        console.log('已授权账户:', account.value);
      } else {
        console.log('尝试请求账户授权...');
        try {
          const newAccounts = await window.ethereum.request({ 
            method: 'eth_requestAccounts'
          });
          account.value = newAccounts[0];
          isConnected.value = true;
          console.log('账户授权成功:', account.value);
        } catch (error) {
          console.error('账户授权失败:', error);
          throw error;
        }
      }

      // 检查网络ID
      console.log('检查网络ID...');
      const networkId = await web3.value.eth.net.getId();
      console.log('当前网络ID:', networkId);
      
      // 初始化投票合约
      console.log('初始化合约...');
      const contractAddress = "0x487440ce9d1A2d38F9f3D0FD33846bb3cD830AA4";
      console.log('合约地址:', contractAddress);
      
      // 验证合约地址格式
      if (!web3.value.utils.isAddress(contractAddress)) {
        throw new Error('无效的合约地址');
      }
      
      contract.value = new web3.value.eth.Contract(
        votingJSON.abi,
        contractAddress
      );

      // 验证合约是否已部署
      console.log('验证合约部署状态...');
      try {
        const code = await web3.value.eth.getCode(contractAddress);
        console.log('合约代码:', code);
        
        if (code === '0x' || code === '') {
          throw new Error('合约未部署到当前网络');
        }
      } catch (error) {
        console.error('合约验证失败:', error);
        throw new Error('合约验证失败，请检查网络连接和合约地址');
      }
      
      console.log('Web3初始化成功');
      await loadVotes();
    } else {
      throw new Error('请安装MetaMask!');
    }
  } catch (error) {
    console.error('Web3初始化失败:', error);
    console.error('错误详情:', {
      message: error.message,
      stack: error.stack,
      code: error.code,
      data: error.data
    });
    
    let errorMessage = '连接失败: ';
    if (error.message.includes('wallet_requestPermissions')) {
      errorMessage += '用户拒绝了钱包连接请求';
    } else if (error.message.includes('nonce too low')) {
      errorMessage += '交易nonce错误，请刷新页面重试';
    } else if (error.message.includes('network')) {
      errorMessage += '网络连接错误，请检查网络设置';
    } else if (error.message.includes('合约')) {
      errorMessage += error.message;
    } else {
      errorMessage += error.message;
    }
    
    alert(errorMessage);
    if (error.message.includes('wallet_requestPermissions')) {
      isRequesting.value = false;
    }
  } finally {
    isRequesting.value = false;
  }
};

// 切换账号
const switchAccount = async () => {
  try {
    await window.ethereum.request({
      method: 'wallet_requestPermissions',
      params: [{ eth_accounts: {} }]
    });
    // 重新加载投票列表
    await loadVotes();
  } catch (error) {
    console.error('切换账号失败:', error);
    alert('切换账号失败');
  }
};

// 加载所有投票
const loadVotes = async () => {
  try {
    const count = await contract.value.methods.getVoteCount().call();
    voteCount.value = count;
    
    votes.value = [];
    for (let i = 0; i < count; i++) {
      const result = await contract.value.methods.getVoteResult(i).call();
      // 检查用户是否已投票
      const hasVoted = await contract.value.methods.hasVoted(i, account.value).call();
      
      // 如果已投票，获取投票选择
      let userVote = null;
      if (hasVoted) {
        try {
          userVote = await contract.value.methods.userVotes(i, account.value).call();
        } catch (error) {
          console.error('获取用户投票选择失败:', error);
        }
      }
      
      votes.value.push({
        index: i,
        name: result.name,
        yesCount: result.yesCount,
        noCount: result.noCount,
        hasVoted: hasVoted,
        userVote: userVote
      });
    }
  } catch (error) {
    console.error('加载投票失败:', error);
  }
};

// 创建新投票
const createVote = async () => {
  try {
    if (!voteName.value) {
      alert('请输入投票名称');
      return;
    }

    if (!contract.value) {
      throw new Error('合约未初始化');
    }
    
    // 检查是否已授权
    const accounts = await web3.value.eth.getAccounts();
    if (accounts.length === 0) {
      const newAccounts = await window.ethereum.request({ 
        method: 'eth_requestAccounts',
        params: [{ eth_accounts: {} }]
      });
      account.value = newAccounts[0];
    }

    // 检查网络ID
    const networkId = await web3.value.eth.net.getId();
    console.log('当前网络ID:', networkId);
    
    // 创建投票交易
    const transaction = await contract.value.methods.createVote(voteName.value)
      .send({ 
        from: account.value,
        gas: 200000 // 设置gas限制
      });
    
    console.log('投票创建成功，交易哈希:', transaction.transactionHash);
    voteName.value = '';
    await loadVotes();
  } catch (error) {
    console.error('创建投票失败:', error);
    let errorMessage = '创建投票失败';
    
    if (error.message.includes('insufficient funds')) {
      errorMessage = '账户余额不足';
    } else if (error.message.includes('nonce too low')) {
      errorMessage = '交易nonce错误，请刷新页面重试';
    } else if (error.message.includes('user rejected')) {
      errorMessage = '用户拒绝了交易';
    } else if (error.message.includes('network')) {
      errorMessage = '网络连接错误，请检查网络设置';
    }
    
    alert(errorMessage);
  }
};

// 进行投票
const submitVote = async (voteIndex, choice) => {
  try {
    // 先检查是否已投票
    const hasVoted = await contract.value.methods.hasVoted(voteIndex, account.value).call();
    if (hasVoted) {
      alert('您已经投过票了');
      return;
    }

    // 检查是否已授权
    const accounts = await web3.value.eth.getAccounts();
    if (accounts.length === 0) {
      const newAccounts = await window.ethereum.request({ 
        method: 'eth_requestAccounts',
        params: [{ eth_accounts: {} }]
      });
      account.value = newAccounts[0];
    }
    
    // 显示确认对话框
    const confirmMessage = `确定要投${choice ? '赞成' : '反对'}票吗？`;
    if (!confirm(confirmMessage)) {
      return;
    }
    
    await contract.value.methods.vote(voteIndex, choice)
      .send({ from: account.value });
    
    console.log('投票成功');
    await loadVotes();
  } catch (error) {
    console.error('投票失败:', error);
    alert('投票失败，请检查网络连接');
  }
};

// 监听账户变化
const handleAccountsChanged = async (accounts) => {
  account.value = accounts[0];
  isConnected.value = accounts.length > 0;
  if (isConnected.value) {
    await loadVotes();
  }
};

// 监听链变化
const handleChainChanged = (chainId) => {
  window.location.reload();
};

onMounted(() => {
  if (window.ethereum) {
    console.log('设置事件监听器...');
    window.ethereum.on('accountsChanged', handleAccountsChanged);
    window.ethereum.on('chainChanged', handleChainChanged);
  } else {
    console.error('未检测到MetaMask');
  }
});

onUnmounted(() => {
  if (window.ethereum) {
    window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
    window.ethereum.removeListener('chainChanged', handleChainChanged);
  }
});
</script>

<style lang="less" scoped>
.voting-system {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.wallet-section {
  margin: 20px 0;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.vote-section {
  margin-top: 20px;
}

.create-vote {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  
  h2 {
    font-size: 14px;
    margin-bottom: 15px;
    color: #333;
  }
}

.input-group {
  display: flex;
  gap: 10px;
  
  .vote-input {
    flex: 1;
    padding: 6px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 12px;
    
    &:focus {
      outline: none;
      border-color: #4CAF50;
    }
  }
}

.vote-list {
  h2 {
    font-size: 14px;
    margin-bottom: 15px;
    color: #333;
  }
}

.vote-item {
  padding: 15px;
  margin-bottom: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  
  .vote-info {
    margin-bottom: 10px;
    
    h3 {
      font-size: 13px;
      margin-bottom: 8px;
      color: #333;
    }
    
    p {
      font-size: 12px;
      color: #666;
      margin: 3px 0;
    }
  }
}

.vote-actions {
  display: flex;
  gap: 10px;
}

button {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  
  &:hover:not(:disabled) {
    opacity: 0.9;
  }

  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
}

.create-btn {
  background-color: #4CAF50;
  color: white;
}

.vote-btn {
  &.yes {
    background-color: #4CAF50;
    color: white;
  }
  
  &.no {
    background-color: #f44336;
    color: white;
  }

  &:disabled {
    background-color: #cccccc;
  }
}

.wallet-info {
  p {
    margin: 5px 0;
    font-size: 12px;
  }
}

.switch-btn {
  background-color: #2196F3;
  color: white;
  margin-top: 10px;
}

.vote-status {
  color: #2196F3;
  font-weight: bold;
  margin-top: 5px;
}

.back-btn {
  margin-bottom: 20px;
  
  button {
    background-color: #666;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    
    &:hover {
      background-color: #555;
    }
  }
}
</style> 