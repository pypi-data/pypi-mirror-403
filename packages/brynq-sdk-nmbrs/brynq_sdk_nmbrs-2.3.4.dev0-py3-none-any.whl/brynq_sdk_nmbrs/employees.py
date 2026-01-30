import logging
from typing import Any, Dict, Optional

import pandas as pd
import requests
from pydantic import BaseModel
from zeep.exceptions import Fault
from zeep.helpers import serialize_object

from brynq_sdk_functions import Functions

from .address import Address
from .bank import Bank
from .contract import Contract
from .costcenter import EmployeeCostcenter
from .days import VariableDays
from .department import EmployeeDepartment
from .document import Payslip
from .employment import Employment
from .function import EmployeeFunction
from .hours import FixedHours, VariableHours
from .leave import Leave, LeaveBalance
from .salaries import Salaries
from .schedules import Schedule
from .schemas.employees import (
    AdditionalEmployeeInfo,
    BasicInfo,
    BirthInfo,
    BsnGet,
    ContactInfo,
    CreateEmployeePersonalInfo,
    DefaultEmployeeTemplates,
    EmployeeCreate,
    EmployeeDelete,
    EmployeeGet,
    EmployeeUpdate,
    PartnerInfo,
    Period,
)
from .wage_tax import WageTax
from .wagecomponents import EmployeeFixedWageComponents, EmployeeVariableWageComponents


