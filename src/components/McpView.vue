<!-- MCP 对话组件 -->
<template>
  <div class="mcp-section">
    <div class="back-btn">
      <button @click="$emit('back')">返回主页</button>
    </div>
    <div class="mcp-content">
      <h2>MCP 对话</h2>
      <div class="chat-container">
        <div class="chat-messages" ref="messagesContainer">
          <div v-for="(message, index) in messages" :key="index" 
               :class="['message', message.role === 'user' ? 'user-message' : 'assistant-message']">
            <div class="message-content">{{ message.content }}</div>
          </div>
        </div>
        <div class="chat-input">
          <input 
            v-model="userInput" 
            @keyup.enter="sendMessage"
            placeholder="输入消息，按回车发送..."
            :disabled="isProcessing"
          />
          <button @click="sendMessage" :disabled="isProcessing">
            {{ isProcessing ? '处理中...' : '发送' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { mcpService } from '../services/mcp-server';

const messages = ref([]);
const userInput = ref('');
const isProcessing = ref(false);
const messagesContainer = ref(null);

// 初始化 MCP 客户端
onMounted(async () => {
  try {
    await mcpService.initialize();
    messages.value.push({
      role: 'assistant',
      content: 'MCP 客户端已成功初始化，您可以开始对话了。'
    });
  } catch (error) {
    console.error('MCP 客户端初始化失败:', error);
    messages.value.push({
      role: 'assistant',
      content: 'MCP 客户端初始化失败，请检查服务器是否正常运行。错误信息：' + error.message
    });
  }
});

// 发送消息
const sendMessage = async () => {
  if (!userInput.value.trim() || isProcessing.value) return;

  const userMessage = userInput.value.trim();
  messages.value.push({ role: 'user', content: userMessage });
  userInput.value = '';
  isProcessing.value = true;

  try {
    const response = await mcpService.processQuery(userMessage);
    messages.value.push({ role: 'assistant', content: response });
  } catch (error) {
    console.error('发送消息失败:', error);
    messages.value.push({
      role: 'assistant',
      content: '发送消息失败，请重试。错误信息：' + error.message
    });
  } finally {
    isProcessing.value = false;
    await nextTick();
    scrollToBottom();
  }
};

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};
</script>

<style lang="less" scoped>
.mcp-section {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);

  .mcp-content {
    h2 {
      font-size: 24px;
      color: #333;
      margin-bottom: 20px;
    }
  }
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 600px;
  background: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.4;
  word-wrap: break-word;
}

.user-message {
  align-self: flex-end;
  background: #007AFF;
  color: white;
}

.assistant-message {
  align-self: flex-start;
  background: white;
  color: #333;
}

.chat-input {
  display: flex;
  padding: 16px;
  background: white;
  border-top: 1px solid #eee;
  gap: 12px;

  input {
    flex: 1;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;

    &:focus {
      outline: none;
      border-color: #007AFF;
    }

    &:disabled {
      background: #f5f5f5;
      cursor: not-allowed;
    }
  }

  button {
    padding: 8px 16px;
    background: #007AFF;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;

    &:hover:not(:disabled) {
      background: #0056b3;
    }

    &:disabled {
      background: #ccc;
      cursor: not-allowed;
    }
  }
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