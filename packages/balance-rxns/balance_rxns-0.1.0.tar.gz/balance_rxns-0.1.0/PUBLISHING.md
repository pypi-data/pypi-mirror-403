# 发布到 PyPI 指南

## 准备工作

在发布之前，请确保：

1. **更新版本号**
   - 编辑 `pyproject.toml` 中的 `version` 字段
   - 编辑 `src/balance_rxns/__init__.py` 中的 `__version__`

2. **更新作者信息**
   - 编辑 `pyproject.toml` 中的 `authors` 字段，填写你的名字和邮箱
   - 更新 `project.urls` 中的 GitHub 仓库链接

3. **测试代码**
   - 确保所有示例代码都能正常运行
   - 在本地测试包的安装和使用

## 构建包

使用 uv 构建包：

```bash
uv build
```

这将在 `dist/` 目录下生成两个文件：
- `balance_rxns-0.1.0.tar.gz` (源码分发包)
- `balance_rxns-0.1.0-py3-none-any.whl` (wheel 包)

## 发布到 PyPI

### 方法 1: 使用 uv publish (推荐)

```bash
# 发布到 PyPI
uv publish

# 发布到 TestPyPI (测试用)
uv publish --publish-url https://test.pypi.org/legacy/
```

首次发布时，会提示你输入 PyPI 的用户名和密码/token。

### 方法 2: 使用 twine

1. 安装 twine：
```bash
pip install twine
```

2. 发布到 TestPyPI (测试)：
```bash
twine upload --repository testpypi dist/*
```

3. 从 TestPyPI 测试安装：
```bash
pip install --index-url https://test.pypi.org/simple/ balance-rxns
```

4. 确认无误后，发布到正式 PyPI：
```bash
twine upload dist/*
```

## PyPI 账号设置

1. 在 https://pypi.org/ 注册账号
2. 启用 2FA (双因素认证)
3. 创建 API Token:
   - 访问 https://pypi.org/manage/account/token/
   - 创建新 token (scope 选择 "Entire account" 或特定项目)
   - 保存 token (格式: `pypi-xxx...`)

4. 使用 token 上传：
   - 用户名使用: `__token__`
   - 密码使用你的 API token

## 版本管理建议

遵循语义化版本 (Semantic Versioning):
- `0.1.0` - 初始版本
- `0.1.1` - bug 修复
- `0.2.0` - 添加新功能（向后兼容）
- `1.0.0` - 第一个稳定版本
- `2.0.0` - 破坏性更改

## 发布检查清单

- [ ] 更新版本号
- [ ] 更新 CHANGELOG
- [ ] 更新 README.md
- [ ] 运行所有测试
- [ ] 更新作者信息和 GitHub 链接
- [ ] 构建包 (`uv build`)
- [ ] 检查生成的文件
- [ ] (可选) 先发布到 TestPyPI 测试
- [ ] 发布到 PyPI
- [ ] 创建 Git tag
- [ ] 推送到 GitHub

## Git 标签

发布后创建版本标签：

```bash
git tag v0.1.0
git push origin v0.1.0
```

## 持续集成 (可选)

可以设置 GitHub Actions 自动发布：

在 `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'
    - name: Install uv
      run: pip install uv
    - name: Build package
      run: uv build
    - name: Publish to PyPI
      env:
        UV_PUBLISH_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
      run: uv publish
```

记得在 GitHub 仓库设置中添加 `PYPI_API_TOKEN` secret。

## 故障排除

### 文件名冲突
如果遇到 "File already exists" 错误，需要更新版本号后重新构建。

### 认证失败
确保使用正确的 API token，用户名应为 `__token__`。

### 包名已被占用
如果包名已被占用，需要更改 `pyproject.toml` 中的 `name` 字段。

## 相关链接

- PyPI: https://pypi.org/
- TestPyPI: https://test.pypi.org/
- PyPI 指南: https://packaging.python.org/
- Twine 文档: https://twine.readthedocs.io/
