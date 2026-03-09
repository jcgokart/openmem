# Contributing to trae-memory

欢迎贡献！请遵循以下指南。

## 开发环境

```bash
# 克隆仓库
git clone https://github.com/jcgokart/trae-memory.git
cd trae-memory

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .
```

## 代码规范

- 使用 4 空格缩进
- 类型提示尽量添加
- 异常要捕获并提供友好错误信息

## 测试

```bash
# 运行测试
pytest tests/
```

## 提交规范

- 提交信息格式：`type: description`
- type: `feat`, `fix`, `docs`, `refactor`

## 问题反馈

请使用 GitHub Issues 报告 bug 或功能请求。