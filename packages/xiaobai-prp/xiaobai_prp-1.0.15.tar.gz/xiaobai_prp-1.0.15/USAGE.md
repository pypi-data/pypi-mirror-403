# PRP 使用帮助 | PRP Usage Guide

## 目录 | Table of Contents
- [中文版 - Chinese Version](#prp-使用指南)
- [English Version - English Version](#prp-usage-guide)

---

## PRP 使用指南

### 简介
PRP (Python Registry Provider) 是一个用于管理 Python 包镜像源的工具，类似于 npm 的 nrm。它可以帮助您轻松切换不同的 PyPI 镜像源。

### 基本用法

安装 PRP 后，您可以使用它在不同的 Python 包镜像之间切换：

```bash
# 列出所有可用的包镜像源
prp ls

# 切换到特定的包镜像源（例如 TUNA 镜像）
prp use tuna

# 测试包镜像源的速度
prp test

# 添加自定义包镜像源
prp add myregistry https://myregistry.example.com/simple/

# 删除包镜像源
prp del myregistry
```

### 与 pip 配合使用

一旦使用 PRP 切换到某个包镜像源，您可以正常使用 pip。如果您想临时使用特定镜像，可以检查当前包镜像源：

```bash
# 检查当前包镜像源
prp current

# 然后正常使用 pip 安装包
pip install package_name
```

另外，您可以临时覆盖源：

```bash
# 使用特定镜像安装（不受 PRP 影响）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ package_name
```

### 配置位置

PRP 将其配置存储在 `~/.prp/config.json` 中。这包括所有可用的包镜像源和当前活动的包镜像源。

### 可用的包镜像源

默认情况下，PRP 包含这些流行的包镜像源：
- `pypi`: 官方 PyPI 仓库
- `tuna`: 清华大学镜像
- `aliyun`: 阿里云镜像
- `douban`: 豆瓣镜像
- `huawei`: 华为云镜像
- `ustc`: 中国科学技术大学镜像

### 自定义

您可以通过直接编辑 `~/.prp/config.json` 或使用 `prp add` 和 `prp del` 命令来自定义包镜像源。

### 故障排除

如果遇到问题：
1. 确保您已安装最新版本的 PRP
2. 检查您的互联网连接是否能正常访问所选的包镜像源
3. 验证包镜像源 URL 是否可访问

---

## PRP Usage Guide

### Introduction
PRP (Python Registry Provider) is a tool for managing Python package index sources, similar to nrm for npm. It helps you easily switch between different PyPI mirror sources.

### Basic Usage

After installing PRP, you can use it to switch between different Python package indexes:

```bash
# List all available package index sources
prp ls

# Switch to a specific package index source (e.g., TUNA mirror)
prp use tuna

# Test the speed of package index sources
prp test

# Add a custom package index source
prp add myregistry https://myregistry.example.com/simple/

# Remove a package index source
prp del myregistry
```

### Using with pip

Once you've switched to a package index source using PRP, you can use pip normally. If you want to temporarily use a specific index, you can check the current package index source:

```bash
# Check current package index source
prp current

# Then use pip normally to install packages
pip install package_name
```

Alternatively, you can temporarily override the source:

```bash
# Install with a specific index (not affected by PRP)
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ package_name
```

### Configuration Location

PRP stores its configuration in `~/.prp/config.json`. This includes all available package index sources and the currently active one.

### Available Package Index Sources

By default, PRP comes with these popular package index sources:
- `pypi`: Official PyPI repository
- `tuna`: Tsinghua University mirror
- `aliyun`: Alibaba Cloud mirror
- `douban`: Douban mirror
- `huawei`: Huawei Cloud mirror
- `ustc`: University of Science and Technology of China mirror

### Customization

You can customize the package index sources by directly editing `~/.prp/config.json` or using the `prp add` and `prp del` commands.

### Troubleshooting

If you encounter issues:
1. Make sure you have the latest version of PRP installed
2. Check that your internet connection works with the selected package index source
3. Verify that the package index source URL is accessible