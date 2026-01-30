from typing import TYPE_CHECKING, Any, Dict

import pandas as pd
import requests

from brynq_sdk_functions import Functions

from .schemas.costcenter import (
    CostcenterCreate,
    CostcenterGet,
    CostCentersResponse,
    CostcenterUpdate,
    EmployeeCostcenterGet,
    EmployeeCostCentersResponse,
    EmployeeCostcenterUpdate,
)

if TYPE_CHECKING:
    from brynq_sdk_nmbrs import Nmbrs


class EmployeeCostcenter:
    def __init__(self, nmbrs):
        self.nmbrs: Nmbrs = nmbrs

    def get(self,
            created_from: str = None,
            employee_id: str = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        costcenters = pd.DataFrame()
        for company in self.nmbrs.company_ids:
            costcenters = pd.concat([costcenters, self._get(company, created_from, employee_id)])

        valid_costcenters, invalid_costcenters = Functions.validate_data(df=costcenters, schema=EmployeeCostcenterGet, debug=True)

        return valid_costcenters, invalid_costcenters

    def _get(self,
            company_id: str,
            created_from: str = None,
            employee_id: str = None) -> pd.DataFrame:
        params = {}
        if created_from:
            params['createdFrom'] = created_from
        if employee_id:
            params['employeeId'] = employee_id
        request = requests.Request(method='GET',
                                   url=f"{self.nmbrs.base_url}companies/{company_id}/employees/costcenters",
                                   params=params)
        data = self.nmbrs.get_paginated_result(request)

        # Parse and validate API response using Pydantic models
        if not data:
            return pd.DataFrame()

        # Validate response structure with Pydantic
        response = EmployeeCostCentersResponse(data=data)

        # Serialize models to dicts using model_dump with by_alias=True
        serialized_data = [item.model_dump(by_alias=True, mode='json') for item in response.data]

        # Use json_normalize to flatten nested structure efficiently
        df = pd.json_normalize(
            serialized_data,
            record_path='employeeCostCenters',
            meta=['employeeId']
        )

        # Flatten nested costUnits object if it exists
        if 'costUnits' in df.columns:
            # Check if costUnits contains dict-like objects
            cost_units_dicts = df['costUnits'].dropna()
            if not cost_units_dicts.empty and isinstance(cost_units_dicts.iloc[0], dict):
                cost_units_expanded = pd.json_normalize(cost_units_dicts)
                cost_units_expanded.columns = [f'costUnits.{col}' for col in cost_units_expanded.columns]
                # Reindex to match original DataFrame index and fill missing values with None
                cost_units_expanded = cost_units_expanded.reindex(df.index)
                df = pd.concat([df.drop(columns=['costUnits']), cost_units_expanded], axis=1)
            else:
                # If costUnits is not dict-like or all None, create columns with None
                for col in ['costUnits.costUnitId', 'costUnits.code', 'costUnits.description']:
                    df[col] = None
                df = df.drop(columns=['costUnits'])

        return df

    def update(self, employee_id: str, data: Dict[str, Any]):
        """
        Update a costcenter for an employee using Pydantic validation.

        Args:
            employee_id: The ID of the employee
            data: Dictionary containing costcenter data with fields matching
                 the EmployeeCostcenterUpdate schema (using camelCase field names)

        Returns:
            Response from the API
        """
        # this is the Nmbrs GUID that is returned after creating an employee, for some reason also included in body here.
        data['employee_id'] = employee_id
        data['default'] = True
        # Validate with Pydantic model - this will raise an error if required fields are missing
        nested_data = self.nmbrs.flat_dict_to_nested_dict(data, EmployeeCostcenterUpdate)
        costcenter_model = EmployeeCostcenterUpdate(**nested_data)

        if self.nmbrs.mock_mode:
            return costcenter_model

        # Convert validated model to dict for API payload
        payload = costcenter_model.model_dump(exclude_none=True, by_alias=True)

        # Send request
        resp = self.nmbrs.session.put(
            url=f"{self.nmbrs.base_url}employees/{employee_id}/employeecostcenter",
            json=payload,
            timeout=self.nmbrs.timeout
        )
        return resp



class Costcenter:
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def get(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        costcenters = pd.DataFrame()
        for company in self.nmbrs.company_ids:
            costcenters = pd.concat([costcenters, self._get(company)])

        valid_costcenters, invalid_costcenters = Functions.validate_data(df=costcenters, schema=CostcenterGet, debug=True)

        return valid_costcenters, invalid_costcenters

    def _get(self,
            company_id: str):
        request = requests.Request(method='GET',
                                   url=f"{self.nmbrs.base_url}companies/{company_id}/costcenters")
        data = self.nmbrs.get_paginated_result(request)

        # Parse and validate API response using Pydantic models
        if not data:
            return pd.DataFrame()

        # Validate response structure with Pydantic
        response = CostCentersResponse(data=data)

        # Serialize models to dicts and convert to DataFrame efficiently
        serialized_data = [item.model_dump(by_alias=True, mode='json') for item in response.data]
        df = pd.DataFrame(serialized_data)

        return df

    def create(self, company_id: str, data: Dict[str, Any]):
        """
        Create a new costcenter using Pydantic validation.

        Args:
            company_id: The ID of the company
            data: Dictionary containing costcenter data with fields matching
                 the CostcenterCreate schema (using camelCase field names)

        Returns:
            Response from the API
        """
        # Validate with Pydantic model - this will raise an error if required fields are missing
        nested_data = self.nmbrs.flat_dict_to_nested_dict(data, CostcenterCreate)
        costcenter_model = CostcenterCreate(**nested_data)

        if self.nmbrs.mock_mode:
            return costcenter_model

        # Convert validated model to dict for API payload
        payload = costcenter_model.model_dump(exclude_none=True, by_alias=True)

        # Send request
        resp = self.nmbrs.session.post(
            url=f"{self.nmbrs.base_url}companies/{company_id}/costcenter",
            json=payload,
            timeout=self.nmbrs.timeout
        )
        return resp

    def update(self, company_id: str, data: Dict[str, Any]):
        """
        Update a costcenter using Pydantic validation.

        Args:
            company_id: The ID of the company
            data: Dictionary containing costcenter data with fields matching
                 the CostcenterUpdate schema (using camelCase field names)

        Returns:
            Response from the API
        """
        # Validate with Pydantic model - this will raise an error if required fields are missing
        nested_data = self.nmbrs.flat_dict_to_nested_dict(data, CostcenterUpdate)
        costcenter_model = CostcenterUpdate(**nested_data)

        if self.nmbrs.mock_mode:
            return costcenter_model

        # Convert validated model to dict for API payload
        payload = costcenter_model.model_dump(exclude_none=True, by_alias=True)

        # Send request
        resp = self.nmbrs.session.put(
            url=f"{self.nmbrs.base_url}companies/{company_id}/costcenter",
            json=payload,
            timeout=self.nmbrs.timeout
        )
        return resp
