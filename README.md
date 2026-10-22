<p align="center">
  <img src="https://play.ljcan.com/logo.svg" alt="PlayPilot Logo" width="96" height="96" />
</p>

<h1 align="center">PlayPilot CLI</h1>

<p align="center">
  <strong>Google Play 上架合规预检工具 · 纯静态排查常见被拒风险与修复指引</strong><br />
  <em>Pure-static, zero-retention pre-flight compliance auditor for Android AAB & APK</em>
</p>

<p align="center">
  <a href="https://play.ljcan.com"><img src="https://img.shields.io/badge/🌐%20Live%20Web%20App-play.ljcan.com-00C853?style=for-the-badge&logo=googleplay&logoColor=white" alt="Live Web App" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="License" /></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
</p>

---

> ### 🌐 在线免安装体验 (Web App)
> 如果不想在本地配置 Python 或 Java 环境，可以直接使用网页版：  
> 👉 **[https://play.ljcan.com](https://play.ljcan.com)**  
> *上传安装包即可开始排查 · 本地临时分析不保存文件 · 支持一键导出 Play Console 数据安全 CSV*

---

## 🌟 核心排查能力 (Features)

* ⚡ **纯静态快速分析**：无需真机或模拟器运行环境，直接静态解析 AAB/APK 安装包特征。
* 🛡️ **数据安全保障**：所有分析均在本地机器完成，绝不上传包体到任何第三方服务器。
* 📐 **16KB 动态库页面对齐排查**：静态检查 64 位 `.so` 共享库 ELF Header，排查 Android 15 要求的 16KB Page Alignment，规避启动闪退风险。
* 📋 **数据安全表单对照导出**：自动匹配常见第三方 SDK（如 AdMob、Firebase、Adjust 等），支持导出符合 Play Console 导入格式的 CSV 表格。
* 💡 **代码修复建议**：针对不合规项生成修改建议，可直接复制给 Cursor、Claude Code 或 GitHub Copilot 等工具辅助修改。
* 🎯 **全面覆盖常见 Google Play 政策审查项**：
  * Target SDK 适配要求（Android 14 / 15）
  * 64 位原生库 16KB 页面对齐合规
  * Android 14 前台服务 (`foregroundServiceType`) 声明校验
  * 广告 ID (`AD_ID`) 权限与 SDK 声明匹配
  * 账号注销政策与公开注销链接检查
  * 存储权限与 Photo Picker 替代建议
  * 隐私政策网址有效性检测

---

## 🛠️ 快速上手 (Quick Start)

### 1. 环境要求 (Prerequisites)
- Python 3.10+
- Java Runtime (JRE 11+)：如果需要解析 `.aab` 格式（调用内部 bundletool.jar）

### 2. 安装依赖 (Install)
```bash
git clone https://github.com/LiJier/playpilot-cli.git
cd playpilot-cli
pip install -r requirements.txt
```

### 3. 执行检查 (Usage)

#### 基础检测
```bash
python cli.py path/to/app-release.aab
```

#### 中文输出模式
```bash
python cli.py path/to/app-release.apk --lang zh
```

#### 带合规网址验证
```bash
python cli.py path/to/app-release.aab \
  --lang zh \
  --privacy-url "https://example.com/privacy" \
  --account-del-url "https://example.com/delete-account"
```

---

## 🤖 CI/CD 自动化集成 (GitHub Actions)

可将 PlayPilot CLI 轻松嵌入流水线中，在提审构建阶段自动执行合规预检：

```yaml
name: Play Store Pre-flight Check

on:
  push:
    branches: [ release/**, main ]

jobs:
  preflight-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Set up Java
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run PlayPilot Compliance Check
        run: |
          python cli.py build/outputs/bundle/release/app-release.aab --lang en
```

---

## 🧪 运行单元测试 (Running Tests)

```bash
python -m unittest discover tests
```

---

## 📄 开源许可 (License)

本项目采用 [MIT License](LICENSE) 开源许可。
