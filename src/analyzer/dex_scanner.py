import json
import os
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Set

class DexScanner:
    def __init__(self, signatures_file: str = None):
        if signatures_file is None:
            current_dir = Path(__file__).parent.parent
            signatures_file = str(current_dir / "data" / "sdk_signatures.json")
        self.signatures_file = signatures_file
        self.signatures = self._load_signatures()

    def _load_signatures(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.signatures_file):
            return []
        with open(self.signatures_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def scan(self, archive_path: str) -> List[Dict[str, Any]]:
        """
        Scans all DEX files inside the AAB/APK archive for SDK class signatures.
        Uses high-speed byte pattern matching on the string pool to keep RAM < 30MB.
        """
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        matched_sdk_ids: Set[str] = set()

        # Pre-build byte patterns for search
        # E.g. com.google.android.gms.ads -> b"com/google/android/gms/ads", b"com.google.android.gms.ads"
        patterns_to_sdk = []
        for sdk in self.signatures:
            sdk_id = sdk["id"]
            for prefix in sdk.get("signature_prefixes", []):
                # slash format
                p_slash = prefix.replace(".", "/").encode("utf-8")
                # dot format
                p_dot = prefix.replace("/", ".").encode("utf-8")
                patterns_to_sdk.append((p_slash, sdk_id))
                patterns_to_sdk.append((p_dot, sdk_id))

        with zipfile.ZipFile(archive_path, "r") as z:
            for item in z.infolist():
                # Matches classes.dex, base/dex/classes.dex, etc.
                if item.filename.endswith(".dex"):
                    with z.open(item) as dex_file:
                        # Read in 4MB chunks with overlap to avoid boundary cuts
                        overlap_size = 1024
                        chunk_size = 4 * 1024 * 1024
                        prev_tail = b""
                        
                        while True:
                            chunk = dex_file.read(chunk_size)
                            if not chunk:
                                break
                            data = prev_tail + chunk
                            
                            for pattern, sdk_id in patterns_to_sdk:
                                if sdk_id not in matched_sdk_ids:
                                    if pattern in data:
                                        matched_sdk_ids.add(sdk_id)
                            
                            # If all known SDKs are already matched, we can early terminate!
                            if len(matched_sdk_ids) == len(self.signatures):
                                break
                                
                            prev_tail = chunk[-overlap_size:]

        # Return full SDK metadata for all matched IDs
        results = [sdk for sdk in self.signatures if sdk["id"] in matched_sdk_ids]
        return results
