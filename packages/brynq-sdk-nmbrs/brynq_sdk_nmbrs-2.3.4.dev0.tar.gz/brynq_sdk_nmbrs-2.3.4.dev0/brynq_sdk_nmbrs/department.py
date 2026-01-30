from typing import Any, Dict

import pandas as pd
import requests
from zeep.exceptions import Fault

from brynq_sdk_functions import Functions

from .schemas.department import (
    DepartmentCreate,
    DepartmentGet,
    DepartmentMasterCreate,
    DepartmentMasterDelete,
    DepartmentMasterUpdate,
    EmployeeDepartmentGet,
    EmployeeDepartmentUpdate,
    Period,
)


class EmployeeDepartment:
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def get(self,
            created_from: str = None,
            employee_id: str = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        departments = pd.DataFrame()
        for company in self.nmbrs.company_ids:
            departments = pd.concat([departments, self._get(company, created_from, employee_id)])

        valid_departments, invalid_departments = Functions.validate_data(df=departments, schema=EmployeeDepartmentGet, debug=True)

        return valid_departments, invalid_departments

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
                                   url=f"{self.nmbrs.base_url}companies/{company_id}/employees/departments",
                                   params=params)

        data = self.nmbrs.get_paginated_result(request)
        df = pd.json_normalize(
            data,
            record_path='departments',
            meta=['employeeId']
        )

        return df

    # def create(self, employee_id: str, data: Dict[str, Any]):
    #     """
    #     Create a new department for an employee using Pydantic validation.

    #     Args:
    #         employee_id: The ID of the employee
    #         data: Dictionary containing department data with fields matching
    #              the DepartmentCreate schema (using camelCase field names)

    #     Returns:
    #         Response from the API
    #     """
    #     # Validate with Pydantic model
    #     nested_data = self.nmbrs.flat_dict_to_nested_dict(data, DepartmentCreate)
    #     department_model = DepartmentCreate(**nested_data)

    #     if self.nmbrs.mock_mode:
    #         return department_model

    #     # Convert validated model to dict for API payload
    #     payload = department_model.model_dump(exclude_none=True, by_alias=True)

    #     # Send request
    #     resp = self.nmbrs.session.post(
    #         url=f"{self.nmbrs.base_url}employees/{employee_id}/department",
    #         json=payload,
    #         timeout=self.nmbrs.timeout
    #     )
    #     return resp

    def update(self, employee_id: str, data: Dict[str, Any]):
        """
        Update a department for an employee using Pydantic validation.

        Args:
            employee_id: The ID of the employee
            data: Dictionary containing department data with fields matching
                 the DepartmentUpdate schema (using camelCase field names)

        Returns:
            Response from the API
        """
        # Validate with Pydantic model
        nested_data = self.nmbrs.flat_dict_to_nested_dict(data, EmployeeDepartmentUpdate)
        department_model = EmployeeDepartmentUpdate(**nested_data)

        if self.nmbrs.mock_mode:
            return department_model

        # Convert validated model to dict for API payload
        payload = department_model.model_dump(exclude_none=True, by_alias=True, mode='json')

        # Send request
        resp = self.nmbrs.session.put(
            url=f"{self.nmbrs.base_url}employees/{employee_id}/department",
            json=payload,
            timeout=self.nmbrs.timeout
        )
        return resp



class Departments:
    """Master department operations (Debtor level) - uses SOAP for create/update/delete."""
    
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def get(self,
            debtor_id: str) -> pd.DataFrame:
        request = requests.Request(method='GET',
                                   url=f"{self.nmbrs.base_url}debtors/{debtor_id}/departments")

        data = self.nmbrs.get_paginated_result(request)

        df = pd.DataFrame(data)
        valid_departments, invalid_departments = Functions.validate_data(df=df, schema=DepartmentGet, debug=True)

        return valid_departments, invalid_departments

    def create(self, data: Dict[str, Any]) -> int:
        """
        Create a new master department for a debtor using SOAP API.

        Args:
            data: Dictionary containing department data with fields matching DepartmentMasterCreate schema:
                - debtor_id: Debtor ID
                - code: Department code
                - description: Department description

        Returns:
            The ID of the newly created department.
        """
        dept_model = DepartmentMasterCreate(**data)

        if self.nmbrs.mock_mode:
            return 12345  # Mock ID

        try:
            DepartmentType = self.nmbrs.soap_client_debtors.get_type('ns0:Department')
            soap_department = DepartmentType(
                Id=0,  # 0 for new department
                Code=dept_model.code,
                Description=dept_model.description
            )

            response = self.nmbrs.soap_client_debtors.service.Department_Insert(
                DebtorId=dept_model.debtor_id,
                department=soap_department,
                _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_debtors}
            )
            return response

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to create Department: {str(e)}")

    def update(self, data: Dict[str, Any]):
        """
        Update a master department for a debtor using SOAP API.

        Args:
            data: Dictionary containing department data with fields matching DepartmentMasterUpdate schema:
                - debtor_id: Debtor ID
                - department_id: Department ID to update
                - code: Department code
                - description: Department description

        Returns:
            Response from the API
        """
        dept_model = DepartmentMasterUpdate(**data)

        if self.nmbrs.mock_mode:
            return dept_model

        try:
            DepartmentType = self.nmbrs.soap_client_debtors.get_type('ns0:Department')
            soap_department = DepartmentType(
                Id=dept_model.department_id,
                Code=dept_model.code,
                Description=dept_model.description
            )

            response = self.nmbrs.soap_client_debtors.service.Department_Update(
                DebtorId=dept_model.debtor_id,
                department=soap_department,
                _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_debtors}
            )
            return response

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to update Department: {str(e)}")

    def delete(self, data: Dict[str, Any]):
        """
        Delete a master department for a debtor using SOAP API.

        Args:
            data: Dictionary containing department data with fields matching DepartmentMasterDelete schema:
                - debtor_id: Debtor ID
                - department_id: Department ID to delete

        Returns:
            Response from the API
        """
        dept_model = DepartmentMasterDelete(**data)

        if self.nmbrs.mock_mode:
            return True

        try:
            response = self.nmbrs.soap_client_debtors.service.Department_Delete(
                DebtorId=dept_model.debtor_id,
                id=dept_model.department_id,
                _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_debtors}
            )
            return response

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to delete Department: {str(e)}")
