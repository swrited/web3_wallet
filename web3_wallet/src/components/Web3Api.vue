<template>
  <div class="web3-api">
    <h1>Web3 API</h1>
    <h1>账户信息</h1>
    <van-divider />
    <p>地址: {{ address }}</p>
    <p>私钥: {{ privateKey }}</p>
    <p>余额：{{ balance !== null ? balance : '加载中...' }}</p>
    <h1>转账操作</h1>
    <van-divider />
    <van-button type="primary" @click="sent">开始转账</van-button>
    <p>交易状态: {{ transactionStatus !== null ? transactionStatus : '未开始' }}</p>
  </div>
</template>

<script>
import { defineComponent, ref } from 'vue';
import Web3 from 'web3';
import { Buffer } from 'buffer';
import { FeeMarketEIP1559Transaction } from '@ethereumjs/tx';

export default defineComponent({
  name: 'Web3Api',
  setup() {
    const address = ref('0xA52612a2aF760ed36A9db21075cf0eEafd69Cdc1');
    const privateKey = ref('0xd0841fe17d5f496892f9b7c6d5098214428fdcc0065e8c18c6775f307dfe9200');
    const balance = ref(null);
    const transactionStatus = ref(null);

    const web3 = new Web3("wss://sepolia.infura.io/ws/v3/86fa8d2d26f7440aa9ca5504cbc7e095");

    // 获取余额
    web3.eth.getBalance(address.value).then(res => {
      balance.value = web3.utils.fromWei(res, 'ether');
    }).catch(err => {
      console.error(err);
      balance.value = '获取失败';
    });

    // 发送交易
    const sent = async () => {
      transactionStatus.value = '加载中...';
      try {
        // 检查账户余额
        const accountBalance = await web3.eth.getBalance(address.value);
        const value = web3.utils.toWei('0.01', 'ether'); // 转账 0.01 ETH
        if (BigInt(accountBalance) < BigInt(value)) {
          throw new Error('账户余额不足');
        }

        // 获取 Nonce
        const nonce = await web3.eth.getTransactionCount(address.value);

        // 获取 Gas 费用
        const gasPrice = await web3.eth.getGasPrice();

        // 设置固定 Gas Limit
        const gasLimit = 21000; // 固定 Gas Limit 为 21000

        // 检查余额是否足够支付 Gas 费用和转账金额
        const totalCost = BigInt(value) + BigInt(gasPrice) * BigInt(gasLimit);
        if (BigInt(accountBalance) < totalCost) {
          throw new Error(`账户余额不足以支付 Gas 费用和转账金额。需要 ${web3.utils.fromWei(totalCost.toString(), 'ether')} ETH，当前余额 ${web3.utils.fromWei(accountBalance.toString(), 'ether')} ETH`);
        }

        // 构建交易
        const txParams = {
          nonce: web3.utils.toHex(nonce),
          to: '0xC78cEFA7aC8640fCD0b4108604C758D0dC407068',
          value: web3.utils.toHex(value),
          gasPrice: web3.utils.toHex(gasPrice),
          gasLimit: web3.utils.toHex(gasLimit),
          chainId: web3.utils.toHex(11155111), // Sepolia 测试网
        };

        // 签名交易
        const tx = FeeMarketEIP1559Transaction.fromTxData(txParams);
        const privKey = Buffer.from(privateKey.value.slice(2), 'hex');
        const signedTx = tx.sign(privKey);
        const serializedTx = signedTx.serialize();
        const raw = '0x' + Buffer.from(serializedTx).toString('hex');

        // 发送交易
        const receipt = await web3.eth.sendSignedTransaction(raw);
        console.log('交易成功:', receipt);
        transactionStatus.value = '交易成功';
      } catch (err) {
        console.error('发送交易错误:', err);
        transactionStatus.value = '交易失败';
      }
    };

    return {
      address,
      privateKey,
      balance,
      transactionStatus,
      sent,
    };
  }
});
</script>

<style scoped>
body {
  background-color: #f0f0f0;
  padding: 20px;
}
.web3-api {
  /* 你的样式 */
}
</style>