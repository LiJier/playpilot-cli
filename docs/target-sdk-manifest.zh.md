# 检查 Target SDK 和 Manifest 权限

[English](target-sdk-manifest.md) · [项目说明](../README_ZH.md) · [真实检查示例](../examples/README_ZH.md) · [16 KB ELF 对齐](16kb-elf-alignment.zh.md)

Gradle 和源码中的 Manifest 是构建配置。实际发布包还会合并依赖的 Manifest，因此应检查最终生成的 APK 或 AAB。

## 查看安装包信息

```bash
python -X utf8 cli.py path/to/app-release.apk --lang zh
```

PlayPilot 会输出包名、Min SDK、Target SDK、识别到的 SDK 和规则结果。APK 使用 `pyaxmlparser` 解析；AAB 通过仓库内的 `bundletool.jar` 提取 Manifest，需要兼容的 Java 运行环境。

如果包名是 `unknown.apk`、SDK 值为 `0`，或出现解析问题，应先排查文件和解析环境。缺少这些信息时，后面的规则结果可能不完整。

## 判断 Target SDK 是否需要升级

当前规则对普通应用的新提交和更新检查 API 36。通过 Manifest 中的必需设备特性，识别 Wear OS/Automotive 的 API 35 和 TV/XR 的 API 34 例外；可选设备特性不会降低普通应用的检查门槛。

存量应用的可见性、组织内部私有分发和延期资格，需要在 Play Console 单独确认。[Google 官方目标 API 要求](https://developer.android.com/google/play/requirements/target-sdk?hl=zh-cn)的本次核对日期为 2026-10-28。

[公开测试包示例](../examples/README_ZH.md)的 Target SDK 为 25，实际运行得到：

```text
  COMPLIANCE SCORE: 75 / 100
  Findings: 1 Fatal | 0 High Risk | 0 Warnings
```

一次致命失败扣 25 分，所以得分为 75。这个分数用于汇总风险，不代表审核通过率。该测试包没有原生库，不能用来验证 16 KB 运行兼容性。

## 找到权限和前台服务声明的来源

根据终端提示，查看合并后的 Manifest，确认权限来自自己的代码还是某个依赖。当前规则覆盖部分受限权限、全量应用查询、存储和媒体访问、广告 ID、精确闹钟、全屏意图及前台服务声明。

移除权限前，先确认对应功能是否需要它。填写前台服务类型时，也要以服务实际执行的工作为准；受限权限是否允许使用，仍需结合应用用途和 Google Play 要求判断。修改后重新构建，再检查发布包。

要查看解析出的完整 Manifest 信息，可在仓库根目录运行：

```python
import json
import sys
sys.path.insert(0, "src")
from analyzer.manifest_parser import ManifestParser

print(json.dumps(ManifestParser().parse("path/to/app-release.apk"), indent=2, ensure_ascii=False))
```

## 检查隐私网址

```bash
python -X utf8 cli.py path/to/app-release.apk --lang zh --privacy-url https://example.com/privacy
```

将示例网址换成自己的隐私政策页面。`--privacy-url` 会实际请求网址，检查可访问性、重定向和 TLS 证书；协议内容是否准确、完整，需要另行检查。

`--account-del-url` 把账号删除网址交给规则引擎，不会测试实际删除流程。

## 在 CI 中使用

当前 CLI 即使发现失败项，也可能返回退出码 `0`，尚未提供根据规则结果阻止构建的选项或结构化报告参数。将它接入 CI 后，需要查看检查结果，不能仅凭命令成功结束就判定构建合规。

[网页政策参考](https://play.ljcan.com/policies/) · [Data Safety 复核指南](sdk-data-safety-review.zh.md)
