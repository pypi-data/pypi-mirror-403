import pandas as pd
import requests
from brynq_sdk_functions import Functions as BrynQFunctions
import math
from typing import Dict, Any, Union
from .schemas.function import (
    EmployeeFunctionGet, FunctionUpdate, FunctionGet,
    FunctionCreate, FunctionDelete, FunctionMasterUpdate
)
from zeep.exceptions import Fault
from zeep.helpers import serialize_object


class EmployeeFunction:
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def get(self,
            created_from: str = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        functions = pd.DataFrame()
        for company in self.nmbrs.company_ids:
            functions = pd.concat([functions, self._get(company, created_from)])

        valid_functions, invalid_functions = BrynQFunctions.validate_data(df=functions, schema=EmployeeFunctionGet, debug=True)

        return valid_functions, invalid_functions

    def _get(self,
            company_id: str,
            created_from: str = None) -> pd.DataFrame:
        params = {}
        if created_from:
            params['createdFrom'] = created_from
        try:
            request = requests.Request(method='GET', url=f"{self.nmbrs.base_url}companies/{company_id}/employees/functions", params=params)
            data = self.nmbrs.get_paginated_result(request)
            df = pd.json_normalize(
                data,
                record_path='functions',
                meta=['employeeId']
            )
        except requests.HTTPError as e:
            df = pd.DataFrame()
        return df

    def update(self, employee_id: str, data: Dict[str, Any]):
        """
        Update a function for an employee using Pydantic validation.

        Args:
            employee_id: The ID of the employee
            data: Dictionary containing function data with fields matching
                 the FunctionUpdate schema (using camelCase field names)

        Returns:
            Response from the API
        """
        # Validate with Pydantic model
        nested_data = self.nmbrs.flat_dict_to_nested_dict(data, FunctionUpdate)
        function_model = FunctionUpdate(**nested_data)

        if self.nmbrs.mock_mode:
            return function_model

        # Convert validated model to dict for API payload
        payload = function_model.model_dump(exclude_none=True, by_alias=True)

        # Send request
        resp = self.nmbrs.session.put(
            url=f"{self.nmbrs.base_url}employees/{employee_id}/function",
            json=payload,
            timeout=self.nmbrs.timeout
        )
        return resp

    def get_current(self, employee_id: Union[int, str]) -> pd.DataFrame:
        """
        Get current function for a specific employee using SOAP API.

        Args:
            employee_id: The ID of the employee

        Returns:
            DataFrame with current function
        """
        if self.nmbrs.mock_mode:
            return pd.DataFrame()

        try:
            response = self.nmbrs.soap_client_employees.service.Function_GetCurrent(
                EmployeeId=int(employee_id),
                _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_employees}
            )

            if response:
                serialized = serialize_object(response)
                if not isinstance(serialized, list):
                    serialized = [serialized]
                df = pd.DataFrame(serialized)
                df['employee_id'] = str(employee_id)
                return df
            else:
                return pd.DataFrame()

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")


class Functions:
    """
    Master Functions (Debtor level) - manages function definitions.
    Uses DebtorService SOAP API for create, update, delete.
    """
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def get(self, debtor_id: str) -> (pd.DataFrame, pd.DataFrame):
        try:
            request = requests.Request(method='GET',
                                       url=f"{self.nmbrs.base_url}debtors/{debtor_id}/functions")

            data = self.nmbrs.get_paginated_result(request)
            df = pd.DataFrame(data)
            valid_functions, invalid_functions = BrynQFunctions.validate_data(df=df, schema=FunctionGet, debug=True)

        except requests.HTTPError as e:
            df = pd.DataFrame()

        return valid_functions, invalid_functions

    def create(self, debtor_id: Union[int, str], data: Dict[str, Any]):
        """
        Create a new master function using SOAP API.

        Args:
            debtor_id: The ID of the debtor
            data: Dictionary containing function data with fields matching FunctionCreate schema

        Returns:
            Response from the API (function ID)
        """
        function_model = FunctionCreate(**data)

        if self.nmbrs.mock_mode:
            return function_model

        try:
            response = self.nmbrs.soap_client_debtors.service.Function_Insert(
                DebtorId=int(debtor_id),
                function={
                    'Id': 0,  # 0 for new function
                    'Code': function_model.code,
                    'Description': function_model.description
                },
                _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_debtors}
            )
            return response
        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")

    def delete(self, debtor_id: Union[int, str], function_id: Union[int, str]):
        """
        Delete a master function using SOAP API.

        Args:
            debtor_id: The ID of the debtor
            function_id: The ID of the function to delete

        Returns:
            Response from the API
        """
        delete_model = FunctionDelete(function_id=int(function_id))

        if self.nmbrs.mock_mode:
            return delete_model

        try:
            response = self.nmbrs.soap_client_debtors.service.Function_Delete(
                DebtorId=int(debtor_id),
                id=delete_model.function_id,
                _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_debtors}
            )
            return response
        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")

    def update(self, debtor_id: Union[int, str], data: Dict[str, Any]):
        """
        Update a master function using SOAP API.

        Args:
            debtor_id: The ID of the debtor
            data: Dictionary containing function data with fields matching FunctionMasterUpdate schema

        Returns:
            Response from the API
        """
        function_model = FunctionMasterUpdate(**data)

        if self.nmbrs.mock_mode:
            return function_model

        try:
            response = self.nmbrs.soap_client_debtors.service.Function_Update(
                DebtorId=int(debtor_id),
                function={
                    'Id': function_model.function_id,
                    'Code': function_model.code,
                    'Description': function_model.description
                },
                _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_debtors}
            )
            return response
        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
