# GitHub Actions Docker 镜像打包指南

本指南将详细介绍如何使用 GitHub Actions 自动构建和发布 Docker 镜像到 GitHub Container Registry (GHCR)。

## 🎯 特色优势

- ✅ **零配置**：无需创建外部账号或设置密钥
- ✅ **Fork 友好**：其他用户 fork 后立即可用
- ✅ **完全免费**：使用 GitHub 自带的容器注册表
- ✅ **自动化**：推送代码即自动构建镜像

## 前置准备

### 启用 GitHub Container Registry
GitHub Container Registry 对所有用户免费开放，无需额外配置。只需确保：

1. 你的仓库是公开的，或者你有 GitHub Pro/Team/Enterprise 账号
2. 仓库已启用 Actions（默认启用）

## 🚀 使用方法

### 1. 自动构建（推荐）
项目已包含 GitHub Actions 工作流文件，无需任何配置：

- **推送到 main 分支**：自动构建 `latest` 标签
- **创建 release 标签**：自动构建版本标签
- **Pull Request**：构建测试（不推送）

### 2. 手动触发
在 GitHub 仓库页面：
1. 点击 "Actions" 标签
2. 选择 "Build and Push Docker Image" 工作流
3. 点击 "Run workflow" 按钮

### 3. 工作流说明

#### 触发条件
- `push` 到 `main` 分支
- 创建以 `v` 开头的标签（如 `v1.0.0`）
- 对 `main` 分支的 Pull Request
- 手动触发

#### 构建目标
- **GitHub Container Registry**: `ghcr.io/你的用户名/仓库名`

#### 支持平台
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64)

#### 工作流文件内容
```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

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

    - name: Log in to Container Registry
      if: github.event_name != 'pull_request'
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
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

## 📦 版本管理

推荐使用语义化版本标签：
```bash
git tag v1.0.0
git push origin v1.0.0
```

这会自动创建以下镜像标签：
- `latest` (main 分支)
- `v1.0.0` (完整版本)
- `v1.0` (次版本)
- `v1` (主版本)

## 🐳 镜像使用

### 拉取镜像
```bash
# 拉取最新版本
docker pull ghcr.io/你的用户名/仓库名:latest

# 拉取指定版本
docker pull ghcr.io/你的用户名/仓库名:v1.0.0
```

### 运行容器
```bash
docker run -d \
  --name baojimi-lite \
  -p 7860:7860 \
  -e GEMINI_API_KEYS="your_api_key1,your_api_key2" \
  -e LAOPOBAO_AUTH="your_auth_key" \
  -e MAX_TRY=3 \
  ghcr.io/你的用户名/仓库名:latest
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

## 🍴 Fork 用户指南

如果你 fork 了这个项目，**无需任何配置**即可使用：

### 立即可用
1. Fork 这个仓库到你的 GitHub 账号
2. 推送代码到 main 分支或创建 release 标签
3. GitHub Actions 会自动构建并推送镜像

### 镜像地址
你的镜像将自动发布到：
- `ghcr.io/你的用户名/你的仓库名:latest`
- `ghcr.io/你的用户名/你的仓库名:v1.0.0` (如果创建了标签)

### 使用示例
```bash
# 如果你的 GitHub 用户名是 john，仓库名是 baojimi-lite
docker pull ghcr.io/john/baojimi-lite:latest
docker run -d -p 7860:7860 \
  -e GEMINI_API_KEYS="your_keys" \
  ghcr.io/john/baojimi-lite:latest
```