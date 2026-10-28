# PlayPilot CLI — Google Play APK/AAB 上架预检工具

在本机静态检查 Android 安装包的 Target SDK、部分 Manifest 权限、SDK 指纹和原生库 16 KB ELF 段对齐风险。

[English](README.md) · **简体中文** · [版本说明](CHANGELOG_ZH.md) · MIT

[安装依赖](#安装)后运行：

```bash
python -X utf8 cli.py path/to/app-release.apk --lang zh
```

## 输出示例

下面是检查 Androguard 公开 hello-world 测试包的输出。运行日期为 2026-10-28，包名 `de.rhab.helloworld`，Target SDK 25，Min SDK 21。

```text
  COMPLIANCE SCORE: 75 / 100
  Findings: 1 Fatal | 0 High Risk | 0 Warnings
============================================================
  [FATAL]  Target SDK 等级合规性检查
           Tip: 修改 build.gradle 中的 targetSdk 与 compileSdk 至 36 或更高版本。...
```

这个旧测试包触发了一项致命风险，扣 25 分，得分为 75/100。分数用于汇总检查结果，不代表审核通过率。

[完整输出、固定来源、SHA-256 和复现方法](examples/README_ZH.md)：

```bash
python -X utf8 examples/reproduce_hello_world.py --download --lang zh --check
```

此命令会在样例缺失时下载公开测试 APK、校验哈希后静态检查，不安装或运行 APK。样例没有原生库且未命中 SDK；这不能证明实际运行兼容或没有数据收集。

## 能检查什么

| 本工具检查 | 仍需单独复核 |
| --- | --- |
| APK/AAB Manifest 与部分目标 API、权限规则 | 完整政策适用性、商店资料、账号资格 |
| 已知 DEX SDK 前缀和框架文件特征 | 真实行为、库的配置/版本、自有代码与后端数据流 |
| 原生库 ELF 加载段对齐 | 最终 APK ZIP 对齐及 16 KB 设备上的运行 |
| 指定隐私网址的 HTTP 可访问性、TLS | 协议内容完整性、实际账号和数据删除流程 |

CLI 不上传安装包，也不删除用户原文件；指定 `--privacy-url` 才会请求该隐私网址。未知 SDK、解析失败或回退结果需人工核查。当前命令行没有 Data Safety 交互问卷或 CSV 导出参数；即使存在失败项，也可能以退出码 `0` 结束，因此不是 CI 自动阻断机制。

## 网页工作台

需要可视化报告、修复提示或人工确认后的 Data Safety CSV，可使用 **[PlayPilot 网页版](https://play.ljcan.com/)**。上传包体仅在当前页面会话内临时保存，会话结束删除。SDK 候选不会自动变成申报答案，须确认实际数据行为，并在 Play Console 导入前后复核。

## 安装

需要 Python 3.10+。目前已在 Windows / Python 3.13.7 验证。检查 AAB 还需要兼容仓库 bundletool 的 Java 运行环境；检查 APK 不需要 Java。

```bash
git clone https://github.com/LiJier/playpilot-cli.git
cd playpilot-cli
python -m pip install -r requirements.txt
python -X utf8 cli.py path/to/app-release.apk --lang zh
```

`-X utf8` 用于确保终端 Unicode 输出，尤其适用于 Windows。AAB 检查前先确认 Java 工具可启动：

```bash
java -jar src/bin/bundletool.jar version
python -X utf8 cli.py path/to/app-release.aab --lang zh
```

## 参数

| 参数 | 行为 |
| --- | --- |
| `file` | 本地 APK 或 AAB 文件路径 |
| `--lang en` / `--lang zh` | 英文（默认）或中文检查结果 |
| `--privacy-url URL` | 实际探测指定隐私网址；未填时不请求隐私网页 |
| `--account-del-url URL` | 向规则引擎提供删除网址，不测试实际删除流程 |

```bash
python -X utf8 cli.py path/to/app-release.apk --lang zh --privacy-url https://example.com/privacy
python -X utf8 cli.py --help
```

请将 `example.com` 替换为自己的页面。

## 使用指南

- [检查 APK/AAB 的 16 KB ELF 对齐](docs/16kb-elf-alignment.zh.md)：找出有问题的 `.so`，分别检查段对齐、APK 打包和实际运行。
- [检查 Target SDK 和 Manifest 权限](docs/target-sdk-manifest.zh.md)：查看最终发布包中的目标 API、权限和前台服务声明。
- [用 SDK 检测辅助 Data Safety 复核](docs/sdk-data-safety-review.zh.md)：根据 SDK 配置核对收集、共享、用途和删除方式。
- [检查示例与复现方法](examples/README_ZH.md)：复现公开 APK 的检查结果，比较 4 KB 和 16 KB ELF 文件头。

## 评分、规则与版本

Web 与 CLI 共用 100 分起算、致命失败扣 25、高危失败扣 15、警告扣 5、最低 15 分的评分规则，仅用于汇总静态风险。

截至 2026-10-28，普通应用的新提交和更新要求 API 36。工具根据 Manifest 中的必需设备特性检查 Wear OS/Automotive 35、TV/XR 34 例外。存量分发和延期资格请在 Play Console 确认。[Google 官方要求](https://developer.android.com/google/play/requirements/target-sdk)

```bash
python -m unittest discover tests
python -X utf8 examples/elf_alignment_demo.py
```

[版本记录](CHANGELOG_ZH.md)列出了功能、验证环境和已知问题。CLI 与 Web 后端分别编号；当前从源码安装，尚未发布 PyPI 包或可执行文件。

## 开源许可

[MIT](LICENSE)。示例 APK 仅引用上游固定版本，不随仓库或 Release 分发。
