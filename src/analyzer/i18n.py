# -*- coding: utf-8 -*-
"""
# PlayPilot i18n Translation Dictionary & Helper Module
Provides bilingual (zh/en) support for UI, Data Safety items, and report generations.
"""

DATA_TYPES_I18N = {
    "Approximate location": {
        "zh": "粗略位置 (Approximate location)",
        "en": "Approximate location"
    },
    "Precise location": {
        "zh": "精确位置 (Precise location)",
        "en": "Precise location"
    },
    "Name": {
        "zh": "姓名 (Name)",
        "en": "Name"
    },
    "Email address": {
        "zh": "电子邮件地址 (Email address)",
        "en": "Email address"
    },
    "User IDs": {
        "zh": "用户 ID (User IDs)",
        "en": "User IDs"
    },
    "Address": {
        "zh": "住址/物理地址 (Address)",
        "en": "Address"
    },
    "Phone number": {
        "zh": "电话号码 (Phone number)",
        "en": "Phone number"
    },
    "Purchase history": {
        "zh": "购买/充值记录 (Purchase history)",
        "en": "Purchase history"
    },
    "User payment info": {
        "zh": "用户支付信息 (User payment info)",
        "en": "User payment info"
    },
    "Crash logs": {
        "zh": "崩溃日志与调用栈 (Crash logs)",
        "en": "Crash logs"
    },
    "Diagnostics": {
        "zh": "性能与诊断数据 (Diagnostics)",
        "en": "Diagnostics"
    },
    "App interactions": {
        "zh": "应用互动与展示事件 (App interactions)",
        "en": "App interactions"
    },
    "In-app search history": {
        "zh": "应用内搜索历史 (In-app search history)",
        "en": "In-app search history"
    },
    "Installed apps": {
        "zh": "已安装的应用列表 (Installed apps)",
        "en": "Installed apps"
    },
    "Other user-generated content": {
        "zh": "用户生成内容/提示词 (Other user-generated content)",
        "en": "Other user-generated content"
    },
    "Voice or sound recordings": {
        "zh": "语音或录音文件 (Voice or sound recordings)",
        "en": "Voice or sound recordings"
    },
    "Device or other IDs": {
        "zh": "设备或其他 ID (Device or other IDs)",
        "en": "Device or other IDs"
    }
}

PURPOSES_I18N = {
    "App functionality": {
        "zh": "应用功能 (App functionality)",
        "en": "App functionality"
    },
    "Analytics": {
        "zh": "数据分析 (Analytics)",
        "en": "Analytics"
    },
    "Developer communications": {
        "zh": "开发者通信 (Developer communications)",
        "en": "Developer communications"
    },
    "Advertising or marketing": {
        "zh": "商业广告或营销 (Advertising or marketing)",
        "en": "Advertising or marketing"
    },
    "Fraud prevention, security, and compliance": {
        "zh": "防欺诈、安全与合规 (Fraud prevention, security, and compliance)",
        "en": "Fraud prevention, security, and compliance"
    },
    "Personalization": {
        "zh": "个性化推荐 (Personalization)",
        "en": "Personalization"
    },
    "Account management": {
        "zh": "账号管理体系 (Account management)",
        "en": "Account management"
    }
}

