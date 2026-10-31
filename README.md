# 市场行情概率测算器

基于几何布朗运动（GBM）/ Black-Scholes 假设的专业市场概率测算工具。支持单目标价与价格区间两种模式，同时计算风险中性概率与真实世界概率。

## 功能

- 单目标价概率（高于/低于目标价）
- 价格区间概率
- 风险中性概率（使用无风险利率）
- 真实世界概率（使用预期收益率）
- 深色专业界面

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`

## 部署方式

### 1. Streamlit Community Cloud（推荐，免费）

1. 将本项目推送到 GitHub 仓库
2. 访问 [share.streamlit.io](https://share.streamlit.io)
3. 连接 GitHub，选择仓库，主文件填 `app.py`
4. 点击 Deploy

### 2. Render / Railway

- 新建 Web Service
- 构建命令：`pip install -r requirements.txt`
- 启动命令：`streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

### 3. Docker（可选）

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 参数说明

| 参数 | 说明 |
|------|------|
| 当前价格 | 标的当前市价 |
| 目标价格 / 区间 | 要测算的价格水平 |
| 交易日 | 未来天数（一年约 252 个交易日） |
| 年化波动率 | 历史波动率或期权隐含波动率 |
| 无风险利率 | 用于风险中性概率 |
| 预期收益率 | 用于真实世界概率 |
| 股息率 | 股票股息或加密货币资金成本 |

## 免责声明

本工具仅供学习与研究使用，不构成任何投资建议。市场有风险，决策需谨慎。模型基于对数正态假设，真实市场存在肥尾与跳跃。
