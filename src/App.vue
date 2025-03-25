<template>
  <div class="app-container">
    <header class="header">
      <div class="header-content">
        <div class="logo">
          <img src="./assets/logo.png" alt="Logo" />
        </div>
        <div class="nav-buttons">
          <div class="location-info" v-if="location">
            <span>📍 {{ location }}</span>
            <button class="refresh-btn" @click="getWeather" title="刷新位置">
              🔄
            </button>
            <button class="select-location-btn" @click="showLocationDialog = true" title="选择位置">
              📍
            </button>
          </div>
          <div class="weather-info" v-if="weather">
            <span>{{ weather.temperature }}°C</span>
            <span>{{ weather.description }}</span>
          </div>
          <button @click="showTranslationDialog = true" class="translate-btn">
            <span class="icon">🌐</span>
            <span class="text">{{ currentLanguage }}</span>
          </button>
        </div>
      </div>
    </header>

    <main class="main-content">
      <div v-if="!currentView" class="menu-container">
        <button class="menu-btn vote-btn" @click="currentView = 'voting'">
          <span class="icon">📊</span>
          <span class="text">投票系统</span>
        </button>
        <button class="menu-btn article-btn" @click="currentView = 'article'">
          <span class="icon">📰</span>
          <span class="text">文章阅读</span>
        </button>
        <button class="menu-btn mcp-btn" @click="currentView = 'mcp'">
          <span class="icon">🎮</span>
          <span class="text">MCP</span>
        </button>
      </div>

      <VotingSystem v-if="currentView === 'voting'" @back="currentView = null" />
      <ArticleView v-if="currentView === 'article'" @back="currentView = null" />
      <McpView v-if="currentView === 'mcp'" @back="currentView = null" />
    </main>

    <!-- 语言选择对话框 -->
    <div v-if="showTranslationDialog" class="dialog-overlay">
      <div class="dialog-content">
        <h3>选择语言</h3>
        <div class="language-options">
          <button 
            v-for="lang in languages" 
            :key="lang.code"
            :class="['lang-btn', { active: currentLanguage === lang.name }]"
            @click="selectLanguage(lang)"
          >
            {{ lang.name }}
          </button>
        </div>
        <button class="close-btn" @click="showTranslationDialog = false">关闭</button>
      </div>
    </div>

    <!-- 位置选择对话框 -->
    <div v-if="showLocationDialog" class="dialog-overlay">
      <div class="dialog-content">
        <h3>选择位置</h3>
        <div class="location-options">
          <button 
            v-for="loc in locations" 
            :key="loc.code"
            :class="['loc-btn', { active: selectedLocation === loc.name }]"
            @click="selectLocation(loc)"
          >
            {{ loc.name }}
          </button>
        </div>
        <button class="close-btn" @click="showLocationDialog = false">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import VotingSystem from './components/VotingSystem.vue';
import ArticleView from './components/ArticleView.vue';
import McpView from './components/McpView.vue';

// AI翻译相关
const DEEPSEEK_API_KEY = 'sk-a74d9a6d8d204890a5ef7efc6a70ec46';
const DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions';

// 天气相关
const weather = ref(null);
const WEATHER_API_URL = 'https://api.open-meteo.com/v1/forecast';

// 语言相关
const currentLanguage = ref('zh');
const translations = {
  zh: {
    title: '投票系统',
    connectWallet: '连接钱包',
    connecting: '连接中...',
    walletConnected: '已连接钱包',
    address: '地址',
    switchAccount: '切换账号',
    createVote: '创建新投票',
    enterVoteName: '请输入投票名称',
    create: '创建',
    voteList: '投票列表',
    yesVotes: '赞成票',
    noVotes: '反对票',
    youVoted: '您已投票',
    yes: '赞成',
    no: '反对'
  },
  en: {
    title: 'Voting System',
    connectWallet: 'Connect Wallet',
    connecting: 'Connecting...',
    walletConnected: 'Wallet Connected',
    address: 'Address',
    switchAccount: 'Switch Account',
    createVote: 'Create New Vote',
    enterVoteName: 'Enter vote name',
    create: 'Create',
    voteList: 'Vote List',
    yesVotes: 'Yes Votes',
    noVotes: 'No Votes',
    youVoted: 'You Voted',
    yes: 'Yes',
    no: 'No'
  }
};

