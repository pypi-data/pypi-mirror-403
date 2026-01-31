from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID

from dateutil import parser
from pydantic import BaseModel, ConfigDict, Field, field_validator


def check_iso_format(v: Optional[str]):
    if v is None:
        return v
    try:
        return parser.parse(v)
    except Exception:
        raise ValueError('date must be ISO8601 format')


class AHttpMethodType(Enum):
    HTTP_METHOD_GET = 'GET'
    HTTP_METHOD_POST = 'POST'


class GenericRequest(BaseModel):
    url: str
    method: AHttpMethodType

    model_config = ConfigDict(validate_assignment=True, validate_default=True)


class Landing(GenericRequest):
    pass


class ANotify(GenericRequest):
    pass


class APaymentDataSplit(BaseModel):
    code: str
    amount: float
    meta: dict

    model_config = ConfigDict(validate_assignment=True, validate_default=True)


class APaymentDataStamp(BaseModel):
    amount: Optional[float]
    collection_data: Optional[str]
    reason: str

    model_config = ConfigDict(validate_assignment=True, validate_default=True)


class APaymentData(BaseModel):
    reason: str
    amount: float
    expire_at: str
    split: Union[List[Optional[APaymentDataSplit]], Dict[str, Optional[float]], None]
    stamps: Union[List[Optional[APaymentDataStamp]], Dict[str, Optional[float]], None]
    notify: ANotify
    landing: Landing
    config_id: UUID

    model_config = ConfigDict(validate_assignment=True, validate_default=True)

    @field_validator('expire_at')
    def expire_at_must_be_iso8601(cls, v):
        return check_iso_format(v)


class Applicant(BaseModel):
    email_address: Optional[str] = Field(None, alias='applicant.data.email_address')
    natoAIl: Optional[str] = Field(None, alias='applicant.data.Born.data.natoAIl')
    place_of_birth: Optional[str] = Field(None, alias='applicant.data.Born.data.place_of_birth')
    gender: Optional[str] = Field(None, alias='applicant.data.gender.data.gender')
    address: Optional[str] = Field(None, alias='applicant.data.address.data.address')
    house_number: Optional[str] = Field(None, alias='applicant.data.address.data.house_number')
    municipality: Optional[str] = Field(None, alias='applicant.data.address.data.municipality')
    county: Optional[str] = Field(None, alias='applicant.data.address.data.county')
    postal_code: Optional[str] = Field(None, alias='applicant.data.address.data.postal_code')
    name: str = Field(alias='applicant.data.completename.data.name')
    surname: str = Field(alias='applicant.data.completename.data.surname')
    fiscal_code: str = Field(alias='applicant.data.fiscal_code.data.fiscal_code')

    model_config = ConfigDict(validate_assignment=True)

    @field_validator('natoAIl')
    def natoAIl_must_be_iso8601(cls, v):  # noqa: N802
        return check_iso_format(v)


# TODO: gestire anagrafiche con meno dati
class Application(BaseModel):
    id: UUID
    tenant_id: UUID
    service_id: UUID
    user: UUID
    status_name: str
    created_at: str
    payment_data: APaymentData
    applicant: Applicant = Field(alias='data')
    locale: Optional[str] = None
    event_version: str
    event_id: UUID

    model_config = ConfigDict(validate_assignment=True, validate_default=True)

    @field_validator('status_name')
    def status_name_must_be_status_payment_pending(cls, v):
        if 'status_payment_pending' not in v:
            raise ValueError('status_name must be status_payment_pending')
        return v

    @field_validator('event_version')
    def event_version_must_be_two(cls, v):
        if '2' not in v:
            raise ValueError('event_version must be 2')
        return v.title()

    @field_validator('created_at')
    def created_at_must_be_iso8601(cls, v):
        return check_iso_format(v)
