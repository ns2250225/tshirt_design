#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}开始部署 T-Shirt Design Generator...${NC}"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: 未找到 docker 命令，请先安装 Docker。"
    exit 1
fi

# 检查 Docker Compose 是否可用
if ! command -v docker-compose &> /dev/null; then
    # 尝试 docker compose (新版)
    if ! docker compose version &> /dev/null; then
        echo "错误: 未找到 docker-compose 或 docker compose，请先安装。"
        exit 1
    fi
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

echo -e "${GREEN}停止旧容器 (如果存在)...${NC}"
$DOCKER_COMPOSE_CMD down

echo -e "${GREEN}构建并启动服务...${NC}"
$DOCKER_COMPOSE_CMD up -d --build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}部署成功！${NC}"
    echo -e "${GREEN}前端访问地址: http://localhost${NC}"
    echo -e "${GREEN}后端 API 地址: http://localhost:5000${NC}"
else
    echo "部署失败，请检查错误日志。"
    exit 1
fi
