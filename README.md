# JMComic API - Vercel Flask 解决方案

一个基于 Flask 的 JMComic API 服务，部署在 Vercel 平台上。

## 🚀 项目简介

这是一个为 JMComic 提供的 RESTful API 服务，使用 Flask 框架开发，并部署在 Vercel 无服务器平台上。项目提供了对 JMComic 内容的程序化访问接口。

## ✨ 特性

- 🌐 **RESTful API** - 标准的 REST API 设计
- ⚡ **Vercel 部署** - 无服务器架构，快速响应
- 🔒 **安全可靠** - 基于 Flask 的安全框架
- 📚 **JMComic 集成** - 专为 JMComic 内容优化
- 🐍 **Python 驱动** - 使用 Flask 轻量级框架

## 🛠️ 技术栈

- **后端框架**: Flask
- **部署平台**: Vercel
- **编程语言**: Python 3.x
- **API 风格**: RESTful

## 📦 安装与部署

### 前提条件

- Python 3.7+
- Vercel 账户
- Git

### 本地开发

1. **克隆项目**
```bash
git clone https://github.com/sf-yuzifu/vercel-flask-jmcomic-api.git
cd vercel-flask-jmcomic-api
```

2. **安装 Vercel CLI**
```bash
npm i -g vercel
```

3. **运行开发服务器**
```bash
vercel dev
```

### Vercel 部署

1. **Fork 或克隆此仓库**

2. **安装 Vercel CLI**

3. **部署到 Vercel**
```bash
vercel
```

或者通过 Vercel 控制台直接导入 GitHub 仓库进行部署。

## 📖 API 文档

### 基础信息

- **基础URL**: `https://your-app.vercel.app`
- **默认端口**: 3000 (Vercel)

### 可用端点

#### 获取本子信息
```
GET /album/<comic_id>/info
```
参数:
- `comic_id`: 本子ID

#### 获取本子封面
```
GET /album/<comic_id>/cover
```
参数:
- `comic_id`: 本子ID

#### 获取本子内容
```
GET /photo/<comic_id>/<page>
```
参数:
- `comic_id`: 本子ID
- `page`: 第几页的图片，不填默认第一页

## 🗂️ 项目结构

```
vercel-flask-jmcomic-api/
├── api/
│   └── index.py          # Vercel Serverless Function 入口
├── requirements.txt      # Python 依赖
├── vercel.json          # Vercel 配置文件
└── README.md            # 项目说明文档
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## ⚠️ 免责声明

本项目仅用于学习和研究目的，请勿用于商业用途。使用者应对其行为负责，作者不承担任何法律责任。

## 📞 联系

- GitHub: [@sf-yuzifu](https://github.com/sf-yuzifu)
- 项目地址: [https://github.com/sf-yuzifu/vercel-flask-jmcomic-api](https://github.com/sf-yuzifu/vercel-flask-jmcomic-api)

## 感谢以下项目

### JMComic Python API

<a href="https://github.com/hect0x7/JMComic-Crawler-Python">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github-readme-stats.vercel.app/api/pin/?username=hect0x7&repo=JMComic-Crawler-Python&theme=radical" />
    <source media="(prefers-color-scheme: light)" srcset="https://github-readme-stats.vercel.app/api/pin/?username=hect0x7&repo=JMComic-Crawler-Python" />
    <img alt="Repo Card" src="https://github-readme-stats.vercel.app/api/pin/?username=hect0x7&repo=JMComic-Crawler-Python" />
  </picture>
</a>

---

如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！