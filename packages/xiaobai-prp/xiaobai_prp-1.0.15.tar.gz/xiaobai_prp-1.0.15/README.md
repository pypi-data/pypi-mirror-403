# PRP - Python Registry Provider (Python包镜像提供商)

[![Downloads](https://pepy.tech/badge/xiaobai-prp)](https://pepy.tech/project/xiaobai-prp)

## 目录 (Table of Contents)
- [简介](#prp---python-registry-provider-python包镜像提供商)
- [功能](#功能)
- [安装](#安装)
- [使用方法](#使用方法)
- [可用镜像源](#可用镜像源)
- [贡献](#贡献)
- [许可证](#许可证)

PRP (Python Registry Provider) 是一个用于管理Python包镜像源的命令行工具，类似于npm的nrm。它允许您轻松切换不同的Python包镜像，如PyPI、TUNA、阿里云等。

PRP (Python Registry Provider) is a command-line tool for managing Python package index sources, similar to `nrm` for npm. It allows you to easily switch between different Python package indexes such as PyPI, TUNA, Aliyun, and more.

## 功能 (Features)

- 列出所有可用包镜像源 (List all available package index sources)
- 一键切换包镜像源 (Switch between package index sources with a single command)
- 支持多源切换 (Support switching to multiple sources simultaneously)
- 支持自动检测最快源 (Support automatically detecting the fastest source)
- 支持按速度排序选择前N个源 (Support selecting top N fastest sources by speed)
- 添加自定义包镜像源 (Add custom package index sources)
- 支持批量添加多个包镜像源 (Support adding multiple package index sources at once)
- 删除包镜像源 (Remove package index sources)
- 支持批量删除多个包镜像源 (Support removing multiple package index sources at once)
- 恢复默认配置 (Restore to default configuration)
- 测试包镜像源速度 (Test package index source speeds)
- 查看当前包镜像源 (View current package index source)

## 安装 (Installation)

```bash
pip install xiaobai-prp
```

## 使用方法 (Usage)

### 列出所有包镜像源 (List all package index sources)
```bash
prp ls
```

### 切换到最快包镜像源 (Switch to the fastest package index source)
```bash
prp use                 # 自动检测并切换到最快的镜像源 (Auto-detect and switch to the fastest source)
prp use --fastest       # 同上，显式指定 (Same as above, explicitly specified)
```

### 按速度排序选择前N个镜像源 (Select top N fastest sources by speed)
```bash
prp use 1               # 将所有镜像源按网速快慢排序，选择最快的1个镜像源作为主源 (Sort all sources by speed, select the fastest 1 source as main source)
prp use 2               # 将所有镜像源按网速快慢排序，选择最快的2个镜像源，第一个为主源，第二个为备用源 (Sort all sources by speed, select the fastest 2 sources, first as main, second as backup)
prp use 3               # 将所有镜像源按网速快慢排序，选择最快的3个镜像源，第一个为主源，其余为备用源 (Sort all sources by speed, select the fastest 3 sources, first as main, rest as backups)
prp use N               # 将所有镜像源按网速快慢排序，选择最快的N个镜像源 (Sort all sources by speed, select the fastest N sources)
```

### 切换单个包镜像源 (Switch to a single package index source)
```bash
prp use tuna
```

### 切换多个包镜像源 (Switch to multiple package index sources)
```bash
# 第一个作为主源，后续作为额外源
prp use aliyun tuna pypi
```

### 添加自定义包镜像源 (Add a custom package index source)
```bash
prp add myregistry https://myregistry.example.com/simple/
```

### 批量添加多个包镜像源 (Add multiple package index sources at once)
```bash
# 支持添加多个源，格式为: name1 url1 [home1] name2 url2 [home2]
prp add myregistry1 https://myregistry1.example.com/simple/ myregistry2 https://myregistry2.example.com/simple/
```

### 添加带主页的包镜像源 (Add package index source with homepage)
```bash
prp add myregistry https://myregistry.example.com/simple/ https://myregistry.example.com
```

### 批量添加带主页的多个包镜像源 (Add multiple package index sources with homepages)
```bash
prp add myregistry1 https://myregistry1.example.com/simple/ https://myregistry1.example.com myregistry2 https://myregistry2.example.com/simple/ https://myregistry2.example.com
```

### 删除包镜像源 (Delete a package index source)
```bash
prp del myregistry
```

### 批量删除多个包镜像源 (Delete multiple package index sources at once)
```bash
prp del myregistry1 myregistry2
```

### 恢复默认配置 (Restore to default configuration)
```bash
prp reset
```

### 测试包镜像源速度 (Test package index source speeds)
```bash
# 测试所有源的速度
prp test

# 测试特定源的速度
prp test tuna
```

### 显示当前包镜像源 (Show current package index source)
```bash
prp current
```

### 显示版本信息 (Show version information)
```bash
prp version
```

## 可用镜像源 (Available Registries)

- pypi - 官方PyPI仓库 (Official PyPI repository)
- pypi-test - PyPI测试仓库 (PyPI test repository)
- tuna - 清华大学镜像 (Tsinghua University mirror)
- aliyun - 阿里云镜像 (Alibaba Cloud mirror)
- douban - 豆瓣镜像 (Douban mirror)
- huawei - 华为云镜像 (Huawei Cloud mirror)
- ustc - 中国科学技术大学镜像 (University of Science and Technology of China mirror)

## 贡献 (Contributing)

欢迎贡献！请随时提交Pull Request。
Contributions are welcome! Please feel free to submit a Pull Request.

## 许可证 (License)

本项目采用GPLv3许可证 - 详见LICENSE文件。
This project is licensed under the GNU General Public License v3 (GPLv3) License - see the LICENSE file for details.