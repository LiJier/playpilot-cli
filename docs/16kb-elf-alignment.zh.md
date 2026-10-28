# 检查 APK/AAB 的 16 KB ELF 对齐

[English](16kb-elf-alignment.md) · [项目说明](../README_ZH.md) · [检查示例](../examples/README_ZH.md) · [Target SDK 与权限](target-sdk-manifest.zh.md)

应用里的原生库可能来自自己的 C/C++ 代码，也可能由框架或 SDK 引入。修改 `targetSdk` 不会改变已有 `.so` 文件的对齐方式，需要检查实际发布包。

## 运行检查

[安装依赖](../README_ZH.md#安装)后执行：

```bash
python -X utf8 cli.py path/to/app-release.apk --lang zh
# 检查 AAB 还需要 Java 和仓库中的 bundletool
python -X utf8 cli.py path/to/app-release.aab --lang zh
```

终端会显示原生库检查汇总和规则结果。要查看具体库路径、ABI 和对齐值，可在仓库根目录运行下面的 Python 代码，将路径换成自己的安装包：

```python
import sys
sys.path.insert(0, "src")
from analyzer.elf_scanner import ElfScanner

result = ElfScanner().scan("path/to/app-release.apk")
for lib in result["libraries"]:
    print(lib["path"], lib["abi"], lib["min_load_align_hex"], lib["is_16kb_aligned"])
```

扫描器检查 ELF 的 `PT_LOAD` 段对齐，以及加载地址与文件偏移的关系。16 KB 对应 `0x4000`；不满足条件的 64 位库会被标出。常见的目标 ABI 目录是 `arm64-v8a` 和 `x86_64`。

如果结果为空，先确认包里是否确实没有原生库。损坏或无法解析的库可能被跳过，不能只凭空列表判断兼容性。

仓库里有一个小示例：

```bash
python -X utf8 examples/elf_alignment_demo.py
```

它生成两个 ELF 文件头并调用扫描器：`0x1000` 检查失败，`0x4000` 检查通过。文件头仅用于演示，不是可以加载运行的库。

## 分别检查 ELF、APK 打包和实际运行

先从发布包中解出有问题的 `.so`，再使用 Android NDK 和 SDK Build Tools 检查：

```bash
llvm-readelf -lW libexample.so
zipalign -c -P 16 -v 4 app-release.apk
```

查看 `llvm-readelf` 输出中 `LOAD` 行的 `Align` 列。PlayPilot 不执行 `zipalign`，APK 内库文件的 ZIP 对齐需要单独检查。

AAB 是发布容器，还要检查由它生成的 APK。最后在 16 KB 设备或模拟器上验证启动和关键功能，确认库能够正常加载。

## 找到库的来源，再重新构建

- **自己的原生代码**：按 Android 官方指南调整 NDK、链接和打包配置，重新编译。
- **第三方 SDK**：向提供商获取兼容版本，并确认最终包没有混入旧库。
- **Flutter、React Native、Unity 等框架**：同时检查引擎和原生插件。识别出框架名称，并不意味着其所有库都已兼容。

重建后，对同一份发布产物重新执行上述检查，并保存结果。

截至 2026-10-28，Android 官方指南要求 Google Play 上面向 API 35 及以上的应用在 64 位设备上支持 16 KB 页面，并列出 2027-02-01 为不兼容更新的发布阻断日期。提交前请查看最新官方要求和 Play Console 通知。

[Android 官方：支持 16 KB 页面](https://developer.android.com/guide/practices/page-sizes?hl=zh-cn) · [网页检查步骤](https://play.ljcan.com/guides/16kb-page-alignment/)
