<template>
    <div class="transfer-container">
        <h1>转账</h1>
        
        <div class="transfer-form">
            <div class="form-group">
                <label>接收地址：</label>
                <input 
                    type="text" 
                    v-model="toAddress" 
                    placeholder="请输入接收方钱包地址"
                    :class="{ 'error': addressError }"
                >
                <span class="error-message" v-if="addressError">{{ addressError }}</span>
            </div>

            <div class="form-group">
                <label>转账金额（ETH）：</label>
                <input 
                    type="number" 
                    v-model="amount" 
                    placeholder="请输入转账金额"
                    step="0.000000000000000001"
                    :class="{ 'error': amountError }"
                >
                <span class="error-message" v-if="amountError">{{ amountError }}</span>
            </div>

            <div class="balance-info">
                <p>当前余额：{{ balance }} ETH</p>
            </div>

            <button 
                @click="sendTransaction" 
                :disabled="!isValid || isSending"
                class="send-btn"
            >
                {{ isSending ? '发送中...' : '发送' }}
            </button>
        </div>

        <!-- 转账进度显示 -->
        <div class="transfer-progress" v-if="isSending">
            <div class="progress-bar">
                <div class="progress-fill" :style="{ width: progress + '%' }"></div>
            </div>
            <div class="progress-status">
                <span class="loading-spinner"></span>
                <span>{{ progressStatus }}</span>
            </div>
        </div>

        <!-- 交易状态显示 -->
        <div class="transaction-status" v-if="txHash">
            <h3>交易状态：</h3>
            <p>交易哈希：{{ txHash }}</p>
            <p>状态：{{ txStatus }}</p>
        </div>
    </div>
</template>

<script>
import { ref, computed, defineComponent, defineEmits } from 'vue';
import { ethers } from 'ethers';

