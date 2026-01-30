#!/bin/bash
# 一键 Docker 构建和上传 service-forge 基础镜像脚本
# 支持本地和远程两种模式
# 用法: ./build.sh --local 或 ./build.sh --remote

# 配置参数
IMAGE_NAME="service-forge"
REPOSITORY_NAME="service-forge"
VERSION="latest"
DOCKERFILE="dockerfile.base"

# 解析命令行参数
MODE=""
if [ "$1" == "--local" ]; then
    MODE="local"
    REGISTRY_ADDRESS="${SF_REGISTRY_LOCAL_ADDRESS}"
    if [ -z "$REGISTRY_ADDRESS" ]; then
        echo "错误: 环境变量 SF_REGISTRY_LOCAL_ADDRESS 未设置!"
        exit 1
    fi
elif [ "$1" == "--remote" ]; then
    MODE="remote"
    REGISTRY_ADDRESS="${SF_REGISTRY_REMOTE_ADDRESS}"
    if [ -z "$REGISTRY_ADDRESS" ]; then
        echo "错误: 环境变量 SF_REGISTRY_REMOTE_ADDRESS 未设置!"
        exit 1
    fi
else
    echo "用法: $0 --local 或 $0 --remote"
    echo ""
    echo "  --local  构建并推送到本地仓库 (使用 SF_REGISTRY_LOCAL_ADDRESS)"
    echo "  --remote 构建并推送到远程仓库 (使用 SF_REGISTRY_REMOTE_ADDRESS)"
    exit 1
fi

echo "=== 开始构建 service-forge 基础镜像 (模式: $MODE) ==="

if [ ! -f "$DOCKERFILE" ]; then
    echo "错误: 找不到基础镜像 Dockerfile $DOCKERFILE!"
    exit 1
fi

# 1. 构建 Docker 镜像
echo "步骤 1/3: 构建 Docker 基础镜像..."
docker build -f $DOCKERFILE -t $IMAGE_NAME:latest .
if [ $? -ne 0 ]; then
    echo "错误: Docker 基础镜像构建失败!"
    exit 1
fi
echo "✓ 基础镜像构建成功"

# 2. 获取镜像ID并标记
echo "步骤 2/3: 标记基础镜像..."
IMAGE_ID=$(docker images -q $IMAGE_NAME:latest)
if [ -z "$IMAGE_ID" ]; then
    echo "错误: 找不到 $IMAGE_NAME:latest 镜像!"
    exit 1
fi
TARGET_IMAGE="$REGISTRY_ADDRESS/$REPOSITORY_NAME:$VERSION"
docker tag $IMAGE_ID $TARGET_IMAGE
echo "✓ 基础镜像标记完成: $TARGET_IMAGE"

# 3. 推送镜像
echo "步骤 3/3: 推送基础镜像到仓库..."
docker push $TARGET_IMAGE
if [ $? -ne 0 ]; then
    echo "错误: 基础镜像推送失败!"
    exit 1
fi
echo "✓ 基础镜像推送成功"

echo "=== 基础镜像构建完成 ==="
echo "基础镜像地址: $TARGET_IMAGE"
