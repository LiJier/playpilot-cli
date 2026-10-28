import json
import csv
import io
import hashlib
from collections import OrderedDict
from pathlib import Path
from urllib.parse import urlsplit
from .i18n import translate_data_type, translate_purpose

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "data" / "data_safety_template.json"

DATA_TYPE_TO_KEY = {
    "Device or other IDs": "PSL_DEVICE_ID",
    "Approximate location": "PSL_APPROX_LOCATION",
    "Precise location": "PSL_PRECISE_LOCATION",
    "App interactions": "PSL_USER_INTERACTION",
    "In-app search history": "PSL_IN_APP_SEARCH_HISTORY",
    "Installed apps": "PSL_APPS_ON_DEVICE",
    "Crash logs": "PSL_CRASH_LOGS",
    "Diagnostics": "PSL_PERFORMANCE_DIAGNOSTICS",
    "Other app performance data": "PSL_OTHER_PERFORMANCE",
    "User IDs": "PSL_USER_ACCOUNT",
    "Name": "PSL_NAME",
    "Email address": "PSL_EMAIL",
    "Phone number": "PSL_PHONE",
    "Purchase history": "PSL_PURCHASE_HISTORY",
    "User payment info": "PSL_CREDIT_DEBIT_BANK_ACCOUNT_NUMBER",
    "Photos": "PSL_PHOTOS",
    "Videos": "PSL_VIDEOS",
    "Voice or sound recordings": "PSL_AUDIO",
    "Contacts": "PSL_CONTACTS",
    "Other user-generated content": "PSL_USER_GENERATED_CONTENT",
    "Files and docs": "PSL_FILES_AND_DOCS",
}

PURPOSE_TO_KEY = {
    "App functionality": "PSL_APP_FUNCTIONALITY",
    "Analytics": "PSL_ANALYTICS",
    "Developer communications": "PSL_DEVELOPER_COMMUNICATIONS",
    "Fraud prevention, security, and compliance": "PSL_FRAUD_PREVENTION_SECURITY",
    "Advertising or marketing": "PSL_ADVERTISING",
    "Personalization": "PSL_PERSONALIZATION",
    "Account management": "PSL_ACCOUNT_MANAGEMENT",
}

# SDK signatures provide review hints, never questionnaire answers.
COLLECTS = "PSL_DATA_COLLECTION_COLLECTS_PERSONAL_DATA"
ACCOUNTS = "PSL_SUPPORTED_ACCOUNT_CREATION_METHODS"
DELETION = "PSL_SUPPORT_DATA_DELETION_BY_USER"
OUTSIDE = "PSL_HAS_OUTSIDE_APP_ACCOUNTS"
OUTSIDE_TYPES = "PSL_OUTSIDE_APP_ACCOUNT_TYPES"
TEXT_FIELDS = {"PSL_ACM_SPECIFY", "PSL_ACCOUNT_DELETION_URL", "PSL_DATA_DELETION_URL", "PSL_OUTSIDE_APP_ACCOUNT_TYPE_SPECIFY"}


def answer_key(question, response=""):
    return f"{question}|{response or ''}"


class DataSafetyValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("; ".join(error["message"] for error in errors))


