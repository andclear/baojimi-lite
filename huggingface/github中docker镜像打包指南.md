# GitHub Actions Docker 镜像打包指南

本指南将详细介绍如何使用 GitHub Actions 自动构建和发布 Docker 镜像到 Docker Hub 和 GitHub Container Registry。

## 前置准备

### 1. 创建 Docker Hub 账号
- 访问 [Docker Hub](https://hub.docker.com/) 注册账号
- 记录你的用户名，后续需要用到

### 2. 生成 Docker Hub Access Token
- 登录 Docker Hub
- 进入 Account Settings > Security
- 点击 "New Access Token"
- 输入描述（如：GitHub Actions）
- 选择权限：Read, Write, Delete
- 复制生成的 token（只显示一次）

### 3. 配置 GitHub Secrets
在你的 GitHub 仓库中设置以下 Secrets：

1. 进入仓库 Settings > Secrets and variables > Actions
2. 点击 "New repository secret" 添加以下密钥：

| Secret 名称 | 值 | 说明 |
|------------|----|----|
| `DOCKER_HUB_USERNAME` | 你的 Docker Hub 用户名 | 用于登录 Docker Hub |
| `DOCKER_HUB_ACCESS_TOKEN` | 刚才生成的 Access Token | 用于认证 |

## 创建 GitHub Actions 工作流

### 1. 创建工作流文件
在你的仓库根目录创建 `.github/workflows/docker-build.yml` 文件：

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY_DOCKERHUB: docker.io
  REGISTRY_GHCR: ghcr.io
  IMAGE_NAME: baojimi-lite

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Docker Hub
      if: github.event_name != 'pull_request'
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY_DOCKERHUB }}
        username: ${{ secrets.DOCKER_HUB_USERNAME }}
        password: ${{ secrets.DOCKER_HUB_ACCESS_TOKEN }}

    - name: Log in to GitHub Container Registry
      if: github.event_name != 'pull_request'
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY_GHCR }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: |
          ${{ env.REGISTRY_DOCKERHUB }}/${{ secrets.DOCKER_HUB_USERNAME }}/${{ env.IMAGE_NAME }}
          ${{ env.REGISTRY_GHCR }}/${{ github.repository }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=raw,value=latest,enable={{is_default_branch}}

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: ${{ github.event_name != 'pull_request' }}
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

### 2. 工作流说明

#### 触发条件
- `push` 到 `main` 分支
- 创建以 `v` 开头的标签（如 `v1.0.0`）
- 对 `main` 分支的 Pull Request

#### 构建目标
- **Docker Hub**: `docker.io/你的用户名/baojimi-lite`
- **GitHub Container Registry**: `ghcr.io/你的用户名/仓库名`

#### 支持平台
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64)

## 使用方法

### 1. 自动构建
- 推送代码到 `main` 分支会自动触发构建
- 创建 release 标签会构建对应版本的镜像

### 2. 手动触发
- 在 GitHub 仓库的 Actions 页面
- 选择 "Build and Push Docker Image" 工作流
- 点击 "Run workflow"

### 3. 版本管理
推荐使用语义化版本标签：
```bash
git tag v1.0.0
git push origin v1.0.0
```

这会创建以下镜像标签：
- `latest`
- `v1.0.0`
- `v1.0`
- `v1`

## 镜像使用

### 从 Docker Hub 拉取
```bash
docker pull 你的用户名/baojimi-lite:latest
```

### 从 GitHub Container Registry 拉取
```bash
docker pull ghcr.io/你的用户名/仓库名:latest
```

### 运行容器
```bash
docker run -d \
  --name baojimi-lite \
  -p 7860:7860 \
  -e GEMINI_API_KEYS="your_api_key1,your_api_key2" \
  -e LAOPOBAO_AUTH="your_auth_key" \
  -e MAX_TRY=3 \
  你的用户名/baojimi-lite:latest
```

## 环境变量说明

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `GEMINI_API_KEYS` | 是 | - | Gemini API 密钥，多个用逗号分隔 |
| `LAOPOBAO_AUTH` | 否 | - | 服务访问密钥，留空则无需认证 |
| `MAX_TRY` | 否 | 3 | API 调用失败时的最大重试次数 |

## 故障排除

### 1. 构建失败
- 检查 Dockerfile 语法
- 确认所有依赖文件存在
- 查看 Actions 日志获取详细错误信息

### 2. 推送失败
- 确认 Docker Hub 凭据正确
- 检查仓库权限设置
- 验证网络连接

### 3. 镜像无法运行
- 检查环境变量配置
- 确认端口映射正确
- 查看容器日志：`docker logs 容器名`

## 高级配置

### 1. 多阶段构建优化
如需优化镜像大小，可以修改 Dockerfile 使用多阶段构建。

### 2. 自定义构建参数
在工作流中添加 build-args：
```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    build-args: |
      BUILD_DATE=${{ steps.meta.outputs.created }}
      VCS_REF=${{ github.sha }}
```

### 3. 安全扫描
添加镜像安全扫描步骤：
```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ steps.meta.outputs.tags }}
    format: 'sarif'
    output: 'trivy-results.sarif'
```

## Fork 用户指南

如果你 fork 了这个项目，只需要：

1. 在你的仓库中设置 `DOCKER_HUB_USERNAME` 和 `DOCKER_HUB_ACCESS_TOKEN` secrets
2. 推送代码到 main 分支或创建 release 标签
3. GitHub Actions 会自动构建并推送镜像到你的 Docker Hub 账号

镜像将发布到：
- `docker.io/你的用户名/baojimi-lite`
- `ghcr.io/你的用户名/你的仓库名`