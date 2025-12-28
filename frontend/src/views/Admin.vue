<template>
  <div class="admin-container">
    <h2>用户管理</h2>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>角色</th>
            <th>积分</th>
            <th>IP地址</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>
              <span :class="['role-badge', user.role]">{{ user.role }}</span>
            </td>
            <td>{{ user.points }}</td>
            <td>{{ user.ip_address || '未知' }}</td>
            <td>{{ new Date(user.created_at).toLocaleString() }}</td>
            <td>
              <button @click="editPoints(user)" class="edit-btn">修改积分</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 修改积分弹窗 -->
    <div v-if="editingUser" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <h3>修改积分 - {{ editingUser.username }}</h3>
        <input type="number" v-model.number="newPoints" min="0" />
        <div class="modal-actions">
          <button @click="closeModal" class="cancel-btn">取消</button>
          <button @click="savePoints" class="save-btn">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const users = ref([]);
const loading = ref(true);
const editingUser = ref(null);
const newPoints = ref(0);

const API_BASE = import.meta.env.PROD ? '/api' : 'http://localhost:5000/api';

const getHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : ''
  };
};

const fetchUsers = async () => {
  loading.value = true;
  try {
    const res = await fetch(`${API_BASE}/admin/users`, {
      headers: getHeaders()
    });
    if (res.ok) {
      users.value = await res.json();
    } else {
      alert('获取用户列表失败');
    }
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const editPoints = (user) => {
  editingUser.value = user;
  newPoints.value = user.points;
};

const closeModal = () => {
  editingUser.value = null;
};

const savePoints = async () => {
  if (!editingUser.value) return;
  
  try {
    const res = await fetch(`${API_BASE}/admin/users/${editingUser.value.id}/points`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify({ points: newPoints.value })
    });
    
    if (res.ok) {
      // 更新本地列表
      editingUser.value.points = newPoints.value;
      closeModal();
    } else {
      alert('修改失败');
    }
  } catch (e) {
    alert(`请求错误: ${e.message}`);
  }
};

onMounted(() => {
  fetchUsers();
});
</script>

<style scoped>
.admin-container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

h2 {
  margin-bottom: 20px;
  color: #2c3e50;
}

.table-wrapper {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background-color: #f8f9fa;
  font-weight: bold;
  color: #555;
}

.role-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
}

.role-badge.admin {
  background-color: #e74c3c;
  color: white;
}

.role-badge.user {
  background-color: #3498db;
  color: white;
}

.edit-btn {
  padding: 6px 12px;
  background-color: #f39c12;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 20px;
  border-radius: 8px;
  min-width: 300px;
}

.modal h3 {
  margin-bottom: 15px;
}

.modal input {
  width: 100%;
  padding: 8px;
  margin-bottom: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.cancel-btn {
  background-color: #95a5a6;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.save-btn {
  background-color: #2ecc71;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}
</style>
