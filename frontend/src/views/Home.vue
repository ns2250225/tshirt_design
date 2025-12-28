<template>
  <div class="home-container">
    <div class="main-content">
      <!-- 左侧：输入与控制 -->
      <div class="control-panel">
        <section class="input-section">
          <h2>1. 输入设计灵感</h2>
          <textarea 
            v-model="userInput" 
            placeholder="描述你的设计想法，例如：一只在冲浪的皮卡丘，文字是“冲浪啊”..."
            rows="3"
            ref="inputRef"
          ></textarea>
        </section>

        <section class="style-section">
          <h2>2. 选择风格</h2>
          <select v-model="selectedStyleIndex">
            <option disabled value="-1">请选择一种风格</option>
            <option v-for="(style, index) in styles" :key="index" :value="index">
              {{ style.name }}
            </option>
          </select>
          <div v-if="selectedStyleIndex !== -1" class="style-desc">
            <small>{{ styles[selectedStyleIndex].prompt }}</small>
          </div>
        </section>

        <button 
          @click="optimizePrompt" 
          :disabled="!userInput || selectedStyleIndex === -1 || isOptimizing"
          class="action-btn"
        >
          {{ isOptimizing ? '优化中...' : '优化提示词' }}
        </button>

        <section class="optimized-section">
          <h2>3. 优化结果 (可编辑)</h2>
          <textarea 
            v-model="optimizedPrompt" 
            rows="5"
            placeholder="优化后的提示词将显示在这里..."
          ></textarea>
        </section>

        <section class="ratio-section">
          <h2>4. 图片比例</h2>
          <div class="ratio-options">
            <label>
              <input type="radio" value="1:1" v-model="aspectRatio">
              1:1 (正方形)
            </label>
            <label>
              <input type="radio" value="2:3" v-model="aspectRatio">
              2:3 (纵向)
            </label>
          </div>
        </section>

        <button 
          @click="generateImage" 
          :disabled="!optimizedPrompt || isGenerating"
          class="primary-btn"
        >
          {{ isGenerating ? '生成设计图案中...' : '生成设计图案 (消耗10积分)' }}
        </button>
        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
      </div>

      <!-- 右侧：结果展示 -->
      <div class="result-panel">
        <div class="image-container">
          <div v-if="!generatedImage" class="placeholder">
            <span>设计图案将显示在这里</span>
          </div>
          <img v-else :src="generatedImage" alt="Generated Design" class="generated-img" />
        </div>

        <div class="result-actions" v-if="generatedImage">
          <button @click="downloadImage" class="secondary-btn">下载图片</button>
          <button @click="downloadNoBgImage" :disabled="isRemovingBg" class="action-btn">
            {{ isRemovingBg ? '抠图中...' : '下载抠图版' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- 下方：图案画廊 -->
    <section class="gallery-section">
      <h2>✨ 灵感画廊 (最近生成)</h2>
      <div v-if="gallery.length === 0" class="empty-gallery">
        <p>暂无生成记录，快来创作你的第一个设计吧！</p>
      </div>
      <div v-else class="gallery-grid">
        <div v-for="item in gallery" :key="item.id" class="gallery-item">
          <div class="gallery-img-wrapper">
            <img :src="`${API_HOST}${item.image_url}`" :alt="item.user_input" loading="lazy" />
          </div>
          <div class="gallery-info">
            <p class="gallery-prompt" :title="item.user_input">{{ item.user_input }}</p>
            <div class="gallery-actions">
              <button @click="copyDesign(item)" class="copy-btn">做同款</button>
              <button @click="downloadNoBgImage(item.image_url)" :disabled="isRemovingBg" class="action-btn small-btn">抠图</button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const styles = ref([]);
const selectedStyleIndex = ref(-1);
const userInput = ref('');
const optimizedPrompt = ref('');
const aspectRatio = ref('1:1');
const generatedImage = ref(null);
const currentImageUrl = ref('');
const isOptimizing = ref(false);
const isGenerating = ref(false);
const isRemovingBg = ref(false);
const errorMsg = ref('');
const gallery = ref([]);
const inputRef = ref(null);

const API_BASE = import.meta.env.PROD ? '/api' : 'http://localhost:5000/api';
const API_HOST = import.meta.env.PROD ? '' : 'http://localhost:5000';

const getHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : ''
  };
};

