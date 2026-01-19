# 🎯 彩票数据分析与推荐系统

基于AI的彩票数据分析系统，支持双色球和大乐透的智能分析与推荐。

## ✨ 功能特点

- 🤖 **AI智能分析**：使用Google Gemini和DeepSeek进行深度数据分析
- 📊 **传统统计**：热号、冷号、奇偶比、大小比等多维度分析
- 💡 **智能推荐**：基于分析结果生成5组推荐号码
- 🔄 **自动运行**：GitHub Actions定时自动执行
- 📱 **微信推送**：通过企业微信机器人发送分析结果
- 💾 **数据缓存**：智能缓存减少API调用

## 📋 支持的彩票

| 彩票类型 | 开奖时间 | 分析时间 |
|---------|---------|---------|
| 双色球 | 周二、四、日 21:15 | 当天12:00 |
| 大乐透 | 周一、三、六 21:25 | 当天12:00 |

## 🚀 快速开始（Fork方法）

### 方法一：Fork后使用（推荐⭐）

1. **Fork本项目**
   - 点击右上角 **Fork** 按钮
   - 选择你的GitHub账号

2. **克隆到本地**
   ```bash
   git clone https://github.com/你的用户名/lottery_analysis_assistant.git
   cd lottery_analysis_assistant
   ```

3. **创建配置文件**
   ```bash
   cp config/config.example.yaml config/config.yaml
   ```

4. **填入你的密钥**
   编辑 `config/config.yaml`，替换以下内容：
   ```yaml
   ai:
     providers:
       gemini:
         api_key: "YOUR_GEMINI_API_KEY"  # 填入你的Gemini API Key
       deepseek:
         api_key: "YOUR_DEEPSEEK_API_KEY"  # 填入你的DeepSeek API Key
   
   notification:
     wechat:
       webhook_url: "YOUR_WECHAT_WEBHOOK_URL"  # 填入你的企业微信Webhook URL
   ```

5. **安装依赖并测试**
   ```bash
   pip install -r requirements.txt
   python src/main.py --lottery ssq --test  # 测试模式
   ```

6. **设置GitHub Secrets**（可选，用于自动化运行）
   - 在仓库 Settings → Secrets and variables → Actions 中添加：
     - `WECHAT_WEBHOOK_URL`
     - `GEMINI_API_KEY`
     - `DEEPSEEK_API_KEY`

### 方法二：从头开始

按照以下步骤操作：
```bash
git clone https://github.com/你的用户名/lottery_analysis_assistant.git
cd lottery_analysis_assistant
cp config/config.example.yaml config/config.yaml
# 编辑config/config.yaml填入密钥
pip install -r requirements.txt
python src/main.py --lottery ssq
```

---

## 📋 配置文件说明

- `config/config.example.yaml` - 配置模板（已提交到GitHub）
- `config/config.yaml` - 实际配置文件（已加入.gitignore，不会提交）
- `.env` - 环境变量文件（已加入.gitignore）

**注意**：敏感信息不会提交到GitHub，保护你的API密钥安全！

---

| Secret Name | Description |
|------------|-------------|
| `WECHAT_WEBHOOK_URL` | 企业微信机器人Webhook URL |
| `GEMINI_API_KEY` | Google Gemini API密钥 |
| `DEEPSEEK_API_KEY` | DeepSeek API密钥（可选） |

### 3. 自动运行

系统会自动在以下时间运行：
- **双色球**：每周二、四、日 中午12:00（北京时间）
- **大乐透**：每周一、三、六 中午12:00（北京时间）

### 4. 手动触发

在GitHub Actions页面可以手动触发运行。

## 📊 分析维度

### 传统统计分析
- 热号/冷号频率分析
- 奇偶比例趋势
- 大小号码分布
- 连号模式分析
- 和值统计
- 遗漏值分析

### AI深度分析
- 模式识别
- 趋势预测
- 综合推荐理由

## 💡 输出示例

```
🤖 AI智能分析 - 双色球第2025019期

📅 上一期开奖信息：
- 期号：2025018期
- 开奖号码：08 15 22 27 29 33 | 11
- 开奖时间：2025-01-18 21:15

📊 传统统计分析：
- 热号TOP10：08, 15, 22, 29, 33, ...
- 冷号TOP10：03, 07, 14, 19, 25, ...
- 平均奇偶比：3:3
- 平均大小比：2:4

💡 AI智能推荐（5组）：
⭐⭐⭐ 第1组：08 15 22 27 29 33 | 11
  推荐理由：热号组合，符合近期大小交替模式

⭐⭐ 第2组：05 12 18 24 30 31 | 06
  推荐理由：平衡组合，包含上升趋势的偶数号码

...
```

## 📁 项目结构

```
lottery-analysis/
├── .github/
│   └── workflows/
│       └── lottery-analysis.yml    # GitHub Actions配置
├── src/
│   ├── config/                     # 配置模块
│   ├── data/                       # 数据获取和缓存
│   ├── analysis/                   # 数据分析
│   │   └── traditional/            # 传统统计分析
│   ├── recommendation/             # 推荐生成
│   ├── notification/               # 企业微信通知
│   ├── ai/                         # AI分析
│   └── main.py                     # 主程序入口
├── config/
│   └── config.yaml                 # 配置文件
├── data/
│   └── cache/                      # 数据缓存
├── logs/                           # 日志文件
├── requirements.txt                # Python依赖
└── README.md                       # 项目说明
```

## ⚠️ 免责声明

- 本分析仅供参考，不构成任何购彩建议
- 彩票具有随机性，请理性购彩
- 请量力而行，适度投注

## 📝 License

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！
