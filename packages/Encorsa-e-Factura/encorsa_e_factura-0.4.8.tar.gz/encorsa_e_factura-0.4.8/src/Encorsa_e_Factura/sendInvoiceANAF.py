#!/usr/bin/env python3
import json
import io
import os
import sys
import zipfile
from typing import Dict, Any, Tuple, List, Optional

import requests
import xml.etree.ElementTree as ET

# Project-local imports
try:
    from sincronizare import XMLProcessor
except:
    from .sincronizare import XMLProcessor
    
try:
    from XMLFromTemplateBuilder import XMLFromTemplateBuilder
except:
    from .XMLFromTemplateBuilder import XMLFromTemplateBuilder
    
try:
    from AnafUtils import get_token_with_refresh
except:
    from .AnafUtils import get_token_with_refresh
    
try:
    from xml_namespaces import namespaces, nota_namespaces
except:
    from .xml_namespaces import namespaces, nota_namespaces


# Constants for supported standards
STANDARD_UBL = "UBL"
STANDARD_CN = "CN"
SUPPORTED_STANDARDS = {STANDARD_UBL, STANDARD_CN}

# Mapping of standards to their configurations
STANDARD_CONFIG = {
    STANDARD_UBL: {
        "namespaces": namespaces,
        "root_element": "Invoice",
        "root_namespace": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "root_hint": "/ubl:Invoice"
    },
    STANDARD_CN: {
        "namespaces": nota_namespaces,
        "root_element": "CreditNote",
        "root_namespace": "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2",
        "root_hint": "/default:CreditNote"
    }
}


def _bool_str(v: Optional[str]) -> Optional[str]:
    """Convert value to ANAF boolean string format ('DA' or None)."""
    if v is None:
        return None
    s = str(v).strip().upper()
    return "DA" if s == "DA" else None


def _build_upload_url(env: str, params: Dict[str, Any]) -> str:
    """
    Build the ANAF upload URL with required and optional query parameters.
    
    Args:
        env: "test" or "prod"
        params: must include "standard" and "cif"; may include "extern", "autofactura", "executare"
    
    Returns:
        Complete URL with query parameters
    """
    base = f"https://api.anaf.ro/{'test' if env.lower() == 'test' else 'prod'}/FCTEL/rest/upload"
    
    # Required parameters
    q = [("standard", params["standard"]), ("cif", params["cif"])]
    
    # Optional flags (only accept "DA")
    for key in ("extern", "autofactura", "executare"):
        val = _bool_str(params.get(key))
        if val:
            q.append((key, val))
    
    # Assemble URL
    from urllib.parse import urlencode
    return f"{base}?{urlencode(q)}"


def _ensure_bytes(data, encoding="utf-8") -> bytes:
    """Convert data to bytes if not already."""
    if data is None:
        return b""
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    return str(data).encode(encoding or "utf-8", errors="replace")


def _zip_bytes(filename: str, content: bytes) -> bytes:
    """Create a ZIP archive containing the given content."""
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, content)
    return mem.getvalue()


