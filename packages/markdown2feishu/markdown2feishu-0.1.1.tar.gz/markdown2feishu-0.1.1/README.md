# markdown2feishu

Convert Markdown to Feishu/Lark documents.

## Features

- **文档推送**: 将 Markdown 转换为飞书云文档
- **群消息**: 通过 Webhook 发送消息到飞书群聊
- **丰富语法**: 支持标题、列表、表格、代码块、公式等

## Installation

```bash
pip install markdown2feishu

# With CLI support
pip install markdown2feishu[cli]
```

## Quick Start

### Python API

```python
import asyncio
from markdown2feishu import FeishuClient

async def main():
    async with FeishuClient() as client:
        # 方式一: 推送 Markdown 文件
        doc = await client.push_file("README.md")

        # 方式二: 推送 Markdown 字符串
        doc = await client.push_markdown(
            content="# Hello World\n\nThis is **bold** text.",
            title="My Document"
        )

        # 指定目标文件夹
        doc = await client.push_file(
            "README.md",
            title="自定义标题",  # 可选，默认使用文件名
            folder_token="xxxxx"
        )

        print(f"Document URL: {doc.url}")

asyncio.run(main())

# 直接传入凭据 (不使用环境变量)
async def with_credentials():
    async with FeishuClient(
        app_id="cli_xxxxx",
        app_secret="xxxxx",
        folder_token="xxxxx",  # 可选
    ) as client:
        doc = await client.push_file("README.md")
        print(f"Document URL: {doc.url}")
```

### CLI

```bash
# 设置凭据
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"

# 推送文件到飞书文档
feishu-md push README.md

# 推送到指定文件夹
feishu-md push README.md --folder <folder_token>

# 发送到群聊 (需配置 webhook_url)
feishu-md push README.md --webhook
```

## Configuration

凭据可通过以下方式提供 (优先级从高到低):

1. **代码参数**: 直接传入 `FeishuClient(app_id=..., app_secret=...)`
2. **环境变量**: `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_WEBHOOK_URL`, `FEISHU_FOLDER_TOKEN`
3. **配置文件**: `.feishu.toml` (当前目录) 或 `~/.feishu.toml`

### 配置文件示例

```toml
[feishu]
app_id = "cli_xxxxx"
app_secret = "xxxxx"

# 可选: 默认文档保存文件夹
folder_token = "xxxxx"

# 可选: 群机器人 Webhook URL
webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"
```

### 获取凭据

1. **App ID / Secret**: [飞书开放平台](https://open.feishu.cn) → 创建应用 → 凭证与基础信息
2. **Folder Token**: 打开飞书云文档文件夹，URL 中 `/folder/` 后的字符串
3. **Webhook URL**: 飞书群 → 设置 → 群机器人 → 添加自定义机器人

## Supported Markdown Syntax

### 基础格式

| 语法 | 示例 | 说明 |
|------|------|------|
| 标题 | `# H1` `## H2` ... | 支持 1-9 级 |
| 粗体 | `**text**` | |
| 斜体 | `*text*` 或 `_text_` | |
| 删除线 | `~~text~~` | |
| 行内代码 | `` `code` `` | |
| 链接 | `[text](url)` | |

### 块级元素

| 语法 | 说明 |
|------|------|
| 代码块 | ` ```python ` 支持语法高亮 (75种语言) |
| 引用 | `> quote` |
| 无序列表 | `- item` |
| 有序列表 | `1. item` |
| 表格 | 标准 Markdown 表格 |
| 分割线 | `---` |

### 数学公式

支持 LaTeX 语法:

```markdown
行内公式: $E = mc^2$

块级公式:
$$
\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$
```

### 嵌套格式注意事项

当粗体内嵌套斜体时，建议使用不同标记符:

```markdown
# 推荐写法
**粗体 _斜体_ 粗体**

# 避免 (可能解析错误)
**粗体 *斜体* 粗体**
```

## Webhook vs Document

| 功能 | 文档推送 | Webhook 群消息 |
|------|---------|---------------|
| 用途 | 创建可编辑的云文档 | 发送群聊通知 |
| 凭据 | app_id + app_secret | webhook_url |
| 格式支持 | 完整 Markdown + 公式 | 部分 Markdown (见下表) |
| 输出 | 文档 URL | 卡片消息 |

### Webhook 支持的格式

飞书卡片消息仅支持部分 Markdown 语法:

| 语法 | 支持 |
|------|------|
| `**粗体**` | ✅ |
| `*斜体*` | ✅ |
| `[链接](url)` | ✅ |
| `~~删除线~~` | ✅ |
| 换行 `\n` | ✅ |
| 代码块 | ✅ |
| `# 标题` | ❌ |
| `` `行内代码` `` | ❌ |
| 表格 | ❌ |
| 公式 | ❌ |

> 如需完整格式支持，请使用文档推送功能。

### Webhook 使用示例

```python
async with FeishuClient() as client:
    await client.send_webhook(
        content="**部署成功** \n\n环境: production",
        title="CI/CD 通知"
    )
```

## License

MIT
