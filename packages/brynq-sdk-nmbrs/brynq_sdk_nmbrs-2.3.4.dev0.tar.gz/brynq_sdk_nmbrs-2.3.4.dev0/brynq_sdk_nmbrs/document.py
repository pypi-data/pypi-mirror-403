from io import BytesIO
import base64
from typing import Dict, Any, Union

import pandas as pd
import requests
from zeep.exceptions import Fault

from .schemas.document import DocumentUpload


class EmployeeDocument:
    """Handle employee document operations via SOAP API."""
    
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def upload(self, data: Dict[str, Any], file_content: bytes) -> bool:
        """
        Upload a document to an employee using SOAP API.

        Args:
            data: Dictionary containing document data with fields matching DocumentUpload schema:
                - employee_id: Employee ID
                - document_name: Document name (with extension, e.g., "contract.pdf")
                - document_type_guid: Document type GUID
            file_content: Binary content of the file to upload

        Returns:
            True if upload was successful
        """
        doc_model = DocumentUpload(**data)

        if self.nmbrs.mock_mode:
            return True

        try:
            # Convert file content to base64
            body_base64 = base64.b64encode(file_content)

            response = self.nmbrs.soap_client_employees.service.EmployeeDocument_UploadDocument(
                EmployeeId=doc_model.employee_id,
                StrDocumentName=doc_model.document_name,
                Body=body_base64,
                GuidDocumentType=doc_model.document_type_guid,
                _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_employees}
            )

            return response

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to upload document: {str(e)}")


class Payslip:
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def get(self,
            employee_id: str,
            period: int = None,
            year: int = None) -> pd.DataFrame:
        params = {}
        if period:
            params['period'] = period
        if year:
            params['year'] = year
        resp = self.nmbrs.session.get(f"{self.nmbrs.base_url}employees/{employee_id}/payslipperperiod/",
                                      params=params,
                                      timeout=self.nmbrs.timeout)
        resp.raise_for_status()
        task_id = resp.json()['taskId']

        resp = self.nmbrs.session.get(f"{self.nmbrs.base_url}documents/{task_id}", timeout=self.nmbrs.timeout)

        return BytesIO(resp.content)


