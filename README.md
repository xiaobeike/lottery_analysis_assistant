# 🎯 彩票数据分析与推荐系统

基于AI的彩票数据分析系统，支持双色球和大乐透的智能分析与推荐。通过企业微信自动推送分析结果。

## ✨ 功能特点

- 🤖 **AI智能分析**：使用Google Gemini和DeepSeek进行深度数据分析
- 📊 **传统统计**：热号、冷号、奇偶比、大小比等多维度分析
- 💡 **智能推荐**：基于分析结果生成5组推荐号码（3组推荐+2组参考）
- 🔄 **自动运行**：GitHub Actions定时自动执行（每周二四日/一三六 12:00）
- 📱 **微信推送**：通过企业微信机器人发送分析结果
- 💾 **本地数据**：爬取并保存最近30期历史数据

## 📋 支持的彩票

| 彩票类型 | 开奖时间 | 分析时间 |
|---------|---------|---------|
| 双色球 | 周二、四、日 21:15 | 当天12:00 |
| 大乐透 | 周一、三、六 21:25 | 当天12:00 |

## 🚀 快速开始

### 1. Fork本项目（推荐）

1. 点击GitHub右上角 **Fork** 按钮
2. 克隆到本地：
   ```bash
   git clone https://github.com/你的用户名/lottery_analysis_assistant.git
   cd lottery_analysis_assistant
   ```

### 2. 设置环境变量（任选一种方式）

#### 方式一：本地开发（使用.env文件）
```bash
cp .env.example .env
# 编辑.env文件，填入你的密钥
```

#### 方式二：GitHub Actions自动运行（推荐）
在仓库 **Settings → Secrets and variables → Actions** 中添加：

| Secret Name | Value |
|------------|-------|
| `WECHAT_WEBHOOK_URL` | 企业微信机器人Webhook URL |
| `GEMINI_API_KEY` | Google Gemini API密钥 |
| `DEEPSEEK_API_KEY` | DeepSeek API密钥（可选） |

### 3. 安装依赖并运行
```bash
pip install -r requirements.txt

# 首次运行会自动从 500.com 爬取最近30期历史数据
python src/main.py --lottery ssq --test   # 测试运行（不发送消息）
python src/main.py --lottery ssq          # 实际运行（发送消息到企业微信）
python src/main.py --lottery dlt          # 分析大乐透
```

### 4. 数据来源
- 数据来源：500彩票网 (kaijiang.500.com)
- 首次运行自动获取最近30期历史数据
- 后续运行只获取最新一期，保持30条历史记录
- 带请求延迟和重试机制，避免被封

## 🔧 配置说明

### 环境变量

系统通过以下环境变量获取配置：

| 环境变量 | 说明 | 必需 |
|---------|------|------|
| `WECHAT_WEBHOOK_URL` | 企业微信机器人Webhook URL | ✅ |
| `GEMINI_API_KEY` | Google Gemini API密钥 | ✅ |
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | ❌（可选） |

### 本地开发

创建 `.env` 文件：
```bash
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
GEMINI_API_KEY=your_gemini_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
```

### GitHub Actions

在仓库Secrets中设置以上环境变量，系统会自动在开奖当天12:00运行。

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
🤖 AI智能分析 - 双色球第2026008期

📅 上一期开奖信息：
- 期号：2026008
- 开奖号码：6 9 16 27 31 33 | 10

📊 传统统计分析：
- 热号TOP10：13, 5, 2, 9, 30...
- 冷号TOP10：21, 25, 29, 11...
- 平均奇偶比：3.0:3.0
- 平均大小比：2.7:3.3

💡 AI智能推荐
🎯 最推荐（按评分排序）：
⭐⭐⭐ 第2组：1 2 13 22 23 24 | 15
  推荐理由：热号组合，奇偶均衡...
📌 参考推荐：
⭐ 第1组：13 17 22 29 30 31 | 16
  推荐理由：热号组合，含连号...

📋 推荐号码汇总
推荐   号码                           评分
----------------------------------------
[推荐]第 2组  1 2 13 22 23 24 | 15   100.0
...

🎯 最推荐：第 2, 4, 5 组
```

## 📁 项目结构

```
lottery_analysis_assistant/
├── .github/
│   └── workflows/
│       └── lottery-analysis.yml    # GitHub Actions定时任务
├── src/
│   ├── ai/                         # AI分析模块
│   │   ├── analyzer.py
│   │   ├── gemini_client.py
│   │   └── deepseek_client.py
│   ├── analysis/                   # 数据分析
│   │   └── traditional/
│   │       ├── ssq_analyzer.py
│   │       └── dlt_analyzer.py
│   ├── data/                       # 数据获取
│   │   ├── spider.py                # 500.com 数据爬虫
│   │   └── fetcher.py               # 数据获取器
│   ├── recommendation/             # 推荐生成
│   │   └── generator.py
│   ├── notification/               # 企业微信推送
│   │   ├── wechat_bot.py
│   │   └── message_builder.py
│   ├── config/                     # 配置模块
│   │   └── settings.py
│   └── main.py                     # 主程序入口
├── .env.example                    # 环境变量模板
├── requirements.txt                # Python依赖
└── README.md                       # 项目说明
```

## ⚠️ 免责声明

### 数据来源与版权声明

- 本项目开源免费，仅供学习和研究使用
- 开奖数据来源于公开网站 (500.com)，本项目不存储、拥有或原始生成任何彩票数据
- 所有数据版权归彩票发行机构所有，本项目不主张任何版权
- 如数据来源方认为侵权，请联系删除：xiaobeike007@gmail.com

### 分析结果声明

- 彩票开奖具有**完全随机性**，历史数据无法预测未来结果
- 本项目的分析算法、推荐号码、AI建议**仅供参考**，不构成任何购彩建议
- 任何以本项目分析结果进行购彩的行为，风险自负
- 本项目不对任何因使用本项目而造成的直接或间接损失承担责任

### 用户承诺

使用本项目即表示您已阅读并同意：

1. 彩票具有赌博性质，请**理性购彩**
2. 请**量力而行**，投入金额应在个人承受范围内
3. **禁止未满18岁**人士购买彩票
4. 如有购彩成瘾问题，请寻求专业帮助

**如不同意以上条款，请立即停止使用本项目。**

## 📝 License

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！
