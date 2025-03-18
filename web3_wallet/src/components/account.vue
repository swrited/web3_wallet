<template>
    <div class="wallet-layout">
        <!-- 主页面 -->
        <div v-if="!wallet && !showCreateWallet && !showImportWallet" class="main-page">
            <h1 class="main-title">WMD_Wallet</h1>
            <div class="action-buttons">
                <button @click="showCreateWallet = true" class="action-btn primary">
                    <i class="fas fa-plus"></i>
                    创建新账号
                </button>
                <button @click="showImportWallet = true" class="action-btn primary">
                    <i class="fas fa-sign-in-alt"></i>
                    登录已有账号
                </button>
            </div>
        </div>

        <!-- 创建钱包模态框 -->
        <div v-else-if="showCreateWallet" class="modal">
            <div class="modal-content">
                <h3>创建新钱包</h3>
                <div class="form-group">
                    <label>设置密码</label>
                    <input type="password" v-model="password" placeholder="请输入密码" />
                </div>
                <div class="form-group">
                    <label>确认密码</label>
                    <input type="password" v-model="confirmPassword" placeholder="请再次输入密码" />
                </div>
                <div class="button-group">
                    <button @click="showCreateWallet = false" class="close-btn">取消</button>
                    <button @click="createWallet" class="action-btn primary">创建钱包</button>
                </div>
            </div>
        </div>

        <!-- 助记词确认模态框 -->
        <div v-else-if="showMnemonic" class="modal">
            <div class="modal-content">
                <h3>请保存您的助记词</h3>
                <p class="warning">请将以下助记词安全保存，不要在不安全的环境下查看！</p>
                <div class="mnemonic-box">
                    {{ generatedMnemonic }}
                </div>
                <button @click="confirmMnemonic" class="action-btn primary">我已安全保存</button>
                <button @click="showMnemonic = false" class="close-btn">取消</button>
            </div>
        </div>

        <!-- 助记词验证模态框 -->
        <div v-else-if="showVerifyMnemonic" class="modal">
            <div class="modal-content">
                <h3>请按顺序选择助记词</h3>
                <div class="selected-words">
                    <div v-for="(word, index) in selectedWords" :key="index" class="word-item">
                        {{ word }}
                    </div>
                </div>
                <div class="word-options">
                    <button 
                        v-for="(word, index) in shuffledMnemonic" 
                        :key="index"
                        @click="selectWord(word)"
                        class="word-btn"
                        :disabled="selectedWords.includes(word)"
                    >
                        {{ word }}
                    </button>
                </div>
                <button @click="verifyMnemonic" class="action-btn primary">确认</button>
                <button @click="showVerifyMnemonic = false" class="close-btn">取消</button>
            </div>
        </div>

        <!-- 导入钱包模态框 -->
        <div v-else-if="showImportWallet" class="modal">
            <div class="modal-content">
                <h3>导入钱包</h3>
                <div class="import-options">
                    <button 
                        :class="['import-btn', { active: importType === 'privateKey' }]"
                        @click="importType = 'privateKey'"
                    >私钥导入</button>
                    <button 
                        :class="['import-btn', { active: importType === 'mnemonic' }]"
                        @click="importType = 'mnemonic'"
                    >助记词导入</button>
                </div>
                
                <!-- 私钥导入表单 -->
                <div v-if="importType === 'privateKey'" class="form-group">
                    <label>输入私钥</label>
                    <input type="text" v-model="importPrivateKey" placeholder="请输入私钥" />
                    <button @click="importByPrivateKey" class="action-btn primary">导入</button>
                </div>

                <!-- 助记词导入表单 -->
                <div v-if="importType === 'mnemonic'" class="form-group">
                    <label>输入助记词</label>
                    <input type="text" v-model="importMnemonic" placeholder="请输入助记词" />
                    <button @click="importByMnemonic" class="action-btn primary">导入</button>
                </div>

                <button @click="showImportWallet = false" class="close-btn">取消</button>
            </div>
        </div>

        <!-- 钱包界面 -->
        <div v-else-if="wallet" class="wallet-container">
            <!-- 顶部账户信息 -->
            <div class="account-header">
                <div class="account-info">
                    <div class="account-selector" @click="toggleAccountMenu">
                        <h2>Account1</h2>
                        <p class="address">{{ wallet ? formatAddress(wallet.address) : '' }}</p>
                        <i class="fas fa-chevron-down" :class="{ 'rotate': showAccountMenu }"></i>
                    </div>
                </div>
            </div>

            <!-- 账号切换菜单 -->
            <div class="account-menu" v-if="showAccountMenu">
                <div class="account-list">
                    <div v-for="(acc, index) in savedAccounts" 
                         :key="index" 
                         class="account-item"
                         :class="{ 'active': acc.address === wallet?.address }"
                         @click="switchAccount(acc)">
                        <div class="account-item-info">
                            <h3>Account{{ index + 1 }}</h3>
                            <p class="address">{{ formatAddress(acc.address) }}</p>
                        </div>
                        <i class="fas fa-check" v-if="acc.address === wallet?.address"></i>
                    </div>
                </div>
                <div class="account-menu-actions">
                    <button @click="showCreateWallet = true" class="menu-action-btn">
                        <i class="fas fa-plus"></i>
                        添加新账号
                    </button>
                    <button @click="showImportWallet = true" class="menu-action-btn">
                        <i class="fas fa-sign-in-alt"></i>
                        登录已有账号
                    </button>
                </div>
            </div>

            <!-- 主内容区 -->
            <div class="main-content">
                <!-- 左侧代币区域 -->
                <div class="tokens-section">
                    <div class="asset-section">
                        <div class="asset-info">
                            <div class="asset-amount">
                                <h3>{{ balance === '0' ? '查询中...' : balance + ' SepoliaETH' }}</h3>
                                <p class="asset-value">+US$0 (+0.00%)</p>
                            </div>
                            <div class="asset-actions">
                                <button @click="showSendModal = true" class="action-btn primary">
                                    <i class="fas fa-paper-plane"></i>
                                    转账
                                </button>
                                <button @click="showReceiveModal = true" class="action-btn primary">
                                    <i class="fas fa-qrcode"></i>
                                    收款
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 右侧账号信息区域 -->
                <div class="account-section">
                    <h3>账号信息</h3>
                    <div class="account-details">
                        <div class="detail-item">
                            <label>钱包地址</label>
                            <div class="address-box">
                                <span>{{ wallet ? wallet.address : '' }}</span>
                                <button @click="copyAddress" class="copy-btn">
                                    {{ copySuccess ? '已复制' : '复制' }}
                                </button>
                            </div>
                        </div>
                        <div class="detail-item">
                            <label>导出选项</label>
                            <div class="export-options">
                                <button @click="exportPrivateKey" class="export-btn">导出私钥</button>
                                <button @click="exportKeystore" class="export-btn">导出Keystore</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 转账组件 -->
            <div class="transfer-section" v-if="showSendModal">
                <Transfer :wallet="wallet" @transaction-complete="addTransaction" />
            </div>

            <!-- 收款二维码弹窗 -->
            <div class="modal" v-if="showReceiveModal">
                <div class="modal-content">
                    <h3>收款地址</h3>
                    <div class="qr-code">
                        <div class="address-display">
                            {{ wallet ? wallet.address : '' }}
                        </div>
                    </div>
                    <button @click="copyAddress" class="copy-btn">
                        {{ copySuccess ? '已复制' : '复制地址' }}
                    </button>
                    <button @click="showReceiveModal = false" class="close-btn">关闭</button>
                </div>
            </div>

            <!-- 私钥展示弹窗 -->
            <div class="modal" v-if="showPrivateKeyModal">
                <div class="modal-content">
                    <h3>私钥信息</h3>
                    <p class="warning">请妥善保管您的私钥，不要在不安全的环境下查看！</p>
                    <div class="private-key-box">
                        <div class="private-key-header">
                            <span>私钥：</span>
                            <button @click="copyPrivateKey" class="copy-btn">
                                {{ copySuccess ? '已复制' : '复制' }}
                            </button>
                        </div>
                        <div class="private-key-content">
                            {{ wallet ? wallet.privateKey : '' }}
                        </div>
                    </div>
                    <button @click="showPrivateKeyModal = false" class="close-btn">关闭</button>
                </div>
            </div>

            <!-- 底部支持信息 -->
            <div class="wallet-support">
                <div class="support-item">
                    <i class="fab fa-metamask"></i>
                    <span>支持 MetaMask</span>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import {ref, defineComponent, computed} from 'vue';
