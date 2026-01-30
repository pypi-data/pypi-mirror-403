import pandas as pd
import requests
from typing import Dict, Any
from zeep.exceptions import Fault
from brynq_sdk_functions import Functions
from .department import Departments
from .function import Functions as NmbrsFunctions
from .schemas.debtor import DebtorsGet, DebtorCreate, DebtorUpdate


class Debtors:
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs
        self.departments = Departments(nmbrs)
        self.functions = NmbrsFunctions(nmbrs)

    def get(self) -> (pd.DataFrame, pd.DataFrame):
        request = requests.Request(method='GET',
                                   url=f"{self.nmbrs.base_url}debtors")
        data = self.nmbrs.get_paginated_result(request)

        df = pd.DataFrame(data)

        valid_debtors, invalid_debtors = Functions.validate_data(df=df, schema=DebtorsGet, debug=True)

        return valid_debtors, invalid_debtors

    def create(self, data: Dict[str, Any]) -> int:
        """
        Create a new debtor using SOAP API.

        Args:
            data: Dictionary containing debtor data with fields matching DebtorCreate schema:
                - number: Debtor number
                - name: Debtor name

        Returns:
            The ID of the newly created debtor.
        """
        debtor_model = DebtorCreate(**data)

        if self.nmbrs.mock_mode:
            return 12345  # Mock ID

        try:
            DebtorType = self.nmbrs.soap_client_debtors.get_type('ns0:Debtor')
            soap_debtor = DebtorType(
                Id=0,  # 0 for new debtor
                Number=debtor_model.number,
                Name=debtor_model.name
            )

            response = self.nmbrs.soap_client_debtors.service.Debtor_Insert(
                Debtor=soap_debtor,
                _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_debtors}
            )
            return response

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to create Debtor: {str(e)}")

    def update(self, data: Dict[str, Any]):
        """
        Update a debtor using SOAP API.

        Args:
            data: Dictionary containing debtor data with fields matching DebtorUpdate schema:
                - debtor_id: Debtor ID to update
                - number: Debtor number
                - name: Debtor name

        Returns:
            Response from the API
        """
        debtor_model = DebtorUpdate(**data)

        if self.nmbrs.mock_mode:
            return debtor_model

        try:
            DebtorType = self.nmbrs.soap_client_debtors.get_type('ns0:Debtor')
            soap_debtor = DebtorType(
                Id=debtor_model.debtor_id,
                Number=debtor_model.number,
                Name=debtor_model.name
            )

            response = self.nmbrs.soap_client_debtors.service.Debtor_Update(
                Debtor=soap_debtor,
                _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_debtors}
            )
            return response

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to update Debtor: {str(e)}")
