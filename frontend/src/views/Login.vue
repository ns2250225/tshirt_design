<template>
  <div class="login-container">
    <div class="card">
      <h2>{{ isRegister ? '注册新账号' : '登录' }}</h2>
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="username" type="text" required placeholder="请输入用户名" />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" required placeholder="请输入密码" />
        </div>
        <div class="error-msg" v-if="errorMsg">{{ errorMsg }}</div>
        <button type="submit" class="submit-btn" :disabled="isLoading">
          {{ isLoading ? '处理中...' : (isRegister ? '注册' : '登录') }}
        </button>
      </form>
      <div class="toggle-mode">
        <span @click="toggleMode">
          {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const isRegister = ref(false);
const username = ref('');
const password = ref('');
const errorMsg = ref('');
const isLoading = ref(false);

const API_BASE = import.meta.env.PROD ? '/api' : 'http://localhost:5000/api';

const toggleMode = () => {
  isRegister.value = !isRegister.value;
  errorMsg.value = '';
};

const handleSubmit = async () => {
  errorMsg.value = '';
  isLoading.value = true;
  
  const endpoint = isRegister.value ? '/auth/register' : '/auth/login';
  
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    });
    
    const data = await res.json();
    
    if (res.ok) {
      if (isRegister.value) {
        // 注册成功后自动登录或切换到登录页
        // 这里选择自动登录
        await performLogin();
      } else {
        handleLoginSuccess(data);
      }
    } else {
      errorMsg.value = data.error || '操作失败';
    }
  } catch (e) {
    errorMsg.value = `请求失败: ${e.message}`;
  } finally {
    isLoading.value = false;
  }
};

const performLogin = async () => {
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    });
    const data = await res.json();
    if (res.ok) {
      handleLoginSuccess(data);
    } else {
      isRegister.value = false; // 切换回登录页让用户重试
      errorMsg.value = '注册成功但登录失败，请手动登录';
    }
  } catch (e) {
    isRegister.value = false;
    errorMsg.value = '注册成功但登录失败，请手动登录';
  }
};

const handleLoginSuccess = (data) => {
  localStorage.setItem('token', data.token);
  localStorage.setItem('user', JSON.stringify(data.user));
  // 触发事件更新导航栏
  window.dispatchEvent(new Event('user-updated'));
  router.push('/');
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
}

.card {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 400px;
}

h2 {
  text-align: center;
  margin-bottom: 20px;
  color: #2c3e50;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  color: #666;
}

input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  margin-top: 10px;
}

.submit-btn:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.error-msg {
  color: #e74c3c;
  margin-bottom: 10px;
  font-size: 0.9rem;
  text-align: center;
}

.toggle-mode {
  text-align: center;
  margin-top: 15px;
  font-size: 0.9rem;
  color: #7f8c8d;
}

.toggle-mode span {
  color: #3498db;
  cursor: pointer;
  text-decoration: underline;
}
</style>
