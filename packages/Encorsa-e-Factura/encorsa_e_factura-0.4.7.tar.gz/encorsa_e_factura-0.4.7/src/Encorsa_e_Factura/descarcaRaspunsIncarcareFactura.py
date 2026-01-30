#!/usr/bin/env python3
import requests
import json
import zipfile
import io
from typing import Dict, Any, Tuple


def download_invoice_response_anaf(
    id_descarcare: str,
    extras_json_str: str,
) -> Tuple[int, Dict[str, Any]]:
    """
    Download the response from ANAF for a processed invoice.
    
    Parameters:
        id_descarcare: Download ID obtained from stareMesaj or lista mesaje response
        extras_json_str: JSON string containing:
            {
              "env": "test" | "prod",                         # default: "test"
              "oauth": {
                  "client_id": "...",
                  "client_secret": "...",
                  "refresh_token": "...",
                  "parameters": {
                      "proxi_pt_anaf_https": "",              # optional proxy for HTTPS
                      "proxi_pt_anaf_http": ""                # optional proxy for HTTP
                  }
              },
              "timeout_seconds": 60                           # optional: default 60
            }
    
    Returns:
        Tuple of (status_code, response_dict)
        
        On success (200 with ZIP):
        {
            "xml_content": "<?xml ...",
            "upload_id": "5028442192",
            "size_bytes": 1234
        }
        
        On error (200 with JSON or other status):
        {
            "error": "error message",
            "title": "Descarcare mesaj"
        }
    
    Raises:
        ValueError: If required parameters are missing or invalid
        RuntimeError: If OAuth token cannot be obtained
    """
    try:
        from AnafUtils import get_token_with_refresh
    except:
        from .AnafUtils import get_token_with_refresh
    
    # 1) Validate id_descarcare
    if not id_descarcare:
        raise ValueError("id_descarcare is required")
    
    id_str = str(id_descarcare).strip()
    
    # 2) Parse extras
    try:
        extras: Dict[str, Any] = json.loads(extras_json_str)
    except Exception as exc:
        raise ValueError(f"Invalid extras_json_str: {exc}")
    
    env = (extras.get("env") or "test").lower()
    timeout_seconds = int(extras.get("timeout_seconds", 60))
    
    # 3) OAuth2: obtain access token
    oauth = extras.get("oauth") or {}
    client_id = oauth.get("client_id")
    client_secret = oauth.get("client_secret")
    refresh_token = oauth.get("refresh_token")
    token_params = oauth.get("parameters") or {}
    
    if not (client_id and client_secret and refresh_token):
        raise ValueError("extras_json_str.oauth must include client_id, client_secret, and refresh_token")
    
    access_token = get_token_with_refresh(refresh_token, client_id, client_secret, token_params)
    if not access_token:
        raise RuntimeError("Could not obtain access_token from get_token_with_refresh, token is empty!")
    
    # Configure proxy if provided
    proxies = {}
    if token_params.get("proxi_pt_anaf_https"):
        proxies["https"] = token_params["proxi_pt_anaf_https"]
    if token_params.get("proxi_pt_anaf_http"):
        proxies["http"] = token_params["proxi_pt_anaf_http"]
    
    # 4) Build URL
    base = f"https://api.anaf.ro/{'test' if env == 'test' else 'prod'}/FCTEL/rest/descarcare"
    url = f"{base}?id={id_str}"
    
    # 5) Prepare headers
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    
    # 6) Send GET request
    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=timeout_seconds,
            proxies=proxies or None,
            stream=True
        )
        
        if resp.status_code != 200:
            # Try to parse JSON error response
            try:
                error_data = resp.json()
                return resp.status_code, {
                    "error": error_data.get("eroare", resp.text),
                    "title": error_data.get("titlu", "Error")
                }
            except Exception:
                return resp.status_code, {
                    "error": resp.text or f"HTTP {resp.status_code}",
                    "title": "Request Error"
                }
        
        # Status code is 200 - check content type
        content_type = resp.headers.get('Content-Type', '').lower()
        
        # Try to determine if it's JSON or ZIP
        content = resp.content
        
        # First, try to parse as JSON (error response)
        if 'application/json' in content_type or content.startswith(b'{'):
            try:
                error_data = json.loads(content)
                return 200, {
                    "error": error_data.get("eroare", "Unknown error"),
                    "title": error_data.get("titlu", "Descarcare mesaj")
                }
            except Exception:
                pass  # Not JSON, continue to ZIP handling
        
        # Try to handle as ZIP file
        try:
            zip_buffer = io.BytesIO(content)
            with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                # List all files in the ZIP
                file_list = zip_file.namelist()
                
                # Find the XML file without "semnatura_" prefix
                xml_file = None
                upload_id = None
                
                for filename in file_list:
                    if filename.endswith('.xml') and not filename.startswith('semnatura_'):
                        xml_file = filename
                        # Extract upload ID from filename (e.g., "5028442192.xml" -> "5028442192")
                        upload_id = filename.replace('.xml', '')
                        break
                
                if not xml_file:
                    return 200, {
                        "error": "No valid XML file found in ZIP archive",
                        "title": "Invalid Archive"
                    }
                
                # Extract and read the XML content
                xml_content = zip_file.read(xml_file).decode('utf-8')
                
                return 200, {
                    "xml_content": xml_content,
                    "upload_id": upload_id,
                    "size_bytes": len(xml_content)
                }
        
        except zipfile.BadZipFile:
            # Not a valid ZIP file
            # Try one more time to parse as JSON in case content-type was wrong
            try:
                error_data = json.loads(content)
                return 200, {
                    "error": error_data.get("eroare", "Unknown error"),
                    "title": error_data.get("titlu", "Descarcare mesaj")
                }
            except Exception:
                return 200, {
                    "error": "Invalid response format (neither ZIP nor JSON)",
                    "title": "Invalid Response"
                }
    
    except requests.RequestException as exc:
        return 0, {
            "error": str(exc),
            "title": "Request Exception"
        }


