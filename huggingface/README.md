---
title: Baojimi Lite
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
---

# 报吉米 Lite - Hugging Face Spaces 部署版

这是一个基于 Gemini API 的智能对话助手，专为 Hugging Face Spaces 优化部署。

## 功能特性

- 🤖 基于 Google Gemini API 的智能对话
- 🔐 支持访问密钥认证
- 📱 响应式 Web 界面
- 📊 实时调用日志监控
- 🔄 自动重试机制
- 🎨 现代化 UI 设计

## 环境变量配置

在 Hugging Face Spaces 的 Settings 中配置以下环境变量：

### 必需变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `GEMINI_API_KEYS` | Gemini API 密钥，多个用逗号分隔 | `key1,key2,key3` |

### 可选变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `LAOPOBAO_AUTH` | 无 | 访问密钥，设置后需要输入密钥才能使用 |
| `MAX_TRY` | 3 | API 调用失败时的最大重试次数 |

## 部署步骤

### 1. 创建 Hugging Face Space

1. 访问 [Hugging Face Spaces](https://huggingface.co/spaces)
2. 点击 "Create new Space"
3. 填写 Space 信息：
   - **Space name**: `baojimi-lite`
   - **License**: MIT
   - **SDK**: Docker
   - **Hardware**: CPU basic (免费) 或根据需要选择

### 2. 上传文件

只需要将以下 2 个文件上传到你的 Space：

```
├── Dockerfile              # 使用 huggingface/Dockerfile
└── README.md               # 使用 huggingface/README.md
```

**注意**：Dockerfile 会自动拉取预构建的镜像 `ghcr.io/andclear/baojimi-lite:latest`，无需上传其他代码文件。

### 3. 配置环境变量

在 Space 的 Settings 页面添加环境变量：

1. 点击 Space 页面右上角的 "Settings"
2. 在 "Repository secrets" 部分添加：
   - `GEMINI_API_KEYS`: 你的 Gemini API 密钥
   - `LAOPOBAO_AUTH`: （可选）访问密钥
   - `MAX_TRY`: （可选）重试次数，默认为 3

### 4. 启动部署

1. 保存设置后，Space 会自动开始构建
2. 构建完成后，你的应用将在 `https://你的用户名-baojimi-lite.hf.space` 可用

## 获取 Gemini API 密钥

1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 登录你的 Google 账号
3. 点击 "Create API Key"
4. 复制生成的 API 密钥

## 使用说明

### 基本使用

1. 打开部署的 Space 链接
2. 如果设置了 `LAOPOBAO_AUTH`，需要先输入访问密钥
3. 在对话框中输入你的问题
4. 点击发送或按 Enter 键获得回复

### 功能说明

- **智能对话**: 支持多轮对话，AI 会记住上下文
- **日志监控**: 右侧面板显示实时调用日志
- **错误处理**: 自动重试失败的请求，显示详细错误信息
- **响应式设计**: 支持桌面和移动设备

## 故障排除

### 1. 构建失败

- 检查 Dockerfile 语法
- 确认所有文件都已正确上传
- 查看构建日志获取详细错误信息

### 2. 应用无法启动

- 检查环境变量配置
- 确认 `GEMINI_API_KEYS` 已正确设置
- 验证 API 密钥的有效性

### 3. API 调用失败

- 检查 Gemini API 密钥是否有效
- 确认 API 配额是否充足
- 查看应用日志获取详细错误信息

### 4. 访问被拒绝

- 如果设置了 `LAOPOBAO_AUTH`，确认输入的密钥正确
- 检查 Space 的可见性设置

## 性能优化

### 1. 硬件升级

如果遇到性能问题，可以考虑升级 Space 硬件：
- CPU basic → CPU enhanced
- 添加 GPU 支持（如需要）

### 2. API 密钥轮换

配置多个 Gemini API 密钥可以：
- 提高请求限制
- 增加服务可靠性
- 分散 API 配额使用

### 3. 缓存优化

应用已内置对话历史缓存，无需额外配置。

## 安全注意事项

1. **API 密钥安全**: 
   - 不要在代码中硬编码 API 密钥
   - 使用 Hugging Face Secrets 管理敏感信息

2. **访问控制**:
   - 建议设置 `LAOPOBAO_AUTH` 限制访问
   - 定期更换访问密钥

3. **监控使用**:
   - 定期检查 API 使用量
   - 监控异常访问模式

## 技术栈

- **后端**: FastAPI + Python 3.10
- **前端**: 原生 HTML/CSS/JavaScript
- **AI 模型**: Google Gemini API
- **部署**: Hugging Face Spaces + Docker

## 许可证

MIT License - 详见 LICENSE 文件

## 🍴 Fork 用户部署指南

如果你 fork 了这个项目并想部署到 Hugging Face Spaces：

### 1. 修改 Dockerfile
将 `huggingface/Dockerfile` 中的镜像地址改为你的：

```dockerfile
# 将这行
FROM ghcr.io/andclear/baojimi-lite:latest

# 改为你的镜像地址
FROM ghcr.io/你的用户名/你的仓库名:latest
```

### 2. 确保镜像已构建
- 推送代码到你的 GitHub 仓库
- 等待 GitHub Actions 自动构建镜像
- 在 GitHub 仓库的 Packages 页面确认镜像已发布

### 3. 部署到 Hugging Face
- 按照上述部署步骤操作
- 使用修改后的 Dockerfile 和 README.md

## 支持

如有问题，请在原项目仓库提交 Issue：
[GitHub Issues](https://github.com/andclear/baojimi-lite/issues)