class DataSafetyCsvExporter:
    """Export blank/reviewed drafts or explicitly confirmed declarations.

    The bundled template is a versioned questionnaire, not proof of compatibility
    with every Play Console account. No SDK inference is written as an answer.
    """

    _template_cache = None

    @classmethod
    def _get_template(cls):
        if cls._template_cache is None:
            with TEMPLATE_PATH.open(encoding="utf-8") as source:
                cls._template_cache = json.load(source)
        return cls._template_cache

    @classmethod
    def template_id(cls):
        fields = [[r[0], r[1] or "", r[3]] for r in cls._get_template()[1:]]
        return hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()

    @classmethod
    def _groups(cls):
        groups = OrderedDict()
        for row in cls._get_template()[1:]:
            groups.setdefault(row[0], []).append(row)
        return groups

    @classmethod
    def suggestions(cls, detected_sdks):
        result = {}
        for sdk in detected_sdks:
            for name in sdk.get("data_safety", {}).get("collected_data", []):
                key = DATA_TYPE_TO_KEY.get(name)
                if key:
                    item = result.setdefault(key, {"data_type": name, "sdk_names": []})
                    sdk_name = sdk.get("name") or sdk.get("id") or "Unknown SDK"
                    if sdk_name not in item["sdk_names"]:
                        item["sdk_names"].append(sdk_name)
        return result

    @classmethod
    def review(cls, answers=None, detected_sdks=None, lang="en", template_csv=None):
        """Return visible questions, sanitized answers and blocking errors.

        Branches no longer applicable are omitted from both drafts and exports.
        All active facts remain unanswered until explicitly supplied by a user.
        """
        groups = cls._groups()
        rows = {answer_key(r[0], r[1]): r for r in cls._get_template()[1:]}
        clean, errors = {}, []

        def error(field, code, message):
            errors.append({"field": field, "code": code, "message": message})

        for key, value in (answers or {}).items():
            row = rows.get(key)
            if row is None:
                error(key, "unknown", "Unknown questionnaire field")
                continue
            if value is None or value == "":
                continue
            if row[0] in TEXT_FIELDS:
                if not isinstance(value, str) or len(value) > 2000 or any(ord(c) < 32 for c in value) or value.lstrip().startswith(("=", "+", "-", "@")):
                    error(key, "text", "Invalid text answer")
                    continue
                if value.strip():
                    clean[key] = value.strip()
            elif type(value) is bool:
                clean[key] = value
            else:
                error(key, "boolean", "Answer must be a boolean, not a string or number")

        def value(q, r=""):
            return clean.get(answer_key(q, r))

        has_data = value(COLLECTS) is True
        account_methods = [r[1] for r in groups[ACCOUNTS] if value(ACCOUNTS, r[1]) is True]
        has_accounts = any(r != "PSL_ACM_NONE" for r in account_methods)
        outside = value(OUTSIDE) is True
        selected_types = {r[1] for q, rr in groups.items() if q.startswith("PSL_DATA_TYPES_") for r in rr if value(q, r[1]) is True} if has_data else set()

        def active(q):
            if q.startswith("PSL_DATA_TYPES_"):
                return has_data
            if q.startswith("PSL_DATA_USAGE_RESPONSES:"):
                _, dt, suffix = q.split(":")
                if dt not in selected_types:
                    return False
                base = f"PSL_DATA_USAGE_RESPONSES:{dt}:PSL_DATA_USAGE_COLLECTION_AND_SHARING"
                if suffix in ("PSL_DATA_USAGE_EPHEMERAL", "DATA_USAGE_USER_CONTROL", "DATA_USAGE_COLLECTION_PURPOSE"):
                    return value(base, "PSL_DATA_USAGE_ONLY_COLLECTED") is True
                if suffix == "DATA_USAGE_SHARING_PURPOSE":
                    return value(base, "PSL_DATA_USAGE_ONLY_SHARED") is True
                return True
            conditions = {
                "PSL_DATA_COLLECTION_ENCRYPTED_IN_TRANSIT": has_data,
                "PSL_ACM_SPECIFY": "PSL_ACM_OTHER" in account_methods,
                "PSL_ACCOUNT_DELETION_URL": has_accounts,
                "PSL_DATA_DELETION_URL": value(DELETION, "DATA_DELETION_YES") is True,
                OUTSIDE_TYPES: outside,
                "PSL_OUTSIDE_APP_ACCOUNT_TYPE_SPECIFY": outside and value(OUTSIDE_TYPES, "PSL_OUTSIDE_APP_ACCOUNT_TYPE_OTHER") is True,
            }
            return conditions.get(q, True)

        visible = {q for q in groups if active(q)}
        clean = {k: v for k, v in clean.items() if k.split("|")[0] in visible}
        if "PSL_ACM_NONE" in account_methods and len(account_methods) > 1:
            error(ACCOUNTS, "exclusive", "No account creation cannot be combined with other account methods")
        if has_data and not selected_types:
            error(COLLECTS, "data_types", "Select at least one collected or shared data type")

        questions = []
        optional = {"PSL_DATA_COLLECTION_COMPLIES_FAMILY_POLICY", "PSL_INDEPENDENTLY_VALIDATED", "PSL_UPI_BADGE_OPT_IN"}
        for q, rr in groups.items():
            if q not in visible:
                continue
            is_choice = rr[0][1] is not None
            kind = "single" if rr[0][3] == "SINGLE_CHOICE" else "multiple" if is_choice else "text" if q in TEXT_FIELDS else "boolean"
            required = q not in optional and not q.startswith("PSL_DATA_TYPES_")
            chosen = [r for r in rr if value(q, r[1]) is True]
            if required and (not chosen if is_choice else value(q) is None):
                error(q, "required", "Please answer this question")
            if kind == "single" and len(chosen) > 1:
                error(q, "single", "Select exactly one answer")
            if q.endswith("_URL") and value(q):
                try:
                    url = urlsplit(value(q))
                    valid = url.scheme in ("http", "https") and bool(url.hostname) and not url.username and not url.password and not any(c.isspace() for c in value(q))
                    url.port
                except ValueError:
                    valid = False
                if not valid:
                    error(q, "url", "Enter an absolute HTTP or HTTPS URL")
            label, options = cls._labels(q, rr, lang)
            questions.append({"id": q, "label": label, "kind": kind, "required": required, "options": options})

        if template_csv is not None:
            try:
                if len(template_csv) > 1_000_000:
                    raise ValueError("Template too large")
                supplied = list(csv.reader(io.StringIO(template_csv.lstrip("\ufeff"))))
                expected = cls._get_template()
                expected_keys = {(r[0], r[1] or "", r[3]) for r in expected[1:]}
                actual_keys = {(r[0], r[1], r[3]) for r in supplied[1:] if len(r) == 5}
                if not supplied or supplied[0] != expected[0] or any(len(r) != 5 for r in supplied) or len(actual_keys) != len(supplied) - 1 or actual_keys != expected_keys:
                    raise ValueError("Template fields or requirements differ")
            except (ValueError, csv.Error, IndexError):
                error("template", "template", "The Console template differs from the supported questionnaire; complete it in Play Console")
        suggestions = cls.suggestions(detected_sdks or [])
        for item in suggestions.values():
            item["label"] = translate_data_type(item["data_type"], lang)
        return {"template_id": cls.template_id(), "questions": questions, "answers": clean, "errors": errors, "suggestions": suggestions}

    @staticmethod
    def _labels(q, rows, lang):
        label = rows[0][4].split(" / ")[0] if rows[0][1] else rows[0][4]
        options = [{"id": r[1], "label": r[4].split(" / ")[-1]} for r in rows if r[1]]
        if lang != "zh":
            if q.startswith("PSL_DATA_USAGE_RESPONSES:"):
                label = " / ".join(rows[0][4].split(" / ")[:2])
            return label, options
        global_labels = {
            COLLECTS: "应用是否收集或共享需要申报的用户数据？",
            "PSL_DATA_COLLECTION_ENCRYPTED_IN_TRANSIT": "所有收集或共享的用户数据是否在传输中加密？",
            ACCOUNTS: "应用支持哪些账号创建方式？（可多选）",
            "PSL_ACM_SPECIFY": "请说明其他账号创建方式",
            "PSL_ACCOUNT_DELETION_URL": "账号及关联数据删除请求网址",
            DELETION: "用户是否可以请求删除数据？",
            "PSL_DATA_DELETION_URL": "数据删除请求网址",
            OUTSIDE: "用户能否使用在应用外创建的账号登录？",
            OUTSIDE_TYPES: "这些外部账号通过什么方式创建？",
            "PSL_OUTSIDE_APP_ACCOUNT_TYPE_SPECIFY": "请说明其他外部账号创建方式",
            "PSL_DATA_COLLECTION_COMPLIES_FAMILY_POLICY": "是否展示遵守家庭政策的承诺？（仅适用于儿童受众或相关计划）",
            "PSL_INDEPENDENTLY_VALIDATED": "应用是否已通过仍有效的 MASA 独立安全评估？",
            "PSL_UPI_BADGE_OPT_IN": "是否展示 UPI 徽章？（仅适用于已获得认证的应用）",
        }
        option_labels = {
            "PSL_ACM_USER_ID_PASSWORD": "用户名和密码", "PSL_ACM_USER_ID_OTHER_AUTH": "用户名和其他身份验证", "PSL_ACM_USER_ID_PASSWORD_OTHER_AUTH": "用户名、密码及其他身份验证", "PSL_ACM_OAUTH": "OAuth", "PSL_ACM_OTHER": "其他", "PSL_ACM_NONE": "应用不允许创建账号",
            "DATA_DELETION_YES": "是", "DATA_DELETION_NO": "否", "DATA_DELETION_NO_AUTO_DELETED": "否，但用户数据会在 90 天内自动删除",
            "PSL_LOGIN_WITH_OUTSIDE_APP_ID": "应用外身份标识（如 SIM 绑定、服务订阅）", "PSL_LOGIN_THROUGH_EMPLOYMENT_OR_ENTERPRISE_ACCOUNT": "雇佣关系或企业账号", "PSL_OUTSIDE_APP_ACCOUNT_TYPE_OTHER": "其他",
            "PSL_DATA_USAGE_ONLY_COLLECTED": "收集", "PSL_DATA_USAGE_ONLY_SHARED": "共享", "PSL_DATA_USAGE_USER_CONTROL_OPTIONAL": "用户可以选择是否收集", "PSL_DATA_USAGE_USER_CONTROL_REQUIRED": "必须收集，用户无法关闭",
        }
        label = global_labels.get(q, label)
        if q.startswith("PSL_DATA_TYPES_"):
            category = rows[0][4].split(" / ")[0]
            label = "收集或共享的数据类型 · " + {
                "Personal info": "个人信息", "Financial info": "财务信息", "Location": "位置",
                "Web browsing": "网页浏览", "Messages": "消息", "Photos and videos": "照片和视频",
                "Audio files": "音频", "Health and fitness": "健康和健身", "Contacts": "通讯录",
                "Calendar": "日历", "App info and performance": "应用信息和性能", "Files and docs": "文件和文档",
                "App activity": "应用活动", "Device or other IDs": "设备或其他 ID",
            }.get(category, category)
        if q.startswith("PSL_DATA_USAGE_RESPONSES:"):
            dt = rows[0][4].split("(", 1)[-1].split(")", 1)[0]
            suffix = q.split(":")[-1]
            label = translate_data_type(dt, "zh") + " · " + {
                "PSL_DATA_USAGE_COLLECTION_AND_SHARING": "收集、共享或两者都有？",
                "PSL_DATA_USAGE_EPHEMERAL": "是否仅在内存中为实时请求临时处理？",
                "DATA_USAGE_USER_CONTROL": "用户是否可以选择不收集？",
                "DATA_USAGE_COLLECTION_PURPOSE": "收集的具体用途（可多选）",
                "DATA_USAGE_SHARING_PURPOSE": "共享的具体用途（可多选）",
            }[suffix]
        for option in options:
            option["label"] = option_labels.get(option["id"], translate_purpose(translate_data_type(option["label"], "zh"), "zh"))
        return label, options

    @classmethod
    def export_csv(cls, detected_sdks=None, account_deletion_url=None, *, answers=None,
                   confirmed=False, template_id=None, template_csv=None):
        # Preserve an explicitly provided URL as a draft hint, independent of SDKs.
        supplied = dict(answers or {})
        if account_deletion_url and not confirmed:
            supplied.setdefault(answer_key("PSL_ACCOUNT_DELETION_URL"), account_deletion_url)
        review = cls.review(supplied, detected_sdks, template_csv=template_csv)
        errors = list(review["errors"])
        if confirmed:
            if template_id != cls.template_id():
                errors.append({"field": "template", "code": "template", "message": "Refresh and review the current questionnaire version"})
            if errors:
                raise DataSafetyValidationError(errors)
        else:
            # Drafts permit missing facts, but never invalid values or templates.
            invalid = [e for e in errors if e["code"] not in ("required", "data_types")]
            if invalid:
                raise DataSafetyValidationError(invalid)
        clean = review["answers"]
        if account_deletion_url and not confirmed:
            # A URL alone does not establish account creation or a deletion policy.
            key = answer_key("PSL_ACCOUNT_DELETION_URL")
            if key not in clean:
                hint = cls.review({answer_key(ACCOUNTS, "PSL_ACM_OTHER"): True, key: account_deletion_url})
                url_errors = [e for e in hint["errors"] if e["field"] == "PSL_ACCOUNT_DELETION_URL"]
                if url_errors:
                    raise DataSafetyValidationError(url_errors)
                clean[key] = account_deletion_url.strip()
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(cls._get_template()[0])
        for q, r, _, requirement, label in cls._get_template()[1:]:
            value = clean.get(answer_key(q, r), "")
            if type(value) is bool:
                value = "TRUE" if value else "FALSE"
            writer.writerow([q, r or "", value, requirement, label])
        return output.getvalue()
