import datetime
import functools
import json
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from json import JSONEncoder
from typing import List, Optional
from uuid import UUID

from dateutil import parser
from pydantic import BaseModel, ConfigDict, condecimal, constr, field_validator, model_validator

from ..utils.logger import payment_logger as logger


def check_iso_format(v):
    if isinstance(v, str):
        try:
            return parser.parse(v)  # Converte stringa in datetime
        except Exception:
            raise ValueError('date must be a valid ISO8601 datetime')
    if isinstance(v, datetime.datetime):
        return v  # Se è già un datetime, lo lascia invariato
    raise ValueError('expire_at must be a datetime or an ISO8601 string')


def check_isoformat_none_case(v):
    if v is not None:
        if isinstance(v, str):
            try:
                return parser.parse(v)  # Converte stringa in datetime
            except Exception:
                raise ValueError('date must be a valid ISO8601 datetime')
        if isinstance(v, datetime.datetime):
            return v  # Se è già un datetime, lo lascia invariato
        raise ValueError('date must be a datetime or an ISO8601 string')


class HttpMethodType(Enum):
    HTTP_METHOD_GET = 'GET'
    HTTP_METHOD_POST = 'POST'
    HTTP_METHOD_PUT = 'PUT'
    HTTP_METHOD_PATCH = 'PATCH'
    HTTP_METHOD_DELETE = 'DELETE'

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class CurrencyType(Enum):
    CURRENCY_EUR = 'EUR'

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class PaymentStatus(Enum):
    STATUS_CREATION_PENDING = 'CREATION_PENDING'
    STATUS_CREATION_FAILED = 'CREATION_FAILED'
    STATUS_PAYMENT_PENDING = 'PAYMENT_PENDING'
    STATUS_PAYMENT_STARTED = 'PAYMENT_STARTED'
    STATUS_PAYMENT_CONFIRMED = 'PAYMENT_CONFIRMED'
    STATUS_PAYMENT_FAILED = 'PAYMENT_FAILED'
    STATUS_NOTIFICATION_PENDING = 'NOTIFICATION_PENDING'
    STATUS_COMPLETE = 'COMPLETE'
    STATUS_EXPIRED = 'EXPIRED'
    STATUS_CANCELED = 'CANCELED'

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class PaymentType(Enum):
    TYPE_PAGOPA = 'PAGOPA'
    TYPE_STAMP = 'STAMP'

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class PayerType(Enum):
    TYPE_HUMAN = 'human'
    TYPE_LEGAL = 'legal'

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class PaymentDataSplit(BaseModel):
    code: str
    amount: Optional[condecimal(ge=Decimal('0'), max_digits=12, decimal_places=2)] = None
    meta: dict

    @field_validator('amount', mode='before')
    def _parse_split_amount(cls, v):
        if v in (None, ''):
            return None
        return Decimal(str(v)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def amount_cents(self) -> int:
        if self.amount is None:
            return 0
        return int((self.amount * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class Document(BaseModel):
    id: Optional[str]
    ref: Optional[str]
    hash: str

    model_config = ConfigDict(validate_assignment=True, validate_default=True)

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class Receiver(BaseModel):
    tax_identification_number: str
    name: str
    iban: Optional[str]
    address: Optional[str]
    building_number: Optional[str]
    postal_code: Optional[str]
    town_name: Optional[str]
    country_subdivision: Optional[str]
    country: Optional[str]

    model_config = ConfigDict(validate_assignment=True, validate_default=True)

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class PaymentData(BaseModel):
    transaction_id: Optional[str]
    paid_at: Optional[datetime.datetime]
    expire_at: Optional[datetime.datetime]
    amount: Optional[condecimal(ge=Decimal('0'), max_digits=12, decimal_places=2)] = None
    currency: CurrencyType
    type: Optional[PaymentType]
    notice_code: Optional[str]
    iud: str
    iuv: Optional[str]
    receiver: Optional[Receiver]
    due_type: Optional[str]
    pagopa_category: Optional[str]
    document: Optional[Document]
    split: List[Optional[PaymentDataSplit]]

    model_config = ConfigDict(validate_assignment=True, validate_default=True)

    @field_validator('paid_at', 'expire_at', mode='before')
    def _parse_optional_datetime(cls, v):
        return check_isoformat_none_case(v)

    @field_validator('amount', mode='before')
    def _parse_amount(cls, v):
        if v in (None, ''):
            return None
        return Decimal(str(v)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def amount_cents(self) -> Optional[int]:
        if self.amount is None:
            return None
        return int((self.amount * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    @model_validator(mode='after')
    def _check_splits_total(self):
        amt = self.amount  # Decimal | None
        splits = self.split or []  # List[PaymentDataSplit] | []

        # Se manca amount o non ci sono split, non validiamo la somma
        if amt is None or not splits:
            return self

        total = sum((s.amount for s in splits if s is not None), Decimal('0'))

        # Confronto commerciale a 2 decimali
        total_q = total.quantize(Decimal('0.01'))
        amt_q = amt.quantize(Decimal('0.01'))

        # Accetta:
        # 1) split come importi: somma == amount
        # 2) (opzionale) split come pesi: somma == 1.00
        if not (total_q == amt_q or total_q == Decimal('1.00')):
            raise ValueError(f'Somma degli split {total_q} diversa da amount {amt_q}')

        return self

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class OnlinePaymentBegin(BaseModel):
    url: Optional[str] = None
    last_opened_at: Optional[datetime.datetime] = None
    method: Optional[HttpMethodType] = None

    @field_validator('last_opened_at', mode='before')
    def last_opened_at_must_be_iso8601(cls, v):
        return check_isoformat_none_case(v)

    model_config = ConfigDict(validate_assignment=True, validate_default=True)

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class OnlinePaymentLanding(OnlinePaymentBegin):
    pass


class OfflinePayment(OnlinePaymentBegin):
    pass


class Receipt(OnlinePaymentBegin):
    pass


class Confirm(OnlinePaymentBegin):
    pass


class Cancel(OnlinePaymentBegin):
    pass


class Notify(BaseModel):
    url: Optional[str]
    method: Optional[HttpMethodType]
    sent_at: Optional[datetime.datetime]

    @field_validator('sent_at', mode='before')
    def sent_at_must_be_iso8601(cls, v):
        return check_isoformat_none_case(v)

    model_config = ConfigDict(validate_assignment=True, validate_default=True)

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class Update(BaseModel):
    url: Optional[str]
    last_check_at: Optional[datetime.datetime]
    next_check_at: Optional[datetime.datetime]
    method: Optional[HttpMethodType]

    @field_validator('last_check_at', 'next_check_at', mode='before')
    def _validate_check_times(cls, v):
        return check_isoformat_none_case(v)

    model_config = ConfigDict(validate_assignment=True, validate_default=True)

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class Links(BaseModel):
    online_payment_begin: OnlinePaymentBegin
    online_payment_landing: OnlinePaymentLanding
    offline_payment: OfflinePayment
    receipt: Receipt
    notify: Optional[List[Notify]]
    update: Update
    confirm: Confirm = Confirm(**{'url': None, 'last_opened_at': None, 'method': None})
    cancel: Cancel = Cancel(**{'url': None, 'last_opened_at': None, 'method': None})

    model_config = ConfigDict(validate_assignment=True, validate_default=True)

    def append_notify(self, notify):
        for item in notify:
            self.notify.append(Notify(**item))

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class Payer(BaseModel):
    type: PayerType
    tax_identification_number: str
    name: str
    family_name: Optional[str]
    street_name: Optional[str]
    building_number: Optional[str]
    postal_code: Optional[str]
    town_name: Optional[str]
    country_subdivision: Optional[str]
    country: Optional[str]
    email: Optional[str]

    model_config = ConfigDict(validate_assignment=True, validate_default=True)

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class Debtor(Payer):
    pass


class Fault(BaseModel):
    title: str
    detail: str
    type: str
    instance: Optional[str] = None

    model_config = ConfigDict(validate_assignment=True, validate_default=True)

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class Payment(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    tenant_id: UUID
    service_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    status: PaymentStatus
    reason: Optional[constr(max_length=140)]
    remote_id: UUID
    payment: PaymentData
    links: Links
    payer: Payer
    debtor: Optional[Debtor]
    locale: Optional[str] = None
    event_id: UUID
    event_version: str
    event_created_at: datetime.datetime
    app_id: str

    model_config = ConfigDict(validate_assignment=True, validate_default=True)

    @field_validator('created_at', 'updated_at', 'event_created_at')
    def _validate_required_datetimes(cls, v):
        return check_iso_format(v)

    @field_validator('event_version')
    def event_version_must_be_two(cls, v):
        if float(v) != 2.0:
            raise ValueError('event must have 2.0 as version')
        return v.title()

    def update_time(self, field):
        self._rsetattr(
            field,
            datetime.datetime.now().replace(microsecond=0).astimezone().isoformat(),
        )
        return self

    def update_check_time(self):
        if not self.links.update.last_check_at:
            return

        last_check = self.links.update.last_check_at
        next_check = datetime.datetime.now()

        minutes_checkpoint = self.created_at + datetime.timedelta(minutes=5)
        quarter_checkpoint = self.created_at + datetime.timedelta(minutes=15)
        week_checkpoint = self.created_at + datetime.timedelta(days=7)
        month_checkpoint = self.created_at + datetime.timedelta(days=30)
        year_checkpoint = self.created_at + datetime.timedelta(days=365)

        if last_check <= minutes_checkpoint:
            next_check = next_check + datetime.timedelta(minutes=1)
        elif last_check <= quarter_checkpoint:
            next_check = next_check + datetime.timedelta(minutes=5)
        elif last_check <= week_checkpoint:
            next_check = next_check + datetime.timedelta(hours=1)
        elif last_check <= month_checkpoint:
            next_check = next_check + datetime.timedelta(hours=6)
        elif last_check <= year_checkpoint:
            days_ahead = 6 - next_check.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_check = next_check + datetime.timedelta(days=days_ahead)
        else:
            next_check = None
            self.status = PaymentStatus.STATUS_EXPIRED

        self.links.update.next_check_at = (
            next_check.replace(microsecond=0).astimezone().isoformat() if next_check else None
        )

        return self

    def _rsetattr(self, attr, val):
        pre, _, post = attr.rpartition('.')
        return setattr(self._rgetattr(pre) if pre else self, post, val)

    def _rgetattr(self, attr, *args):
        def _getattr(obj, attr):
            return getattr(obj, attr, *args)

        return functools.reduce(_getattr, [self] + attr.split('.'))

    def is_payment_creation_needed(self):
        if self.status != PaymentStatus.STATUS_CREATION_PENDING:
            logger.info(f'Event {self.id} from application {self.remote_id}: Payment creation not required')
            return False
        return True

    def json(self):
        return json.dumps(self, cls=PaymentEncoder)


class PaymentEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat()
        elif isinstance(o, UUID):
            return str(o)
        elif isinstance(o, Decimal):
            return float(o.quantize(Decimal('0.01')))
        elif isinstance(o, (PaymentType, PayerType, PaymentStatus, HttpMethodType, CurrencyType)):
            return o.value
        elif isinstance(o, BaseModel):
            return o.model_dump()
        return o.__dict__
