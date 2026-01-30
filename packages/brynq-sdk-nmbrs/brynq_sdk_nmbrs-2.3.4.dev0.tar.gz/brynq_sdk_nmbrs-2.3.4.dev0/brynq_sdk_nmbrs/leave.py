import math
import pandas as pd
import requests
from brynq_sdk_functions import Functions
from typing import Dict, Any, Union
from .schemas.leave import LeaveBalanceGet, LeaveGet, LeaveCreate, LeaveDelete, LeaveUpdate
from zeep.exceptions import Fault


class Leave:
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def get(self,
            changed_from: str = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        leave = pd.DataFrame()
        for company in self.nmbrs.company_ids:
            leave = pd.concat([leave, self._get(company, changed_from)])

        valid_leave, invalid_leave = Functions.validate_data(df=leave, schema=LeaveGet, debug=True)

        return valid_leave, invalid_leave

    def _get(self,
            company_id: str,
            changed_from: str = None) -> pd.DataFrame:
        params = {}
        if changed_from:
            params['changed_from'] = changed_from
        try:
            request = requests.Request(method='GET',
                                       url=f"{self.nmbrs.base_url}companies/{company_id}/employees/leaverequests",
                                       params=params)

            data = self.nmbrs.get_paginated_result(request)
            df = pd.json_normalize(
                data,
                record_path='EmployeeLeaveRequests',
                meta=['employeeId']
            )
        except requests.HTTPError as e:
            df = pd.DataFrame()

        return df

    def create(self, employee_id: str, data: Dict[str, Any]):
        """
        Create a new leave request for an employee using Pydantic validation.

        Args:
            employee_id: The ID of the employee
            data: Dictionary containing leave request data in the format matching LeaveCreate schema

        Returns:
            Response from the API
        """
        # Validate with Pydantic model - this will raise an error if required fields are missing
        nested_data = self.nmbrs.flat_dict_to_nested_dict(data, LeaveCreate)
        leave_model = LeaveCreate(**nested_data)

        if self.nmbrs.mock_mode:
            return leave_model

        # Convert validated model to dict for API payload
        payload = leave_model.model_dump(exclude_none=True, by_alias=True)

        # Send request
        resp = self.nmbrs.session.post(
            url=f"{self.nmbrs.base_url}employees/{employee_id}/leaverequest",
            json=payload,
            timeout=self.nmbrs.timeout
        )
        return resp

    def delete(self, employee_id: str, leave_request_id: str):
        """
        Delete a leave request for an employee.

        Args:
            employee_id: The ID of the employee
            leave_request_id: The ID of the leave request to delete

        Returns:
            Response from the API
        """
        # Create and validate a BankDelete model
        leave_model = LeaveDelete(leave_request_id=leave_request_id)

        if self.nmbrs.mock_mode:
            return leave_model

        # Send request
        resp = self.nmbrs.session.delete(
            url=f"{self.nmbrs.base_url}employees/{employee_id}/leave/{leave_request_id}",
            timeout=self.nmbrs.timeout
        )
        return resp

    def update(self, data: Dict[str, Any]):
        """
        Update a leave request for an employee using SOAP API.
        (REST API does not support leave update)

        Args:
            data: Dictionary containing leave data with fields matching LeaveUpdate schema:
                - employee_id: Employee ID
                - leave_id: Leave ID
                - start_date: Start date
                - end_date: End date
                - description: Optional description

        Returns:
            Response from the API
        """
        leave_model = LeaveUpdate(**data)

        if self.nmbrs.mock_mode:
            return leave_model

        try:
            resp = self.nmbrs.soap_client_employees.service.Leave_Update(
                EmployeeId=leave_model.employee_id,
                Leave={
                    'Id': leave_model.leave_id,
                    'Start': leave_model.start_date,
                    'End': leave_model.end_date,
                    'Description': leave_model.description or ''
                },
                _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_employees}
            )
            return resp
        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")


class LeaveBalance:
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def get(self,
            changed_from: str = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        leave = pd.DataFrame()
        for company in self.nmbrs.company_ids:
            leave = pd.concat([leave, self._get(company, changed_from)])

        valid_leave, invalid_leave = Functions.validate_data(df=leave, schema=LeaveBalanceGet, debug=True)

        return valid_leave, invalid_leave

    def _get(self,
            company_id: str,
            changed_from: str = None) -> pd.DataFrame:
        """
        Note: changed_from parameter is accepted for consistency but not used
        by the leaveBalances endpoint.
        """
        try:
            request = requests.Request(method='GET',
                                       url=f"{self.nmbrs.base_url}companies/{company_id}/employees/leaveBalances")

            data = self.nmbrs.get_paginated_result(request)
            df = pd.json_normalize(
                data,
                record_path='leaveBalances',
                meta=['employeeId']
            )
        except requests.HTTPError as e:
            df = pd.DataFrame()

        return df


class LeaveGroup:
    """
    LeaveGroup (Leave Type Groups) - uses SOAP CompanyLeaveTypeGroups_Get
    """
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def get(self, company_id: Union[int, str] = None) -> pd.DataFrame:
        """
        Get leave type groups using SOAP API.
        
        Args:
            company_id: Optional. If provided, get groups for this company only.
                       If not provided, get groups for all companies.
        
        Returns:
            DataFrame with leave type groups
        """
        if self.nmbrs.mock_mode:
            return pd.DataFrame()

        from zeep.helpers import serialize_object
        
        all_groups = []
        try:
            # If company_id provided, only get for that company
            if company_id is not None:
                company_ids = [int(company_id)]
            else:
                # Get all company IDs from SOAP
                companies_response = self.nmbrs.soap_client_companies.service.List_GetAll(
                    _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header}
                )
                
                # Handle response - could be list or object with Company attribute
                companies = []
                if companies_response:
                    if hasattr(companies_response, 'Company'):
                        companies = companies_response.Company or []
                    elif isinstance(companies_response, list):
                        companies = companies_response
                
                company_ids = [c.ID for c in companies]
            
            for cid in company_ids:
                try:
                    response = self.nmbrs.soap_client_companies.service.CompanyLeaveTypeGroups_Get(
                        CompanyId=cid,
                        _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header}
                    )
                    if response and response.LeaveTypeGroup:
                        groups = serialize_object(response.LeaveTypeGroup)
                        if not isinstance(groups, list):
                            groups = [groups]
                        for group in groups:
                            group['company_id'] = str(cid)
                        all_groups.extend(groups)
                except Exception:
                    continue
            
            return pd.DataFrame(all_groups)
        
        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
