import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"

class ManifestParser:
    def __init__(self, bundletool_path: str = None):
        if bundletool_path is None:
            # Default to bundled jar in bin directory
            current_dir = Path(__file__).parent.parent
            bundletool_path = str(current_dir / "bin" / "bundletool.jar")
        self.bundletool_path = bundletool_path

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parses either an .aab or .apk file and returns structured manifest data.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_lower = file_path.lower()
        if file_lower.endswith(".aab"):
            xml_str = self._dump_aab_manifest(file_path)
            return self._parse_xml_string(xml_str)
        elif file_lower.endswith(".apk"):
            return self._parse_apk_manifest(file_path)
        else:
            # Try AAB first then APK
            try:
                xml_str = self._dump_aab_manifest(file_path)
                return self._parse_xml_string(xml_str)
            except Exception:
                return self._parse_apk_manifest(file_path)

    def _dump_aab_manifest(self, aab_path: str) -> str:
        """
        Calls bundletool.jar to dump the manifest from an .aab file.
        """
        if not os.path.exists(self.bundletool_path):
            raise RuntimeError(f"bundletool.jar not found at: {self.bundletool_path}")

        cmd = [
            "java", "-jar", self.bundletool_path,
            "dump", "manifest",
            "--bundle", aab_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout

    def _parse_apk_manifest(self, apk_path: str) -> Dict[str, Any]:
        """
        Parses APK manifest using pyaxmlparser.
        """
        try:
            from pyaxmlparser import APK
            apk = APK(apk_path)
            
            target_sdk = 0
            try:
                target_sdk = int(apk.get_target_sdk_version() or 0)
            except (ValueError, TypeError):
                pass

            min_sdk = 0
            try:
                min_sdk = int(apk.get_min_sdk_version() or 0)
            except (ValueError, TypeError):
                pass

            manifest_elem = apk.get_android_manifest_xml()
            if manifest_elem is not None:
                from lxml import etree
                xml_str = etree.tostring(manifest_elem, encoding="utf-8").decode("utf-8", errors="replace")
                parsed = self._parse_xml_string(xml_str)
            else:
                parsed = {
                    "package_name": apk.package or "",
                    "version_name": apk.version_name or "",
                    "version_code": str(apk.version_code or ""),
                    "min_sdk": min_sdk,
                    "target_sdk": target_sdk,
                    "permissions": list(apk.get_permissions() or []),
                    "services": [{"name": s, "foreground_service_type": "", "has_fgs_type": False} for s in (apk.get_services() or [])],
                    "activities": list(apk.get_activities() or []),
                    "meta_data": {}
                }

            # Fill missing attributes from APK object if needed
            if not parsed.get("package_name") and apk.package:
                parsed["package_name"] = apk.package
            if not parsed.get("version_name") and apk.version_name:
                parsed["version_name"] = apk.version_name
            if not parsed.get("version_code") and apk.version_code:
                parsed["version_code"] = str(apk.version_code)
            if (not parsed.get("target_sdk") or parsed.get("target_sdk") == 0) and target_sdk > 0:
                parsed["target_sdk"] = target_sdk
            if (not parsed.get("min_sdk") or parsed.get("min_sdk") == 0) and min_sdk > 0:
                parsed["min_sdk"] = min_sdk
            if not parsed.get("permissions") and apk.get_permissions():
                parsed["permissions"] = list(apk.get_permissions())
            if not parsed.get("activities") and apk.get_activities():
                parsed["activities"] = list(apk.get_activities())

            return parsed
        except Exception as e:
            # Fallback if pyaxmlparser fails
            return self._parse_apk_fallback(apk_path, str(e))

    def _parse_apk_fallback(self, apk_path: str, error_msg: str) -> Dict[str, Any]:
        """
        Fallback parser if pyaxmlparser has issues.
        """
        return {
            "package_name": "unknown.apk",
            "version_name": "",
            "version_code": "",
            "min_sdk": 0,
            "target_sdk": 0,
            "permissions": [],
            "services": [],
            "activities": [],
            "meta_data": {},
            "parse_warning": f"APK parsing fallback: {error_msg}"
        }

    def _parse_xml_string(self, xml_content: str) -> Dict[str, Any]:
        """
        Extracts package, targetSdk, permissions, services, etc. from XML content.
        """
        root = ET.fromstring(xml_content)
        
        # Helper to get attribute regardless of namespace or raw prefix
        def get_attr(element, attr_name):
            # Try with namespace
            val = element.attrib.get(f"{ANDROID_NS}{attr_name}")
            if val is not None:
                return val
            # Try with prefix
            val = element.attrib.get(f"android:{attr_name}")
            if val is not None:
                return val
            # Try raw
            return element.attrib.get(attr_name, "")

        package_name = root.attrib.get("package", "")
        version_name = get_attr(root, "versionName")
        version_code = get_attr(root, "versionCode")

        target_sdk = 0
        min_sdk = 0
        uses_sdk = root.find("uses-sdk")
        if uses_sdk is not None:
            t_sdk_str = get_attr(uses_sdk, "targetSdkVersion")
            m_sdk_str = get_attr(uses_sdk, "minSdkVersion")
            try:
                target_sdk = int(t_sdk_str) if t_sdk_str else 0
            except ValueError:
                target_sdk = 0
            try:
                min_sdk = int(m_sdk_str) if m_sdk_str else 0
            except ValueError:
                min_sdk = 0

        # Permissions
        permissions = []
        for perm in root.findall("uses-permission") + root.findall("uses-permission-sdk-23"):
            p_name = get_attr(perm, "name")
            if p_name and p_name not in permissions:
                permissions.append(p_name)

        # Services & foregroundServiceType
        services = []
        app_elem = root.find("application")
        if app_elem is not None:
            for s in app_elem.findall("service"):
                s_name = get_attr(s, "name")
                fgs_type = get_attr(s, "foregroundServiceType")
                services.append({
                    "name": s_name,
                    "foreground_service_type": fgs_type,
                    "has_fgs_type": bool(fgs_type and fgs_type.strip())
                })

        # Activities
        activities = []
        if app_elem is not None:
            for a in app_elem.findall("activity"):
                a_name = get_attr(a, "name")
                if a_name:
                    activities.append(a_name)

        return {
            "package_name": package_name,
            "version_name": version_name,
            "version_code": version_code,
            "min_sdk": min_sdk,
            "target_sdk": target_sdk,
            "uses_features": [
                {"name": get_attr(feature, "name"), "required": get_attr(feature, "required") != "false"}
                for feature in root.findall("uses-feature") if get_attr(feature, "name")
            ],
            "permissions": permissions,
            "services": services,
            "activities": activities,
            "meta_data": {}
        }
