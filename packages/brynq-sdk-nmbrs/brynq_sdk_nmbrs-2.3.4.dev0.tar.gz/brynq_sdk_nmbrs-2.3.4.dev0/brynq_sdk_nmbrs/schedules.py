import pandas as pd
import requests
from brynq_sdk_functions import Functions
from .schemas.schedules import ScheduleGet, ScheduleCreate, ScheduleUpdate
from datetime import datetime
from typing import Dict, Any, Tuple, Union
from zeep.exceptions import Fault
from zeep.helpers import serialize_object


class Schedule:
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def get(self,
            created_from: str = None,
            employee_id: str = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        schedules = pd.DataFrame()
        for company in self.nmbrs.company_ids:
            schedules = pd.concat([schedules, self._get(company, created_from, employee_id)])

        valid_schedules, invalid_schedules = Functions.validate_data(df=schedules, schema=ScheduleGet, debug=True)

        return valid_schedules, invalid_schedules

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
                                   url=f"{self.nmbrs.base_url}companies/{company_id}/employees/schedules",
                                   params=params)

        data = self.nmbrs.get_paginated_result(request)
        df = pd.json_normalize(
            data,
            record_path='schedules',
            meta=['employeeId']
        )
        return df

    def create(self,
               employee_id: str,
               data: Dict[str, Any]):
        """
        Create a new schedule for an employee using Pydantic validation

        Args:
            employee_id: The employee ID
            data: Schedule data dictionary with the following keys:
                - start_date_schedule: Start date of the schedule
                - weekly_hours: Hours per week (optional)
                - hours_monday, hours_tuesday, etc.: Hours for each day

        Returns:
            Response from the API
        """
        # Validate with Pydantic schema
        try:
            nested_data = self.nmbrs.flat_dict_to_nested_dict(data, ScheduleCreate)
            validated_data = ScheduleCreate(**nested_data)

            if self.nmbrs.mock_mode:
                return validated_data

            # Convert validated model to dict for API payload
            payload = validated_data.model_dump_json(exclude_none=True, by_alias=True)

            # Use the validated data for the API call
            resp = self.nmbrs.session.post(
                url=f"{self.nmbrs.base_url}employees/{employee_id}/schedule",
                data=payload,
                timeout=self.nmbrs.timeout,
                headers={'Content-Type': 'application/json'}
            )
            return resp

        except Exception as e:
            raise ValueError(f"Schedule validation failed: {str(e)}")

    def update(self, data: Dict[str, Any]):
        """
        Update a schedule for an employee using SOAP API.

        Args:
            data: Dictionary containing schedule data with fields matching ScheduleUpdate schema:
                - employeeId: Employee ID
                - startDate: Start date of the schedule
                - parttimePercentage: Part-time percentage (0-100)
                - hoursMonday, hoursTuesday, etc.: Hours for each day of week 1
                - hoursMonday2, hoursTuesday2, etc.: Hours for each day of week 2

        Returns:
            Response from the API
        """
        try:
            schedule_model = ScheduleUpdate(**data)

            if self.nmbrs.mock_mode:
                return schedule_model

            # Convert to SOAP object
            schedule_soap = schedule_model.to_soap_schedule(self.nmbrs.soap_client_employees)

            # Make SOAP request - CompanyRoosterNr is separate parameter (0 = no template)
            response = self.nmbrs.soap_client_employees.service.Schedule_UpdateCurrent(
                EmployeeId=schedule_model.employee_id,
                Schedule=schedule_soap,
                CompanyRoosterNr=schedule_model.company_rooster_nr or 0,
                _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_employees}
            )

            return response

        except Fault as e:
            raise Exception(f"SOAP request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to update Schedule: {str(e)}")

    def get_current(self, employee_id: Union[int, str]) -> pd.DataFrame:
        """
        Get current schedule for an employee via SOAP.

        Args:
            employee_id: The ID of the employee

        Returns:
            DataFrame with current schedule
        """
        if self.nmbrs.mock_mode:
            return pd.DataFrame()

        try:
            response = self.nmbrs.soap_client_employees.service.Schedule_GetCurrent(
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
        except Exception as e:
            raise Exception(f"Failed to get Schedule: {str(e)}")
