<!-- 文章查看组件 -->
<template>
  <div class="article-section">
    <div class="back-btn">
      <button @click="$emit('back')">返回主页</button>
    </div>
    <div class="article-content">
      <h2>{{ article.title }}</h2>
      <div class="article-meta">
        <span class="date">{{ article.date }}</span>
        <span class="source">{{ article.source }}</span>
      </div>
      <div class="article-text">
        <p v-for="(paragraph, index) in article.content" :key="index">
          {{ paragraph }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

// 文章数据
const article = ref({
  title: 'AI时代下家电消费变革',
  date: '2024-03-19',
  source: '知乎行业沙龙',
  content: [
    '3月19日，全球家电与消费电子行业盛会AWE2025即将在上海开幕之时，知乎举办了主题为"AI科技知未来"的行业沙龙。知乎携手家电行业伙伴、行业机构、经济学专家、知乎答主一起，带来一场"AI时代下家电消费变革"的专业讨论。',
    '知乎COO张荣乐在分享中表示，过去专业内容和人群的价值一直被低估，进入AI时代，专业创作者不仅不会被AI取代，每个行业10%的头部专家价值都会被放大。未来，知乎将通过知乎直答等AI创新帮助家电合作伙伴树立产品专业影响力。'
  ]
});
</script>

<style lang="less" scoped>
.article-section {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);

  .article-content {
    h2 {
      font-size: 24px;
      color: #333;
      margin-bottom: 15px;
    }

    .article-meta {
      display: flex;
      gap: 20px;
      margin-bottom: 20px;
      color: #666;
      font-size: 14px;
    }

    .article-text {
      p {
        font-size: 16px;
        line-height: 1.6;
        color: #444;
        margin-bottom: 15px;
      }
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
 