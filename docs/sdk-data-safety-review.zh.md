# 根据 SDK 检测结果复核 Data Safety 声明

[English](sdk-data-safety-review.md) · [项目说明](../README_ZH.md) · [Target SDK 与权限](target-sdk-manifest.zh.md) · [检查示例](../examples/README_ZH.md)

识别出一个 SDK 后，还要确认应用启用了它的哪些功能、发送了什么数据，以及接收方如何处理。仅凭 SDK 名称，无法填写完整的数据安全声明。

## 查看检测结果

```bash
python -X utf8 cli.py path/to/app-release.apk --lang zh
```

CLI 会列出识别到的 SDK 名称和相关规则结果。检测使用 DEX 中的已知字节前缀，不运行应用，也不能据此确定 SDK 版本。混淆、动态加载和未收录的 SDK 可能漏检。

自己的业务代码、WebView 和服务端数据传输也需要检查。示例中的 hello-world APK 没有命中 SDK，但这并不能说明应用没有收集数据。

要查看签名库中与 SDK 关联的数据类型和用途，可在仓库根目录运行下面的代码，替换安装包路径：

```python
import json
import sys
sys.path.insert(0, "src")
from analyzer.dex_scanner import DexScanner

for sdk in DexScanner().scan("path/to/app-release.apk"):
    print(sdk["name"])
    print(json.dumps(sdk.get("data_safety", {}), indent=2, ensure_ascii=False))
```

这些字段用于提示需要复核的事项。SDK 级别的用途不一定适用于每一种数据，`shared_with_third_parties` 也不能直接代替 Google Play 对“共享”的判断。

## 逐项核对实际行为

对每一种相关数据，记录启用的功能、发送时机、目的地、接收方角色、收集用途、共享用途，以及用户能否选择不提供。最好同时保留配置或测试记录，方便后续版本复查。

| 要确认的问题 | 可以查阅的依据 |
| --- | --- |
| 按 Google 定义，属于收集、共享、两者都有，还是均不属于？ | 实际数据流、SDK 说明、合同及共享例外情形 |
| 所有相关用户是否都能选择不收集？ | 同意设置、退出或启用入口，以及拒绝后的应用功能 |
| 是否仅作临时处理？ | 数据是否只保存在内存中，用于处理实时请求；同时检查服务端和 SDK |
| 相关数据是否全部在传输中加密？ | 每个端点和传输路径，不能只检查主业务 API |
| 用户如何删除数据？ | 实际账号注销、数据删除入口及保留期限 |

[Google 官方 Data Safety 说明](https://support.google.com/googleplay/android-developer/answer/10787469?hl=zh-Hans)解释了收集、共享和例外情形。本次核对日期为 2026-10-28；应用及所用 SDK 的声明准确性由开发者负责。

## 填写问卷并导出

当前 CLI 没有交互问卷、答案文件输入或 CSV 导出参数。仓库保留了共享生成器，供开发者在代码中调用。

可在[网页工作台](https://play.ljcan.com/)查看 SDK 候选数据，补充扫描未发现的数据类型，再分别填写收集、共享、用途等答案。网页也支持对比从目标 Play Console 账号导出的 CSV 模板。

暂时无法确认的答案可以留空并下载草稿；完成必填项、通过校验并确认后，才能导出已确认 CSV。未检测到 SDK 或未提供删除网址，不会自动填成“全部加密”“无账号”或“90 天内删除”。

导入前，先从 Play Console 导出原有答案作为备份，因为导入会覆盖现有内容。导入后再核对控制台中的答案。模板匹配和本地校验通过，只能说明文件满足工具支持的格式与填写规则，不能证明实际数据行为已核实，也不能保证审核通过；项目尚未在你的目标账号中验证真实导入。

[网页 Data Safety 填报指南](https://play.ljcan.com/guides/google-play-data-safety/)
