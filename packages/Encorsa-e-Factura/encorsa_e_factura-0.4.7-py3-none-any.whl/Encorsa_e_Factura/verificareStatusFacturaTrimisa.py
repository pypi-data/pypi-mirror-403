#!/usr/bin/env python3
import requests
from typing import Dict, Any, Tuple, Optional
import json
import xml.etree.ElementTree as ET

try:
    from AnafUtils import get_token_with_refresh
except:
    from .AnafUtils import get_token_with_refresh


def check_invoice_status_anaf(
    id_incarcare: str,
    extras_json_str: str,
) -> Tuple[int, Dict[str, Any]]:
    """
    Check the status of a previously uploaded invoice to ANAF.

    According to ANAF documentation, the 'stare' field can have these values:
    - "ok": File validated and processed successfully. Invoice is available to buyer.
    - "nok": Errors identified, file not processed. Invoice does NOT reach buyer.
    - "XML cu erori nepreluat de sistem": File rejected during upload.
    - "in prelucrare": Processing not yet completed.

    Parameters:
        id_incarcare: Upload index (numeric string) received from upload operation
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

        Response structure on success (200):
        - XML format with header containing:
          - xmlns: namespace
          - xmlns:mfp: namespace for MFP
          - stareMesaj: root element
          - ExecutionStatus: status indicator
          - stare: "ok" | "nok" | "in prelucrare" | "XML cu erori nepreluat de sistem"
          - id_descarcare: download ID (present when stare is "ok" or "nok")

        Response structure on error (400):
        - JSON format:
          {
            "timestamp": "2019-08-2021 11:01:56",
            "status": "400",
            "errors": "Bad Request",
            "message": "Parametrul id_incarcare este obligatoriu"
          }

    Raises:
        ValueError: If required parameters are missing or invalid
        RuntimeError: If OAuth token cannot be obtained
    """

    # 1) Validate id_incarcare
    if not id_incarcare:
        raise ValueError("id_incarcare is required")

    id_str = str(id_incarcare).strip()
    if not id_str.isdigit():
        raise ValueError(
            f"id_incarcare must be numeric (e.g., '18'), got: {id_incarcare}"
        )

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
        raise ValueError(
            "extras_json_str.oauth must include client_id, client_secret, and refresh_token"
        )

    access_token = get_token_with_refresh(
        refresh_token, client_id, client_secret, token_params
    )
    if not access_token:
        raise RuntimeError(
            "Could not obtain access_token from get_token_with_refresh, token is empty!"
        )

    # Configure proxy if provided
    proxies = {}
    if token_params.get("proxi_pt_anaf_https"):
        proxies["https"] = token_params["proxi_pt_anaf_https"]
    if token_params.get("proxi_pt_anaf_http"):
        proxies["http"] = token_params["proxi_pt_anaf_http"]

    # 4) Build URL
    base = f"https://api.anaf.ro/{'test' if env == 'test' else 'prod'}/FCTEL/rest/stareMesaj"
    url = f"{base}?id_incarcare={id_str}"

    # 5) Prepare headers
    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    # 6) Send GET request
    try:
        resp = requests.get(
            url, headers=headers, timeout=timeout_seconds, proxies=proxies or None
        )

        # Try parse as JSON first (for error responses)
        try:
            return resp.status_code, resp.json()
        except Exception:
            # Success responses are XML format
            return resp.status_code, {
                "xml": resp.text,
                "content_type": resp.headers.get("Content-Type", ""),
            }

    except requests.RequestException as exc:
        return 0, {"error": str(exc), "url": url}



def parse_anaf_status_response(status_code, response):
    """
    Parse ANAF invoice status XML response and return comprehensive JSON result
    """
    result = {
        "http_status_code": status_code,
        "success": False,
        "state": None,
        "download_id": None,
        "in_processing": False,
        "errors": [],
        "raw_response": response.get("xml", "") if isinstance(response, dict) else str(response)
    }
    
    try:
        # Extract XML from response
        xml_text = response.get("xml", "") if isinstance(response, dict) else str(response)
        
        # Parse XML
        root = ET.fromstring(xml_text)
        
        # Define namespace
        ns = {'ns': 'mfp:anaf:dgti:efactura:stareMesajFactura:v1'}
        
        # Get header attributes
        stare = root.get('stare')
        download_id = root.get('id_descarcare')
        
        result["state"] = stare
        result["download_id"] = download_id
        
        # Determine success based on state
        if stare == "ok":
            result["success"] = True
            if not download_id:
                result["errors"].append({
                    "message": "Status is 'ok' but no download ID provided",
                    "type": "missing_data"
                })
        elif stare == "in prelucrare":
            result["in_processing"] = True
            result["errors"].append({
                "message": "Invoice is still being processed",
                "type": "processing"
            })
        elif stare:
            # Any other state value (like "XML cu erori nepreluat de sistem")
            result["errors"].append({
                "message": f"Invoice processing failed: {stare}",
                "type": "processing_error"
            })
        
        # Check for Errors element
        errors = root.findall('ns:Errors', ns)
        if not errors:
            # Fallback: search without namespace prefix
            for child in root:
                if child.tag.endswith('Errors'):
                    errors.append(child)
        
        for error in errors:
            error_msg = error.get('errorMessage', '')
            if error_msg:
                result["errors"].append({
                    "message": error_msg,
                    "type": "validation_error"
                })
        
        # If no state attribute and no errors found, add generic error
        if not stare and not result["errors"]:
            result["errors"].append({
                "message": "Unknown response format",
                "type": "unknown_error"
            })
    
    except ET.ParseError as e:
        result["errors"].append({
            "message": f"XML parsing error: {str(e)}",
            "type": "parse_error"
        })
    except Exception as e:
        result["errors"].append({
            "message": f"Unexpected error: {str(e)}",
            "type": "system_error"
        })
    
    return result


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

    # Check status
    status_code, response = check_invoice_status_anaf("5028681936", json.dumps(extras))

    print(f"Status Code: {status_code}")

    if status_code == 200:
        if "xml" in response:
            # Parse XML response
            parsed = parse_anaf_status_response(status_code, response)
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
            print(response)

            # Check invoice state
            stare = parsed.get("stare")
            if stare == "ok":
                print("✓ Invoice validated and processed successfully")
                print(f"  Download ID: {parsed.get('id_descarcare')}")
            elif stare == "nok":
                print("✗ Invoice has errors and was not processed")
                print(f"  Download ID for error details: {parsed.get('id_descarcare')}")
            elif stare == "in prelucrare":
                print("⧗ Invoice is still being processed")
            else:
                print(f"? Unknown status: {stare}")
        else:
            print(f"Response: {response}")
    else:
        print(f"Error Response: {response}")
