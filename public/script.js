document.addEventListener('DOMContentLoaded', () => {
    const statusBox = document.getElementById('status-box');
    const keyCountEl = document.getElementById('key-count');
    const checkKeysBtn = document.getElementById('check-keys-btn');
    const authKeyInput = document.getElementById('auth-key');
    const loader = document.getElementById('loader');
    const resultsEl = document.getElementById('results');
    const copyInvalidBtn = document.getElementById('copy-invalid');
    const refreshLogsBtn = document.getElementById('refreshLogs');
    const errorModal = document.getElementById('errorModal');
    const closeModalBtn = document.querySelector('.close-btn');
    const modalErrorText = document.getElementById('modal-error-text');
    const copyErrorBtn = document.getElementById('copy-error-btn');
    const askAiBtn = document.getElementById('ask-ai-btn');

    let invalidKeys = [];

    let logErrors = {}; // Store full error messages by log ID
    let displayedLogIds = new Set(); // Keep track of displayed log IDs

    async function fetchStatus() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) throw new Error('网络响应错误');
            const data = await response.json();
          
            statusBox.textContent = `服务状态正常 (running)`;
            statusBox.className = 'status ok';
            keyCountEl.textContent = data.key_count;
        } catch (error) {
            statusBox.textContent = `服务状态异常: ${error.message}`;
            statusBox.className = 'status error';
        }
    }

    function fetchLogs() {
        fetch('/api/logs')
        .then(response => {
            if (response.status === 401) {
                throw new Error('授权码无效或未提供');
            }
            if (!response.ok) {
                throw new Error('获取日志失败');
            }
            return response.json();
        })
        .then(logs => {
            const logsContainer = document.getElementById('logsContainer');
            if (!logsContainer) return;
            const isFirstLoad = displayedLogIds.size === 0;
            if (isFirstLoad && logs.length === 0) {
                logsContainer.innerHTML = '<p>暂无日志</p>';
                return;
            } else if (isFirstLoad) {
                logsContainer.innerHTML = ''; // Clear only on first load
            }
            logs.reverse().forEach(log => { // Reverse to prepend new logs at the top
                if (displayedLogIds.has(log.id)) return; // Skip already displayed logs
                const card = document.createElement('div');
                card.className = 'log-card';
                const statusClass = log.status === 'success' ? 'status-success' : 'status-failed';

                let errorDisplay = '';
                if (log.error_info) {
                    logErrors[log.id] = log.error_info; // Store the full error message
                    const displayError = log.error_info.split('\n')[0]; // Show only the first line in the log card
                    errorDisplay = `<p class="log-error"><strong>错误:</strong> ${displayError}...</p>`;
                    if (log.status === 'failed') {
                         errorDisplay += `<button class="check-error-btn" data-log-id="${log.id}">查错</button>`;
                    }
                }

                card.innerHTML = `
                    <p class="log-meta"><strong>时间:</strong> ${log.timestamp}</p>
                    <p><strong>模型:</strong> ${log.model}</p>
                    <p><strong>状态:</strong> <span class="${statusClass}">${log.status}</span></p>
                    <p><strong>Key:</strong> ${log.key_used || 'N/A'}</p>
                    <p><strong>流式:</strong> ${log.stream ? '是' : '否'}</p>
                    ${errorDisplay}
                `;
                logsContainer.insertBefore(card, logsContainer.firstChild);
                displayedLogIds.add(log.id);
            });

            document.querySelectorAll('.check-error-btn').forEach(button => {
                button.addEventListener('click', (e) => {
                    const logId = e.target.getAttribute('data-log-id');
                    const errorText = logErrors[logId] || '错误详情未找到。';
                    modalErrorText.innerText = errorText;
                    errorModal.style.display = 'block';
                });
            });
        })
        .catch(error => {
            console.error('获取日志时出错:', error);
            const logsContainer = document.getElementById('logsContainer');
            if (logsContainer) {
                logsContainer.innerHTML = `<p style="color: red;">加载日志失败: ${error.message}，请检查授权码或网络连接。</p>`;
            }
        });
    }

    if (refreshLogsBtn) {
        refreshLogsBtn.addEventListener('click', fetchLogs);
    }

    // Initial fetch and periodic refresh
    fetchLogs();
    setInterval(fetchLogs, 5000); // Refresh every 5 seconds

    checkKeysBtn.addEventListener('click', async () => {
        const authKey = authKeyInput.value;
        const headers = {};
        if (authKey) {
            headers['Authorization'] = `Bearer ${authKey}`;
        }

        loader.style.display = 'inline-block';
        checkKeysBtn.disabled = true;
        resultsEl.innerHTML = '<p>正在检测中，请稍候...</p>';
        copyInvalidBtn.style.display = 'none';
        invalidKeys = [];

        try {
            const response = await fetch('/api/check-keys', {
                method: 'POST',
                headers: headers
            });

            if (response.status === 401) {
                throw new Error('认证失败，请检查你的 LAOPOBAO_AUTH 密钥。');
            }
             if (response.status === 429) {
                throw new Error('请求过于频繁，请稍后再试。');
            }
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`检测失败: ${errorData.detail || response.statusText}`);
            }

            const data = await response.json();
            invalidKeys = data.invalid_keys;
          
            let resultsHTML = `<h3>检测完成</h3>`;
            resultsHTML += `<p>✅ 有效 Key 数量: ${data.valid_keys.length}</p>`;
            resultsHTML += `<p>❌ 无效 Key 数量: ${data.invalid_keys.length}</p>`;
          
            if (data.invalid_keys.length > 0) {
                resultsHTML += `<h4>已失效的 Key:</h4><ul>`;
                data.invalid_keys.forEach(key => {
                    resultsHTML += `<li>${key.substring(0, 4)}...${key.substring(key.length - 4)}</li>`;
                });
                resultsHTML += `</ul>`;
                copyInvalidBtn.style.display = 'block';
            } else {
                resultsHTML += `<p>所有 Key 均有效！</p>`;
            }

            resultsEl.innerHTML = resultsHTML;

        } catch (error) {
            resultsEl.innerHTML = `<p style="color: red;">发生错误: ${error.message}</p>`;
        } finally {
            loader.style.display = 'none';
            checkKeysBtn.disabled = false;
        }
    });

    copyInvalidBtn.addEventListener('click', () => {
        if (invalidKeys.length > 0) {
            navigator.clipboard.writeText(invalidKeys.join(','))
                .then(() => alert('已失效的 Key 已复制到剪贴板！'))
                .catch(err => alert('复制失败: ' + err));
        }
    });

    closeModalBtn.addEventListener('click', () => {
        errorModal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target == errorModal) {
            errorModal.style.display = 'none';
        }
    });

    copyErrorBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(modalErrorText.innerText).then(() => {
            copyErrorBtn.textContent = '已复制';
            setTimeout(() => { copyErrorBtn.textContent = '一键复制错误信息'; }, 2000);
        }).catch(err => {
            copyErrorBtn.textContent = '复制失败';
            setTimeout(() => { copyErrorBtn.textContent = '一键复制错误信息'; }, 2000);
        });
    });

    askAiBtn.addEventListener('click', () => {
        const query = `我在使用gemini API调用gemini模型对话时，遇到了错误，错误内容如下：\n\n---\n${modalErrorText.innerText}\n---\n\n请帮我分析一下可能的原因和解决方法。`;
        navigator.clipboard.writeText(query).then(() => {
            askAiBtn.textContent = '正在前往当贝AI';
            window.open('https://ai.dangbei.com/', '_blank');
            setTimeout(() => { askAiBtn.textContent = '复制错误并问AI'; }, 2000);
        }).catch(err => {
            askAiBtn.textContent = '复制失败';
            setTimeout(() => { askAiBtn.textContent = '复制错误并问AI'; }, 2000);
        });
    });

    fetchStatus();
    loader.style.display = 'none';
});