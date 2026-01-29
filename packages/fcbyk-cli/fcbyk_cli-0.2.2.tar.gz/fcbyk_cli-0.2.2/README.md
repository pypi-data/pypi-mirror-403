![image](https://github.com/user-attachments/assets/655b2999-fd7a-4a63-bc54-c0297c16e0a8)

[![PyPI](https://img.shields.io/pypi/v/fcbyk-cli.svg)](https://pypi.org/project/fcbyk-cli/)
[![Tests](https://github.com/fcbyk/fcbyk-cli/actions/workflows/test.yml/badge.svg)](https://github.com/fcbyk/fcbyk-cli/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/fcbyk/fcbyk-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/fcbyk/fcbyk-cli)
[![License](https://img.shields.io/github/license/fcbyk/fcbyk-cli.svg)](https://github.com/fcbyk/fcbyk-cli/blob/main/LICENSE)

## 子命令

- `lansend`：在指定端口开启 `http服务器`，用于局域网内共享文件
- `ai`：在控制台与 `ai` 聊天 （需自行配置`api-key`）
- `pick`：随机抽取一个元素（可用于抽奖、随机选择等）
- `slide`：同一局域网内，手机控制电脑PTT翻页

## 安装

#### 使用 pip 安装

```bash
pip install fcbyk-cli
```

> GUI为可选依赖

```bash
pip install fcbyk-cli[gui]
```

#### 从源码安装（可按需调整代码）

- 前端构建
```bash
git clone https://github.com/fcbyk/fcbyk-cli.git
cd web-ui
npm install
npm run build:flatten
```

- 后端安装
```bash
cd ..
cd fcbyk-cli
pip install -e .
```

## 查看帮助信息

```bash
fcbyk --help
fcbyk --version
```

## 系统要求

- Python 3.6+
- Windows