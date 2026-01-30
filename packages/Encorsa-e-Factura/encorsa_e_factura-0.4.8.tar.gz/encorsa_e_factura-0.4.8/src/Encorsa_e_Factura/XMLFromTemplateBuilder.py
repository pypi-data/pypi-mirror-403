import xml.etree.ElementTree as ET
import sys
from typing import Dict, List, Tuple, Any, Optional


class XMLFromTemplateBuilder:
    def __init__(self, namespaces: Dict[str, str]):
        """
        namespaces: mapping prefix -> URI, used to build Clark-notation tags and register prefixes for output.
        """
        self.namespaces = namespaces or {}
        # Register prefixes so ET.tostring emits prefixes instead of ns0, ns1...
        for pfx, uri in self.namespaces.items():
            if pfx is not None and pfx != "":
                ET.register_namespace(pfx, uri)


    # ----------------------------
    # Public API
    # ----------------------------
    def build_document(
        self,
        scalars: Dict[str, Tuple[str, str]],
        item_lists_dict: Dict[str, Tuple[str, List[Tuple[str, str]]]],
        data_by_guid: Dict[str, Any],
        root_hint: Optional[str] = None,
        xml_declaration: bool = True,
        encoding: str = "utf-8",
        as_string: bool = True,
        indent: bool = False,
        # MODIFIED: Added element_order parameter to specify document order
        element_order: Optional[Dict[str, List[str]]] = None,
    ):
        """
        Build an XML document using the compiled template paths and a JSON payload keyed by field GUIDs/list IDs.

        - If root_hint is not provided, the root is inferred from the first segment of any available path in scalars or item_lists_dict. 
        - indent: If provided (e.g., "  " or "\t"), formats XML with indentation. None = no formatting (default).
        - element_order: Dict mapping parent absolute path to ordered list of child element names (qnames).
                        Example: {"/ubl:Invoice": ["cbc:ID", "cac:InvoiceLine", "cbc:Note"]}
        - Returns bytes/str if as_string is True, otherwise returns the root Element for further processing.
        """
        # MODIFIED: Store element_order for use in helper methods
        self.element_order = element_order or {}
        
        # 1) Determine root absolute path like "/ubl:Invoice"
        root_abs = root_hint or self._infer_root_path(scalars, item_lists_dict)
        if not root_abs:
            raise ValueError("Cannot infer root from empty scalars/item_lists_dict; provide root_hint like '/ubl:Invoice'")


        # 2) Create root element
        root_tag = self._qname_to_clark(self._first_seg(root_abs))
        root = ET.Element(root_tag)


        # 3) Apply scalar values
        #    scalars: path -> (guid, "")
        for abs_path, (guid, _) in scalars.items():
            if guid not in data_by_guid:
                continue
            value = data_by_guid[guid]
            if value is None:
                continue
            self._apply_value_at_abs_path(root, root_abs, abs_path, value)


        # 4) Apply lists
        #    item_lists_dict: list_id -> (base_abs_path, [(rel_path, guid), ...])
        for list_id, (base_abs, rel_cols) in item_lists_dict.items():
            rows = data_by_guid.get(list_id)
            if not isinstance(rows, list) or len(rows) == 0:
                continue


            # Determine parent of base_abs and the row tag to create per item
            parent_abs, row_seg = self._split_parent_last(base_abs)
            parent_el = self._ensure_abs_path(root, root_abs, parent_abs)
            row_tag = self._qname_to_clark(row_seg)


            for row in rows:
                # MODIFIED: Use _insert_child_ordered instead of ET.SubElement to maintain order
                row_el = self._insert_child_ordered(parent_el, row_tag, parent_abs, row_seg)
                for rel_path, col_guid in rel_cols:
                    if col_guid not in row:
                        continue
                    col_val = row[col_guid]
                    # rel_path is from row element; can be "/cbc:Name", "/cac:Price/cbc:PriceAmount", or "@attr" on base or "path@attr"
                    self._apply_value_at_rel_path(row_el, rel_path, col_val)

        
        # NEW: Apply indentation if requested
        if indent:
            self._indent_tree(root)

        if as_string:
            xml_bytes = ET.tostring(root, encoding=encoding, xml_declaration=xml_declaration)
            try:
                return xml_bytes.decode(encoding) if isinstance(xml_bytes, (bytes, bytearray)) else xml_bytes
            except Exception:
                return xml_bytes  # leave as bytes if decoding not desired
        return root


    # ----------------------------
    # MODIFIED: New method to insert child elements in correct order
    # ----------------------------
    def _insert_child_ordered(self, parent: ET.Element, child_tag: str, parent_abs_path: str, child_qname: str) -> ET.Element:
        """
        Insert a child element into parent while maintaining the order specified in element_order.
        
        Args:
            parent: Parent element to insert into
            child_tag: Clark notation tag of child to insert
            parent_abs_path: Absolute path of parent element
            child_qname: QName of child (e.g., "cbc:ID")
        
        Returns:
            The newly created child element
        """
        # Check if we have ordering rules for this parent
        if parent_abs_path not in self.element_order:
            # No ordering specified, just append
            return ET.SubElement(parent, child_tag)
        
        order_list = self.element_order[parent_abs_path]
        
        # Find the position where this child should be inserted
        try:
            target_index = order_list.index(child_qname)
        except ValueError:
            # Child not in order list, append at end
            return ET.SubElement(parent, child_tag)
        
        # Find the correct insertion position among existing children
        insert_pos = 0
        for i, existing_child in enumerate(parent):
            existing_qname = self._clark_to_qname(existing_child.tag)
            try:
                existing_index = order_list.index(existing_qname)
                if existing_index < target_index:
                    insert_pos = i + 1
                else:
                    break
            except ValueError:
                # Existing child not in order list, skip
                continue
        
        # Create new element and insert at correct position
        new_element = ET.Element(child_tag)
        parent.insert(insert_pos, new_element)
        return new_element


    # ----------------------------
    # MODIFIED: New helper method to convert Clark notation back to QName
    # ----------------------------
    def _clark_to_qname(self, clark_tag: str) -> str:
        """
        Convert Clark notation back to QName format.
        "{http://uri}LocalName" -> "prefix:LocalName"
        "LocalName" -> "LocalName"
        """
        if not clark_tag.startswith("{"):
            return clark_tag
        
        # Extract URI and local name
        uri, local = clark_tag[1:].split("}", 1)
        
        # Find matching prefix
        for prefix, namespace_uri in self.namespaces.items():
            if namespace_uri == uri:
                return f"{prefix}:{local}"
        
        # No prefix found, return just local name
        return local


    # ----------------------------
    # NEW: Indentation helper
    # ----------------------------
    def _indent_tree(self, elem: ET.Element, indent_str: str = "  ", level: int = 0):
        """
        Add whitespace to the tree for pretty-printing.
        
        For Python 3.9+, uses built-in ET.indent().
        For older versions, implements manual indentation.
        """
        if sys.version_info >= (3, 9):
            # Use built-in indent function
            ET.indent(elem, space=indent_str, level=level)
        else:
            # Manual indentation for older Python versions
            self._indent_manual(elem, indent_str, level)
    
    
    def _indent_manual(self, elem: ET.Element, indent_str: str = "  ", level: int = 0):
        """
        Manually indent XML tree for Python < 3.9.
        Adds newlines and indentation to make XML human-readable.
        """
        i = "\n" + (indent_str * level)
        j = "\n" + (indent_str * (level - 1))
        
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + indent_str
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for subelem in elem:
                self._indent_manual(subelem, indent_str, level + 1)
            # Fix the tail of the last child
            if not subelem.tail or not subelem.tail.strip():
                subelem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


    # ----------------------------
    # Helpers: paths and building
    # ----------------------------
    def _infer_root_path(
        self,
        scalars: Dict[str, Tuple[str, str]],
        item_lists_dict: Dict[str, Tuple[str, List[Tuple[str, str]]]]
    ) -> Optional[str]:
        # Try from scalars
        if scalars:
            any_path = next(iter(scalars.keys()))
            return "/" + self._first_seg(any_path)
        # Else, from list base paths
        for base_abs, _ in item_lists_dict.values():
            return "/" + self._first_seg(base_abs)
        return None


    def _first_seg(self, abs_path: str) -> str:
        # "/ubl:Invoice/cbc:ID" -> "ubl:Invoice"
        parts = [p for p in abs_path.split("/") if p]
        return parts[0] if parts else ""


    def _split_parent_last(self, abs_path: str):
        # "/a/b/c" -> ("/a/b", "c")
        parts = [p for p in abs_path.split("/") if p]
        if not parts:
            return "/", ""
        parent = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        return parent, parts[-1]


    def _qname_to_clark(self, qname: str) -> str:
        # "cbc:ID" -> "{uri}ID", "Invoice" -> "Invoice"
        if ":" in qname:
            prefix, local = qname.split(":", 1)
            uri = self.namespaces.get(prefix)
            if uri:
                return f"{{{uri}}}{local}"
        return qname


    def _ensure_abs_path(self, root: ET.Element, root_abs: str, abs_path: str) -> ET.Element:
        """
        Ensure all elements along the absolute path exist; return the final element.
        Assumes abs_path starts with the same root element as root_abs.
        
        MODIFIED: Now uses _insert_child_ordered to maintain element order when creating new elements.
        """
        if not abs_path:
            return root
        root_seg = self._first_seg(root_abs)
        parts = [p for p in abs_path.split("/") if p]
        if not parts:
            return root
        # Validate/align root
        if parts[0] != root_seg:
            # If mismatch, we still try to traverse from current root, assuming global root matches
            pass
        # Start from root, walk remaining segments
        current = root
        # MODIFIED: Build cumulative path to pass to _insert_child_ordered
        current_path = "/" + root_seg
        
        for idx, seg in enumerate(parts):
            if idx == 0:
                # already at root
                continue
            tag = self._qname_to_clark(seg)
            found = None
            for ch in current:
                if ch.tag == tag:
                    found = ch
                    break
            if found is None:
                # MODIFIED: Use _insert_child_ordered instead of ET.SubElement
                found = self._insert_child_ordered(current, tag, current_path, seg)
            current = found
            # MODIFIED: Update current path
            current_path = current_path + "/" + seg
        return current


    def _apply_value_at_abs_path(self, root: ET.Element, root_abs: str, abs_path: str, value: Any):
        """
        Set element text or attribute at an absolute path like
        "/ubl:Invoice/cbc:ID" or "/ubl:Invoice/cbc:ID@schemeID".
        """
        if "@" in abs_path:
            elem_path, attr_name = abs_path.rsplit("@", 1)
            elem = self._ensure_abs_path(root, root_abs, elem_path)
            self._set_attribute(elem, attr_name, value)
        else:
            elem = self._ensure_abs_path(root, root_abs, abs_path)
            elem.text = "" if value is None else str(value)


    def _apply_value_at_rel_path(self, row_el: ET.Element, rel_path: str, value: Any):
        """
        Apply a value relative to the given row element.
        rel_path examples:
          "/cbc:Name" -> child element text
          "/cac:Price/cbc:PriceAmount" -> nested element text
          "@attr" or "/@attr" -> attribute on row element
          "/cbc:ID@schemeID" -> attribute on a child element
        """
        path = rel_path or ""
        if path == "/":
            path = ""


        if "@" in path:
            # Could be "@attr" (on row), "/@attr", or "path@attr"
            elem_path, attr_name = path.rsplit("@", 1)
            elem_path = elem_path.strip()
            if elem_path in ("", "/"):
                elem = row_el
            else:
                elem = self._ensure_rel_path(row_el, elem_path)
            self._set_attribute(elem, attr_name, value)
        else:
            if path in ("", "/"):
                # Direct text on the row element
                row_el.text = "" if value is None else str(value)
            else:
                elem = self._ensure_rel_path(row_el, path)
                elem.text = "" if value is None else str(value)


    def _ensure_rel_path(self, base: ET.Element, rel_path: str) -> ET.Element:
        """
        Ensure all elements along rel_path (starting with "/") exist beneath 'base'.
        
        MODIFIED: Now uses _insert_child_ordered to maintain element order.
        Note: For relative paths, we can't easily determine the parent absolute path,
        so ordering may not work perfectly for deeply nested relative paths unless
        you extend this to track parent context.
        """
        parts = [p for p in rel_path.split("/") if p]
        current = base
        for seg in parts:
            tag = self._qname_to_clark(seg)
            found = None
            for ch in current:
                if ch.tag == tag:
                    found = ch
                    break
            if found is None:
                # MODIFIED: Use _insert_child_ordered
                # Note: We don't have absolute path context here, so we pass empty string
                # If you need ordering for relative paths, you'll need to track parent context
                found = self._insert_child_ordered(current, tag, "", seg)
            current = found
        return current


    def _set_attribute(self, elem: ET.Element, qname: str, value: Any):
        """
        Set attribute value, supporting namespaced attribute names like "cbc:schemeID".
        """
        if ":" in qname:
            prefix, local = qname.split(":", 1)
            uri = self.namespaces.get(prefix)
            if uri:
                elem.set(f"{{{uri}}}{local}", "" if value is None else str(value))
                return
        elem.set(qname, "" if value is None else str(value))