class Employees:
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs
        self.logger = logging.getLogger(__name__)
        self.address = Address(nmbrs)
        self.functions = EmployeeFunction(nmbrs)
        self.contract = Contract(nmbrs)
        self.departments = EmployeeDepartment(nmbrs)
        self.costcenter = EmployeeCostcenter(nmbrs)
        self.schedule = Schedule(nmbrs)
        self.employment = Employment(nmbrs)
        self.variable_hours = VariableHours(nmbrs)
        self.fixed_hours = FixedHours(nmbrs)
        self.variable_days = VariableDays(nmbrs)
        self.salaries = Salaries(nmbrs)
        self.variable_wagecomponents = EmployeeVariableWageComponents(nmbrs)
        self.fixed_wagecomponents = EmployeeFixedWageComponents(nmbrs)
        self.banks = Bank(nmbrs)
        self.payslips = Payslip(nmbrs)
        self.wage_tax = WageTax(nmbrs)
        self.leave = Leave(nmbrs)
        self.leave_balance = LeaveBalance(nmbrs)

    def get(self,
            employee_type: str = None
            ) -> (pd.DataFrame, pd.DataFrame):
        employees = pd.DataFrame()
        for company in self.nmbrs.company_ids:
            company_employees = self._get(company, employee_type)
            if not company_employees.empty:
                employees = pd.concat([employees, company_employees])

        valid_employees, invalid_employees = Functions.validate_data(df=employees, schema=EmployeeGet, debug=True)

        return valid_employees, invalid_employees

    def _get(self,
            company_id: str,
            employee_type: str = None) -> pd.DataFrame:
        params = {} if employee_type is None else {'employeeType': employee_type}
        request = requests.Request(method='GET',
                                   url=f"{self.nmbrs.base_url}companies/{company_id}/employees/personalinfo",
                                   params=params)

        data = self.nmbrs.get_paginated_result(request)
        if not data:
            return pd.DataFrame()

        df = pd.json_normalize(
            data,
            record_path='info',
            meta=['employeeId']
        )
        if df.empty:
            return df

        df['companyId'] = company_id
        if 'createdAt' in df.columns and 'employeeId' in df.columns:
            df['createdAt'] = pd.to_datetime(df['createdAt'])
            df = df.loc[df.groupby('employeeId')['createdAt'].idxmax()]

        return df.reset_index(drop=True)

    def get_private_info(self) -> str:
        combined = []
        for company_id in self.nmbrs.company_ids:
            request = requests.Request(method='GET',
                                    url=f"{self.nmbrs.base_url}companies/{company_id}/employees/privateInfos")
            data = self.nmbrs.get_paginated_result(request)
            df = pd.json_normalize(
                data,
                record_path='privateInfos',
                meta=['employeeId']
            )
            df['companyId'] = company_id
            combined.append(df)
        df = pd.concat(combined, ignore_index=True)
        valid_bsn, invalid_bsn = Functions.validate_data(df, BsnGet)

        return valid_bsn, invalid_bsn

    def get_default_templates(self) -> pd.DataFrame:
        default_templates = pd.DataFrame()
        for company in self.nmbrs.company_ids:
            default_templates_temp = self._get_default_templates(company)
            default_templates_temp['companyId'] = company
            default_templates = pd.concat([default_templates, default_templates_temp])

        valid_default_templates, invalid_default_templates = Functions.validate_data(df=default_templates, schema=DefaultEmployeeTemplates, debug=True)

        return valid_default_templates, invalid_default_templates


    def _get_default_templates(self, company_id: str, employee_type: str = None) -> pd.DataFrame:
        params = {} if employee_type is None else {'employeeType': employee_type}
        request = requests.Request(method='GET',
                                   url=f"{self.nmbrs.base_url}companies/{company_id}/defaulttemplates",
                                   params=params)
        data = self.nmbrs.get_paginated_result(request)
        return pd.DataFrame(data)

    def create(self, company_id: str, data: Dict[str, Any]):
        """
        Create a new employee using Pydantic validation.

        Args:
            company_id: The ID of the company
            data: Dictionary structured according to the EmployeeCreate schema with:
                 - PersonalInfo: containing basicInfo, birthInfo, contactInfo, etc.
                 - AdditionalEmployeeInfo: containing service date, etc.

        Returns:
            Response from the API
        """
        # Validate with Pydantic model
        nested_data = self.nmbrs.flat_dict_to_nested_dict(data, EmployeeCreate)
        employee_model = EmployeeCreate(**nested_data)

        if self.nmbrs.mock_mode:
            return employee_model

        # Convert validated model to dict for API payload
        payload = employee_model.model_dump(exclude_none=True, by_alias=True)

        # Send request
        resp = self.nmbrs.session.post(
            url=f"{self.nmbrs.base_url}companies/{company_id}/employees",
            json=payload,
            timeout=self.nmbrs.timeout
        )


        return resp

    def update(self, employee_id: str, data: Dict[str, Any]):
        """
        Update an employee using Pydantic validation.

        Args:
            employee_id: The ID of the employee
            data: Dictionary structured according to the EmployeeUpdate schema with:
                 - employeeId: The ID of the employee to update
                 - personalInfo: containing any of basicInfo, birthInfo, contactInfo, etc.

        Returns:
            Response from the API
        """
        # Validate with Pydantic model
        nested_data = self.nmbrs.flat_dict_to_nested_dict(data, EmployeeUpdate)
        employee_model = EmployeeUpdate(**nested_data)

        if self.nmbrs.mock_mode:
            return employee_model

        # Convert validated model to dict for API payload
        payload = employee_model.model_dump(exclude_none=True, by_alias=True)

        # Send request
        resp = self.nmbrs.session.put(
            url=f"{self.nmbrs.base_url}employees/{employee_id}/personalInfo",
            json=payload,
            timeout=self.nmbrs.timeout
        )

        # Handle social security number update if present
        #TODO niuet overtschirjven
        if 'social_security_number' in data:
            social_security_payload = {
                "socialSecurityNumber": data['social_security_number']
            }
            resp = self.nmbrs.session.put(
                url=f"{self.nmbrs.base_url}employees/{employee_id}/socialsecuritynumber",
                json=social_security_payload,
                timeout=self.nmbrs.timeout
            )

        return resp

    def get_soap_ids(self) -> pd.DataFrame:
        """
        Get all employees using the SOAP API.

        Returns:
            pd.DataFrame: DataFrame containing all companies
        """
        try:
            # Make SOAP request with the proper header structure
            emp_list = []
            comp_ids = self.nmbrs.soap_company_ids.i_d.unique()
            for company_id in comp_ids:
                response = self.nmbrs.soap_client_employees.service.Function_GetAll_AllEmployeesByCompany_V2(
                    _soapheaders=[self.nmbrs.soap_auth_header_employees],
                    CompanyID=company_id
                )

                # Convert response to DataFrame
                if response:
                    # Convert Zeep objects to Python dictionaries
                    serialized_response = serialize_object(response)

                    # TODO: add validation here
                    # Convert to DataFrame
                    df = pd.DataFrame(serialized_response)
                    df = self.nmbrs._rename_camel_columns_to_snake_case(df)
                    if not df.empty:
                        emp_list.append(df)

            if len(emp_list) > 0:
                return pd.concat(emp_list, ignore_index=True)
            else:
                return pd.DataFrame()

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
        except Exception as e:
            self.logger.exception("Exception occurred:")
            raise Exception(f"Failed to get companies: {str(e)}")

    def get_soap_personal_info(self):
        try:
            emp_list = []
            comp_ids = self.nmbrs.soap_company_ids.i_d.unique()
            for company_id in comp_ids:
                response = self.nmbrs.soap_client_employees.service.PersonalInfo_GetAll_AllEmployeesByCompany(
                    _soapheaders=[self.nmbrs.soap_auth_header_employees],
                    CompanyID=company_id
                )

                if response:
                    serialized_response = serialize_object(response)
                    df = pd.json_normalize(
                        serialized_response,
                        record_path=['EmployeePersonalInfos', 'PersonalInfo_V2'],
                        meta=['EmployeeId']
                    )
                    df = self.nmbrs._rename_camel_columns_to_snake_case(df)
                    if not df.empty:
                        emp_list.append(df)
            if len(emp_list) > 0:
                return pd.concat(emp_list, ignore_index=True)
            else:
                return pd.DataFrame()

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
        except Exception as e:
            self.logger.exception("Exception occurred:")
            raise Exception(f"Failed to get companies: {str(e)}")