// 添加新的响应式变量
const title = ref('投票系统');
const location = ref('');
const showTranslationDialog = ref(false);
const translateInput = ref('');
const translateResult = ref('');
const translatedTexts = ref({});
const showLocationDialog = ref(false);
const locationSearch = ref('');
const locationResults = ref([]);
const selectedLocation = ref(null);

// 添加视图控制
const currentView = ref(null);

// 修改翻译函数
const translateText = async (text, targetLang) => {
  try {
    const response = await fetch(DEEPSEEK_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DEEPSEEK_API_KEY}`
      },
      body: JSON.stringify({
        model: "deepseek-chat",
        messages: [
          {
            role: "system",
            content: `你是一个专业的翻译助手，请将以下文本翻译成${targetLang === 'zh' ? '中文' : '英文'}，只返回翻译结果：`
          },
          {
            role: "user",
            content: text
          }
        ],
        temperature: 0.7,
        max_tokens: 1000
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`翻译失败: ${errorData.error?.message || response.statusText}`);
    }

    const data = await response.json();
    if (!data.choices || !data.choices[0] || !data.choices[0].message) {
      throw new Error('无效的响应格式');
    }
    return data.choices[0].message.content.trim();
  } catch (error) {
    console.error('翻译失败:', error);
    return text;
  }
};

// 修改t函数
const t = async (key) => {
  const text = translations[currentLanguage.value][key] || key;
  
  // 检查是否已经翻译过
  if (!translatedTexts.value[key]) {
    translatedTexts.value[key] = await translateText(text, currentLanguage.value);
  }
  return translatedTexts.value[key];
};

// 修改翻译对话框的翻译函数
const handleTranslate = async () => {
  if (!translateInput.value) return;
  
  try {
    translateResult.value = await translateText(
      translateInput.value,
      currentLanguage.value === 'zh' ? 'en' : 'zh'
    );
  } catch (error) {
    console.error('翻译失败:', error);
    translateResult.value = '翻译失败，请重试';
  }
};

// 添加位置搜索功能
const searchLocation = async () => {
  if (!locationSearch.value) {
    locationResults.value = [];
    return;
  }

  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locationSearch.value)}&limit=5`
    );
    const data = await response.json();
    locationResults.value = data;
  } catch (error) {
    console.error('搜索位置失败:', error);
  }
};

// 修改选择位置函数
const selectLocation = async (result) => {
  try {
    selectedLocation.value = result;
    // 使用更友好的显示名称
    location.value = result.display_name.split('，')[0];
    showLocationDialog.value = false;
    locationSearch.value = '';
    locationResults.value = [];
    
    // 获取选中位置的天气
    const weatherResponse = await fetch(
      `${WEATHER_API_URL}?latitude=${result.lat}&longitude=${result.lon}&current=temperature_2m,weather_code&timezone=auto`
    );
    
    if (!weatherResponse.ok) {
      throw new Error('获取天气失败');
    }
    
    const data = await weatherResponse.json();
    
    // 转换天气代码为描述
    const weatherDescriptions = {
      0: '晴朗',
      1: '多云',
      2: '阴天',
      3: '阴天',
      45: '雾',
      48: '霾',
      51: '小雨',
      53: '中雨',
      55: '大雨',
      61: '小雨',
      63: '中雨',
      65: '大雨',
      71: '小雪',
      73: '中雪',
      75: '大雪',
      77: '雪粒',
      80: '阵雨',
      81: '阵雨',
      82: '暴雨',
      85: '阵雪',
      86: '暴雪',
      95: '雷雨',
      96: '雷阵雨',
      99: '雷阵雨'
    };

    weather.value = {
      temperature: Math.round(data.current.temperature_2m),
      description: weatherDescriptions[data.current.weather_code] || '未知天气'
    };
  } catch (error) {
    console.error('选择位置失败:', error);
    alert('获取天气失败，请重试');
  }
};

