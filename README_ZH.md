# PlayPilot CLI — Google Play APK/AAB 上架预检工具

在本机静态检查 Android 安装包的 Target SDK、部分 Manifest 权限、SDK 指纹和原生库 16 KB ELF 段对齐风险。

[English](README.md) · **简体中文** · [版本说明](CHANGELOG.md) · MIT

[安装依赖](#安装)后运行：

```bash
python -X utf8 cli.py path/to/app-release.apk --lang zh
```

## 真实输出示例

2026-10-28 实际运行当前 CLI 检查 Androguard 的公开 hello-world 测试 APK，提取到包名 `de.rhab.helloworld`、Target SDK 25、Min SDK 21。英语输出摘录：

```text
  COMPLIANCE SCORE: 75 / 100
  Findings: 1 Fatal | 0 High Risk | 0 Warnings
============================================================
  [FATAL]  Target SDK Version Compliance Check
           Tip: Update targetSdk and compileSdk in your build.gradle to 36 or higher....
```

这是旧测试包的真实结果，不是客户案例，也不是当前合规应用。一次致命失败扣 25 分，因此得分 75/100；分数不代表审核通过率。

[完整输出、固定来源、SHA-256 和复现方法](examples/README.md)：

```bash
python -X utf8 examples/reproduce_hello_world.py --download --check
```

此命令会在样例缺失时下载公开测试 APK、校验哈希后静态检查，不安装或运行 APK。样例没有原生库且未命中 SDK；这不能证明实际运行兼容或没有数据收集。

## 能力边界

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

源码要求 Python 3.10+；本版本在 Windows / Python 3.13.7 验证，并不代表完成所有系统和版本组合测试。AAB 解析还需要兼容仓库 bundletool 的 Java 运行环境；APK 检查不需要 Java。

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

## 按问题查阅指南

以下专题正文为英文，与默认 README 面向同一开发者群体：

- [检查 APK/AAB 的 16 KB ELF 对齐](docs/16kb-elf-alignment.md)：定位库文件，区分 ELF、ZIP 和运行验证。
- [检查 Target SDK 和 Manifest 权限](docs/target-sdk-manifest.md)：理解解析结果、设备例外及受限权限。
- [用 SDK 检测辅助 Data Safety 复核](docs/sdk-data-safety-review.md)：按实际配置核对收集、共享、用途和删除方式。
- [可复现检查案例](examples/README.md)：公开 APK 的真实输出与明确标注的合成 ELF 样例。

## 评分、规则与版本

Web 与 CLI 共用 100 分起算、致命失败扣 25、高危失败扣 15、警告扣 5、最低 15 分的评分规则，仅用于汇总静态风险。

按 2026-10-28 核验的规则，普通应用新提交及更新要求 API 36；Manifest 必需设备特性识别 Wear OS/Automotive 35、TV/XR 34 例外。存量可见性和延期资格需分别核实。[Google 官方要求](https://developer.android.com/google/play/requirements/target-sdk)

```bash
python -m unittest discover tests
python -X utf8 examples/elf_alignment_demo.py
```

[v0.1.0 版本说明](CHANGELOG.md) 记录当前功能、实际验证和已知限制。CLI 版本号与 Web 后端独立；目前从源码安装，没有 PyPI 包或编译后二进制发行物。仓库内共享 CSV 生成器供开发调用，不代表 CLI 已提供终端填答流程。

## 开源许可

[MIT](LICENSE)。示例 APK 仅引用上游固定版本，不随仓库或 Release 分发。
