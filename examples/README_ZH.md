# 检查示例与复现方法

[English](README.md) · [项目说明](../README_ZH.md)

## 公开 APK：检查过低的 Target SDK

这里使用 Androguard 的公开 `hello-world.apk`。2026-10-28 实际运行 PlayPilot 后，保存了中英文终端输出，仅统一换行并去掉行尾空格。

- [上游 APK 的固定版本](https://github.com/androguard/androguard/blob/581f7a3251545a97f66ee92b674dd810ee380a00/tests/data/APK/hello-world.apk)
- [下载地址、SHA-256、文件大小和命令](hello-world-source.json)
- [中文诊断输出](hello-world-cli.zh.txt) · [英文诊断输出](hello-world-cli.txt)

检查时使用 Windows / Python 3.13.7，核心代码对应提交 [`f2f2c24`](https://github.com/LiJier/playpilot-cli/commit/f2f2c243800b7ff4ae66e655345746e1a7570bfb)。后续文档更新未修改检测引擎。

安装项目依赖后运行：

```bash
python -X utf8 examples/reproduce_hello_world.py --download --lang zh --check
```

脚本会在样例缺失时下载固定版本的 APK，核对 SHA-256 后保存在已忽略的 `downloads/` 目录中，再调用 CLI 静态检查。APK 不会被安装或运行，也不随仓库或 Release 分发。

`--check` 会比较本次输出和已保存的记录；有差异时显示差异，不覆盖原文件。规则或依赖更新后，结果可能变化。去掉 `--lang zh` 可复现英文输出。

这次检查得到：

| 项目 | 结果 |
| --- | --- |
| 包名 | `de.rhab.helloworld` |
| Target SDK / Min SDK | 25 / 21 |
| 已识别 SDK | 0 |
| 原生库 | 未发现 |
| 规则结果 | 1 项致命风险，得分 75/100 |

这个旧测试包适合演示 Target SDK 提示，不是线上应用案例。此次没有提供隐私网址，因此也没有验证隐私网页。未命中 SDK 不等于没有数据收集；原生库进度行中的 `Safe` 仅表示这次没有发现库文件。

## 合成 ELF 文件头：比较 4 KB 与 16 KB 对齐

```bash
python -X utf8 examples/elf_alignment_demo.py
```

脚本在临时 ZIP 中生成两个 ELF64 文件头，调用实际的 `ElfScanner` 检查并输出结果，结束后删除生成文件：

```text
Synthetic ELF headers; not an APK or runtime compatibility test.
lib/arm64-v8a/lib4kb.so | PT_LOAD 0x1000 | FAIL
lib/arm64-v8a/lib16kb.so | PT_LOAD 0x4000 | PASS
Libraries: 2; require review: 1
```

`0x1000` 是 4 KB，对齐检查失败；`0x4000` 是 16 KB，检查通过。这些只有文件头的样例不能加载运行。检查实际应用时，还要验证 APK ZIP 对齐以及 16 KB 设备上的运行情况，详见 [ELF 对齐指南](../docs/16kb-elf-alignment.zh.md)。
