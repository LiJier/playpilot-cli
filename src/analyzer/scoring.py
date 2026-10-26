"""Shared scoring for Web and CLI: fatal -25, high -15, warning -5; floor 15."""

from typing import Dict, Any


def calculate_score_and_categories(eval_result: Dict[str, Any]):
    if not eval_result or "findings" not in eval_result:
        return 100, 0, 0, 0, {
            "core_sdk": 0, "privacy_safety": 0, "foreground_service": 0,
            "account_deletion": 0, "ad_monetization": 0, "storage_photo": 0
        }

    findings = eval_result["findings"]
    for f in findings:
        rid = f.get("rule_id") or f.get("id", "")
        f["rule_id"] = rid
        f["id"] = rid

    fatal_cnt = sum(1 for f in findings if f.get("status") == "FAIL" and f.get("severity") == "FATAL")
    high_cnt = sum(1 for f in findings if f.get("status") == "FAIL" and f.get("severity") in ["HIGH", "MEDIUM_HIGH"])
    warn_cnt = sum(1 for f in findings if f.get("status") in ["WARN", "MEDIUM"])

    deduction = (fatal_cnt * 25) + (high_cnt * 15) + (warn_cnt * 5)
    score = max(15, min(100, 100 - deduction))

    cat_stats = {
        "core_sdk": 0,
        "privacy_safety": 0,
        "foreground_service": 0,
        "account_deletion": 0,
        "ad_monetization": 0,
        "storage_photo": 0
    }
    for f in findings:
        rid = f.get("rule_id") or f.get("id", "")
        if f.get("status") in ["FAIL", "WARN"]:
            if rid in ["RULE_TARGET_SDK", "RULE_16KB_PAGE_ALIGNMENT", "RULE_RESTRICTED_PERMISSIONS", "RULE_QUERY_ALL_PACKAGES", "RULE_POST_NOTIFICATIONS", "RULE_EXACT_ALARM", "RULE_FULL_SCREEN_INTENT"]:
                cat_stats["core_sdk"] += 1
            elif rid in ["RULE_PRIVACY_POLICY_URL", "RULE_DATA_SAFETY_DISCLOSURE", "RULE_AI_CONTENT_POLICY"]:
                cat_stats["privacy_safety"] += 1
            elif rid in ["RULE_FOREGROUND_SERVICE"]:
                cat_stats["foreground_service"] += 1
            elif rid in ["RULE_ACCOUNT_DELETION_POLICY"]:
                cat_stats["account_deletion"] += 1
            elif rid in ["RULE_AD_ID_DECLARATION"]:
                cat_stats["ad_monetization"] += 1
            elif rid in ["RULE_STORAGE_PHOTO_PICKER"]:
                cat_stats["storage_photo"] += 1

    return score, fatal_cnt, high_cnt, warn_cnt, cat_stats

