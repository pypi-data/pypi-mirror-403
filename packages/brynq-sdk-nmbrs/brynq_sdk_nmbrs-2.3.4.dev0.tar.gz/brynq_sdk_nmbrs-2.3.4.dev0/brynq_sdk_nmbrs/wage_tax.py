from typing import Any, Dict, List, Union, Tuple
import pandas as pd
import requests
from .schemas.wage_tax import (
    WageTaxGet, WageTaxUpdate, CompanyWageTaxGet,
    WageTaxSettingsGet, WageTaxSettingsCreate
)
from zeep.exceptions import Fault
from zeep.ns import WSDL, SOAP_ENV_11
from zeep.xsd import ComplexType, Element, String
from zeep.helpers import serialize_object
from brynq_sdk_functions import Functions


class WageTaxSettings:
    """Wage Tax Settings History - uses REST API."""

    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def get(self,
            created_from: str = None,
            employee_id: str = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get wage tax settings history for all employees across all companies.

        Args:
            created_from: Optional filter to get settings created from a specific date (ISO format)
            employee_id: Optional filter to get settings for a specific employee

        Returns:
            Tuple of (valid_settings, invalid_settings) DataFrames
        """
        wage_tax_settings = pd.DataFrame()
        for company in self.nmbrs.company_ids:
            wage_tax_settings = pd.concat([wage_tax_settings, self._get(company, created_from, employee_id)])

        valid_settings, invalid_settings = Functions.validate_data(
            df=wage_tax_settings,
            schema=WageTaxSettingsGet,
            debug=True
        )

        return valid_settings, invalid_settings

    def _get(self,
             company_id: str,
             created_from: str = None,
             employee_id: str = None) -> pd.DataFrame:
        """
        Get wage tax settings history for a specific company.

        Args:
            company_id: The ID of the company
            created_from: Optional filter to get settings created from a specific date
            employee_id: Optional filter to get settings for a specific employee

        Returns:
            DataFrame containing wage tax settings history
        """
        params = {}
        if created_from:
            params['createdFrom'] = created_from
        if employee_id:
            params['employeeId'] = employee_id

        request = requests.Request(
            method='GET',
            url=f"{self.nmbrs.base_url}companies/{company_id}/employees/wagetaxsettings",
            params=params
        )

        data = self.nmbrs.get_paginated_result(request)
        df = pd.json_normalize(
            data,
            record_path='wageTaxSettings',
            meta=['employeeId']
        )

        return df

    def create(self, employee_id: str, data: Dict[str, Any]):
        """
        Create a new wage tax setting for an employee using Pydantic validation.

        Args:
            employee_id: The ID of the employee
            data: Dictionary containing wage tax settings data with fields matching
                 the EmployeeWageTaxSettingsCreate schema (using camelCase field names)

        Returns:
            Response from the API
        """
        # Validate with Pydantic model
        nested_data = self.nmbrs.flat_dict_to_nested_dict(data, WageTaxSettingsCreate)
        wage_tax_model = WageTaxSettingsCreate(**nested_data)

        if self.nmbrs.mock_mode:
            return wage_tax_model

        # Convert validated model to dict for API payload
        payload = wage_tax_model.model_dump(exclude_none=True, by_alias=True)

        # Send request
        resp = self.nmbrs.session.post(
            url=f"{self.nmbrs.base_url}employees/{employee_id}/wagetaxsetting",
            json=payload,
            timeout=self.nmbrs.timeout
        )
        return resp


class WageTax:
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs
        self.soap_client_companies = nmbrs.soap_client_companies
        self.soap_client_employees = nmbrs.soap_client_employees

    def get_settings(self, year: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get salary tables for all companies for a specific period and year.

        Args:
            period (int): The period number
            year (int): The year

        Returns:
            pd.DataFrame: DataFrame containing the salary tables
        """
        wagetax_settings = pd.DataFrame()
        for company in self.nmbrs.soap_company_ids.to_dict(orient='records'):
            wagetax_settings_temp = self._get(company['i_d'], year)
            if not wagetax_settings_temp.empty:
                wagetax_settings_temp['companyId'] = company['number']
                wagetax_settings = pd.concat([wagetax_settings, wagetax_settings_temp])

        valid_wagetax_settings, invalid_wagetax_settings = Functions.validate_data(df=wagetax_settings, schema=CompanyWageTaxGet, debug=True)

        # No validation schema for now, but could be added later
        return valid_wagetax_settings, invalid_wagetax_settings

    def _get(self, company_id: int, year: int) -> pd.DataFrame:
        """
        Get salary tables for a specific company, period and year.

        Args:
            company_id (int): The ID of the company
            period (int): The period number
            year (int): The year

        Returns:
            pd.DataFrame: DataFrame containing the salary tables
        """
        try:
            # Make SOAP request with the proper header structure
            response = self.soap_client_companies.service.WageTax_GetList(
                CompanyId=company_id,
                intYear=year,
                _soapheaders=[self.nmbrs.soap_auth_header]
            )

            # Convert response to DataFrame
            if response:
                # Convert Zeep objects to Python dictionaries
                serialized_response = serialize_object(response)

                # Convert to list if it's not already
                if not isinstance(serialized_response, list):
                    serialized_response = [serialized_response]

                # Convert to DataFrame
                df = pd.DataFrame(serialized_response)

                return df
            else:
                return pd.DataFrame()

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to get salary tables: {str(e)}")

    def get(self, employee_id: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get wage tax settings for a specific employee.

        Args:
            employee_id (int): The ID of the employee

        Returns:
            pd.DataFrame: DataFrame containing the wage tax settings
        """
        try:
            # Get the auth header using the centralized method
            auth_header = self.nmbrs._get_soap_auth_header_employees()

            # Make SOAP request with the proper header structure
            response = self.soap_client_employees.service.WageTax_GetList(
                EmployeeId=employee_id,
                _soapheaders=[auth_header]
            )

            # Convert response to DataFrame
            if response:
                # Convert Zeep objects to Python dictionaries
                serialized_response = serialize_object(response)

                # Convert to list if it's not already
                if not isinstance(serialized_response, list):
                    serialized_response = [serialized_response]

                # Convert to DataFrame
                df = pd.DataFrame(serialized_response)
                df['EmployeeId'] = employee_id
                valid_wage_tax, invalid_wage_tax = Functions.validate_data(df=df, schema=WageTaxGet, debug=True)

                return valid_wage_tax, invalid_wage_tax
            else:
                return pd.DataFrame(), pd.DataFrame()

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to get wage tax settings: {str(e)}")

    def update(self, data: Dict[str, Any]) -> pd.DataFrame:
        try:
            wage_tax_model = WageTaxUpdate(**data)

            if self.nmbrs.mock_mode:
                return wage_tax_model

            # Get the auth header using the centralized method
            auth_header = self.nmbrs._get_soap_auth_header_employees()

            # Use the model's built-in SOAP conversion method
            wage_tax_settings = wage_tax_model.to_soap_settings(self.nmbrs.soap_client_employees)

            # Make SOAP request with clean, simple call
            response = self.nmbrs.soap_client_employees.service.WageTax_UpdateCurrent(
                EmployeeId=wage_tax_model.employee_id,
                LoonheffingSettings=wage_tax_settings,
                _soapheaders=[self.nmbrs.soap_auth_header]
            )

            # Convert response to DataFrame
            if response:
                # Convert Zeep objects to Python dictionaries
                serialized_response = serialize_object(response)

                # Convert to list if it's not already
                if not isinstance(serialized_response, list):
                    serialized_response = [serialized_response]

                # Convert to DataFrame
                df = pd.DataFrame(serialized_response)

                return df
            else:
                return pd.DataFrame()

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to update WageTax: {str(e)}")
