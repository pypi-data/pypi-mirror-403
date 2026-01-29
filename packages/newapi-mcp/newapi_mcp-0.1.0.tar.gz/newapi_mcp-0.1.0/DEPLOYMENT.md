# MCP 发布和部署指南

## 目录
1. [发布到 PyPI](#发布到-pypi)
2. [Stdio 部署](#stdio-部署)
3. [Claude Desktop 集成](#claude-desktop-集成)
4. [本地测试](#本地测试)

---

## 发布到 PyPI

### 前置条件

1. **PyPI 账户**
   - 在 [pypi.org](https://pypi.org) 注册账户
   - 生成 API Token：Settings → API tokens → Create token

2. **安装发布工具**
   ```bash
   pip install build twine
   ```

### 发布步骤

#### 1. 更新版本号

编辑 `pyproject.toml`：
```toml
[project]
version = "0.1.0"  # 更新版本号
```

#### 2. 构建发行包

```bash
python -m build
```

这会在 `dist/` 目录生成：
- `newapi-mcp-0.1.0.tar.gz` (源代码包)
- `newapi-mcp-0.1.0-py3-none-any.whl` (wheel 包)

#### 3. 验证包内容

```bash
twine check dist/*
```

#### 4. 上传到 PyPI

**方式 A：使用 API Token（推荐）**

```bash
twine upload dist/* -u __token__ -p pypi-YOUR_API_TOKEN
```

**方式 B：使用用户名和密码**

```bash
twine upload dist/*
# 输入用户名和密码
```

#### 5. 验证发布

访问 https://pypi.org/project/newapi-mcp/ 确认包已发布。

### 安装已发布的包

```bash
pip install newapi-mcp
```

---

## Stdio 部署

Stdio 是 MCP 的标准传输方式，用于与 Claude Desktop 等客户端通信。

### 工作原理

```
Claude Desktop
     ↓
  stdin/stdout
     ↓
newapi-mcp server
     ↓
  New API Backend
```

### 配置 Claude Desktop

#### 1. 编辑 Claude Desktop 配置文件

**macOS/Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

#### 2. 添加 MCP 服务器配置

```json
{
  "mcpServers": {
    "newapi-mcp": {
      "command": "python",
      "args": ["-m", "newapi_mcp"],
      "env": {
        "NEWAPI_BASE_URL": "https://your-newapi-instance.com",
        "NEWAPI_API_KEY": "your-api-key"
      }
    }
  }
}
```

#### 3. 重启 Claude Desktop

关闭并重新打开 Claude Desktop。MCP 服务器应该会自动启动。

### 环境变量配置

在 `.env` 文件中配置（或在 Claude Desktop 配置中设置）：

```env
NEWAPI_BASE_URL=https://your-newapi-instance.com
NEWAPI_API_KEY=your-api-key
```

### 验证连接

在 Claude Desktop 中：
1. 打开新对话
2. 查看左下角 MCP 图标
3. 应该看到 "newapi-mcp" 服务器已连接

---

## Claude Desktop 集成

### 完整配置示例

```json
{
  "mcpServers": {
    "newapi-mcp": {
      "command": "python",
      "args": ["-m", "newapi_mcp"],
      "env": {
        "NEWAPI_BASE_URL": "https://api.newapi.com",
        "NEWAPI_API_KEY": "sk-xxx",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 故障排查

#### 1. 服务器无法启动

检查日志：
```bash
# macOS/Linux
tail -f ~/.config/Claude/logs/mcp.log

# Windows
Get-Content $env:APPDATA\Claude\logs\mcp.log -Tail 50
```

#### 2. 工具不可用

- 确认环境变量已设置
- 检查 API 密钥是否有效
- 验证网络连接

#### 3. 连接超时

- 检查 `NEWAPI_BASE_URL` 是否正确
- 确认防火墙允许出站连接
- 验证 API 服务器是否在线

---

## 本地测试

### 1. 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 2. 运行 MCP 服务器

```bash
python -m newapi_mcp
```

或使用命令行工具：
```bash
newapi-mcp
```

### 3. 测试工具

使用 MCP 客户端库测试：

```python
import asyncio
from mcp.client.stdio import StdioClientTransport
from mcp.client import ClientSession

async def test():
    transport = StdioClientTransport(
        command="python",
        args=["-m", "newapi_mcp"]
    )
    
    async with ClientSession(transport) as session:
        # 列出所有工具
        tools = await session.list_tools()
        print(f"Available tools: {len(tools.tools)}")
        
        # 调用工具
        result = await session.call_tool(
            "get_model_list",
            arguments={}
        )
        print(result)

asyncio.run(test())
```

### 4. 运行测试套件

```bash
pytest tests/
```

### 5. 代码质量检查

```bash
# 格式检查
black --check src/

# Lint 检查
ruff check src/

# 类型检查
mypy src/
```

---

## 发布检查清单

在发布前，确保完成以下检查：

- [ ] 更新 `pyproject.toml` 中的版本号
- [ ] 更新 `CHANGELOG.md`（如果有）
- [ ] 所有测试通过：`pytest tests/`
- [ ] 代码格式正确：`black src/`
- [ ] 没有 lint 错误：`ruff check src/`
- [ ] 没有类型错误：`mypy src/`
- [ ] 构建成功：`python -m build`
- [ ] 包验证通过：`twine check dist/*`
- [ ] Git 标签已创建：`git tag v0.1.0`
- [ ] 提交已推送到 GitHub

---

## 版本管理

### 语义化版本

遵循 [Semantic Versioning](https://semver.org/)：

- **MAJOR** (1.0.0): 不兼容的 API 变更
- **MINOR** (0.1.0): 向后兼容的新功能
- **PATCH** (0.0.1): 向后兼容的 bug 修复

### 发布流程

```bash
# 1. 更新版本
# 编辑 pyproject.toml

# 2. 提交更改
git add pyproject.toml
git commit -m "chore: bump version to 0.1.0"

# 3. 创建标签
git tag v0.1.0

# 4. 推送
git push origin main
git push origin v0.1.0

# 5. 构建和发布
python -m build
twine upload dist/*
```

---

## 常见问题

### Q: 如何更新已发布的包？

A: 增加版本号，然后重新发布。PyPI 不允许覆盖已发布的版本。

### Q: Stdio 和 HTTP 有什么区别？

A: 
- **Stdio**: 标准输入/输出，用于本地进程通信（Claude Desktop）
- **HTTP**: 网络传输，用于远程服务器

### Q: 如何在生产环境中运行？

A: 使用进程管理器（如 systemd、supervisor）确保服务器持续运行。

### Q: 如何处理敏感信息（API 密钥）？

A: 
- 使用环境变量
- 不要在代码中硬编码
- 使用 `.env` 文件（不要提交到 Git）
- 在 Claude Desktop 配置中使用环境变量

---

## 相关资源

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [PyPI 发布指南](https://packaging.python.org/tutorials/packaging-projects/)
- [Claude Desktop 文档](https://claude.ai/docs)
- [New API 文档](https://github.com/Calcium-Ion/new-api)
