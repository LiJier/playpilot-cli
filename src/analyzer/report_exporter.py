from datetime import datetime
from typing import Dict, Any, List, Optional

class ReportExporter:
    """
    Generates structured, professional Markdown compliance audit reports.
    Supports both Chinese ('zh') and English ('en').
    """

    @staticmethod
    def generate_markdown_report(
        manifest: Dict[str, Any],
        eval_result: Dict[str, Any],
        detected_sdks: List[Dict[str, Any]],
        data_safety_report: Dict[str, Any],
        all_prompt: str,
        lang: str = "zh"
    ) -> str:
        is_en = (lang == "en")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        pkg = manifest.get("package_name", "unknown")
        ver_name = manifest.get("version_name", "1.0.0")
        ver_code = manifest.get("version_code", "1")
        target_sdk = manifest.get("target_sdk", "unknown")
        min_sdk = manifest.get("min_sdk", "unknown")
        status_text = eval_result.get("status_text", "UNKNOWN")
        counts = eval_result.get("counts", {"fatal": 0, "high": 0, "warn": 0, "pass": 0})

        if is_en:
            title = "# PlayPilot - Google Play Pre-flight Compliance Report"
            meta_header = "## 📱 Application Metadata"
            summary_header = "## 📊 Executive Summary"
            findings_header = "## 🔍 Policy Inspection Findings"
            sdk_header = "## 🧩 Detected Third-Party SDKs & Data Safety"
            prompt_header = "## 💡 Code Fix Suggestions (Remediation Prompt)"
            disclaimer_header = "## ⚖️ Disclaimer"
            disclaimer_text = (
                "> **Disclaimer**: This audit is based on static analysis of package metadata, bytecode, "
                "and public Google Play policies. It serves as pre-submission reference and does not guarantee "
                "official Google Play approval, as actual review outcomes are determined by Google."
            )
            labels = {
                "package": "Package Name",
                "version": "Version",
                "target_sdk": "Target SDK",
                "min_sdk": "Minimum SDK",
                "audit_time": "Audit Time",
                "status": "Audit Status",
                "fatal": "Fatal Blockers",
                "high": "High Risk Violations",
                "warn": "Warnings & Recommendations",
                "pass": "Passed Checks",
                "sdks": "Detected SDKs",
                "problem": "Issue Description",
                "remediation": "Remediation Advice",
                "diff": "Recommended Code Diff",
                "doc": "Official Documentation",
                "sdk_table_name": "SDK Name",
                "sdk_table_cat": "Category",
                "sdk_table_data": "Collected Data",
                "sdk_table_purposes": "Purposes",
                "sdk_table_shared": "Shared 3rd Party"
            }
        else:
            title = "# PlayPilot - Google Play 上架合规预检报告"
            meta_header = "## 📱 应用基础信息 (Application Metadata)"
            summary_header = "## 📊 检查概览 (Summary)"
            findings_header = "## 🔍 检查项明细 (Policy Findings)"
            sdk_header = "## 🧩 第三方 SDK 与数据安全 (Data Safety)"
            prompt_header = "## 💡 代码修复建议 (Remediation Prompt)"
            disclaimer_header = "## ⚖️ 免责声明 (Disclaimer)"
            disclaimer_text = (
                "> **免责声明**：本检查报告基于安装包静态分析与 Google Play 公开政策进行自查参考。"
                "通过预检不代表保证通过 Google Play 官方审核，实际审核结果以 Google 官方为准。"
            )
            labels = {
                "package": "应用包名",
                "version": "应用版本",
                "target_sdk": "Target SDK",
                "min_sdk": "最低 Min SDK",
                "audit_time": "检查生成时间",
                "status": "检查结论",
                "fatal": "严重问题",
                "high": "重点关注项",
                "warn": "建议排查项",
                "pass": "检查通过项",
                "sdks": "第三方 SDK 数",
                "problem": "问题说明",
                "remediation": "修复建议",
                "diff": "建议代码变更 (Code Diff)",
                "doc": "官方政策参考",
                "sdk_table_name": "SDK 名称",
                "sdk_table_cat": "类型",
                "sdk_table_data": "收集的数据类型",
                "sdk_table_purposes": "收集用途",
                "sdk_table_shared": "是否共享给第三方"
            }

        lines = [
            title,
            "",
            f"*{labels['audit_time']}*: `{now_str}` | *PlayPilot Engine Version*: `v1.3.0`",
            "",
            "---",
            "",
            meta_header,
            f"- **{labels['package']}**: `{pkg}`",
            f"- **{labels['version']}**: `{ver_name}` (VersionCode: `{ver_code}`)",
            f"- **{labels['target_sdk']}**: `API {target_sdk}`",
            f"- **{labels['min_sdk']}**: `API {min_sdk}`",
            "",
            summary_header,
            f"**{labels['status']}**: **{status_text}**",
            "",
            f"| {labels['fatal']} | {labels['high']} | {labels['warn']} | {labels['pass']} | {labels['sdks']} |",
            "| :---: | :---: | :---: | :---: | :---: |",
            f"| `{counts.get('fatal', 0)}` | `{counts.get('high', 0)}` | `{counts.get('warn', 0)}` | `{counts.get('pass', 0)}` | `{len(detected_sdks)}` |",
            "",
            "---",
            "",
            findings_header,
            ""
        ]

        # Detailed findings
        for finding in eval_result.get("findings", []):
            status = finding["status"]
            sev = finding.get("severity", "LOW")
            if status == "FAIL" and sev == "FATAL":
                icon = "🛑"
                badge = "FATAL" if is_en else "致命拦截"
            elif status == "FAIL":
                icon = "⚠️"
                badge = "HIGH RISK" if is_en else "高危风险"
            elif status == "WARN":
                icon = "⚡"
                badge = "WARN" if is_en else "优化建议"
            else:
                icon = "✅"
                badge = "PASS" if is_en else "合规通过"

            lines.append(f"### {icon} [{badge}] {finding.get('title', '')}")
            lines.append(f"- **{labels['problem']}**: {finding.get('message', '')}")
            if finding.get("remediation"):
                lines.append(f"- **{labels['remediation']}**: {finding['remediation']}")
            if finding.get("code_diff"):
                lines.append(f"- **{labels['diff']}**:")
                lines.append("```diff")
                lines.append(finding["code_diff"].strip())
                lines.append("```")
            if finding.get("doc_url"):
                lines.append(f"- **{labels['doc']}**: [{finding['doc_url']}]({finding['doc_url']})")
            lines.append("")

        # SDK and Data Safety section
        lines.append("---")
        lines.append("")
        lines.append(sdk_header)
        lines.append("")
        if data_safety_report.get("table_rows"):
            lines.append(f"| {labels['sdk_table_name']} | {labels['sdk_table_cat']} | {labels['sdk_table_data']} | {labels['sdk_table_purposes']} | {labels['sdk_table_shared']} |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for row in data_safety_report["table_rows"]:
                name = row.get("sdk_name", "")
                cat = row.get("category", "")
                collected = row.get("collected_data", "")
                purposes = row.get("purposes", "")
                shared = row.get("shared_with_third_parties", "")
                lines.append(f"| **{name}** | {cat} | {collected} | {purposes} | {shared} |")
            lines.append("")
        else:
            clean_text = (
                "No third-party data collection SDKs detected. Application complies with minimal data policy."
                if is_en else
                "未检测到具有隐私数据收集行为的第三方 SDK，应用属于干净包体。"
            )
            lines.append(f"> {clean_text}\n")

        # Prompt section
        lines.append("---")
        lines.append("")
        lines.append(prompt_header)
        lines.append("")
        lines.append("```markdown")
        lines.append(all_prompt.strip())
        lines.append("```")
        lines.append("")

        # Disclaimer
        lines.append("---")
        lines.append("")
        lines.append(disclaimer_header)
        lines.append("")
        lines.append(disclaimer_text)
        lines.append("")

        return "\n".join(lines)