// 修改获取天气函数
const getWeather = async () => {
  try {
    if (selectedLocation.value) {
      // 如果已选择位置，使用选择的位置
      await selectLocation(selectedLocation.value);
      return;
    }

    const position = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject);
    });

    // 获取位置信息
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}`
    );
    const locationData = await response.json();
    location.value = locationData.display_name.split(',').slice(0, 3).join(',');
    selectedLocation.value = locationData;

    // 获取天气信息
    const weatherResponse = await fetch(
      `${WEATHER_API_URL}?latitude=${position.coords.latitude}&longitude=${position.coords.longitude}&current=temperature_2m,weather_code&timezone=auto`
    );

    const data = await weatherResponse.json();
    
    // 转换天气代码为描述
    const weatherDescriptions = {
      0: '晴朗',
      1: '多云',
      2: '阴天',
      3: '阴天',
      45: '雾',
      48: '霾',
      51: '小雨',
      53: '中雨',
      55: '大雨',
      61: '小雨',
      63: '中雨',
      65: '大雨',
      71: '小雪',
      73: '中雪',
      75: '大雪',
      77: '雪粒',
      80: '阵雨',
      81: '阵雨',
      82: '暴雨',
      85: '阵雪',
      86: '暴雪',
      95: '雷雨',
      96: '雷阵雨',
      99: '雷阵雨'
    };

    weather.value = {
      temperature: Math.round(data.current.temperature_2m),
      description: weatherDescriptions[data.current.weather_code] || '未知天气'
    };
  } catch (error) {
    console.error('获取天气和位置失败:', error);
    alert('获取位置失败，请检查位置权限或手动选择位置');
  }
};

// 修改语言切换函数
const changeLanguage = async () => {
  localStorage.setItem('language', currentLanguage.value);
  // 清空翻译缓存
  translatedTexts.value = {};
};

// 初始化语言
const initLanguage = () => {
  const savedLanguage = localStorage.getItem('language');
  if (savedLanguage) {
    currentLanguage.value = savedLanguage;
  }
};

// 语言选择
const selectLanguage = (lang) => {
  currentLanguage.value = lang.name;
  showTranslationDialog.value = false;
};

// 添加位置选择对话框
const locations = [
  { code: 'beijing', name: '北京' },
  { code: 'shanghai', name: '上海' },
  { code: 'guangzhou', name: '广州' }
];

onMounted(async () => {
  initLanguage();
  console.log('组件已挂载...');
  await getWeather();
});
</script>

<style lang="less" scoped>
.app-container {
  min-height: 100vh;
  background: #f5f5f5;
}

.header {
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 15px 0;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;

  .header-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .logo {
    img {
      height: 40px;
    }
  }

  .nav-buttons {
    display: flex;
    gap: 15px;

    button {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      border: none;
      border-radius: 20px;
      background: #f5f5f5;
      cursor: pointer;
      font-size: 14px;
      transition: all 0.3s ease;

      &:hover {
        background: #e0e0e0;
      }

      .icon {
        font-size: 16px;
      }
    }
  }
}

.main-content {
  max-width: 1200px;
  margin: 80px auto 0;
  padding: 20px;
}

.menu-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  padding: 20px;
}

.menu-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 15px;
  padding: 30px;
  border: none;
  border-radius: 12px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .icon {
    font-size: 32px;
  }

  .text {
    font-size: 16px;
    font-weight: 500;
  }

  &.vote-btn {
    background: linear-gradient(135deg, #4CAF50, #45a049);
    color: white;
  }

  &.article-btn {
    background: linear-gradient(135deg, #2196F3, #1976D2);
    color: white;
  }

  &.mcp-btn {
    background: linear-gradient(135deg, #9C27B0, #7B1FA2);
    color: white;
  }
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;

  .dialog-content {
    background: white;
    padding: 30px;
    border-radius: 12px;
    min-width: 300px;

    h3 {
      margin: 0 0 20px;
      font-size: 18px;
      color: #333;
    }
  }
}

.language-options,
.location-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}

.lang-btn,
.loc-btn {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: #f5f5f5;
  }

  &.active {
    background: #007AFF;
    color: white;
    border-color: #007AFF;
  }
}

.close-btn {
  width: 100%;
  padding: 10px;
  background: #f5f5f5;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;

  &:hover {
    background: #e0e0e0;
  }
}

.location-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #666;
  padding: 5px 10px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.weather-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #666;
  padding: 5px 10px;
  background-color: #f5f5f5;
  border-radius: 4px;
  
  span {
    &:first-child {
      font-weight: bold;
    }
  }
}

.refresh-btn, .select-location-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 5px;
  font-size: 14px;
  
  &:hover {
    opacity: 0.8;
  }
}
</style>
