<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-content">
        <h1 @click="router.push('/')">AI T-Shirt Designer</h1>
        <nav>
          <div v-if="currentUser" class="user-nav">
            <span class="points-badge">💎 {{ currentUser.points }} 积分</span>
            <span class="username">👤 {{ currentUser.username }}</span>
            <router-link v-if="currentUser.role === 'admin'" to="/admin" class="nav-link admin-link">管理后台</router-link>
            <button @click="logout" class="logout-btn">退出</button>
          </div>
          <div v-else class="guest-nav">
            <router-link to="/login" class="nav-link">登录 / 注册</router-link>
          </div>
        </nav>
      </div>
    </header>

    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const currentUser = ref(null);

const updateUser = () => {
  const userStr = localStorage.getItem('user');
  if (userStr) {
    currentUser.value = JSON.parse(userStr);
  } else {
    currentUser.value = null;
  }
};

const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  updateUser();
  router.push('/login');
};

onMounted(() => {
  updateUser();
  window.addEventListener('user-updated', updateUser);
});

onUnmounted(() => {
  window.removeEventListener('user-updated', updateUser);
});
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  padding: 15px 0;
  margin-bottom: 20px;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

h1 {
  font-size: 1.5rem;
  color: #2c3e50;
  cursor: pointer;
  margin: 0;
}

.user-nav, .guest-nav {
  display: flex;
  align-items: center;
  gap: 15px;
}

.points-badge {
  background-color: #f1c40f;
  color: #fff;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 0.9rem;
  text-shadow: 0 1px 1px rgba(0,0,0,0.2);
}

.username {
  color: #555;
  font-weight: 500;
}

.nav-link {
  text-decoration: none;
  color: #3498db;
  font-weight: bold;
}

.nav-link.admin-link {
  color: #e74c3c;
}

.logout-btn {
  background: none;
  border: 1px solid #ddd;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  color: #666;
}

.logout-btn:hover {
  background-color: #f5f5f5;
  color: #333;
}
</style>