def _get_standard_config(standard: str, custom_namespaces: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Get configuration for a given standard.
    
    Args:
        standard: Standard type (UBL, CN, CII, RASP)
        custom_namespaces: Optional custom namespaces to override defaults
    
    Returns:
        Configuration dictionary with namespaces and root element info
    
    Raises:
        ValueError: If standard is not supported
    """
    standard = standard.upper()
    
    if standard not in SUPPORTED_STANDARDS:
        if standard in ("CII", "RASP"):
            raise ValueError(f"Standard '{standard}' is not yet implemented. Currently supported: {', '.join(SUPPORTED_STANDARDS)}")
        else:
            raise ValueError(f"Unknown standard '{standard}'. Supported standards: {', '.join(SUPPORTED_STANDARDS)}")
    
    config = STANDARD_CONFIG[standard].copy()
    
    # Override with custom namespaces if provided
    if custom_namespaces:
        config["namespaces"] = custom_namespaces
    
    return config


# MODIFIED: New function to extract element order from template XML
def _extract_element_order_from_template(
    template_xml_path: str,
    namespaces: Dict[str, str]
) -> Dict[str, List[str]]:
    """
    Parse the template XML and extract the order of child elements for each parent.
    
    Args:
        template_xml_path: Path to the template XML file
        namespaces: Namespace mapping (prefix -> URI)
    
    Returns:
        Dictionary mapping absolute parent paths to ordered lists of child element QNames
        Example: {"/ubl:Invoice": ["cbc:ID", "cbc:IssueDate", "cac:InvoiceLine"]}
    """
    # Parse the template XML
    tree = ET.parse(template_xml_path)
    root = tree.getroot()
    
    # Reverse namespace mapping for converting Clark notation to QName
    uri_to_prefix = {uri: prefix for prefix, uri in namespaces.items()}
    
    def clark_to_qname(tag: str) -> str:
        """Convert {uri}local to prefix:local"""
        if not tag.startswith("{"):
            return tag
        uri, local = tag[1:].split("}", 1)
        prefix = uri_to_prefix.get(uri, "")
        return f"{prefix}:{local}" if prefix else local
    
    def get_qname(element: ET.Element) -> str:
        """Get QName for an element"""
        return clark_to_qname(element.tag)
    
    # Dictionary to store parent path -> ordered child QNames
    element_order = {}
    
    def build_path(ancestors: List[str]) -> str:
        """Build absolute path from ancestor QNames"""
        if not ancestors:
            return "/"
        return "/" + "/".join(ancestors)
    
    def traverse(element: ET.Element, ancestors: List[str]):
        """Recursively traverse the tree and record child element order"""
        current_qname = get_qname(element)
        current_path = build_path(ancestors)
        
        # Get all child elements (not text nodes)
        children = [child for child in element if isinstance(child.tag, str)]
        
        if children:
            # Record the order of children
            child_qnames = []
            seen = set()
            
            for child in children:
                child_qname = get_qname(child)
                # Only record each unique child QName once (preserve first occurrence order)
                if child_qname not in seen:
                    child_qnames.append(child_qname)
                    seen.add(child_qname)
            
            if child_qnames:
                element_order[current_path] = child_qnames
            
            # Recursively process children
            for child in children:
                child_qname = get_qname(child)
                traverse(child, ancestors + [child_qname])
    
    # Start traversal from root
    root_qname = get_qname(root)
    traverse(root, [root_qname])
    
    return element_order


def send_invoice_anaf(
    data_json_str: str,
    template_xml_path: str,
    extras_json_str: str,
    debug=False
) -> Tuple[int, Dict[str, Any]]:
    """
    Build XML from template + data_by_guid and POST it to ANAF using OAuth2.
    
    MODIFIED: Now automatically extracts element order from the template XML to preserve structure.
    
    Parameters:
        data_json_str: JSON string with scalars and list rows keyed by GUIDs and list_id, respectively
        template_xml_path: File path to XML template
        extras_json_str: JSON string containing:
            {
              "env": "test" | "prod",                         # default: "test"
              "standard": "UBL" | "CN",                       # required (CII, RASP not yet supported)
              "cif": "########",                              # required numeric string (e.g., "8000000000")
              "namespaces": {...},                            # optional: prefix -> URI (uses defaults if not provided)
              "extern": "DA",                                 # optional flag
              "autofactura": "DA",                            # optional flag
              "executare": "DA",                              # optional flag
              "oauth": {
                  "client_id": "...",
                  "client_secret": "...",
                  "refresh_token": "...",
                  "parameters": {
                      "proxi_pt_anaf_https": "",              # optional proxy for HTTPS
                      "proxi_pt_anaf_http": ""                # optional proxy for HTTP
                  }
              },
              "serialization": {
                  "root_hint": "/ubl:Invoice",                # optional: auto-determined from standard if not provided
                  "xml_declaration": true,                    # optional: default true
                  "encoding": "utf-8"                         # optional: default utf-8
              },
              "upload": {
                  "as_multipart": false,                      # optional: default false
                  "multipart_field_name": "file",             # optional: default "file"
                  "zip": false,                               # optional: default false
                  "zip_entry_name": "invoice.xml",            # optional: default "invoice.xml"
                  "timeout_seconds": 60                       # optional: default 60
              }
            }
    
    Returns:
        Tuple of (status_code, response_json_or_dict)
    
    Raises:
        ValueError: If required parameters are missing or invalid
        RuntimeError: If OAuth token cannot be obtained
    """
    # 1) Parse inputs
    try:
        data_by_guid: Dict[str, Any] = json.loads(data_json_str)
    except Exception as exc:
        raise ValueError(f"Invalid data_json_str: {exc}")

    try:
        extras: Dict[str, Any] = json.loads(extras_json_str)
    except Exception as exc:
        raise ValueError(f"Invalid extras_json_str: {exc}")

    # 2) Validate and get standard configuration
    standard = extras.get("standard")
    if not standard:
        raise ValueError("extras_json_str must include 'standard' (UBL or CN)")
    
    cif = extras.get("cif")
    if not cif:
        raise ValueError("extras_json_str must include 'cif'")
    
    # Validate CIF is numeric string (as per ANAF swagger example: "8000000000")
    cif_str = str(cif).strip()
    if not cif_str.isdigit():
        raise ValueError(f"CIF must be a numeric string (e.g., '8000000000'), got: {cif}")
    
    # Get namespaces and configuration based on standard
    custom_namespaces = extras.get("namespaces")
    config = _get_standard_config(standard, custom_namespaces)
    doc_namespaces = config["namespaces"]
    
    env = (extras.get("env") or "test").lower()

    # MODIFIED: Extract element order from template XML before processing
    element_order = _extract_element_order_from_template(template_xml_path, doc_namespaces)
    
    if debug:
        print("==== Extracted Element Order ====")
        print(json.dumps(element_order, indent=2))

    # 3) Compile template to scalars + item_lists_dict
    xp = XMLProcessor(template_xml_path, namespaces=doc_namespaces)
    scalars_map, item_lists_dict, _ = xp.compile_template()

    # 4) Build XML using builder
    serialization = extras.get("serialization") or {}
    
    # Use root_hint from serialization config, or fall back to standard's default
    root_hint = serialization.get("root_hint") or config["root_hint"]
    xml_decl = bool(serialization.get("xml_declaration", True))
    encoding = serialization.get("encoding") or "utf-8"

    builder = XMLFromTemplateBuilder(doc_namespaces)
    # MODIFIED: Pass the auto-extracted element_order to builder
    xml_str = builder.build_document(
        scalars=scalars_map,
        item_lists_dict=item_lists_dict,
        data_by_guid=data_by_guid,
        root_hint=root_hint,
        xml_declaration=xml_decl,
        encoding=encoding,
        as_string=True,
        indent=True,
        element_order=element_order  # MODIFIED: Use auto-extracted order
    )
    xml_bytes = _ensure_bytes(xml_str, encoding=encoding)
    
    if debug:
        # print the json and xml files content
        print("==== scalars_map ====")
        print(json.dumps(scalars_map, indent=4))
        print("==== xml_str XML ====")
        print(str(xml_str))

    # 5) OAuth2: obtain access token
    oauth = extras.get("oauth") or {}
    client_id = oauth.get("client_id")
    client_secret = oauth.get("client_secret")
    refresh_token = oauth.get("refresh_token")
    token_params = oauth.get("parameters") or {}

    if not (client_id and client_secret and refresh_token):
        raise ValueError("extras_json_str.oauth must include client_id, client_secret, and refresh_token")

    access_token = get_token_with_refresh(refresh_token, client_id, client_secret, token_params)
    if not access_token:
        raise RuntimeError("Could not obtain access_token from get_token_with_refresh, the token is EMPTY!")

    # Configure proxy if provided in token parameters
    proxies = {}
    if token_params.get("proxi_pt_anaf_https"):
        proxies["https"] = token_params["proxi_pt_anaf_https"]
    if token_params.get("proxi_pt_anaf_http"):
        proxies["http"] = token_params["proxi_pt_anaf_http"]

    # 6) Build endpoint URL and prepare request
    upload_params = {
        "standard": standard.upper(),
        "cif": cif_str,
        "extern": extras.get("extern"),
        "autofactura": extras.get("autofactura"),
        "executare": extras.get("executare"),
    }
    url = _build_upload_url(env, upload_params)

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    upload_cfg = extras.get("upload") or {}
    as_multipart = bool(upload_cfg.get("as_multipart", False))
    multipart_field_name = upload_cfg.get("multipart_field_name") or "file"
    do_zip = bool(upload_cfg.get("zip", False))
    zip_entry_name = upload_cfg.get("zip_entry_name") or "invoice.xml"
    timeout_seconds = int(upload_cfg.get("timeout_seconds", 60))

    payload_bytes = xml_bytes
    if do_zip:
        payload_bytes = _zip_bytes(zip_entry_name, xml_bytes)

    # 7) Send request
    try:
        if as_multipart:
            # Multipart form-data
            filename = zip_entry_name + (".zip" if do_zip else "")
            content_type = "application/zip" if do_zip else "application/xml"
            files = {
                multipart_field_name: (filename, payload_bytes, content_type)
            }
            resp = requests.post(
                url, 
                headers=headers, 
                files=files, 
                timeout=timeout_seconds,
                proxies=proxies or None
            )
        else:
            # Raw body
            headers["Content-Type"] = "application/zip" if do_zip else "application/xml"
            resp = requests.post(
                url, 
                headers=headers, 
                data=payload_bytes, 
                timeout=timeout_seconds,
                proxies=proxies or None
            )

        # Try parse JSON, else return text
        try:
            # TO DO
            # Check the ANAF response even when status code is 200 because there can be validation errors
            # When validation error occurs the JSON property "text" will contain an XML string and the "header" node will have the "ExecutionStatus" attribute != "0" like "1" or something similar to an error code
            # Also the "header" node will have a child node "Errors" that will have and attribute "errorMessage" with the full error description
            # If there is not error the "ExecutionStatus" should be "0" and
            # More than that, the "header" node will have an additional attribute "index_incarcare" that will be equal with some number like "5028440322"
            # The "index_incarcare" must be extracted and returned along the status code and such
            
            return resp.status_code, resp.json()
        except Exception:
            return resp.status_code, {"text": resp.text}

    except requests.RequestException as exc:
        return 0, {"error": str(exc), "url": url}