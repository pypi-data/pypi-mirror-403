# 快速开始指南

## 5 分钟快速部署

### 1. 安装

```bash
pip install newapi-mcp
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
NEWAPI_BASE_URL=https://your-newapi-instance.com
NEWAPI_API_KEY=your-api-key
```

### 3. 运行服务器

```bash
newapi-mcp
```

或使用 Python 模块：

```bash
python -m newapi_mcp
```

### 4. 集成到 Claude Desktop

编辑配置文件：

**macOS/Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

添加配置：

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

重启 Claude Desktop，完成！

---

## 开发者指南

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/yourusername/newapi-mcp.git
cd newapi-mcp

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 代码格式化
black src/

# Lint 检查
ruff check src/

# 类型检查
mypy src/
```

### 发布新版本

```bash
# 使用发布脚本（Linux/macOS）
bash scripts/publish.sh

# 或 Windows
scripts\publish.bat
```

脚本会自动：
- 运行测试
- 检查代码质量
- 构建发行包
- 上传到 PyPI

---

## 可用工具

### 模型定价

- `get_model_pricing()` - 获取所有模型定价
- `get_model_list()` - 获取模型列表
- `get_model_price_by_name(model_name)` - 按名称获取价格
- `get_models_by_vendor(vendor_id)` - 按供应商获取模型
- `get_models_by_ratio_range(min_ratio, max_ratio)` - 按比率范围获取模型
- `get_pricing_statistics()` - 获取定价统计
- `update_model_ratio(model_ratios)` - 更新模型比率
- `update_model_price(model_prices)` - 更新模型价格

### 模型搜索

- `search_models(keyword, vendor_id, min_ratio, max_ratio, limit)` - 高级搜索
- `compare_models(model_names)` - 比较多个模型
- `get_cheapest_models(limit)` - 获取最便宜的模型
- `get_fastest_models(limit)` - 获取最快的模型

### 用户管理

- `get_all_users(page, limit, sort)` - 获取所有用户
- `create_user(username, password, group)` - 创建用户
- `update_user(user_id, username, password, group)` - 更新用户
- `delete_user(user_id)` - 删除用户

### Token 管理

- `create_token(name, unlimited_quota, remain_quota)` - 创建 Token
- `get_token_info()` - 获取 Token 信息
- `estimate_cost(model_name, input_tokens, output_tokens)` - 估算成本
- `list_available_models_for_token()` - 列出可用模型

### 频道管理

- `get_all_channels(page, limit, sort)` - 获取所有频道
- `get_channel_list()` - 获取频道列表
- `get_channel_by_name(name)` - 按名称获取频道
- `create_channel(name, channel_type, key, priority, status)` - 创建频道
- `update_channel(channel_id, name, key, priority, status)` - 更新频道
- `test_channel(channel_id)` - 测试频道连接
- `get_channel_status(channel_id)` - 获取频道状态

### 日志和统计

- `get_all_models(page, limit, sort)` - 获取所有模型
- `get_logs(page, limit, model, start_time, end_time)` - 获取日志
- `get_token_usage()` - 获取 Token 使用统计

---

## 故障排查

### 问题：服务器无法启动

**检查日志：**

```bash
# macOS/Linux
tail -f ~/.config/Claude/logs/mcp.log

# Windows
Get-Content $env:APPDATA\Claude\logs\mcp.log -Tail 50
```

**常见原因：**
- 环境变量未设置
- API 密钥无效
- 网络连接问题

### 问题：工具不可用

**检查：**
1. 确认 MCP 服务器已连接
2. 验证 API 密钥权限
3. 检查 New API 服务器是否在线

### 问题：连接超时

**解决：**
1. 验证 `NEWAPI_BASE_URL` 正确
2. 检查防火墙设置
3. 确认网络连接

---

## 常见问题

**Q: 如何更新到新版本？**

A: 
```bash
pip install --upgrade newapi-mcp
```

**Q: 如何在多个 Claude Desktop 实例中使用？**

A: 在每个实例的配置文件中添加相同的 MCP 服务器配置。

**Q: 如何在生产环境中运行？**

A: 使用进程管理器（如 systemd、supervisor）确保服务器持续运行。

**Q: 如何处理敏感信息？**

A: 
- 使用环境变量
- 不要在代码中硬编码
- 使用 `.env` 文件（不要提交到 Git）

---

## 获取帮助

- 📖 [完整文档](./DEPLOYMENT.md)
- 🐛 [报告问题](https://github.com/yourusername/newapi-mcp/issues)
- 💬 [讨论](https://github.com/yourusername/newapi-mcp/discussions)
- 📧 [联系作者](mailto:your-email@example.com)