// 获取风格列表
onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/styles`);
    const data = await res.json();
    if (data.styles) {
      styles.value = data.styles;
    }
    // 获取画廊数据
    fetchGallery();
  } catch (e) {
    console.error('Failed to load styles:', e);
    errorMsg.value = '无法加载风格列表，请检查后端服务是否启动。';
  }
});

// 获取画廊数据
const fetchGallery = async () => {
  try {
    const res = await fetch(`${API_BASE}/gallery`);
    const data = await res.json();
    if (data.gallery) {
      gallery.value = data.gallery;
    }
  } catch (e) {
    console.error('Failed to load gallery:', e);
  }
};

// 做同款
const copyDesign = (item) => {
  userInput.value = item.user_input;
  // 滚动到顶部输入框
  window.scrollTo({ top: 0, behavior: 'smooth' });
  // 聚焦输入框
  if (inputRef.value) {
    setTimeout(() => inputRef.value.focus(), 500);
  }
};

// 优化提示词
const optimizePrompt = async () => {
  if (!userInput.value || selectedStyleIndex.value === -1) return;
  
  isOptimizing.value = true;
  errorMsg.value = '';
  
  try {
    const res = await fetch(`${API_BASE}/optimize`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        user_input: userInput.value,
        style_prompt: styles.value[selectedStyleIndex.value].prompt
      })
    });
    
    const data = await res.json();
    if (res.status === 401) {
       errorMsg.value = "登录已过期，请重新登录";
       // 可选：跳转登录
       return;
    }
    
    if (data.optimized_prompt) {
      optimizedPrompt.value = data.optimized_prompt;
    } else if (data.error) {
      errorMsg.value = `优化失败: ${data.error}`;
    }
  } catch (e) {
    errorMsg.value = `请求失败: ${e.message}`;
  } finally {
    isOptimizing.value = false;
  }
};

// 生成图片
const generateImage = async () => {
  if (!optimizedPrompt.value) return;
  
  isGenerating.value = true;
  errorMsg.value = '';
  generatedImage.value = null;
  
  try {
    const res = await fetch(`${API_BASE}/generate`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        prompt: optimizedPrompt.value,
        user_input: userInput.value, 
        aspect_ratio: aspectRatio.value
      })
    });
    
    const data = await res.json();
    
    if (res.status === 403) {
        errorMsg.value = `权限拒绝: ${data.error} (请充值或联系管理员)`;
        return;
    }
    
    if (data.image_data) {
      generatedImage.value = `data:image/png;base64,${data.image_data}`;
      currentImageUrl.value = data.image_url;
      // 更新本地存储的积分 (简单的 optimistic update 或重新 fetch user)
      if (data.remaining_points !== undefined) {
          const user = JSON.parse(localStorage.getItem('user') || '{}');
          user.points = data.remaining_points;
          localStorage.setItem('user', JSON.stringify(user));
          // 触发事件通知 App.vue 更新积分显示 (简化版：刷新页面或使用 store)
          window.dispatchEvent(new Event('user-updated'));
      }
      
      // 生成成功后刷新画廊
      fetchGallery();
    } else if (data.error) {
      errorMsg.value = `生成失败: ${data.error}`;
    }
  } catch (e) {
    errorMsg.value = `请求失败: ${e.message}`;
  } finally {
    isGenerating.value = false;
  }
};

// 下载图片
const downloadImage = () => {
  if (!generatedImage.value) return;
  const a = document.createElement('a');
  a.href = generatedImage.value;
  a.download = `tshirt_design_${Date.now()}.png`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};

// 下载抠图版
const downloadNoBgImage = async (url = null) => {
  // 如果传入了 url (来自画廊)，则使用传入的；否则使用当前生成的
  const targetUrl = typeof url === 'string' ? url : currentImageUrl.value;
  
  if (!targetUrl) {
    errorMsg.value = "无法获取图片路径";
    return;
  }
  
  isRemovingBg.value = true;
  errorMsg.value = '';
  
  try {
    const res = await fetch(`${API_BASE}/remove_bg`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ image_url: targetUrl })
    });
    
    const data = await res.json();
    
    if (data.image_url) {
      const link = document.createElement('a');
      link.href = `${API_HOST}${data.image_url}`;
      link.download = `nobg_${Date.now()}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else if (data.error) {
      errorMsg.value = `抠图失败: ${data.error}`;
    }
  } catch (e) {
    errorMsg.value = `请求失败: ${e.message}`;
  } finally {
    isRemovingBg.value = false;
  }
};
</script>

<style scoped>
/* 局部样式 */
.main-content {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
  margin-bottom: 50px;
}

.control-panel {
  flex: 1;
  min-width: 300px;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

section h2 {
  font-size: 1.1rem;
  margin-bottom: 10px;
  color: #34495e;
}

textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: inherit;
  resize: vertical;
}

select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.style-desc {
  margin-top: 5px;
  color: #666;
  font-size: 0.9rem;
  background: #f9f9f9;
  padding: 5px;
  border-radius: 4px;
}

.ratio-options {
  display: flex;
  gap: 20px;
}

.ratio-options label {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

button {
  padding: 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background 0.3s;
}

.action-btn {
  background-color: #e0e0e0;
  color: #333;
}

.action-btn:hover:not(:disabled) {
  background-color: #d0d0d0;
}

.primary-btn {
  background-color: #3498db;
  color: white;
  font-size: 1.1rem;
}

.primary-btn:hover:not(:disabled) {
  background-color: #2980b9;
}

.secondary-btn {
  background-color: #2ecc71;
  color: white;
  flex: 1;
}

.secondary-btn:hover {
  background-color: #27ae60;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-msg {
  color: #e74c3c;
  font-size: 0.9rem;
}

.result-panel {
  flex: 1;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.image-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 2px dashed #ddd;
}

.placeholder {
  color: #aaa;
  font-size: 1.2rem;
}

.generated-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.result-actions {
  display: flex;
  gap: 10px;
}

.gallery-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  margin-top: 30px;
}

.empty-gallery {
  text-align: center;
  padding: 40px;
  color: #999;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.gallery-item {
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.gallery-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.gallery-img-wrapper {
  aspect-ratio: 1;
  overflow: hidden;
  background: #f9f9f9;
}

.gallery-img-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gallery-info {
  padding: 10px;
}

.gallery-prompt {
  font-size: 0.9rem;
  color: #555;
  margin-bottom: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gallery-actions {
  display: flex;
  gap: 5px;
}

.copy-btn {
  flex: 2;
  padding: 8px;
  background-color: #f39c12;
  color: white;
  font-size: 0.9rem;
}

.small-btn {
  flex: 1;
  padding: 8px;
  font-size: 0.9rem;
}

.copy-btn:hover {
  background-color: #e67e22;
}
</style>
