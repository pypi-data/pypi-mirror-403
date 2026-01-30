from typing import Union, Dict, Any

import requests
import pandas as pd

from .schemas.children import ChildCreate, ChildDelete, ChildUpdate


class Children:
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def get(self,
            company_id: str,
            created_from: str = None) -> pd.DataFrame:
        params = {}
        if created_from:
            params['createdFrom'] = created_from
        try:
            request = requests.Request(method='GET',
                                       url=f"{self.nmbrs.base_url}companies/{company_id}/employees/functions",
                                       params=params)

            data = self.nmbrs.get_paginated_result(request)
            df = pd.json_normalize(
                data,
                record_path='functions',
                meta=['employeeId']
            )
        except requests.HTTPError as e:
            df = pd.DataFrame()

        return df

    def create(self, employee_id: Union[int, str], data: Dict[str, Any]):
        """
        Create a new child for an employee using SOAP API.

        Args:
            employee_id: The ID of the employee
            data: Dictionary containing child data with fields matching ChildCreate schema

        Returns:
            Response from the API (child ID)
        """
        # Validate with Pydantic model
        child_model = ChildCreate(**data)

        if self.nmbrs.mock_mode:
            return child_model

        ChildType = self.nmbrs.soap_client_employees.get_type('ns0:Child')
        child = ChildType(
            Id=0,  # Use 0 for new child
            Name=child_model.name,
            FirstName=child_model.first_name,
            Initials=child_model.initials or '',
            Gender=child_model.gender,
            Birthday=child_model.birthday
        )

        # Make the API call
        result = self.nmbrs.soap_client_employees.service.Children_Insert(
            EmployeeId=int(employee_id),
            child=child,
            _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_employees}
        )
        return result

    def delete(self, employee_id: Union[int, str], child_id: Union[int, str]):
        """
        Delete a child for an employee using SOAP API.

        Args:
            employee_id: The ID of the employee
            child_id: The ID of the child to delete

        Returns:
            Response from the API
        """
        # Validate with Pydantic model
        delete_model = ChildDelete(employeeId=int(employee_id), childId=int(child_id))

        if self.nmbrs.mock_mode:
            return delete_model

        # Call SOAP Child_Delete
        resp = self.nmbrs.soap_client_employees.service.Child_Delete(
            EmployeeId=delete_model.employee_id,
            ChildId=delete_model.child_id,
            _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_employees}
        )
        return resp

    def update(self, employee_id: Union[int, str], data: Dict[str, Any]):
        """
        Update a child for an employee using SOAP API.

        Args:
            employee_id: The ID of the employee
            data: Dictionary containing child data with fields matching ChildUpdate schema:
                - id: Child ID to update
                - name: Last name
                - first_name: First name
                - initials: Initials (optional)
                - gender: Gender (male/female/unknown/undefined)
                - birthday: Birthday

        Returns:
            Response from the API
        """
        # Validate with Pydantic model
        child_model = ChildUpdate(**data)

        if self.nmbrs.mock_mode:
            return child_model

        ChildType = self.nmbrs.soap_client_employees.get_type('ns0:Child')
        child = ChildType(
            Id=child_model.id,
            Name=child_model.name,
            FirstName=child_model.first_name,
            Initials=child_model.initials or '',
            Gender=child_model.gender,
            Birthday=child_model.birthday
        )

        # Make the API call
        result = self.nmbrs.soap_client_employees.service.Children_Update(
            EmployeeId=int(employee_id),
            child=child,
            _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_employees}
        )
        return result