import { ethers } from 'ethers';
import Transfer from './transfer.vue'

export default defineComponent({
  name: 'Account',
  components: {
    Transfer
  },
  setup() {
    const password = ref('')
    const showMnemonic = ref(false)
    const showVerifyMnemonic = ref(false)
    const generatedMnemonic = ref('')
    const originalMnemonic = ref('')
    const shuffledMnemonic = ref([])
    const selectedWords = ref([])
    const wallet = ref(null)
    const balance = ref('0')
    const showCreateWallet = ref(false)
    const showImportWallet = ref(false)
    const importType = ref('')
    const importPrivateKey = ref('')
    const importMnemonic = ref('')
    const keystoreFile = ref(null)
    const keystorePassword = ref('')
    const showPrivateKeyModal = ref(false)
    const copySuccess = ref(false)
    const showSwitchAccount = ref(false)
    const showSendModal = ref(false)
    const showReceiveModal = ref(false)
    const currentTab = ref('tokens')
    const transactionFilter = ref('all')
    const privateKeyPassword = ref('')
    const confirmPassword = ref('')
    const showAccountMenu = ref(false)
    const savedAccounts = ref([])

    // 模拟交易记录数据
    const transactions = ref([
        {
            hash: '0x123...',
            type: 'in',
            address: '0x456...',
            amount: '0.1',
            time: '2024-03-20 10:30'
        },
        {
            hash: '0x789...',
            type: 'out',
            address: '0xabc...',
            amount: '0.05',
            time: '2024-03-20 09:15'
        }
    ])

    // 过滤交易记录
    const filteredTransactions = computed(() => {
        if (transactionFilter.value === 'all') {
            return transactions.value
        }
        return transactions.value.filter(tx => tx.type === transactionFilter.value)
    })

    // 更新余额和交易记录
    const updateBalanceAndTransactions = async () => {
        try {
            const provider = new ethers.providers.JsonRpcProvider('https://sepolia.infura.io/v3/86fa8d2d26f7440aa9ca5504cbc7e095')
            const balanceWei = await provider.getBalance(wallet.value.address)
            balance.value = ethers.utils.formatEther(balanceWei)

            // 从 localStorage 获取交易记录
            const savedTransactions = localStorage.getItem(`transactions_${wallet.value.address}`)
            if (savedTransactions) {
                transactions.value = JSON.parse(savedTransactions)
            }
        } catch (error) {
            console.error('获取余额失败:', error)
        }
    }

    // 添加新的交易记录
    const addTransaction = (tx) => {
        if (!wallet.value) return
        
        const newTransaction = {
            hash: tx.hash,
            type: tx.type,
            address: tx.address,
            amount: tx.amount,
            time: new Date().toLocaleString()
        }
        
        // 添加到交易记录列表
        transactions.value.unshift(newTransaction)
        
        // 保存到 localStorage
        localStorage.setItem(`transactions_${wallet.value.address}`, JSON.stringify(transactions.value))
    }

    // 保存钱包到 localStorage
    const saveWallet = () => {
        if (wallet.value) {
            const walletData = {
                address: wallet.value.address,
                privateKey: wallet.value.privateKey
            }
            
            // 获取已保存的账号列表
            const savedAccountsStr = localStorage.getItem('savedAccounts')
            let accounts = savedAccountsStr ? JSON.parse(savedAccountsStr) : []
            
            // 检查是否已存在该账号
            const exists = accounts.some(acc => acc.address === wallet.value.address)
            if (!exists) {
                accounts.push(walletData)
                localStorage.setItem('savedAccounts', JSON.stringify(accounts))
                savedAccounts.value = accounts
            }
        }
    }

    // 重置钱包
    const resetWallet = () => {
        wallet.value = null
        password.value = ''
        showMnemonic.value = false
        showVerifyMnemonic.value = false
        generatedMnemonic.value = ''
        originalMnemonic.value = ''
        shuffledMnemonic.value = []
        selectedWords.value = []
        balance.value = '0'
        showCreateWallet.value = false
        showImportWallet.value = false
        importType.value = ''
        importPrivateKey.value = ''
        importMnemonic.value = ''
        keystoreFile.value = null
        keystorePassword.value = ''
        transactions.value = [] // 清空交易记录
        localStorage.removeItem('wallet') // 清除保存的钱包
        showAccountMenu.value = false
    }

    // 登出功能
    const logout = () => {
        if (confirm('确定要登出当前账号吗？')) {
            resetWallet()
        }
    }

    // 切换到创建账号
    const switchToCreate = () => {
        showSwitchAccount.value = false
        resetWallet()
        showCreateWallet.value = true
    }

    // 切换到导入账号
    const switchToImport = () => {
        showSwitchAccount.value = false
        resetWallet()
        showImportWallet.value = true
    }

    // 格式化地址显示
    const formatAddress = (address) => {
        if (!address) return ''
        return `${address.slice(0, 6)}...${address.slice(-4)}`
    }

    // 复制地址
    const copyAddress = async () => {
        if (!wallet.value) return
        try {
            await navigator.clipboard.writeText(wallet.value.address)
            copySuccess.value = true
            setTimeout(() => {
                copySuccess.value = false
            }, 2000)
        } catch (err) {
            console.error('复制失败:', err)
            alert('复制失败，请手动复制')
        }
    }

    // 导出 Keystore
    const exportKeystore = async () => {
        if (!wallet.value) return
        try {
            const keystore = await wallet.value.encrypt(password.value)
            const blob = new Blob([keystore], { type: 'application/json' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `keystore-${wallet.value.address}.json`
            a.click()
            URL.revokeObjectURL(url)
        } catch (error) {
            console.error('导出Keystore失败:', error)
            alert('导出Keystore失败')
        }
    }

    // 创建钱包
    const createWallet = async () => {
        if (!password.value || !confirmPassword.value) {
            alert('请输入密码')
            return
        }
        if (password.value !== confirmPassword.value) {
            alert('两次输入的密码不一致')
            return
        }

        try {
            const newWallet = ethers.Wallet.createRandom()
            wallet.value = newWallet
            generatedMnemonic.value = newWallet.mnemonic.phrase
            showCreateWallet.value = false
            showMnemonic.value = true
            saveWallet()
        } catch (error) {
            console.error('创建钱包失败:', error)
            alert('创建钱包失败')
        }
    }

    // 确认助记词
    const confirmMnemonic = () => {
        showMnemonic.value = false
        showVerifyMnemonic.value = true
        originalMnemonic.value = generatedMnemonic.value.split(' ')
        shuffledMnemonic.value = [...originalMnemonic.value].sort(() => Math.random() - 0.5)
        selectedWords.value = []
    }

    // 选择助记词
    const selectWord = (word) => {
        selectedWords.value.push(word)
    }

    // 验证助记词
    const verifyMnemonic = () => {
        const isCorrect = selectedWords.value.every((word, index) => word === originalMnemonic.value[index])
        if (isCorrect) {
            showVerifyMnemonic.value = false
            updateBalanceAndTransactions()
        } else {
            alert('助记词顺序错误，请重新选择')
            selectedWords.value = []
        }
    }

    // 通过私钥导入钱包
    const importByPrivateKey = async () => {
        if (!importPrivateKey.value) {
            alert('请输入私钥')
            return
        }

        try {
            const importedWallet = new ethers.Wallet(importPrivateKey.value)
            wallet.value = importedWallet
            showImportWallet.value = false
            saveWallet()
            updateBalanceAndTransactions()
        } catch (error) {
            console.error('导入钱包失败:', error)
            alert('导入钱包失败，请检查私钥是否正确')
        }
    }

    // 通过助记词导入钱包
    const importByMnemonic = async () => {
        if (!importMnemonic.value) {
            alert('请输入助记词')
            return
        }

        try {
            const importedWallet = ethers.Wallet.fromMnemonic(importMnemonic.value)
            wallet.value = importedWallet
            showImportWallet.value = false
            saveWallet()
            updateBalanceAndTransactions()
        } catch (error) {
            console.error('导入钱包失败:', error)
            alert('导入钱包失败，请检查助记词是否正确')
        }
    }

    // 恢复钱包
    const restoreWallet = () => {
        const savedWallet = localStorage.getItem('wallet')
        if (savedWallet) {
            try {
                const walletData = JSON.parse(savedWallet)
                wallet.value = new ethers.Wallet(walletData.privateKey)
                updateBalanceAndTransactions()
            } catch (error) {
                console.error('恢复钱包失败:', error)
                localStorage.removeItem('wallet')
            }
        }
    }

    // 切换账号菜单显示状态
    const toggleAccountMenu = () => {
        showAccountMenu.value = !showAccountMenu.value
    }

    // 切换账号
    const switchAccount = (account) => {
        try {
            wallet.value = new ethers.Wallet(account.privateKey)
            updateBalanceAndTransactions()
            showAccountMenu.value = false
        } catch (error) {
            console.error('切换账号失败:', error)
            alert('切换账号失败')
        }
    }

    // 加载保存的账号列表
    const loadSavedAccounts = () => {
        const savedAccountsStr = localStorage.getItem('savedAccounts')
        if (savedAccountsStr) {
            savedAccounts.value = JSON.parse(savedAccountsStr)
        }
    }

    // 在组件加载时恢复钱包和加载账号列表
    restoreWallet()
    loadSavedAccounts()

    // 复制私钥
    const copyPrivateKey = async () => {
        if (!wallet.value) return
        try {
            await navigator.clipboard.writeText(wallet.value.privateKey)
            copySuccess.value = true
            setTimeout(() => {
                copySuccess.value = false
            }, 2000)
        } catch (err) {
            console.error('复制失败:', err)
            alert('复制失败，请手动复制')
        }
    }

    // 导出私钥
    const exportPrivateKey = () => {
        if (!wallet.value) return
        showPrivateKeyModal.value = true
    }

    return {
      password,
      showMnemonic,
      showVerifyMnemonic,
      generatedMnemonic,
      originalMnemonic,
      shuffledMnemonic,
      selectedWords,
      wallet,
      balance,
      showCreateWallet,
      showImportWallet,
      importType,
      importPrivateKey,
      importMnemonic,
      keystorePassword,
      showPrivateKeyModal,
      copySuccess,
      showSwitchAccount,
      logout,
      switchToCreate,
      switchToImport,
      showSendModal,
      showReceiveModal,
      formatAddress,
      copyAddress,
      currentTab,
      transactionFilter,
      privateKeyPassword,
      transactions,
      filteredTransactions,
      showPrivateKeyModal,
      updateBalanceAndTransactions,
      saveWallet,
      resetWallet,
      addTransaction,
      exportKeystore,
      confirmPassword,
      createWallet,
      confirmMnemonic,
      selectWord,
      verifyMnemonic,
      importByPrivateKey,
      importByMnemonic,
      showAccountMenu,
      savedAccounts,
      toggleAccountMenu,
      switchAccount,
      exportPrivateKey
    }
  }
});
</script>

<style scoped>
.wallet-layout {
    display: flex;
    min-height: 100vh;
    background-color: #f8f9fa;
}

.wallet-container {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    background-color: #f8f9fa;
}

.account-header {
    background-color: #fff;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    position: relative;
    z-index: 100;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.account-info {
    flex: 1;
}

.account-selector {
    display: flex;
    flex-direction: column;
    cursor: pointer;
    position: relative;
    padding-right: 30px;
}

.account-selector h2 {
    margin: 0;
    color: #333;
    font-size: 24px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.account-selector h2::before {
    content: '';
    display: inline-block;
    width: 24px;
    height: 24px;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23333'%3E%3Cpath d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z'/%3E%3C/svg%3E");
    background-size: contain;
    background-repeat: no-repeat;
}

.account-selector .address {
    color: #666;
    font-family: monospace;
    margin: 5px 0;
    font-size: 16px;
}

.account-selector i {
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    transition: transform 0.3s;
}

.account-selector i.rotate {
    transform: translateY(-50%) rotate(180deg);
}

.account-menu {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    margin-top: 8px;
    overflow: hidden;
    border: 1px solid #eee;
}

.account-list {
    max-height: 300px;
    overflow-y: auto;
}

.account-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    cursor: pointer;
    transition: background-color 0.2s;
    border-bottom: 1px solid #eee;
}

.account-item:last-child {
    border-bottom: none;
}

.account-item:hover {
    background-color: #f5f5f5;
}

.account-item.active {
    background-color: #e3f2fd;
}

.account-item-info h3 {
    margin: 0;
    font-size: 16px;
    color: #333;
}

.account-item-info .address {
    margin: 4px 0 0 0;
    font-size: 14px;
    color: #666;
}

.account-item i.fa-check {
    color: #2196F3;
}

.account-menu-actions {
    border-top: 1px solid #eee;
    padding: 8px;
}

.menu-action-btn {
    width: 100%;
    padding: 10px;
    border: none;
    background: none;
    color: #2196F3;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    transition: background-color 0.2s;
}

.menu-action-btn:hover {
    background-color: #f5f5f5;
}

.menu-action-btn i {
    font-size: 16px;
}

.main-content {
    display: flex;
    flex: 1;
    padding: 20px;
    gap: 20px;
    margin-top: 20px;
}

.tokens-section {
    flex: 1;
    background-color: #fff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.account-section {
    flex: 1;
    background-color: #fff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.close-btn {
    width: 100%;
    background-color: #4CAF50;
    color: white;
    padding: 12px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
    margin-top: 20px;
    transition: background-color 0.3s;
}

.close-btn:hover {
    background-color: #45a049;
}

.wallet-support {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
    background-color: #fff;
    border-radius: 12px;
    margin-top: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.support-item {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #666;
}

.support-item i {
    font-size: 24px;
    color: #f6851b;
}

.qr-code {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
    background-color: #f5f5f5;
    border-radius: 8px;
    margin: 20px 0;
}

.address-display {
    font-family: monospace;
    color: #333;
    word-break: break-all;
}

.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-content {
    background-color: white;
    padding: 20px;
    border-radius: 8px;
    width: 90%;
    max-width: 600px;
    position: relative;
}

.warning {
    color: #f44336;
    font-weight: bold;
    margin: 10px 0;
}

.private-key-box {
    background-color: #f5f5f5;
    border-radius: 4px;
    padding: 15px;
    margin: 15px 0;
}

.private-key-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.private-key-content {
    font-family: monospace;
    word-break: break-all;
    color: #333;
    padding: 10px;
    background-color: white;
    border-radius: 4px;
}

.copy-btn {
    background-color: #2196F3;
    color: white;
    padding: 5px 10px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}

.tab-content {
    background-color: #fff;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.asset-section {
    background-color: #fff;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.asset-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.asset-amount h3 {
    margin: 0;
    font-size: 24px;
    color: #333;
}

.asset-value {
    margin: 5px 0 0 0;
    color: #4CAF50;
}

.asset-actions {
    display: flex;
    gap: 10px;
}

.action-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: background-color 0.2s;
}

.action-btn.primary {
    background-color: #00bcd4;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s;
}

.action-btn.primary:hover {
    background-color: #00838f;
}

.logout-btn {
    background-color: #f44336;
    color: white;
}

.logout-btn:hover {
    background-color: #d32f2f;
}

.account-details {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.detail-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.detail-item label {
    font-weight: bold;
    color: #333;
}

.address-box {
    display: flex;
    align-items: center;
    gap: 10px;
    background-color: #f5f5f5;
    padding: 10px;
    border-radius: 4px;
}

.private-key-box {
    display: flex;
    gap: 10px;
}

.private-key-box input {
    flex: 1;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.view-btn {
    padding: 8px 16px;
    background-color: #2196F3;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.export-options {
    display: flex;
    gap: 10px;
}

.export-btn {
    flex: 1;
    padding: 8px;
    background-color: #2196F3;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.main-page {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    background-color: #f8f9fa;
    padding: 20px;
}

.main-title {
    font-size: 48px;
    color: #2196F3;
    margin-bottom: 40px;
    text-align: center;
}

.action-buttons {
    display: flex;
    flex-direction: column;
    gap: 20px;
    width: 100%;
    max-width: 300px;
}

.action-buttons .action-btn {
    width: 100%;
    padding: 15px;
    font-size: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
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
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
}

.mnemonic-box {
    background-color: #f5f5f5;
    padding: 15px;
    border-radius: 4px;
    margin: 15px 0;
    font-family: monospace;
    word-break: break-all;
}

.selected-words {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 20px;
}

.word-item {
    background-color: #e3f2fd;
    padding: 8px 16px;
    border-radius: 4px;
    color: #2196F3;
}

.word-options {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 20px;
}

.word-btn {
    padding: 8px 16px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background: none;
    cursor: pointer;
    transition: all 0.3s;
}

.word-btn:disabled {
    background-color: #f5f5f5;
    color: #999;
    cursor: not-allowed;
}

.import-options {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

.import-btn {
    flex: 1;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background: none;
    cursor: pointer;
    transition: all 0.3s;
}

.import-btn.active {
    background-color: #2196F3;
    color: white;
    border-color: #2196F3;
}

.button-group {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    margin-top: 20px;
}

.close-btn {
    background-color: #f5f5f5;
    color: #666;
    border: 1px solid #ddd;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s;
}

.close-btn:hover {
    background-color: #e0e0e0;
}
</style>