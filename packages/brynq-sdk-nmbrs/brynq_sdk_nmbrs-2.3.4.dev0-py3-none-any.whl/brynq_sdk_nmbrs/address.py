import pandas as pd
import requests
from typing import Dict, Any, Union
from .schemas.address import AddressCreate, AddressGet, AddressDelete, AddressUpdate, Period
from brynq_sdk_functions import Functions


class Address:
    def __init__(self, nmbrs):
        self.nmbrs = nmbrs

    def get(self,
            created_from: str = None) -> pd.DataFrame:
        addresses = pd.DataFrame()
        for company in self.nmbrs.company_ids:
            addresses = pd.concat([addresses, self._get(company, created_from)])

        valid_addresses, invalid_addresses = Functions.validate_data(df=addresses, schema=AddressGet, debug=True)

        return valid_addresses, invalid_addresses

    def _get(self,
            company_id: str,
            created_from: str = None) -> pd.DataFrame:
        params = {} if created_from is None else {'createdFrom': created_from}
        request = requests.Request(method='GET',
                                   url=f"{self.nmbrs.base_url}companies/{company_id}/employees/addresses",
                                   params=params)

        data = self.nmbrs.get_paginated_result(request)
        df = pd.json_normalize(
            data,
            record_path='addresses',
            meta=['employeeId']
        )

        return df

    def create(self, employee_id: str, data: Dict[str, Any]):
        """
        Create a new address for an employee using Pydantic validation.

        Args:
            employee_id: The ID of the employee
            data: Dictionary containing address data with fields matching
                 the AddressCreate schema (using camelCase field names)

        Returns:
            Response from the API
        """
        # Validate with Pydantic model - this will raise an error if required fields are missing
        nested_data = self.nmbrs.flat_dict_to_nested_dict(data, AddressCreate)
        address_model = AddressCreate(**nested_data)

        if self.nmbrs.mock_mode:
            return address_model

        # Convert validated model to dict for API payload
        payload = address_model.model_dump(exclude_none=True, by_alias=True)

        # Send request
        resp = self.nmbrs.session.post(
            url=f"{self.nmbrs.base_url}employees/{employee_id}/address",
            json=payload,
            timeout=self.nmbrs.timeout
        )
        return resp

    def delete(self, employee_id: Union[int, str], address_id: Union[int, str]) -> bool:
        """
        Delete an address for an employee using SOAP API.
        
        REST API does not support address deletion, so we use SOAP as interim solution.

        Args:
            employee_id: The ID of the employee
            address_id: The ID of the address to delete

        Returns:
            bool: True if deletion was successful
            
        Raises:
            Exception: If SOAP client is not available or deletion fails
        """
        # Validate input using Pydantic schema
        delete_model = AddressDelete(employeeId=int(employee_id), addressId=int(address_id))

        if self.nmbrs.mock_mode:
            return delete_model

        # Call SOAP Address_Delete using EmployeeService auth header
        resp = self.nmbrs.soap_client_employees.service.Address_Delete(
            EmployeeId=delete_model.employee_id,
            AddressID=delete_model.address_id,
            _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_employees}
        )
        
        return resp

    def update(self, employee_id: Union[int, str], data: Dict[str, Any]):
        """
        Update an address for an employee using SOAP API.

        Args:
            employee_id: The ID of the employee
            data: Dictionary containing address data with fields matching AddressUpdate schema:
                - id: Address ID to update
                - street: Street name
                - house_number: House number (optional)
                - house_number_addition: House number addition (optional)
                - postal_code: Postal code (optional)
                - city: City name
                - state_province: State or province (optional)
                - country_iso_code: Country ISO code (e.g., "NL")

        Returns:
            Response from the API
        """
        # Validate with Pydantic model
        address_model = AddressUpdate(**data)

        if self.nmbrs.mock_mode:
            return address_model

        # Create EmployeeAddress type
        AddressType = self.nmbrs.soap_client_employees.get_type('ns0:EmployeeAddress')
        soap_address = AddressType(
            Id=address_model.id,
            Default=address_model.default,
            Street=address_model.street,
            HouseNumber=address_model.house_number or '',
            HouseNumberAddition=address_model.house_number_addition or '',
            PostalCode=address_model.postal_code or '',
            City=address_model.city,
            StateProvince=address_model.state_province or '',
            CountryISOCode=address_model.country_iso_code,
            Type=address_model.address_type
        )

        # Call SOAP Address_Update
        result = self.nmbrs.soap_client_employees.service.Address_Update(
            EmployeeId=int(employee_id),
            Address=soap_address,
            _soapheaders={'AuthHeaderWithDomain': self.nmbrs.soap_auth_header_employees}
        )
        return result
