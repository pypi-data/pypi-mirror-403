from typing import Any, Dict, Union, Tuple
import pandas as pd

from .schemas.social_insurance import SocialInsuranceUpdate, SocialInsuranceGet
from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from brynq_sdk_functions import Functions


class SocialInsurance:
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs
        self.soap_client_employees = nmbrs.soap_client_employees

    def get(self, employee_id: Union[int, str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get current social insurance settings for an employee.

        Args:
            employee_id: The ID of the employee

        Returns:
            Tuple of (valid_data, invalid_data) DataFrames
        """
        if self.nmbrs.mock_mode:
            return pd.DataFrame(), pd.DataFrame()

        try:
            response = self.nmbrs.soap_client_employees.service.SVW_GetCurrent(
                EmployeeId=int(employee_id),
                _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_employees}
            )

            if response:
                serialized_response = serialize_object(response)
                if not isinstance(serialized_response, list):
                    serialized_response = [serialized_response]
                df = pd.DataFrame(serialized_response)
                df['employee_id'] = str(employee_id)
                
                valid_data, invalid_data = Functions.validate_data(df=df, schema=SocialInsuranceGet, debug=True)
                return valid_data, invalid_data
            else:
                return pd.DataFrame(), pd.DataFrame()

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to get Social Insurance: {str(e)}")

    def get_all_by_company(self, company_id: Union[int, str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get all social insurance settings for all employees in a company.

        Args:
            company_id: The ID of the company

        Returns:
            Tuple of (valid_data, invalid_data) DataFrames
        """
        if self.nmbrs.mock_mode:
            return pd.DataFrame(), pd.DataFrame()

        try:
            response = self.nmbrs.soap_client_employees.service.SVW_GetAll_AllEmployeesByCompany(
                CompanyID=int(company_id),
                _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_employees}
            )

            if response:
                all_data = []
                for emp in response:
                    emp_id = emp.EmployeeId
                    if emp.EmployeeSVWSettings and emp.EmployeeSVWSettings.EmployeeSVWSettings:
                        for svw in emp.EmployeeSVWSettings.EmployeeSVWSettings:
                            svw_data = serialize_object(svw)
                            svw_data['employee_id'] = str(emp_id)
                            all_data.append(svw_data)
                
                if all_data:
                    df = pd.DataFrame(all_data)
                    valid_data, invalid_data = Functions.validate_data(df=df, schema=SocialInsuranceGet, debug=True)
                    return valid_data, invalid_data
                else:
                    return pd.DataFrame(), pd.DataFrame()
            else:
                return pd.DataFrame(), pd.DataFrame()

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to get Social Insurance for company: {str(e)}")

    def update(self, data: Dict[str, Any]) -> pd.DataFrame:
        try:
            social_insurance_model = SocialInsuranceUpdate(**data)

            if self.nmbrs.mock_mode:
                return social_insurance_model

            # Use the model's built-in SOAP conversion method
            social_insurance_settings = social_insurance_model.to_soap_settings(self.nmbrs.soap_client_employees)

            # Make SOAP request with clean, simple call
            response = self.nmbrs.soap_client_employees.service.SVW_UpdateCurrent(
                EmployeeId=social_insurance_model.employee_id,
                SVWSettings=social_insurance_settings,
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
            raise Exception(f"Failed to update Social Insurance: {str(e)}")
