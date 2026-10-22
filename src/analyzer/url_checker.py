import httpx
from typing import Dict, Any

class UrlChecker:
    @staticmethod
    def check_privacy_url(url: str, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Probes a privacy policy URL for HTTP status, SSL validity, and redirection.
        """
        if not url or not url.strip():
            return {
                "url": url,
                "is_valid": False,
                "status_code": None,
                "error": "未提供隐私政策链接"
            }

        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }

        try:
            with httpx.Client(timeout=timeout, follow_redirects=True, verify=True) as client:
                res = client.get(url, headers=headers)
                is_ok = 200 <= res.status_code < 400
                return {
                    "url": str(res.url),
                    "is_valid": is_ok,
                    "status_code": res.status_code,
                    "error": None if is_ok else f"HTTP 状态码异常: {res.status_code}"
                }
        except httpx.HTTPStatusError as e:
            return {
                "url": url,
                "is_valid": False,
                "status_code": e.response.status_code if e.response else None,
                "error": f"HTTP 请求错误: {str(e)}"
            }
        except httpx.ConnectError:
            return {
                "url": url,
                "is_valid": False,
                "status_code": None,
                "error": "无法连接到服务器，可能存在 DNS 解析失败或主机不可达"
            }
        except httpx.ConnectTimeout:
            return {
                "url": url,
                "is_valid": False,
                "status_code": None,
                "error": "连接超时（超过 5 秒未响应）"
            }
        except Exception as e:
            return {
                "url": url,
                "is_valid": False,
                "status_code": None,
                "error": f"网络异常: {str(e)}"
            }