# Usage example
if __name__ == "__main__":
    extras = {
        "env": "test",
        "standard": "UBL",
        "cif": "18239095",
        "oauth": {
            "client_id": "1309747503a163b2ee37047279d37e8a7e3ee71d085ddf65",
            "client_secret": "0238adeb4847d0b06f58b258545b4d287db73db70b817e8a7e3ee71d085ddf65",
            "refresh_token": "WdHky4t4SX2aHbLZuER6BOrdOE-rpv_SRH1qvw2aE5kR-3bUY1BYVI9kzOXLRKWzV0x8u3VtQZdhUUf4KwEnsJH5-rU7xwp88zfPdSRNJun-uPJC0XF4S05dZSJysK9xTU88wH7Ms80hLLupqWw5FTxPE94hLeTOxO6YamhA77tAiJ97a2jl1D2G8lzc6QAaTDlZ9Ng-0VpeCmGjjNFPDCLl7r18uV4vnm7_ykv9Tdk5jznbw6ygg2TnozuDyw3WKdZ8egIfrBjG4CIeXiAmJmci_CNUaJoVejXOlxsgNzyohA2MVdHkwcaqFNH83d6fIS7DC-O2OB17UEXnq29PGAus3pkkFvgflM9Vc8723SEqSHdl1yM4ZegKu4hexP4QcRs3jNwbKmT4ixL8Y-f1bpXAMmnp0d7VVw9D0n8iIqrFwttp4fISuET1sfnYfyOuuRw4rDEW4_E4M2Rup89_V9nfg85LPXF1EBK3XXF6vdtpnfcX20ypHPSxu7aH8VT46Cf1f-TzQ2d5iI6EXg-7zcaKhh8EGDjIT9011s_TEGCx1GjD-LSQ1rsxlgAcy92GlfzWK3gs7XU-TT9kdg_CEIOht8KRhHPVQrH-aIL_7GJvGLpzArn0BRNtYN--wv-FcuxiYtB_cLDLdyF62SzSzqVBwQMRDzSCnFYhHW-FP0HsdPYQGpJ0As3Cz55SrN7FuZW-SB6H9vEKb5Wt2U40znL6v6W9EiUil2LzlQMxAR6wyZp_PRitJkGApQdbQb3XwqD2rDM80NLmUv25WodBYAJXfUPpVXKXxFotlaX0avBxG_yGUS4zGEKQ20cZehXUxtukqt9i_3buywrmzS7KQHsMYCQkJdq3P4BWjfZh_kZGPLY7m_RLGdSdIh9mdgYXK17eDd4_wIAw3b3jn-4Ulfyil5XZuFv5SgnnM__Tu-4CH0nA9lzr-ifAZ1ylfMu3VVRB3GGEeK1wNsqiwAffyHvLgWGUeFaJM8mHumwHn_3HP6cbIpwQu-ObVcxd1gtAZQWdQnVkF8xHWWcgxRMrbM_Cpqp_ZdnnbcddqKXMOSozrGvmwMS3A3YS7LM0R1B2QkuU0dCOhkcwY3oEZMsR-SUeu6VbN1tOI-PVLbwy1KASitWoJg6A80wGt1ArjjB2UfaZNmzAP48Sa-vFOaz_K-SOgSpqsTFUkeNJB1HudEOxzkTap5cnbp2rXws0aKFKWZaNdzlinD21fAj6q8E_XEjs5TDXfa4jY9vmpOIvb8F-DaZ8GVTvaVfMia8QsMpIbPiPVkScaejUTqB5z5vih_oVg2slW6i9wLGwcvRmcazmXfpVALJAFooexE_-0ByHelKPsLuxHVkqTLuzVS0vc6vkT4SEiJmBldTII9AxdhZuezcpiW9Eyf5BqP2Yvd8cwAvck2Wj4nNm3-gRWXi2LHwMGaow7LDOIX0YysoUj_y-FOmX9FG9QNMuClprnjK6WySEKWEb22MwowrPO3lyVcvht8_vKhkInviR1zomn14mIw7F1g",
        },
    }
    
    # Download invoice response
    status_code, response = download_invoice_response_anaf(
        "3044244370",
        json.dumps(extras)
    )
    
    if status_code == 200 and "xml_content" in response:
        print(f"✓ Invoice XML downloaded successfully")
        print(f"  Upload ID: {response['upload_id']}")
        print(f"  Size: {response['size_bytes']} bytes")
        print(f"  XML Preview: {response['xml_content'][:200]}...")
        
        # Caller can save if needed
        with open(f"{response['upload_id']}.xml", 'w', encoding='utf-8') as f:
            f.write(response['xml_content'])
        print(f"  Saved to: {response['upload_id']}.xml")
    else:
        print(f"✗ Download failed (HTTP {status_code}):")
        print(f"  Error: {response.get('error')}")
        print(f"  Title: {response.get('title')}")
