# 推送到 GitHub 指南

## 📋 步骤

### 1. 创建 GitHub 仓库

1. 登录 GitHub: https://github.com
2. 点击右上角 `+` → `New repository`
3. 仓库名：`xianyu-apk`
4. 设为 **Public**（免费使用 Actions）
5. 点击 `Create repository`

### 2. 关联远程仓库

```bash
cd /home/admin/openclaw/workspace/xianyu-apk

# 替换 YOUR_USERNAME 为你的 GitHub 用户名
git remote add origin https://github.com/YOUR_USERNAME/xianyu-apk.git
```

### 3. 推送到 GitHub

```bash
# 推送代码和标签（自动触发 APK 打包）
git push -u origin main --tags
```

### 4. 查看打包进度

1. 进入 GitHub 仓库页面
2. 点击 `Actions` 标签
3. 查看 `Build APK` 工作流状态

### 5. 下载 APK

打包完成后（约 15-25 分钟）：

1. 进入仓库 `Releases` 页面
2. 找到 `v1.6.0` 版本
3. 下载附件中的 `.apk` 文件

---

## 🔍 当前版本

```
版本：v1.6.0
提交：feat: 添加循环次数和循环间隔设置
功能：
- 商品 ID 管理
- 自动轮询
- URL 变化检测
- 自动化购买（个人号/企业号）
- 购买限制检测 + 自动重试
- 循环次数和循环间隔设置
```

## 📦 项目文件

```
xianyu-apk/
├── main.py              # 主程序
├── webview.py           # WebView 组件
├── xianyu.kv            # 界面样式
├── buildozer.spec       # APK 打包配置
├── requirements.txt     # Python 依赖
├── README.md            # 使用说明
├── .github/workflows/   # GitHub Actions 配置
└── GITHUB_ACTIONS_GUIDE.md  # 云打包指南
```

---

## ⚠️ 注意事项

1. **首次打包**：需要 15-25 分钟（下载 Android SDK/NDK）
2. **后续打包**：5-10 分钟（使用缓存）
3. **GitHub Actions 免费额度**：每月 2000 分钟（Public 仓库）

---

## 🆘 遇到问题？

**问题 1: 推送失败**
```bash
# 检查远程仓库配置
git remote -v

# 如果已有远程，先删除再添加
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/xianyu-apk.git
```

**问题 2: Actions 未触发**
- 确保仓库是 Public
- 检查 `.github/workflows/build.yml` 是否存在
- 查看 GitHub Actions 是否已启用

**问题 3: 打包失败**
- 查看 Actions 日志
- 常见原因：网络问题（重试即可）
