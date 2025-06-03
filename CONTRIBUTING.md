# 贡献指南

感谢您对 Cursor Memory MCP 项目的关注！我们欢迎各种形式的贡献。

## 开发环境设置

### 先决条件

- Python 3.11 或更高版本
- [uv](https://github.com/astral-sh/uv) 包管理器

### 设置开发环境

1. **克隆仓库**
   ```bash
   git clone https://github.com/your-username/cursor-memory-mcp.git
   cd cursor-memory-mcp
   ```

2. **安装 uv**
   ```bash
   # Linux/macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **创建虚拟环境并安装依赖**
   ```bash
   uv venv
   source .venv/bin/activate  # Linux/macOS
   # 或
   .venv\Scripts\activate     # Windows
   
   uv pip install -e ".[dev]"
   ```

## 开发工作流

### 代码风格

我们使用以下工具来保持代码质量：

- **Black**: 代码格式化
- **Ruff**: 代码检查
- **mypy**: 类型检查

运行代码检查：
```bash
# 格式化代码
black src/ tests/

# 检查代码风格
ruff check src/ tests/

# 类型检查
mypy src/ --ignore-missing-imports
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=src/cursor_memory_mcp --cov-report=html
```

### 提交前检查

在提交代码前，请确保：

1. 所有测试通过
2. 代码通过所有检查工具
3. 添加适当的测试用例
4. 更新相关文档

## 贡献类型

### Bug 报告

请使用 [Bug 报告模板](.github/ISSUE_TEMPLATE/bug_report.md) 提交 Bug。

### 功能请求

请使用 [功能请求模板](.github/ISSUE_TEMPLATE/feature_request.md) 提交新功能建议。

### 代码贡献

1. **Fork 仓库**
2. **创建特性分支**: `git checkout -b feature/amazing-feature`
3. **提交更改**: `git commit -m 'Add some amazing feature'`
4. **推送到分支**: `git push origin feature/amazing-feature`
5. **打开 Pull Request**

### Pull Request 指南

- 使用 [Pull Request 模板](.github/PULL_REQUEST_TEMPLATE.md)
- 确保所有检查通过
- 提供清晰的描述
- 链接相关 Issue
- 请求代码审查

## 代码审查流程

1. 所有 PR 需要至少一个维护者的审批
2. 所有 GitHub Actions 检查必须通过
3. 代码需要有适当的测试覆盖率
4. 文档需要更新（如果适用）

## 发布流程

发布由维护者处理，遵循语义版本控制：

- **补丁版本** (0.0.x): Bug 修复
- **次要版本** (0.x.0): 新功能，向后兼容
- **主要版本** (x.0.0): 破坏性更改

## 获取帮助

如果您有任何问题：

1. 查看现有的 [Issues](https://github.com/your-username/cursor-memory-mcp/issues)
2. 创建新的 Issue
3. 参与讨论

## 行为准则

请遵循我们的行为准则，营造一个包容和欢迎的环境。

## 许可证

通过贡献，您同意您的贡献将在 [MIT 许可证](LICENSE) 下许可。 