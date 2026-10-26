import os
import yaml
from pathlib import Path
from typing import Dict, Any, List

RESTRICTED_PERMISSIONS = {
    "android.permission.READ_CONTACTS": {
        "zh": "通讯录读取权限 (需核心通讯功能)",
        "en": "Read Contacts (Requires core communications feature)"
    },
    "android.permission.WRITE_CONTACTS": {
        "zh": "通讯录写入权限 (需核心通讯功能)",
        "en": "Write Contacts (Requires core communications feature)"
    },
    "android.permission.READ_SMS": {
        "zh": "短信读取权限 (极严苛，建议改用 SMS Retriever API)",
        "en": "Read SMS (Highly restricted; prefer SMS Retriever API)"
    },
    "android.permission.RECEIVE_SMS": {
        "zh": "短信接收权限 (建议改用 SMS Retriever API)",
        "en": "Receive SMS (Highly restricted; prefer SMS Retriever API)"
    },
    "android.permission.SEND_SMS": {
        "zh": "短信发送权限 (建议改用隐式 Intent)",
        "en": "Send SMS (Highly restricted; prefer Intent)"
    },
    "android.permission.ACCESS_BACKGROUND_LOCATION": {
        "zh": "后台位置权限 (需提交独立使用理由与视频演示)",
        "en": "Background Location (Requires dedicated justification and video demo)"
    },
    "android.permission.REQUEST_INSTALL_PACKAGES": {
        "zh": "安装未知应用权限 (需专门审核)",
        "en": "Install Unknown Packages (Requires special review)"
    },
    "android.permission.MANAGE_EXTERNAL_STORAGE": {
        "zh": "所有文件访问权限 (极易拒审，建议使用 SAF 或 Photo Picker)",
        "en": "Manage External Storage (High rejection rate; use SAF or Photo Picker)"
    },
    "android.permission.QUERY_ALL_PACKAGES": {
        "zh": "获取已安装应用全量清单权限 (易遭合规下架)",
        "en": "Query All Packages (High risk of policy rejection)"
    }
}

