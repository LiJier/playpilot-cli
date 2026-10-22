from typing import List, Dict, Any
from analyzer.i18n import translate_data_type, translate_purpose, get_ui_text

class DataSafetyMapper:
    @staticmethod
    def generate_report(detected_sdks: List[Dict[str, Any]], lang: str = "zh") -> Dict[str, Any]:
        """
        Takes detected SDKs and synthesizes Play Console Data Safety questionnaire checklist.
        Supports bilingual output ('zh' / 'en').
        """
        table_rows = []
        aggregated_data_types = set()
        aggregated_purposes = set()
        has_third_party_sharing = False
        is_en = (lang == "en")

        for sdk in detected_sdks:
            safety = sdk.get("data_safety", {})
            collected = safety.get("collected_data", [])
            purposes = safety.get("purposes", [])
            is_shared = safety.get("shared_with_third_parties", False)
            if is_shared:
                has_third_party_sharing = True

            localized_collected = [translate_data_type(dt, lang) for dt in collected]
            localized_purposes = [translate_purpose(p, lang) for p in purposes]

            for dt in localized_collected:
                aggregated_data_types.add(dt)
            for p in localized_purposes:
                aggregated_purposes.add(p)

            shared_text = ("Yes" if is_shared else "No") if is_en else ("是 (Yes)" if is_shared else "否 (No)")

            table_rows.append({
                "sdk_name": sdk.get("name", "Unknown SDK"),
                "category": sdk.get("category", "General"),
                "collected_data": ", ".join(localized_collected),
                "purposes": ", ".join(localized_purposes),
                "shared_with_third_parties": shared_text,
                "doc_url": sdk.get("doc_url", "")
            })

        if is_en:
            console_recommendations = [
                {
                    "section": "Data collection & security",
                    "question": "Does your app collect or share any required user data types?",
                    "answer": "Yes" if len(aggregated_data_types) > 0 else "No"
                },
                {
                    "section": "Encryption in transit",
                    "question": "Is all user data collected by your app encrypted in transit?",
                    "answer": "Yes - Complies with HTTPS / TLS 1.2+ standards"
                },
                {
                    "section": "Account deletion",
                    "question": "Does your app allow users to create an account?",
                    "answer": "If account registration is supported, provide web and in-app account deletion links"
                }
            ]
        else:
            console_recommendations = [
                {
                    "section": "数据收集与共享概览 (Data collection & security)",
                    "question": "您的应用是否会收集或共享任何必填的用户数据类型？",
                    "answer": "是 (Yes)" if len(aggregated_data_types) > 0 else "否 (No)"
                },
                {
                    "section": "传输加密 (Encryption in transit)",
                    "question": "您的应用是否会对传输中的所有用户数据进行加密？",
                    "answer": "是 (Yes) - 遵循 HTTPS / TLS 1.2+ 标准"
                },
                {
                    "section": "账号删除机制 (Account deletion)",
                    "question": "应用是否允许用户创建账号？",
                    "answer": "如果包含注册功能，必须在 Console 和应用内提供账号删除链接"
                }
            ]

        return {
            "sdk_count": len(detected_sdks),
            "table_rows": table_rows,
            "has_third_party_sharing": has_third_party_sharing,
            "data_types_summary": sorted(list(aggregated_data_types)),
            "purposes_summary": sorted(list(aggregated_purposes)),
            "console_recommendations": console_recommendations
        }

