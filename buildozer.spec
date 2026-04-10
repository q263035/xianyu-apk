[app]

# 应用标题
title = 闲鱼商品监控器

# 包名（唯一标识）
package.name = xianyuviewer

# 包版本
package.version = 1.7.0

# 版本号（必须）
version = 1.7.0

# 包域名（反向域名格式）
package.domain = org.user

# 应用源代码目录
source.dir = .

# 包含的源代码文件
source.include_exts = py,png,jpg,kv,atlas,json

# 应用入口点
presplash_filename = 

# 应用图标
icon.filename = 

# 安卓版本
android.api = 33
android.minapi = 24
android.ndk = 25b

# 安卓权限
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,SYSTEM_ALERT_WINDOW

# 安卓架构
android.archs = arm64-v8a,armeabi-v7a

# 是否启用全屏
android.fullscreen = True

# 应用方向（portrait=竖屏，landscape=横屏）
android.orientation = portrait

# Python 依赖
requirements = python3,kivy,pyjnius

# 启动 Activity 配置
android.entrypoint = org.kivy.android.PythonActivity

# 日志级别
log_level = 2

# 调试模式（发布时设为 false）
android.debug_release = false

[buildozer]

# 构建目录
build_dir = ./.buildozer

# 包输出目录
bin_dir = ./bin

# Buildozer 版本
requirement = buildozer >= 1.4.0

# python-for-android 参数
p4a.extra_args = --bootstrap=sdl2
