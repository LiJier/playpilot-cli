from typing import List, Dict, Any

class PromptGenerator:
    @staticmethod
    def generate_all_in_one_prompt(
        manifest: Dict[str, Any], 
        findings: List[Dict[str, Any]], 
        lang: str = "zh",
        framework_info: Dict[str, Any] = None
    ) -> str:
        """
        Generates a consolidated, master prompt to feed into any AI coding Agent for one-click app remediation.
        Differentiates actionable code issues from pure console declarations so AI does not hallucinate unnecessary code changes.
        Supports framework-specific guidance (Flutter, React Native, Unity, etc.) and bilingual generation ('zh' / 'en').
        """
        is_en = (lang == "en")

        # Filter issues that actually require code/manifest modification
        code_issues = [
            f for f in findings 
            if f.get("status") == "FAIL" 
            and f.get("requires_code_fix", True) 
            and f.get("prompt", "").strip()
        ]
        
        # Filter operational/console reminders (no code changes required)
        console_notices = [
            f for f in findings
            if f.get("status") in ["FAIL", "WARN"]
            and not f.get("requires_code_fix", True)
        ]

        if not code_issues and not console_notices:
            return (
                "🎉 All checks passed! Current package requires no Google Play compliance fixes."
                if is_en else
                "🎉 检查通过！当前安装包配置正常，无需修改代码。"
            )

        pkg_name = manifest.get("package_name", "your.app.package")
        target_sdk = manifest.get("target_sdk", "Unknown" if is_en else "未知")

        # Scenario A: Code is 100% compliant, only Console questionnaire advice needed
        if not code_issues and console_notices:
            if is_en:
                lines = [
                    f"# Google Play Compliance Status: Code fully compliant, no code changes needed",
                    f"Package: `{pkg_name}` | Target SDK: `{target_sdk}`",
                    f"",
                    f"🎉 **Conclusion**: Application code and AndroidManifest are compliant. No code modifications needed.",
                    f"",
                    f"---",
                    f"### 📋 Google Play Console Questionnaire Advice (Web console settings only, no code changes):"
                ]
                for idx, notice in enumerate(console_notices, 1):
                    lines.append(f"{idx}. **{notice.get('title')}**")
                    lines.append(f"   * **Analysis**: {notice.get('message')}")
                    lines.append(f"   * **Console Action**: {notice.get('remediation')}")
                return "\n".join(lines)
            else:
                lines = [
                    f"# Google Play 上架合规预检：配置正常，无需修改代码",
                    f"应用包名: `{pkg_name}` | Target SDK: `{target_sdk}`",
                    f"",
                    f"🎉 **检查结论**：当前安装包代码与配置正常，**无需修改代码**。",
                    f"",
                    f"---",
                    f"### 📋 Google Play Console 后台问卷填报提示（仅需在网页后台勾选，无需改动代码）："
                ]
                for idx, notice in enumerate(console_notices, 1):
                    lines.append(f"{idx}. **{notice.get('title')}**")
                    lines.append(f"   * **分析说明**：{notice.get('message')}")
                    lines.append(f"   * **后台操作**：{notice.get('remediation')}")
                return "\n".join(lines)

        # Scenario B: There are actionable code issues
        fw_extra_en = ""
        fw_extra_zh = ""
        if framework_info and framework_info.get("is_cross_platform"):
            fw_name = framework_info.get("name", "Cross-Platform")
            fw_hint_en = framework_info.get("config_hint", {}).get("en", "")
            fw_hint_zh = framework_info.get("config_hint", {}).get("zh", "")
            fw_extra_en = f"Framework: `{fw_name}` (Cross-Platform)\nProject Architecture Note: This project is built using {fw_name}. {fw_hint_en}\n"
            fw_extra_zh = f"开发架构: `{fw_name}`（跨端框架）\n项目结构注意: 本项目基于 {fw_name} 构建。{fw_hint_zh}\n"

        if is_en:
            header = f"""# Google Play Compliance Remediation Prompt (AI Agent)
Package: `{pkg_name}`
Target SDK: `{target_sdk}`
{fw_extra_en}
My Android application received compliance violations during Google Play Console pre-flight checks. As a professional Android engineer / AI coding Agent, please inspect the details and provide the updated complete code:
"""
            body_parts = []
            for idx, issue in enumerate(code_issues, 1):
                severity = issue.get("severity", "")
                title = issue.get("title", "")
                msg = issue.get("message", "")
                prompt = issue.get("prompt", "")
                fw_hint = issue.get("framework_hint", "")
                fw_section = f"\n* **Framework Guidance**: {fw_hint}\n" if fw_hint else "\n"
                
                part = f"""---
### Task {idx}: [{severity}] {title}
* **Violation Details**: {msg}
* **Remediation Requirement**:{fw_section}
{prompt}
"""
                body_parts.append(part)

            footer = """---
### Delivery Requirements:
1. Make minimal necessary changes to existing code and manifest files (prioritize project configuration files).
2. Maintain backward compatibility, ensuring smooth compilation and stability on Android 14+ as well as older OS versions.
3. Output complete modified code snippets and indicate exact file paths.
"""
            if console_notices:
                footer += "\n---\n### 💡 Note: Play Console Questionnaire Reminders (Web console settings only, no code modifications needed):\n"
                for n in console_notices:
                    footer += f"- **{n.get('title')}**: {n.get('remediation')}\n"

            return header + "\n".join(body_parts) + "\n" + footer
        else:
            header = f"""# Google Play 上架合规修改建议
应用包名: `{pkg_name}`
当前 Target SDK: `{target_sdk}`
{fw_extra_zh}
我的 Android 应用在提审前检查发现以下需要调整的配置或代码项，请参考下方说明协助完成修改：
"""
            body_parts = []
            for idx, issue in enumerate(code_issues, 1):
                severity = issue.get("severity", "")
                title = issue.get("title", "")
                msg = issue.get("message", "")
                prompt = issue.get("prompt", "")
                fw_hint = issue.get("framework_hint", "")
                fw_section = f"\n* **跨端适配提示**：{fw_hint}\n" if fw_hint else "\n"
                
                part = f"""---
### 问题 {idx}：[{severity}] {title}
* **问题说明**：{msg}
* **修改建议**：{fw_section}
{prompt}
"""
                body_parts.append(part)

            footer = """---
### 修改要求：
1. 仅针对上述存在明确问题的代码或配置文件进行最小化修改（结合对应开发框架的项目结构优先检查对应配置文件）。
2. 保持代码向后兼容，确保修改后在 Android 14+ 以及低版本系统均能正常编译和稳定运行。
3. 请直接输出修改后的完整代码片段，并标明修改的文件路径。
"""
            if console_notices:
                footer += "\n---\n### 💡 附：Play Console 控制台问卷填报提示（仅需在网页后台勾选，无需改动代码）：\n"
                for n in console_notices:
                    footer += f"- **{n.get('title')}**：{n.get('remediation')}\n"

            return header + "\n".join(body_parts) + "\n" + footer

