# GitHub 热门项目中文周报

每周六北京时间 **09:17** 自动获取 GitHub Trending 周榜前十，读取仓库公开元数据和 README，通过 GitHub Models 免费额度生成中文深度分析，发布到 GitHub Pages，并在页面部署成功后向企业微信群推送摘要与链接。

每期报告分别保存在 `docs/reports/YYYY-MM-DD.html`，原始快照保存在 `data/YYYY-MM-DD.json`，因此历史内容会随 Git 仓库永久留存。`docs/index.html` 是自动更新的历史归档首页。

## 一次性配置

### 1. 创建 GitHub 仓库

在 GitHub 新建一个仓库，将本项目全部文件推送到默认分支。公开仓库最省事；如果使用私有仓库，请确认你的 GitHub 套餐支持相应的 Pages 和 Actions 用量。

在仓库的 **Settings → Pages → Build and deployment → Source** 中选择 **GitHub Actions**。

随后进入 **Settings → Actions → General → Workflow permissions**，选择 **Read and write permissions**。工作流需要把每周生成的历史报告提交回仓库。

如果默认分支启用了“禁止直接推送”的分支保护，请为 GitHub Actions 建立允许写入的例外，或取消该规则；否则报告能够生成，但历史提交步骤会失败。

### 2. 创建企业微信群机器人

1. 在企业微信中新建或打开一个内部群聊。
2. 打开群设置，选择 **群机器人 → 添加机器人**。
3. 为机器人设置名称和头像，例如“GitHub 周报”。
4. 复制机器人提供的 Webhook 地址。它通常以 `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=` 开头。
5. 不要把 Webhook 放进代码、Issue、聊天截图或公开日志；拿到该地址的人可以向群里发消息。

在 GitHub 仓库打开 **Settings → Secrets and variables → Actions → Secrets**，新增：

| Secret | 内容 |
|---|---|
| `WECOM_WEBHOOK_URL` | 企业微信群机器人的完整 Webhook 地址 |

模型调用使用 GitHub Actions 自动生成的 `GITHUB_TOKEN`，不需要创建或保存 OpenAI API Key。工作流已经声明 `models: read` 权限。

### 3. 配置可选变量

在 **Settings → Secrets and variables → Actions → Variables** 中可以新增：

| Variable | 默认值 | 用途 |
|---|---|---|
| `SITE_URL` | 自动按仓库名推算 | Pages 首页完整地址，不含末尾 `/`；自定义域名时必须填写 |
| `GITHUB_MODELS_MODEL` | `openai/gpt-4.1-mini` | GitHub Models 目录中的分析模型 |

默认模型侧重免费额度、中文能力和分析质量的平衡。模型 ID 必须使用 GitHub Models 目录中的 `{发布者}/{模型名}` 格式。GitHub Models 的免费使用有速率和 Token 限制；没有主动启用付费使用时，额度耗尽会导致任务失败，不会自动产生模型费用。

## 首次运行与验收

1. 打开仓库 **Actions → Weekly GitHub Report**。
2. 点击 **Run workflow** 手动执行一次，无需等待周六。
3. 等待所有步骤变绿，尤其是 `Deploy GitHub Pages` 和 `Push to WeCom after deployment`。
4. 在 **Settings → Pages** 查看网站地址。
5. 确认企业微信群收到前三名摘要和“查看完整分析”链接。

定时表达式是 `17 1 * * 6`。GitHub Actions 使用 UTC，对应北京时间每周六 09:17。平台繁忙时定时任务可能有少量延迟。

## 本地验证

Python 3.11 以上版本：

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

真实生成需要一个具有 `models: read` 权限的 GitHub Personal Access Token。本地 Token 只应放在环境变量中，不要写入文件：

```powershell
$env:GITHUB_TOKEN = "你的 GitHub Token"
$env:WECOM_WEBHOOK_URL = "你的企业微信机器人地址"
$env:SITE_URL = "https://你的用户名.github.io/仓库名"
python run.py
```

只生成、不发送企业微信消息：

```powershell
python run.py --no-push
```

## 数据口径与边界

- 排名取 GitHub Trending 页面 `since=weekly` 的顺序，周增长数取页面显示的 `stars this week`。
- GitHub 没有为 Trending 提供正式 REST API；页面结构如果发生重大变化，任务会明确失败，而不会用不等价的“总 Star 排名”静默替代。
- 总 Star、Fork、语言、许可证、更新时间和 README 通过 GitHub API补充。
- 每个项目单独调用一次 GitHub Models，并限制 README 输入长度，以适配免费额度和降低单次上下文大小。
- AI 分析只依据抓取到的公开材料，网页会提示读者核验安全性、许可证及生产可用性。
- 同一天重复运行会覆盖当天报告，不会制造重复归档；企业微信仍会再次收到消息。

## 常见问题

**Pages 链接打开 404**：确认 Pages 的 Source 已选择 GitHub Actions，并检查部署步骤是否成功。项目仓库默认地址为 `https://用户名.github.io/仓库名`。

**企业微信返回错误**：重新复制完整 Webhook，确认机器人仍在群内；如果机器人配置了安全规则，需确保消息内容满足关键词等要求。

**模型调用失败**：检查工作流是否包含 `models: read` 权限、所选模型是否仍在 GitHub Models 目录中，以及账户免费额度是否已用完。未启用付费使用时，超出免费额度只会让任务失败。

**定时任务长期不执行**：GitHub 可能停用长期无活动仓库的定时工作流。进入 Actions 页面重新启用并手动运行一次即可。
