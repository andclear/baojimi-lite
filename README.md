---
title: baojimi-lite
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
secrets:
  - GEMINI_API_KEYS
  - LAOPOBAO_AUTH
  - MAX_TRY
---

# baojimi-lite

年轻人的第一个gemini代理轮询服务。

**特点:**
- 兼容 OpenAI API (`/v1/chat/completions`, `/v1/models`)
- 支持流式和非流式响应
- 自动轮询和重试 Gemini API Keys
- 提供简单的状态监控和 Key 检测页面

**API 端点:**
- 代理接口: `https://[your-space-name].hf.space/v1/chat/completions`
- 状态页面: `https://[your-space-name].hf.space/`

## ⚠️ 使用条款
- **本项目为个人学习和实验用途，严禁用于任何商业或非法活动。**
- **这是一个私有项目，请勿公开分享访问地址和密钥。**
- **所有通过本服务发起的 API 请求，其内容和后果由调用者自行承担。**