export default defineComponent({
    name: 'Transfer',
    props: {
        wallet: {
            type: Object,
            required: true
        }
    },
    emits: ['transaction-complete'],
    setup(props, { emit }) {
        const toAddress = ref('')
        const amount = ref('')
        const balance = ref('0')
        const isSending = ref(false)
        const txHash = ref('')
        const txStatus = ref('')
        const addressError = ref('')
        const amountError = ref('')
        const isTransferring = ref(false)
        const progress = ref(0)
        const progressStatus = ref('准备交易...')

        // 验证地址格式
        const isValidAddress = (address) => {
            return /^0x[a-fA-F0-9]{40}$/.test(address)
        }

        // 验证金额
        const isValidAmount = computed(() => {
            const numAmount = parseFloat(amount.value)
            return !isNaN(numAmount) && numAmount > 0 && numAmount <= parseFloat(balance.value)
        })

        // 表单验证
        const isValid = computed(() => {
            return isValidAddress(toAddress.value) && isValidAmount.value
        })

        // 获取余额
        const getBalance = async () => {
            try {
                const provider = new ethers.providers.JsonRpcProvider('https://sepolia.infura.io/v3/86fa8d2d26f7440aa9ca5504cbc7e095')
                const balanceWei = await provider.getBalance(props.wallet.address)
                balance.value = ethers.utils.formatEther(balanceWei)
            } catch (error) {
                console.error('获取余额失败:', error)
            }
        }

        // 发送交易
        const sendTransaction = async () => {
            if (!toAddress.value || !amount.value) {
                alert('请填写完整信息')
                return
            }

            try {
                isSending.value = true
                isTransferring.value = true
                progress.value = 0
                progressStatus.value = '准备交易...'

                const provider = new ethers.providers.JsonRpcProvider('https://sepolia.infura.io/v3/86fa8d2d26f7440aa9ca5504cbc7e095')
                const walletWithProvider = props.wallet.connect(provider)
                
                progress.value = 20
                progressStatus.value = '发送交易...'

                // 获取 gas 价格
                const gasPrice = await provider.getGasPrice()
                // 估算 gas 限制
                const gasLimit = ethers.utils.hexlify(21000)
                // 计算 gas 费用
                const gasCost = gasPrice.mul(gasLimit)
                // 计算转账金额
                const transferAmount = ethers.utils.parseEther(amount.value.toString())
                // 计算总费用
                const totalCost = gasCost.add(transferAmount)
                // 获取账户余额
                const balanceWei = await provider.getBalance(props.wallet.address)

                // 检查余额是否足够支付总费用
                if (balanceWei.lt(totalCost)) {
                    throw new Error(`余额不足，需要 ${ethers.utils.formatEther(totalCost)} ETH (包含 gas 费用)，当前余额 ${ethers.utils.formatEther(balanceWei)} ETH`)
                }

                const tx = await walletWithProvider.sendTransaction({
                    to: toAddress.value,
                    value: transferAmount,
                    gasLimit: gasLimit,
                    gasPrice: gasPrice
                })

                progress.value = 40
                progressStatus.value = '等待确认...'

                await tx.wait()
                
                progress.value = 100
                progressStatus.value = '交易成功！'

                // 添加交易记录
                emit('transaction-complete', {
                    hash: tx.hash,
                    type: 'out',
                    address: toAddress.value,
                    amount: amount.value
                })

                // 清空表单
                toAddress.value = ''
                amount.value = ''

                // 3秒后重置状态
                setTimeout(() => {
                    isSending.value = false
                    isTransferring.value = false
                    progress.value = 0
                    progressStatus.value = ''
                }, 3000)
            } catch (error) {
                console.error('转账失败:', error)
                alert('转账失败: ' + error.message)
                isSending.value = false
                isTransferring.value = false
                progress.value = 0
                progressStatus.value = ''
            }
        }

        // 监听地址输入
        const validateAddress = () => {
            if (!toAddress.value) {
                addressError.value = '请输入接收地址'
            } else if (!isValidAddress(toAddress.value)) {
                addressError.value = '无效的以太坊地址'
            } else {
                addressError.value = ''
            }
        }

        // 监听金额输入
        const validateAmount = () => {
            const numAmount = parseFloat(amount.value)
            if (!amount.value) {
                amountError.value = '请输入转账金额'
            } else if (isNaN(numAmount) || numAmount <= 0) {
                amountError.value = '请输入有效的金额'
            } else if (numAmount > parseFloat(balance.value)) {
                amountError.value = '余额不足'
            } else {
                amountError.value = ''
            }
        }

        // 初始化
        getBalance()

        return {
            toAddress,
            amount,
            balance,
            isSending,
            txHash,
            txStatus,
            addressError,
            amountError,
            isValid,
            sendTransaction,
            validateAddress,
            validateAmount,
            isTransferring,
            progress,
            progressStatus,
            emit
        }
    }
})
</script>

<style scoped>
.transfer-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

.transfer-form {
    background-color: #f5f5f5;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    color: #333;
}

.form-group input {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
}

.form-group input.error {
    border-color: #f44336;
}

.error-message {
    color: #f44336;
    font-size: 14px;
    margin-top: 5px;
    display: block;
}

.balance-info {
    margin: 20px 0;
    padding: 10px;
    background-color: #e8f5e9;
    border-radius: 4px;
}

.send-btn {
    background-color: #4CAF50;
    color: white;
    padding: 12px 24px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    width: 100%;
}

.send-btn:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
}

.transfer-progress {
    margin: 20px 0;
    padding: 15px;
    background-color: #f5f5f5;
    border-radius: 8px;
}

.progress-bar {
    width: 100%;
    height: 8px;
    background-color: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 10px;
}

.progress-fill {
    height: 100%;
    background-color: #2196F3;
    transition: width 0.3s ease;
}

.progress-status {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    color: #666;
}

.loading-spinner {
    width: 20px;
    height: 20px;
    border: 2px solid #f3f3f3;
    border-top: 2px solid #2196F3;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.transaction-status {
    margin-top: 20px;
    padding: 15px;
    background-color: #f5f5f5;
    border-radius: 8px;
}

.transaction-status h3 {
    margin: 0 0 10px 0;
    color: #333;
}

.transaction-status p {
    margin: 5px 0;
    word-break: break-all;
    font-family: monospace;
    color: #666;
}
</style> 