namespaces = {
    'ubl': "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    'qdt': "urn:oasis:names:specification:ubl:schema:xsd:QualifiedDataTypes-2",
    'cac': "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    'cbc': "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}

nota_namespaces = {
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "ccts": "urn:un:unece:uncefact:documentation:2",
    "default": "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2",
    "qdt": "urn:oasis:names:specification:ubl:schema:xsd:QualifiedDataTypes-2",
    "udt": "urn:oasis:names:specification:ubl:schema:xsd:UnqualifiedDataTypes-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


xpath_CUI = './cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID'
xpath_CUI2 = './cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID'
xpath_ID = './cbc:ID'