class RulesEngine:
    def __init__(self, rules_file: str = None):
        if rules_file is None:
            current_dir = Path(__file__).parent.parent
            rules_file = str(current_dir / "rules" / "rules.yaml")
        self.rules_file = rules_file
        self.rules_dict = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        if not os.path.exists(self.rules_file):
            return {}
        with open(self.rules_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return {r["id"]: r for r in data.get("rules", [])}

    @staticmethod
    def _localize(field_value: Any, lang: str = "zh", default: str = "") -> str:
        if isinstance(field_value, dict):
            return field_value.get(lang) or field_value.get("zh") or field_value.get("en") or default
        if isinstance(field_value, str):
            return field_value
        return default

    def evaluate(self, 
                 manifest: Dict[str, Any], 
                 detected_sdks: List[Dict[str, Any]], 
                 privacy_url_result: Dict[str, Any] = None,
                 account_deletion_url: str = None,
                 lang: str = "zh",
                 elf_result: Dict[str, Any] = None,
                 framework_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluates manifest, SDKs, ELF .so page alignment, privacy URL, and framework context against Google Play compliance rules with bilingual support.
        """
        findings = []
        target_sdk = manifest.get("target_sdk", 0)
        permissions = manifest.get("permissions", [])
        services = manifest.get("services", [])
        detected_sdk_ids = [s["id"] for s in detected_sdks]
        detected_categories = [s.get("category", "") for s in detected_sdks]
        is_en = (lang == "en")

        # 1. Target SDK Check
        r_target_sdk = self.rules_dict.get("RULE_TARGET_SDK")
        if r_target_sdk:
            min_sdk = r_target_sdk.get("min_target_sdk", 36)
            required_features = {
                feature["name"] for feature in manifest.get("uses_features", [])
                if isinstance(feature, dict) and feature.get("required", True)
                and feature.get("name")
            }
            exceptions = r_target_sdk.get("required_feature_min_target_sdk", {})
            matched_minima = [value for feature, value in exceptions.items() if feature in required_features]
            if matched_minima:
                min_sdk = max(matched_minima)

            def target_text(field):
                return self._localize(r_target_sdk.get(field), lang).replace("{min_target_sdk}", str(min_sdk))
            title = self._localize(r_target_sdk.get("title"), lang, "Target SDK Compliance")
            category = self._localize(r_target_sdk.get("category"), lang, "System Requirement")
            doc_url = r_target_sdk.get("doc_url", "")
            
            if target_sdk < min_sdk:
                msg = (
                    f"Current targetSdkVersion is {target_sdk}, which is below the new-app/update requirement of {min_sdk}. Verify any private-app or deadline extension exemption in Play Console."
                    if is_en else
                    f"当前应用 targetSdkVersion 为 {target_sdk}，低于新应用/更新提交要求的 {min_sdk}。内部私有应用或延期资格需在 Play Console 单独核实。"
                )
                findings.append({
                    "rule_id": "RULE_TARGET_SDK",
                    "title": title,
                    "category": category,
                    "severity": r_target_sdk["severity"],
                    "status": "FAIL",
                    "message": msg,
                    "doc_url": doc_url,
                    "remediation": target_text("remediation_summary"),
                    "code_diff": target_text("code_diff"),
                    "prompt": target_text("prompt_template")
                })
            else:
                msg = (
                    f"targetSdkVersion is {target_sdk}, compliant with Google Play specification (>= {min_sdk})."
                    if is_en else
                    f"targetSdkVersion 为 {target_sdk}，符合 Google Play 规范（>= {min_sdk}）。"
                )
                findings.append({
                    "rule_id": "RULE_TARGET_SDK",
                    "title": title,
                    "category": category,
                    "severity": "PASS",
                    "status": "PASS",
                    "message": msg,
                    "doc_url": doc_url
                })

        # 2. Foreground Service Check (Android 14+)
        r_fgs = self.rules_dict.get("RULE_FOREGROUND_SERVICE")
        if r_fgs:
            title = self._localize(r_fgs.get("title"), lang, "Foreground Service Type Requirement")
            category = self._localize(r_fgs.get("category"), lang, "Foreground Service")
            doc_url = r_fgs.get("doc_url", "")
            
            has_fgs_perm = any("FOREGROUND_SERVICE" in p for p in permissions)
            if has_fgs_perm or any(s.get("has_fgs_type") for s in services):
                bad_services = [s["name"] for s in services if not s.get("has_fgs_type")]
                if bad_services:
                    msg = (
                        f"Foreground service permission declared, but the following <service> tags lack android:foregroundServiceType: {', '.join(bad_services)}."
                        if is_en else
                        f"检测到应用申请了前台服务权限，但以下 <service> 未声明 foregroundServiceType 属性：{', '.join(bad_services)}。"
                    )
                    findings.append({
                        "rule_id": "RULE_FOREGROUND_SERVICE",
                        "title": title,
                        "category": category,
                        "severity": r_fgs["severity"],
                        "status": "FAIL",
                        "message": msg,
                        "doc_url": doc_url,
                        "remediation": self._localize(r_fgs.get("remediation_summary"), lang),
                        "code_diff": self._localize(r_fgs.get("code_diff"), lang),
                        "prompt": self._localize(r_fgs.get("prompt_template"), lang)
                    })
                else:
                    msg = (
                        "All foreground services have properly declared foregroundServiceType attributes."
                        if is_en else
                        "前台服务均已正确声明 foregroundServiceType 属性或未违规使用。"
                    )
                    findings.append({
                        "rule_id": "RULE_FOREGROUND_SERVICE",
                        "title": title,
                        "category": category,
                        "severity": "PASS",
                        "status": "PASS",
                        "message": msg,
                        "doc_url": doc_url
                    })
            else:
                msg = (
                    "Application does not request FOREGROUND_SERVICE permission. No risk identified."
                    if is_en else
                    "应用未申请 FOREGROUND_SERVICE 前台服务权限，无此风险。"
                )
                findings.append({
                    "rule_id": "RULE_FOREGROUND_SERVICE",
                    "title": title,
                    "category": category,
                    "severity": "PASS",
                    "status": "PASS",
                    "message": msg,
                    "doc_url": doc_url
                })

        # 3. Advertising ID (AD_ID) Check
        r_ad_id = self.rules_dict.get("RULE_AD_ID_DECLARATION")
        if r_ad_id:
            title = self._localize(r_ad_id.get("title"), lang, "Advertising ID Declaration")
            category = self._localize(r_ad_id.get("category"), lang, "Advertising Policy")
            doc_url = r_ad_id.get("doc_url", "")
            
            has_ad_sdk = "Advertising and Monetization" in detected_categories or any(
                sid in ["admob", "facebook_ads", "unity_ads", "applovin", "adjust", "appsflyer", "ironsource", "mintegral", "pangle", "inmobi", "liftoff_vungle", "chartboost"] 
                for sid in detected_sdk_ids
            )
            has_gaid_client = "google_ads_identifier" in detected_sdk_ids
            has_ad_id_perm = "com.google.android.gms.permission.AD_ID" in permissions

            if has_ad_sdk and not has_ad_id_perm:
                msg = (
                    "Commercial advertising/monetization SDKs detected, but com.google.android.gms.permission.AD_ID permission is missing in AndroidManifest.xml."
                    if is_en else
                    "包内检测到商业广告/变现 SDK，但在 Manifest 中未显式包含 com.google.android.gms.permission.AD_ID 权限声明。"
                )
                findings.append({
                    "rule_id": "RULE_AD_ID_DECLARATION",
                    "title": title,
                    "category": category,
                    "severity": r_ad_id["severity"],
                    "status": "FAIL",
                    "message": msg,
                    "doc_url": doc_url,
                    "remediation": self._localize(r_ad_id.get("remediation_summary"), lang),
                    "code_diff": self._localize(r_ad_id.get("code_diff"), lang),
                    "prompt": self._localize(r_ad_id.get("prompt_template"), lang)
                })
            elif has_ad_sdk and has_ad_id_perm:
                msg = (
                    "Ad SDKs and AD_ID permission declaration are aligned (Ensure 'Yes, contains ads' is selected in Play Console)."
                    if is_en else
                    "商业广告 SDK 与 AD_ID 权限声明匹配一致（注意在 Play Console 勾选包含广告）。"
                )
                findings.append({
                    "rule_id": "RULE_AD_ID_DECLARATION",
                    "title": title,
                    "category": category,
                    "severity": "PASS",
                    "status": "PASS",
                    "message": msg,
                    "doc_url": doc_url
                })
            elif has_gaid_client:
                # App does NOT have ad networks, but has a GAID reader (e.g. from domestic map/device ID SDK)
                if not has_ad_id_perm:
                    if is_en:
                        gaid_title = "Third-party Library References GAID Client (Not Ad Display, No Code Fix Needed)"
                        gaid_msg = "No commercial ad components found, but a 3rd-party library (e.g. AMap / device fingerprinting SDK) includes the Google Advertising ID client (com.google.android.gms.ads.identifier). If your app does not serve ads, NO CODE CHANGES ARE REQUIRED. On Android 13+ devices, the OS zeroes out this ID automatically. In Google Play Console questionnaire, select 'No' for ads."
                        gaid_remediation = "[No code change needed] Declare 'No' in Google Play Console App Content questionnaire to pass review."
                    else:
                        gaid_title = "第三方底层库包含 GAID 广告 ID 接口（非商业广告，无需改代码）"
                        gaid_msg = "包内未发现商业广告变现组件，但检测到第三方库（如高德地图/设备识别 SDK）内置了读取 Google 广告 ID 的底层接口 (com.google.android.gms.ads.identifier)。若您的应用不投放商业广告，【代码层面无需做任何修改】。在 Android 13+ 设备上系统会自动将该接口屏蔽并返回全零虚拟 ID。在 Google Play Console 问卷中若被问及是否投放广告，直接勾选'否'即可。"
                        gaid_remediation = "【无需修改代码】在 Google Play Console 应用内容问卷中声明'应用不包含广告'即可正常过审。"

                    findings.append({
                        "rule_id": "RULE_AD_ID_DECLARATION",
                        "title": gaid_title,
                        "category": category,
                        "severity": "MEDIUM",
                        "status": "WARN",
                        "requires_code_fix": False,
                        "message": gaid_msg,
                        "doc_url": doc_url,
                        "remediation": gaid_remediation,
                        "prompt": ""
                    })
                else:
                    msg = (
                        "AD_ID permission declared. Third-party libraries can read device/advertising identifiers as expected."
                        if is_en else
                        "应用已声明 AD_ID 权限，第三方库可正常读取硬件/广告标识符。"
                    )
                    pass_title = "Advertising ID (AD_ID) Declaration Valid" if is_en else "广告 ID (AD_ID) 声明正常"
                    findings.append({
                        "rule_id": "RULE_AD_ID_DECLARATION",
                        "title": pass_title,
                        "category": category,
                        "severity": "PASS",
                        "status": "PASS",
                        "requires_code_fix": False,
                        "message": msg,
                        "doc_url": doc_url
                    })

        # 4. Restricted Permissions Check
        r_restricted = self.rules_dict.get("RULE_RESTRICTED_PERMISSIONS")
        if r_restricted:
            title = self._localize(r_restricted.get("title"), lang, "Restricted Permissions")
            category = self._localize(r_restricted.get("category"), lang, "Permissions Policy")
            doc_url = r_restricted.get("doc_url", "")
            
            found_restricted = []
            for p in permissions:
                if p in RESTRICTED_PERMISSIONS:
                    perm_desc = RESTRICTED_PERMISSIONS[p].get(lang, RESTRICTED_PERMISSIONS[p]["zh"])
                    found_restricted.append(f"{p} ({perm_desc})")

            if found_restricted:
                prompt_tpl = self._localize(r_restricted.get("prompt_template"), lang)
                prompt_text = prompt_tpl.format(permissions=", ".join(found_restricted))
                msg = (
                    f"Application declared high-risk restricted permissions: {', '.join(found_restricted)}. Requires a dedicated declaration form and video demonstration, with high rejection risk."
                    if is_en else
                    f"应用声明了高风险受限权限：{', '.join(found_restricted)}。Google Play 审核需提交专门用途声明视频，极易被打回。"
                )
                findings.append({
                    "rule_id": "RULE_RESTRICTED_PERMISSIONS",
                    "title": title,
                    "category": category,
                    "severity": r_restricted["severity"],
                    "status": "FAIL",
                    "message": msg,
                    "doc_url": doc_url,
                    "remediation": self._localize(r_restricted.get("remediation_summary"), lang),
                    "code_diff": self._localize(r_restricted.get("code_diff"), lang),
                    "prompt": prompt_text
                })
            else:
                msg = (
                    "No restricted high-risk permissions detected (no SMS, Contacts, Background Location, etc.). Clean permission profile."
                    if is_en else
                    "未发现高危受限权限（无短信、通讯录、后台位置等），权限申请规范轻量。"
                )
                findings.append({
                    "rule_id": "RULE_RESTRICTED_PERMISSIONS",
                    "title": title,
                    "category": category,
                    "severity": "PASS",
                    "status": "PASS",
                    "message": msg,
                    "doc_url": doc_url
                })

        # 5. AI Generated Content Policy
        r_ai = self.rules_dict.get("RULE_AI_CONTENT_POLICY")
        if r_ai:
            if "openai_api" in detected_sdk_ids:
                title = self._localize(r_ai.get("title"), lang, "Generative AI Policy")
                category = self._localize(r_ai.get("category"), lang, "Content Policy")
                msg = (
                    "Detected LLM / AI API integration (OpenAI/LLM). You must declare Generative AI features in Play Console and provide in-app content reporting mechanisms."
                    if is_en else
                    "检测到调用了大语言模型/AI 接口（OpenAI/LLM），需在 Google Play 控制台主动申报生成式 AI 功能并内置不良内容一键举报按钮。"
                )
                findings.append({
                    "rule_id": "RULE_AI_CONTENT_POLICY",
                    "title": title,
                    "category": category,
                    "severity": r_ai["severity"],
                    "status": "WARN",
                    "message": msg,
                    "doc_url": r_ai.get("doc_url", ""),
                    "remediation": self._localize(r_ai.get("remediation_summary"), lang),
                    "code_diff": self._localize(r_ai.get("code_diff"), lang),
                    "prompt": self._localize(r_ai.get("prompt_template"), lang)
                })

        # 6. Privacy Policy URL Probe
        r_privacy = self.rules_dict.get("RULE_PRIVACY_POLICY_URL")
        if r_privacy and privacy_url_result:
            title = self._localize(r_privacy.get("title"), lang, "Privacy Policy URL Check")
            category = self._localize(r_privacy.get("category"), lang, "Privacy & Data Safety")
            doc_url = r_privacy.get("doc_url", "")
            
            is_valid = privacy_url_result.get("is_valid", False)
            status_code = privacy_url_result.get("status_code")
            url = privacy_url_result.get("url", "")
            if not is_valid:
                msg = (
                    f"Privacy Policy URL probe failed (URL: {url}, status: {status_code or 'Network/SSL Error'}). Dead links cause instant rejection!"
                    if is_en else
                    f"隐私政策链接探测失败（URL: {url}，状态: {status_code or '网络连接/SSL异常'}），Google Play 审核会因死链直接驳回！"
                )
                findings.append({
                    "rule_id": "RULE_PRIVACY_POLICY_URL",
                    "title": title,
                    "category": category,
                    "severity": r_privacy["severity"],
                    "status": "FAIL",
                    "message": msg,
                    "doc_url": doc_url,
                    "remediation": self._localize(r_privacy.get("remediation_summary"), lang),
                    "code_diff": self._localize(r_privacy.get("code_diff"), lang),
                    "prompt": self._localize(r_privacy.get("prompt_template"), lang)
                })
            else:
                msg = (
                    f"Privacy policy URL reachable (HTTP {status_code}, valid SSL certificate)."
                    if is_en else
                    f"隐私政策 URL 访问正常（HTTP {status_code}，SSL 证书有效）。"
                )
                findings.append({
                    "rule_id": "RULE_PRIVACY_POLICY_URL",
                    "title": title,
                    "category": category,
                    "severity": "PASS",
                    "status": "PASS",
                    "message": msg,
                    "doc_url": doc_url
                })

        # 7. Package Visibility Check (QUERY_ALL_PACKAGES)
        r_qap = self.rules_dict.get("RULE_QUERY_ALL_PACKAGES")
        if r_qap:
            title = self._localize(r_qap.get("title"), lang, "Package Visibility Policy")
            category = self._localize(r_qap.get("category"), lang, "Package Visibility")
            doc_url = r_qap.get("doc_url", "")
            if "android.permission.QUERY_ALL_PACKAGES" in permissions:
                msg = (
                    "Application declares android.permission.QUERY_ALL_PACKAGES. Google Play strictly restricts broad visibility; non-compliant apps will be rejected immediately."
                    if is_en else
                    "应用申请了全量应用查询权限 android.permission.QUERY_ALL_PACKAGES。Google Play 对该权限审查极其严苛，常规应用提交 100% 被拒审或封禁！"
                )
                findings.append({
                    "rule_id": "RULE_QUERY_ALL_PACKAGES",
                    "title": title,
                    "category": category,
                    "severity": "FATAL",
                    "status": "FAIL",
                    "message": msg,
                    "doc_url": doc_url,
                    "remediation": self._localize(r_qap.get("remediation_summary"), lang),
                    "code_diff": self._localize(r_qap.get("code_diff"), lang),
                    "prompt": self._localize(r_qap.get("prompt_template"), lang)
                })
            else:
                msg = (
                    "No broad QUERY_ALL_PACKAGES permission declared. Complies with Google Play package visibility policy."
                    if is_en else
                    "未申请 QUERY_ALL_PACKAGES 全量包查询权限，符合 Google Play 应用可见性安全规范。"
                )
                findings.append({
                    "rule_id": "RULE_QUERY_ALL_PACKAGES",
                    "title": title,
                    "category": category,
                    "severity": "PASS",
                    "status": "PASS",
                    "message": msg,
                    "doc_url": doc_url
                })

        # 8. Account Deletion Policy
        r_del = self.rules_dict.get("RULE_ACCOUNT_DELETION_POLICY")
        if r_del:
            title = self._localize(r_del.get("title"), lang, "Account Deletion Policy")
            category = self._localize(r_del.get("category"), lang, "Account & Privacy")
            doc_url = r_del.get("doc_url", "")

            auth_sdk_ids = {"google_auth", "facebook_login", "firebase_auth", "supabase_auth", "auth0", "aws_cognito"}
            has_auth_sdk = any(sid in auth_sdk_ids for sid in detected_sdk_ids) or any("Authentication" in s.get("category", "") or "Login" in s.get("category", "") for s in detected_sdks)
            activities = manifest.get("activities", [])
            has_auth_activity = any(
                any(kw in act.lower() for kw in ["login", "register", "auth", "signin", "signup"])
                for act in activities
            )
            has_account_system = has_auth_sdk or has_auth_activity

            if has_account_system:
                if not account_deletion_url:
                    msg = (
                        "User authentication / login detected, but no account deletion URL is configured. Google Play mandates providing an in-app deletion path and a public web deletion link."
                        if is_en else
                        "检测到应用包含用户登录/认证体系，但未提供账号注销网页链接。Google Play 强制要求具备账号功能的应用必须提供应用内注销入口及公开的 Web 注销申请链接！"
                    )
                    findings.append({
                        "rule_id": "RULE_ACCOUNT_DELETION_POLICY",
                        "title": title,
                        "category": category,
                        "severity": "HIGH",
                        "status": "FAIL",
                        "message": msg,
                        "doc_url": doc_url,
                        "remediation": self._localize(r_del.get("remediation_summary"), lang),
                        "code_diff": self._localize(r_del.get("code_diff"), lang),
                        "prompt": self._localize(r_del.get("prompt_template"), lang)
                    })
                else:
                    msg = (
                        f"Account deletion URL declared ({account_deletion_url}). Meets Google Play 2024 Account Deletion policy requirement."
                        if is_en else
                        f"已配置账号注销公开链接（{account_deletion_url}），符合 Google Play 账号与数据删除合规规范。"
                    )
                    findings.append({
                        "rule_id": "RULE_ACCOUNT_DELETION_POLICY",
                        "title": title,
                        "category": category,
                        "severity": "PASS",
                        "status": "PASS",
                        "message": msg,
                        "doc_url": doc_url
                    })
            else:
                msg = (
                    "No account registration or login SDK detected. Exempt from mandatory account deletion web requirement."
                    if is_en else
                    "未检测到账号注册或第三方登录 SDK，无需强制提供外部账号删除网址。"
                )
                findings.append({
                    "rule_id": "RULE_ACCOUNT_DELETION_POLICY",
                    "title": title,
                    "category": category,
                    "severity": "PASS",
                    "status": "PASS",
                    "message": msg,
                    "doc_url": doc_url
                })

        # 9. Storage Access & Photo Picker Policy
        r_storage = self.rules_dict.get("RULE_STORAGE_PHOTO_PICKER")
        if r_storage:
            title = self._localize(r_storage.get("title"), lang, "Storage Access Policy")
            category = self._localize(r_storage.get("category"), lang, "Storage Policy")
            doc_url = r_storage.get("doc_url", "")

            has_manage_storage = "android.permission.MANAGE_EXTERNAL_STORAGE" in permissions
            has_legacy_storage = (
                target_sdk >= 33 and 
                ("android.permission.READ_EXTERNAL_STORAGE" in permissions or "android.permission.WRITE_EXTERNAL_STORAGE" in permissions)
            )

            if has_manage_storage:
                msg = (
                    "Application declares MANAGE_EXTERNAL_STORAGE (All files access). Google Play strictly rejects apps using this unless core functionality is a file manager."
                    if is_en else
                    "应用声明了 MANAGE_EXTERNAL_STORAGE（所有文件访问权限）。除专职文件管理器外，Google Play 严格禁止常规应用申请该权限，提交必遭拒审！"
                )
                findings.append({
                    "rule_id": "RULE_STORAGE_PHOTO_PICKER",
                    "title": title,
                    "category": category,
                    "severity": "FATAL",
                    "status": "FAIL",
                    "message": msg,
                    "doc_url": doc_url,
                    "remediation": self._localize(r_storage.get("remediation_summary"), lang),
                    "code_diff": self._localize(r_storage.get("code_diff"), lang),
                    "prompt": self._localize(r_storage.get("prompt_template"), lang)
                })
            elif has_legacy_storage:
                msg = (
                    "Target SDK is 33+, but legacy READ/WRITE_EXTERNAL_STORAGE permissions are declared. Migrate to Android Photo Picker (PickVisualMedia) or granular media permissions."
                    if is_en else
                    "应用 targetSdkVersion >= 33，但仍声明了旧版 READ/WRITE_EXTERNAL_STORAGE 权限。建议迁移至系统免权限 Photo Picker 或细分媒体权限。"
                )
                findings.append({
                    "rule_id": "RULE_STORAGE_PHOTO_PICKER",
                    "title": title,
                    "category": category,
                    "severity": "HIGH",
                    "status": "FAIL",
                    "message": msg,
                    "doc_url": doc_url,
                    "remediation": self._localize(r_storage.get("remediation_summary"), lang),
                    "code_diff": self._localize(r_storage.get("code_diff"), lang),
                    "prompt": self._localize(r_storage.get("prompt_template"), lang)
                })
            else:
                msg = (
                    "No broad or legacy storage permissions requested. Meets storage access policy standards."
                    if is_en else
                    "未滥用全盘存储或过时存储权限，符合 Google Play 隐私与存储安全政策。"
                )
                findings.append({
                    "rule_id": "RULE_STORAGE_PHOTO_PICKER",
                    "title": title,
                    "category": category,
                    "severity": "PASS",
                    "status": "PASS",
                    "message": msg,
                    "doc_url": doc_url
                })

        # 8. 16KB Page Alignment Check for Native Libraries (.so)
        r_16kb = self.rules_dict.get("RULE_16KB_PAGE_ALIGNMENT")
        if r_16kb:
            title = self._localize(r_16kb.get("title"), lang, "Native Library 16KB Page Alignment")
            category = self._localize(r_16kb.get("category"), lang, "System Requirement")
            doc_url = r_16kb.get("doc_url", "")

            elf_res = elf_result or {}
            has_native = elf_res.get("has_native_libs", False)
            non_compliant = elf_res.get("non_compliant_libs", [])
            total_so = elf_res.get("total_so_count", 0)

            if has_native and len(non_compliant) > 0:
                is_fatal = (target_sdk >= 35)
                sev = "FATAL" if is_fatal else "HIGH"
                bad_names = ", ".join([f"{item['name']} ({item.get('abi', '')}: {item.get('min_load_align_hex', '0x1000')})" for item in non_compliant[:4]])
                if len(non_compliant) > 4:
                    bad_names += f" ... (+{len(non_compliant) - 4})"

                if is_en:
                    msg = (
                        f"Detected {len(non_compliant)} 64-bit native library (.so) files not aligned to 16KB page boundary ({bad_names}). "
                        f"{'Target SDK is 35 (Android 15+); this app will crash on 16KB devices and be rejected by Google Play.' if is_fatal else 'Target SDK is below 35, but upgrading to Android 15 will cause crashes on 16KB devices.'}"
                    )
                else:
                    msg = (
                        f"检测到 {len(non_compliant)} 个 64 位原生动态库 (.so) 未满足 16KB 内存页面对齐要求（如：{bad_names}）。"
                        f"{'当前应用 Target SDK >= 35，提交 Google Play 审核将直接受阻或在 16KB 设备上崩溃！' if is_fatal else '虽然当前 Target SDK < 35，但在 Android 15 设备或后续强制升级时将导致严重闪退。'}"
                    )

                prompt_raw = self._localize(r_16kb.get("prompt_template"), lang)
                prompt_filled = prompt_raw.replace("{non_compliant_libs}", bad_names)

                findings.append({
                    "rule_id": "RULE_16KB_PAGE_ALIGNMENT",
                    "title": title,
                    "category": category,
                    "severity": sev,
                    "status": "FAIL",
                    "message": msg,
                    "doc_url": doc_url,
                    "remediation": self._localize(r_16kb.get("remediation_summary"), lang),
                    "code_diff": self._localize(r_16kb.get("code_diff"), lang),
                    "prompt": prompt_filled
                })
            elif has_native and len(non_compliant) == 0:
                msg = (
                    f"All {total_so} native shared libraries (.so) comply with Android 15+ 16KB page alignment standards."
                    if is_en else
                    f"包内检测到 {total_so} 个原生动态库 (.so)，全部已实现 16KB 内存页面对齐，符合 Android 15+ 架构要求。"
                )
                findings.append({
                    "rule_id": "RULE_16KB_PAGE_ALIGNMENT",
                    "title": title,
                    "category": category,
                    "severity": "PASS",
                    "status": "PASS",
                    "message": msg,
                    "doc_url": doc_url
                })
            else:
                msg = (
                    "No native C/C++ shared libraries (.so) detected. Naturally immune to 16KB page size incompatibility."
                    if is_en else
                    "未检测到 C/C++ 原生动态库 (.so)，天然免疫 16KB 内存页面对齐与闪退风险。"
                )
                findings.append({
                    "rule_id": "RULE_16KB_PAGE_ALIGNMENT",
                    "title": title,
                    "category": category,
                    "severity": "PASS",
                    "status": "PASS",
                    "message": msg,
                    "doc_url": doc_url
                })

        # 9. Exact Alarm Check (SCHEDULE_EXACT_ALARM / USE_EXACT_ALARM)
        r_exact = self.rules_dict.get("RULE_EXACT_ALARM")
        if r_exact:
            title = self._localize(r_exact.get("title"), lang, "Exact Alarm Policy")
            category = self._localize(r_exact.get("category"), lang, "Permissions Policy")
            doc_url = r_exact.get("doc_url", "")
            has_schedule_exact = "android.permission.SCHEDULE_EXACT_ALARM" in permissions
            has_use_exact = "android.permission.USE_EXACT_ALARM" in permissions

            if has_schedule_exact and target_sdk >= 33:
                msg = (
                    "Application requests android.permission.SCHEDULE_EXACT_ALARM. Google Play policy strictly restricts this permission to clock, calendar, and reminder apps. Regular apps face high rejection risk; migrate to WorkManager or USE_EXACT_ALARM."
                    if is_en else
                    "应用声明了 SCHEDULE_EXACT_ALARM 权限。从 Android 13+ 起，Google Play 严格限制非专职闹钟或日历类应用申请该权限，普通应用提审被拒率极高，建议改用 WorkManager 或 USE_EXACT_ALARM。"
                )
                findings.append({
                    "rule_id": "RULE_EXACT_ALARM",
                    "title": title,
                    "category": category,
                    "severity": "HIGH",
                    "status": "FAIL",
                    "message": msg,
                    "doc_url": doc_url,
                    "remediation": self._localize(r_exact.get("remediation_summary"), lang),
                    "code_diff": self._localize(r_exact.get("code_diff"), lang),
                    "prompt": self._localize(r_exact.get("prompt_template"), lang)
                })
            elif has_use_exact:
                msg = (
                    "Application requests android.permission.USE_EXACT_ALARM. Ensure the app core functionality qualifies as an alarm or timer."
                    if is_en else
                    "应用声明了 USE_EXACT_ALARM 权限。该权限仅限专职时钟或计时器类应用使用，提交时请核实是否属于核心功能。"
                )
                findings.append({
                    "rule_id": "RULE_EXACT_ALARM",
                    "title": title,
                    "category": category,
                    "severity": "MEDIUM",
                    "status": "WARN",
                    "message": msg,
                    "doc_url": doc_url,
                    "remediation": self._localize(r_exact.get("remediation_summary"), lang),
                    "code_diff": self._localize(r_exact.get("code_diff"), lang),
                    "prompt": self._localize(r_exact.get("prompt_template"), lang)
                })
            else:
                msg = (
                    "No restricted exact alarm permissions declared. Compliant with timing and battery policies."
                    if is_en else
                    "未申请受限的精确闹钟权限，符合 Google Play 定时与功耗合规政策。"
                )
                findings.append({
                    "rule_id": "RULE_EXACT_ALARM",
                    "title": title,
                    "category": category,
                    "severity": "PASS",
                    "status": "PASS",
                    "message": msg,
                    "doc_url": doc_url
                })

        # 10. Full-Screen Intent Check (USE_FULL_SCREEN_INTENT)
        r_fsi = self.rules_dict.get("RULE_FULL_SCREEN_INTENT")
        if r_fsi:
            title = self._localize(r_fsi.get("title"), lang, "Full-Screen Intent Policy")
            category = self._localize(r_fsi.get("category"), lang, "Permissions Policy")
            doc_url = r_fsi.get("doc_url", "")
            has_fsi = "android.permission.USE_FULL_SCREEN_INTENT" in permissions

            if has_fsi and target_sdk >= 34:
                msg = (
                    "Application requests android.permission.USE_FULL_SCREEN_INTENT on Android 14+ (API 34). Google Play restricts default access only to calling and alarm apps. Non-core apps must guide users to system settings manually."
                    if is_en else
                    "应用在 Target SDK >= 34 下申请了 USE_FULL_SCREEN_INTENT 全屏通知意图权限。从 Android 14 起，非电话或警报类应用在新装设备上该权限默认被系统关闭，提审需在 Console 提交专项声明。"
                )
                findings.append({
                    "rule_id": "RULE_FULL_SCREEN_INTENT",
                    "title": title,
                    "category": category,
                    "severity": "HIGH",
                    "status": "FAIL",
                    "message": msg,
                    "doc_url": doc_url,
                    "remediation": self._localize(r_fsi.get("remediation_summary"), lang),
                    "code_diff": self._localize(r_fsi.get("code_diff"), lang),
                    "prompt": self._localize(r_fsi.get("prompt_template"), lang)
                })
            elif has_fsi:
                msg = (
                    "Application requests USE_FULL_SCREEN_INTENT. When upgrading to Android 14 (targetSdk 34+), this permission will be revoked by default for non-calling apps."
                    if is_en else
                    "应用申请了 USE_FULL_SCREEN_INTENT 权限。后续升级至 Android 14 (targetSdk 34+) 时，非电话类应用在新装设备上默认将失去该权限。"
                )
                findings.append({
                    "rule_id": "RULE_FULL_SCREEN_INTENT",
                    "title": title,
                    "category": category,
                    "severity": "MEDIUM",
                    "status": "WARN",
                    "message": msg,
                    "doc_url": doc_url,
                    "remediation": self._localize(r_fsi.get("remediation_summary"), lang),
                    "code_diff": self._localize(r_fsi.get("code_diff"), lang),
                    "prompt": self._localize(r_fsi.get("prompt_template"), lang)
                })
            else:
                msg = (
                    "No full-screen intent permissions declared. Compliant with notification intrusion policies."
                    if is_en else
                    "未申请全屏通知意图权限，符合 Android 通知交互与防打扰政策。"
                )
                findings.append({
                    "rule_id": "RULE_FULL_SCREEN_INTENT",
                    "title": title,
                    "category": category,
                    "severity": "PASS",
                    "status": "PASS",
                    "message": msg,
                    "doc_url": doc_url
                })

        # Framework-aware enrichment
        if framework_info and framework_info.get("is_cross_platform"):
            fw_id = framework_info.get("id")
            fw_name = framework_info.get("name", "Cross-Platform")
            for f in findings:
                rid = f.get("rule_id")
                if rid == "RULE_16KB_PAGE_ALIGNMENT" and f.get("status") == "FAIL":
                    if fw_id == "flutter":
                        f["framework_hint"] = (
                            "🔷 Flutter 框架适配建议：建议升级 Flutter SDK >= 3.24（集成支持 16KB 内存页面对齐的 NDK r27+）。若使用自定义 C/C++ 插件，在 android/app/build.gradle 中配置 cppFlags \"-Wl,-z,max-page-size=16384\" 并执行 flutter clean && flutter build appbundle。"
                            if not is_en else
                            "🔷 Flutter note: Upgrade to Flutter SDK >= 3.24 (comes with 16KB-ready NDK r27+). For custom C/C++ plugins, configure cppFlags \"-Wl,-z,max-page-size=16384\" in android/app/build.gradle and run flutter clean && flutter build appbundle."
                        )
                    elif fw_id == "unity":
                        f["framework_hint"] = (
                            "🎮 Unity 框架适配建议：建议升级 Unity 编辑器至 2022.3.40+ 或 2023.2.20+；若导出 Gradle 工程，请在导出的 app/build.gradle 中配置 16KB 页面对齐链接参数。"
                            if not is_en else
                            "🎮 Unity note: Upgrade Unity Editor to 2022.3.40+ or 2023.2.20+; if exporting Gradle project, configure 16KB linker flags in app/build.gradle."
                        )
                    elif fw_id == "react_native":
                        f["framework_hint"] = (
                            "⚛️ React Native 框架适配建议：升级 NDK 版本至 r27+，并在 android/app/build.gradle 的 externalNativeBuild 中添加 -Wl,-z,max-page-size=16384。"
                            if not is_en else
                            "⚛️ React Native note: Upgrade NDK to r27+ and add -Wl,-z,max-page-size=16384 in android/app/build.gradle externalNativeBuild."
                        )
                elif rid == "RULE_STORAGE_PHOTO_PICKER" and f.get("status") == "FAIL":
                    if fw_id == "flutter":
                        f["framework_hint"] = (
                            "🔷 Flutter 建议：推荐使用官方 image_picker 插件，Android 13+ 自动调用系统免权限 Photo Picker，无需在 AndroidManifest 中申请读写存储权限。"
                            if not is_en else
                            "🔷 Flutter note: Use official image_picker plugin. It automatically adopts the zero-permission Photo Picker on Android 13+."
                        )
                    elif fw_id == "react_native":
                        f["framework_hint"] = (
                            "⚛️ React Native 建议：推荐使用 react-native-image-picker 库，底层走 Android 系统 Photo Picker，免申请 MANAGE_EXTERNAL_STORAGE。"
                            if not is_en else
                            "⚛️ React Native note: Use react-native-image-picker, which uses Android system Photo Picker without storage permissions."
                        )
                elif rid == "RULE_TARGET_SDK" and f.get("status") == "FAIL":
                    if fw_id == "flutter":
                        f["framework_hint"] = (
                            f"🔷 Flutter 建议：在 android/app/build.gradle 中修改 targetSdkVersion = {min_sdk} 或 targetSdk = {min_sdk}。"
                            if not is_en else
                            f"🔷 Flutter note: Set targetSdkVersion = {min_sdk} or targetSdk = {min_sdk} in android/app/build.gradle."
                        )
                    elif fw_id == "react_native":
                        f["framework_hint"] = (
                            f"⚛️ React Native 建议：在 android/build.gradle 中修改 targetSdkVersion = {min_sdk}。"
                            if not is_en else
                            f"⚛️ React Native note: Update targetSdkVersion = {min_sdk} in android/build.gradle."
                        )

        # Overall Status Calculation
        fatal_count = sum(1 for f in findings if f["severity"] == "FATAL" and f["status"] == "FAIL")
        high_count = sum(1 for f in findings if f["severity"] == "HIGH" and f["status"] == "FAIL")
        warn_count = sum(1 for f in findings if f["status"] == "WARN")
        pass_count = sum(1 for f in findings if f["status"] == "PASS")

        if fatal_count > 0:
            overall_status = "FATAL_BLOCKER"
            status_text = "🚨 Fatal Blockers Found (Submission will be rejected)" if is_en else "🚨 存在致命拒审项，提交 100% 被打回"
            status_color = "#ef4444"
        elif high_count > 0:
            overall_status = "HIGH_RISK"
            status_text = "⚠️ High Risk Compliance Issues (Fix before submission)" if is_en else "⚠️ 存在高危合规风险，建议修复后再提交"
            status_color = "#f97316"
        elif warn_count > 0:
            overall_status = "WARNING"
            status_text = "⚡ Declarations Required (Verify Console questionnaire)" if is_en else "⚡ 存在需主动申报项，注意核对控制台问卷"
            status_color = "#eab308"
        else:
            overall_status = "PASSED"
            status_text = "✅ All Core Compliance Checks Passed (Ready for review)" if is_en else "✅ 核心合规项全数通过，可放心提交审核"
            status_color = "#22c55e"

        for f in findings:
            r_id = f.get("rule_id") or f.get("id", "")
            f["rule_id"] = r_id
            f["id"] = r_id

        return {
            "overall_status": overall_status,
            "status_text": status_text,
            "status_color": status_color,
            "counts": {
                "fatal": fatal_count,
                "high": high_count,
                "warn": warn_count,
                "passed": pass_count
            },
            "findings": findings
        }

