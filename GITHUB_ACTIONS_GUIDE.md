# GitHub Actions 云打包指南

使用 GitHub 的免费 CI/CD 服务自动构建 APK，无需本地环境。

## 📋 前提条件

- GitHub 账号
- 项目已上传到 GitHub 仓库

## 🚀 使用步骤

### 步骤 1: 创建 GitHub 仓库

1. 登录 GitHub (https://github.com)
2. 点击右上角 `+` → `New repository`
3. 仓库名：`xianyu-apk`
4. 设为 **Public**（免费账户 Public 仓库可免费使用 Actions）
5. 点击 `Create repository`

### 步骤 2: 上传项目文件

```bash
# 在项目目录执行
cd /home/admin/openclaw/workspace/xianyu-apk

# 初始化 git
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: 闲鱼商品访问器"

# 关联远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/xianyu-apk.git

# 推送
git push -u origin main
```

### 步骤 3: 触发打包

**方式 A: 推送标签（推荐）**
```bash
# 打版本标签并推送，自动触发打包
git tag v1.0.0
git push origin v1.0.0
```

**方式 B: 手动触发**
1. 进入 GitHub 仓库页面
2. 点击 `Actions` 标签
3. 选择 `Build APK` 工作流
4. 点击 `Run workflow` → `Run workflow`

### 步骤 4: 下载 APK

**如果是标签推送：**
1. 进入仓库 `Releases` 页面
2. 找到 `v1.0.0` 版本
3. 下载附件中的 `.apk` 文件

**如果是手动触发：**
1. 进入仓库 `Actions` 标签
2. 点击正在运行/已完成的 workflow
3. 在页面底部找到 `Artifacts`
4. 下载 `xianyuviewer-debug.zip`

## ⏱️ 预计时间

- 首次运行：15-25 分钟（需下载 Android SDK/NDK，约 2-3GB）
- 后续运行：5-10 分钟（使用缓存）

## 💡 提示

1. **GitHub Actions 免费额度**：每月 2000 分钟（Public 仓库免费）
2. **缓存优化**：首次打包后，SDK/NDK 会被缓存，后续打包更快
3. **APK 大小**：约 20-30MB（包含 Python 运行时和 Kivy 框架）

## 🔧 自定义配置

### 修改应用包名
编辑 `buildozer.spec`：
```ini
package.name = 你的应用名
package.domain = com.你的域名
```

### 修改应用图标
1. 准备 512x512 PNG 图片，命名为 `icon.png`
2. 放入项目根目录
3. 编辑 `buildozer.spec`：
   ```ini
   icon.filename = icon.png
   ```

### 修改版本号
编辑 `buildozer.spec`：
```ini
version = 1.0.1  # 每次发布递增版本号
```

## ⚠️ 常见问题

**Q: Actions 显示权限错误？**
A: 确保仓库是 Public，或检查 GitHub Actions 是否已启用。

**Q: 打包失败？**
A: 查看 Actions 日志，常见原因：
- 网络问题（下载 SDK 失败）→ 重试即可
- 依赖缺失 → 检查 build.yml 中的 apt-get 安装列表

**Q: APK 安装失败？**
A: 确保手机允许安装"未知来源"应用，或检查安卓版本 >= 7.0

## 📦 发布正式版

1. 测试 debug 版本无误后
2. 修改 `buildozer.spec`：
   ```ini
   android.debug_release = true  # 改为 false
   ```
3. 修改 `.github/workflows/build.yml`，添加 release 构建：
   ```yaml
   - name: Build Release APK
     run: buildozer android release
   
   - name: Upload Release APK
     uses: actions/upload-artifact@v3
     with:
       name: xianyuviewer-release
       path: bin/*-release.apk
   ```

## 📞 需要帮助？

查看 GitHub Actions 日志或提交 Issue。