UI_STRINGS = {
    "zh": {
        "page_title": "PlayPilot - Google Play 上架合规预检工具",
        "sidebar_title": "PlayPilot 控制台",
        "sidebar_subtitle": "v1.0.0 · Google Play 合规预检",
        "sidebar_core_policy": "#### 核心检查项",
        "sidebar_policies": """
    - ✅ **Target SDK >= 34** 适配要求
    - ✅ **Android 14 前台服务类型** 校验
    - ✅ **广告 ID (AD_ID)** 权限与声明匹配
    - ✅ **Data Safety 表单** 对照整理
    - ✅ **高危受限权限** 检查
    - ✅ **隐私政策 URL** 可访问性与 SSL 检查
        """,
        "sidebar_zero_retention_title": "#### 🔒 隐私与数据安全",
        "sidebar_zero_retention_desc": "上传的安装包仅在检查期间临时分析，检查完成后会自动清除，不会保存或外传你的应用文件与代码。",
        "main_title": "Google Play 上架合规预检 (PlayPilot)",
        "main_subtitle": "提审前排查 Android 应用常见被拒风险，提供修改建议与数据安全表单对照",
        "upload_label": "拖拽或选择你的 Android 安装包 (.aab 或 .apk)",
        "upload_help": "支持最大 200MB 的 Google Play AAB 或 APK 安装包。",
        "privacy_url_placeholder": "https://yourdomain.com/privacy.html",
        "privacy_url_help": "可选。填写后将自动检查链接是否正常可访问及 SSL 证书是否有效。",
        "demo_btn": "查看示例应用",
        "reset_btn": "清除重置",
        "scanning": "正在分析安装包内容并检查合规项...",
        "metric_status": "检查状态",
        "metric_target_sdk": "Target SDK",
        "metric_fatal": "严重问题",
        "metric_warn": "建议关注项",
        "metric_sdks": "第三方 SDK 数",
        "app_package": "应用包名",
        "app_version": "版本",
        "tab_report": "合规检查报告",
        "tab_prompts": "代码修复建议",
        "tab_safety": "Data Safety 表单对照表",
        "tab_manifest": "包体解析详情",
        "report_title": "Google Play 规则检查清单",
        "prompts_title": "代码修复建议 (Prompt)",
        "prompts_desc": "可将下方修改建议复制给 Cursor、Claude 或 Copilot 等工具辅助修改：",
        "safety_title": "Play Console 数据安全表单（Data Safety）对照表",
        "safety_desc": "根据检测到的第三方 SDK，整理出对应的数据安全表单内容，方便在 Play Console 后台对照填报：",
        "safety_col_name": "SDK 名称",
        "safety_col_category": "类别",
        "safety_col_data": "收集的数据类型",
        "safety_col_purposes": "主要用途",
        "safety_col_shared": "是否与第三方共享",
        "safety_col_doc": "官方披露规范",
        "safety_clean_msg": "未检测到常见的第三方广告或统计 SDK。",
        "safety_console_rec": "#### Play Console 数据安全表单填报参考：",
        "manifest_title": "清单基础属性解析",
        "manifest_perms_title": "申请的所有权限 (Permissions)",
        "disclaimer": "**免责声明**：PlayPilot 的检测结果基于 Google Play 公开政策及安装包静态分析，仅供提审前自查参考，不代表 Google 官方审核结果。",
        "fatal_badge": "严重问题 (FATAL)",
        "high_badge": "重点关注 (HIGH)",
        "warn_badge": "建议排查 (WARN)",
        "pass_badge": "检查通过 (PASS)",
        "problem_desc": "问题说明",
        "remediation_advice": "💡 修复建议",
        "official_doc_ref": "📖 官方政策参考",
        "yes": "是 (Yes)",
        "no": "否 (No)",
        "export_report_btn": "导出检查报告 (.md)",
        "export_csv_btn": "导出数据安全表单 CSV",
        "csv_export_hint": "💡 **导入指引**：在 Google Play Console 进入应用 -> 左侧菜单「应用内容」->「数据安全」-> 点击右上角「从 CSV 导入」，上传此文件即可完成问卷导入，无需手动逐项勾选。",
        "code_diff_title": "建议代码修改对照:",
        "rule_prompt_title": "代码修复建议 (Prompt)",
        "copy_prompt_hint": "可复制下方提示词发给 Cursor 或 Copilot 辅助修改本项：",
        "account_deletion_url_input": "账号删除网址 (可选，如支持注册账号)",
        "account_deletion_url_help": "若应用支持创建账号，在此填写账号注销申请网址，将自动生成在 Data Safety CSV 中。",
        "nav_home": "首页",
        "nav_inspect": "开始检查",
        "nav_records": "检查记录",
        "nav_docs": "审核指南",
        "nav_settings": "设置与语言",
        "promo_card_title": "提审前自查",
        "promo_card_desc": "排查常见审查项，降低被拒风险。",
        "promo_card_btn": "了解更多",
        "hero_title": "Google Play 上架审核预检",
        "hero_desc": "提前排查常见合规问题，避免提交后因违规被拒。",
        "hero_badge_policy": "覆盖官方审核重点",
        "hero_badge_speed": "本地静态分析，快速反馈",
        "hero_badge_remedy": "提供具体修改建议",
        "mode_package": "AAB / APK 包体检查",
        "mode_demo": "内置示例数据体验",
        "app_name_input": "应用名称 (可选)",
        "app_name_placeholder": "例如：MyApp 出海应用",
        "app_pkg_input": "应用包名 (可选)",
        "app_pkg_placeholder": "例如：com.example.app (解析包体时自动填入)",
        "dropzone_title": "拖拽文件到此处，或点击上传",
        "dropzone_hint": "支持 AAB、APK 安装包文件，最大 200MB",
        "start_scan_btn": "▶ 开始检查",
        "diag_result_title": "检查结果示例",
        "score_risks_found": "发现 {n} 项潜在问题",
        "score_clean": "未发现明显风险",
        "score_advice_fix": "建议参考下方提示修改后，再提交 Google Play 审核。",
        "score_advice_clean": "未发现明显风险，可准备提交审核。",
        "cat_core_sdk": "Target SDK 与系统架构",
        "cat_core_sdk_desc": "Target SDK 34+ 适配、16KB 动态库页面对齐与权限规范",
        "cat_privacy_safety": "隐私政策与数据安全",
        "cat_privacy_safety_desc": "隐私政策网页检测与数据安全表单对照",
        "cat_foreground_service": "前台服务与后台行为",
        "cat_foreground_service_desc": "Android 14+ 前台服务类型声明校验",
        "cat_account_deletion": "账号注销规范",
        "cat_account_deletion_desc": "检查是否提供公开网页端账号注销方式",
        "cat_ad_monetization": "广告变现与 ID 申明",
        "cat_ad_monetization_desc": "广告 SDK 与广告 ID (AD_ID) 权限申明匹配",
        "cat_storage_photo": "存储权限与媒体访问",
        "cat_storage_photo_desc": "Photo Picker 免权限替代方案建议",
        "badge_issues_count": "发现 {n} 项问题",
        "badge_no_issues": "未发现问题",
        "tip_title": "温馨提示",
        "tip_desc": "以上结果仅供参考，最终审核结果以 Google Play 官方审核为准。建议在提交前仔细核对所有内容。",
        "recent_records_title": "最近检查记录",
        "view_details": "查看详情 →",
        "theme_selector": "🎨 主题风格",
        "theme_system": "系统",
        "theme_light": "浅色",
        "theme_dark": "暗黑",
        "fast_scan": "静态合规检查",
        "breadcrumb_audit": "Google Play 上架预检",
        "hero_upload_title": "上传安装包进行合规检查",
        "hero_upload_sub": "拖拽 AAB 或 APK 安装包至虚线区域，或点击选择文件",
        "start_audit_btn": "▶ 开始检查",
        "high_density_checklist": "检查项明细",
        "one_click_prompt": "复制修复建议",
        "health_score_title": "合规评分与概览"
    },
    "en": {
        "page_title": "PlayPilot - Google Play Pre-flight Compliance Inspector",
        "sidebar_title": "PlayPilot Console",
        "sidebar_subtitle": "v1.0.0 · Google Play Compliance Pre-check",
        "sidebar_core_policy": "#### Core Policies Covered",
        "sidebar_policies": """
    - ✅ **Target SDK >= 34** requirement
    - ✅ **Android 14 Foreground Service Types** validation
    - ✅ **Advertising ID (AD_ID)** declaration match
    - ✅ **Data Safety Questionnaire** reference mapping
    - ✅ **Restricted & High-Risk Permissions** inspection
    - ✅ **Privacy Policy URL** accessibility & SSL check
        """,
        "sidebar_zero_retention_title": "#### 🔒 Privacy & Data Protection",
        "sidebar_zero_retention_desc": "Uploaded packages are processed temporarily and removed immediately after analysis. We do not store or distribute your files or code.",
        "main_title": "Google Play Pre-flight Compliance Inspector (PlayPilot)",
        "main_subtitle": "Pre-flight compliance checks and code fix suggestions for Android developers",
        "upload_label": "Drag & drop your Android bundle (.aab or .apk)",
        "upload_help": "Supports Google Play AAB or APK files up to 200MB.",
        "privacy_url_placeholder": "https://yourdomain.com/privacy.html",
        "privacy_url_help": "Optional. Checks URL availability, HTTP status, and SSL certificate validity.",
        "demo_btn": "View Demo App",
        "reset_btn": "Clear & Reset",
        "scanning": "Analyzing package contents and checking compliance...",
        "metric_status": "Overall Status",
        "metric_target_sdk": "Target SDK",
        "metric_fatal": "Fatal Blockers",
        "metric_warn": "High Risk / Warnings",
        "metric_sdks": "SDKs Detected",
        "app_package": "Package",
        "app_version": "Version",
        "tab_report": "Policy Report",
        "tab_prompts": "Code Fix Suggestions",
        "tab_safety": "Data Safety Checklist",
        "tab_manifest": "Package Manifest",
        "report_title": "Google Play Policy Inspection Checklist",
        "prompts_title": "Code Fix Suggestions (Prompt)",
        "prompts_desc": "You can copy the suggestions below directly to Cursor, Claude, or Copilot:",
        "safety_title": "Play Console Data Safety Form Checklist",
        "safety_desc": "Based on detected SDKs, here is a reference checklist for your Play Console Data Safety questionnaire:",
        "safety_col_name": "SDK Name",
        "safety_col_category": "Category",
        "safety_col_data": "Collected Data Types",
        "safety_col_purposes": "Purposes",
        "safety_col_shared": "Shared with 3rd Parties",
        "safety_col_doc": "Official Disclosure",
        "safety_clean_msg": "No third-party ad or tracking SDKs detected.",
        "safety_console_rec": "#### Recommended Play Console Questionnaire Answers:",
        "manifest_title": "Manifest Properties Overview",
        "manifest_perms_title": "Declared Permissions",
        "disclaimer": "Disclaimer: PlayPilot provides static compliance checks based on public Google Play policies. It serves as pre-submission assistance and does not replace official Google Play review.",
        "fatal_badge": "FATAL BLOCKER",
        "high_badge": "HIGH RISK",
        "warn_badge": "DISCLOSURE NOTICE",
        "pass_badge": "PASSED",
        "problem_desc": "Issue Details",
        "remediation_advice": "💡 Remediation Advice",
        "official_doc_ref": "📖 Official Policy Reference",
        "yes": "Yes",
        "no": "No",
        "export_report_btn": "Download Check Report (.md)",
        "export_csv_btn": "Download Play Console Data Safety CSV",
        "csv_export_hint": "💡 **How to Import**: In Google Play Console, navigate to your app -> 'App content' (in left menu) -> 'Data safety' -> click 'Import from CSV' in the top right. Upload this file to import questionnaire responses directly without manual checking.",
        "code_diff_title": "Recommended Code Changes:",
        "rule_prompt_title": "Code Fix Suggestion (Prompt)",
        "copy_prompt_hint": "You can copy this prompt directly to Cursor, Claude, or Copilot:",
        "account_deletion_url_input": "Account Deletion URL (Optional)",
        "account_deletion_url_help": "If your app supports account registration, enter the URL where users can request account deletion to include in the CSV.",
        "nav_home": "Home",
        "nav_inspect": "Start Check",
        "nav_records": "History",
        "nav_docs": "Policy Guides",
        "nav_settings": "Settings",
        "promo_card_title": "Pre-submission Check",
        "promo_card_desc": "Check common policies to reduce rejection risks.",
        "promo_card_btn": "Learn More",
        "hero_title": "Google Play Pre-flight Inspection",
        "hero_desc": "Catch common policy issues before submitting to Google Play Console.",
        "hero_badge_policy": "Covers Official Play Policy",
        "hero_badge_speed": "Static analysis with quick feedback",
        "hero_badge_remedy": "Actionable Fix Suggestions",
        "mode_package": "AAB / APK Package Check",
        "mode_demo": "Load Built-in Demo Data",
        "app_name_input": "App Name (Optional)",
        "app_name_placeholder": "e.g. MyApp Global",
        "app_pkg_input": "Package Name (Optional)",
        "app_pkg_placeholder": "e.g. com.example.app (Auto-filled)",
        "dropzone_title": "Drag and drop files here, or browse",
        "dropzone_hint": "Supports AAB, APK files up to 200MB",
        "start_scan_btn": "▶ Start Check",
        "diag_result_title": "Inspection Results & Summary",
        "score_risks_found": "{n} Potential Risks Found",
        "score_clean": "Healthy Compliance Status",
        "score_advice_fix": "Please review the suggestions below before submitting to Google Play Console.",
        "score_advice_clean": "No critical blockers found. Ready to submit to Google Play Console.",
        "cat_core_sdk": "Target SDK & Architecture",
        "cat_core_sdk_desc": "Target SDK 34+, 16KB native page alignment & restricted permissions",
        "cat_privacy_safety": "Privacy Policy & Data Safety",
        "cat_privacy_safety_desc": "Policy URL accessibility and Data Safety mapping",
        "cat_foreground_service": "Foreground Services",
        "cat_foreground_service_desc": "Android 14+ foregroundServiceType declaration",
        "cat_account_deletion": "Account Deletion",
        "cat_account_deletion_desc": "Web-based account deletion URL availability check",
        "cat_ad_monetization": "Ad Monetization & AD_ID",
        "cat_ad_monetization_desc": "Ad SDKs and Advertising ID (AD_ID) parity",
        "cat_storage_photo": "Storage & Photo Picker",
        "cat_storage_photo_desc": "Photo Picker migration & storage permission recommendations",
        "badge_issues_count": "{n} suggestions",
        "badge_no_issues": "Normal",
        "tip_title": "Helpful Notice",
        "tip_desc": "Results are for reference only. The official Google Play review team has final authority. Please review all details prior to submission.",
        "recent_records_title": "Recent History",
        "view_details": "View Details →",
        "theme_selector": "🎨 Theme Style",
        "theme_system": "System",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "fast_scan": "Static Compliance Check",
        "breadcrumb_audit": "Google Play Pre-check",
        "hero_upload_title": "Upload Package for Compliance Check",
        "hero_upload_sub": "Drag and drop your Android AAB or APK package here",
        "start_audit_btn": "▶ Start Check",
        "high_density_checklist": "Inspection Details",
        "one_click_prompt": "Copy Fix Suggestion",
        "health_score_title": "Compliance Score & Summary"
    }
}

def get_ui_text(lang: str = "zh") -> dict:
    return UI_STRINGS.get(lang, UI_STRINGS["zh"])

def translate_data_type(dt: str, lang: str = "zh") -> str:
    # Match against canonical English key
    for k, trans in DATA_TYPES_I18N.items():
        if k.lower() in dt.lower():
            return trans.get(lang, dt)
    return dt

def translate_purpose(p: str, lang: str = "zh") -> str:
    for k, trans in PURPOSES_I18N.items():
        if k.lower() in p.lower():
            return trans.get(lang, p)
    return p
