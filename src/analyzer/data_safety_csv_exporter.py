import json
import csv
import io
from pathlib import Path
from typing import List, Dict, Any, Optional

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

class DataSafetyCsvExporter:
    """
    Exports full Google Play Console compatible Data Safety CSV (UTF-8 without BOM).
    Conforms to the official 783-row questionnaire structure so developers can directly
    upload and import the CSV into Google Play Console -> App Content -> Data Safety.
    """

    _template_cache = None

    @classmethod
    def _get_template(cls) -> List[List[Any]]:
        if cls._template_cache is None:
            if not TEMPLATE_PATH.exists():
                raise FileNotFoundError(f"Data Safety template not found at {TEMPLATE_PATH}")
            with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
                cls._template_cache = json.load(f)
        return cls._template_cache

    @classmethod
    def export_csv(
        cls,
        detected_sdks: List[Dict[str, Any]],
        account_deletion_url: Optional[str] = None
    ) -> str:
        """
        Synthesizes standard Google Play Data Safety CSV string based on detected SDKs.
        """
        template = cls._get_template()

        # 1. Aggregate collected data types and their purposes/sharing
        collected_data_map = {}  # key -> {"purposes": set(), "shared": bool, "ephemeral": bool}
        for sdk in detected_sdks:
            safety = sdk.get("data_safety", {})
            data_items = safety.get("collected_data", [])
            purposes = safety.get("purposes", [])
            is_shared = safety.get("shared_with_third_parties", False)
            is_ephemeral = safety.get("ephemeral", False)

            for dt in data_items:
                dt_key = DATA_TYPE_TO_KEY.get(dt)
                if not dt_key:
                    continue
                if dt_key not in collected_data_map:
                    collected_data_map[dt_key] = {
                        "purposes": set(),
                        "shared": False,
                        "ephemeral": True  # will be false if any SDK is non-ephemeral
                    }
                for p in purposes:
                    p_key = PURPOSE_TO_KEY.get(p)
                    if p_key:
                        collected_data_map[dt_key]["purposes"].add(p_key)
                if is_shared:
                    collected_data_map[dt_key]["shared"] = True
                if not is_ephemeral:
                    collected_data_map[dt_key]["ephemeral"] = False

        has_data = len(collected_data_map) > 0

        # 2. Build answer lookup table (hash_key = f"{q_id},{resp_id or ''}")
        answers = {}

        # Top-level question: Collects personal data?
        answers["PSL_DATA_COLLECTION_COLLECTS_PERSONAL_DATA,"] = "true" if has_data else "false"

        if has_data:
            # Transit encryption
            answers["PSL_DATA_COLLECTION_ENCRYPTED_IN_TRANSIT,"] = "true"

            # Account creation & deletion
            if account_deletion_url:
                answers["PSL_ACCOUNT_DELETION_URL,"] = account_deletion_url
                answers["PSL_SUPPORT_DATA_DELETION_BY_USER,DATA_DELETION_YES"] = "true"
            else:
                answers["PSL_SUPPORTED_ACCOUNT_CREATION_METHODS,PSL_ACM_NONE"] = "true"
                answers["PSL_SUPPORT_DATA_DELETION_BY_USER,DATA_DELETION_NO_AUTO_DELETED"] = "true"

            # Mark collected data types in PSL_DATA_TYPES_*
            for dt_key in collected_data_map:
                # Find the category question ID in template for dt_key
                for row in template[1:]:
                    if str(row[0]).startswith("PSL_DATA_TYPES_") and row[1] == dt_key:
                        answers[f"{row[0]},{dt_key}"] = "true"

            # Fill in usage and handling details for each collected data type
            for dt_key, meta in collected_data_map.items():
                prefix = f"PSL_DATA_USAGE_RESPONSES:{dt_key}"

                # Collection & Sharing mode
                answers[f"{prefix}:PSL_DATA_USAGE_COLLECTION_AND_SHARING,PSL_DATA_USAGE_ONLY_COLLECTED"] = "true"
                if meta["shared"]:
                    answers[f"{prefix}:PSL_DATA_USAGE_COLLECTION_AND_SHARING,PSL_DATA_USAGE_ONLY_SHARED"] = "true"

                # Ephemeral processing
                answers[f"{prefix}:PSL_DATA_USAGE_EPHEMERAL,"] = "true" if meta["ephemeral"] else "false"

                # User control (required for app/SDK operation)
                answers[f"{prefix}:DATA_USAGE_USER_CONTROL,PSL_DATA_USAGE_USER_CONTROL_REQUIRED"] = "true"

                # Collection purposes
                for p_key in meta["purposes"]:
                    answers[f"{prefix}:DATA_USAGE_COLLECTION_PURPOSE,{p_key}"] = "true"

                # Sharing purposes (if shared)
                if meta["shared"]:
                    for p_key in meta["purposes"]:
                        answers[f"{prefix}:DATA_USAGE_SHARING_PURPOSE,{p_key}"] = "true"
        else:
            # Clean app with no data collection
            answers["PSL_SUPPORTED_ACCOUNT_CREATION_METHODS,PSL_ACM_NONE"] = "true"
            answers["PSL_SUPPORT_DATA_DELETION_BY_USER,DATA_DELETION_NO_AUTO_DELETED"] = "true"

        # 3. Assemble CSV
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")

        # Write header
        writer.writerow(template[0])

        # Write all question rows
        for row in template[1:]:
            q_id = row[0]
            resp_id = row[1] if row[1] is not None else ""
            ans_req = row[3]
            label = row[4]

            hash_key = f"{q_id},{resp_id}"
            resp_val = answers.get(hash_key, "")

            writer.writerow([q_id, resp_id, resp_val, ans_req, label])

        return output.getvalue()
