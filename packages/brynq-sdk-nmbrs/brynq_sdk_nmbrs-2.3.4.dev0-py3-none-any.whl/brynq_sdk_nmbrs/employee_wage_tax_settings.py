from typing import Any, Dict

import pandas as pd
import requests

from brynq_sdk_functions import Functions

from .schemas.wage_tax_settings import (
    EmployeeWageTaxSettingsCreate,
    EmployeeWageTaxSettingsGet,
)


class EmployeeWageTaxSettings:
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def get(self,
            employee_id: str = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get wage tax settings history for employees in companies.

        Args:
            employee_id: Optional filter for a specific employee ID

        Returns:
            Tuple of (valid_data, invalid_data) DataFrames
        """
        wage_tax_settings = pd.DataFrame()
        for company in self.nmbrs.company_ids:
            wage_tax_settings = pd.concat([wage_tax_settings, self._get(company, employee_id)])

        valid_settings, invalid_settings = Functions.validate_data(
            df=wage_tax_settings, schema=EmployeeWageTaxSettingsGet, debug=True
        )

        return valid_settings, invalid_settings

    def _get(self,
             company_id: str,
             employee_id: str = None) -> pd.DataFrame:
        """
        Get wage tax settings history for a specific company.

        Args:
            company_id: The ID of the company
            employee_id: Optional filter for a specific employee ID

        Returns:
            DataFrame with wage tax settings
        """
        params = {}
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

        # Flatten nested Calc30PercentRuling object if it exists
        if 'Calc30PercentRuling' in df.columns:
            calc_ruling_dicts = df['Calc30PercentRuling'].dropna()
            if not calc_ruling_dicts.empty and isinstance(calc_ruling_dicts.iloc[0], dict):
                calc_ruling_expanded = pd.json_normalize(calc_ruling_dicts)
                calc_ruling_expanded.columns = [f'Calc30PercentRuling.{col}' for col in calc_ruling_expanded.columns]
                calc_ruling_expanded = calc_ruling_expanded.reindex(df.index)
                df = pd.concat([df.drop(columns=['Calc30PercentRuling']), calc_ruling_expanded], axis=1)
            else:
                # If Calc30PercentRuling is not dict-like or all None, create columns with None
                for col in ['Calc30PercentRuling.Cal30PercentRuling', 'Calc30PercentRuling.endPeriod', 'Calc30PercentRuling.endYear']:
                    df[col] = None
                df = df.drop(columns=['Calc30PercentRuling'])

        return df

    def create(self, employee_id: str, data: Dict[str, Any]):
        """
        Create wage tax settings for an employee using Pydantic validation.

        Args:
            employee_id: The ID of the employee
            data: Dictionary containing wage tax settings data with fields matching
                 the EmployeeWageTaxSettingsCreate schema (using camelCase field names)

        Returns:
            Response from the API
        """
        # Validate with Pydantic model
        nested_data = self.nmbrs.flat_dict_to_nested_dict(data, EmployeeWageTaxSettingsCreate)
        settings_model = EmployeeWageTaxSettingsCreate(**nested_data)

        if self.nmbrs.mock_mode:
            return settings_model

        # Convert validated model to dict for API payload
        payload = settings_model.model_dump(exclude_none=True, by_alias=True, mode='json')

        # Send request
        resp = self.nmbrs.session.post(
            url=f"{self.nmbrs.base_url}employees/{employee_id}/wagetaxsettings",
            json=payload,
            timeout=self.nmbrs.timeout
        )
        return resp
