from pydantic import BaseModel, computed_field
from typing import Dict, List

import json


class ApartmentSettlement(BaseModel):
    apartament: str
    settlement_year: int = Field(..., ge=1900, le=2100)
    settlement_month: int = Field(..., ge=1, le=12)
    total_bills_pln: float = Field(default=0.0, ge=0.0)
    total_rent_pln: float = Field(default=0.0, ge=0.0)
    total_paid_pln: float = Field(default=0.0, ge=0.0)

    @computed_field
    @property
    def remaining_amount_pln(self) -> float:
        return (self.total_bills_pln + self.total_rent_pln) - self.total_paid_pln


class Parameters(BaseModel):
    apartments_json_path: str = 'data/apartments.json'
    tenants_json_path: str = 'data/tenants.json'
    transfers_json_path: str = 'data/transfers.json'
    bills_json_path: str = 'data/bills.json'


class Room(BaseModel):
    name: str
    area_m2: float


class Apartment(BaseModel):
    key: str
    name: str
    location: str
    area_m2: float
    rooms: Dict[str, Room]

    @staticmethod
    def from_json_file(file_path: str) -> Dict[str, 'Apartment']:
        data = None
        with open(file_path, 'r') as file:
            data = json.load(file)
        assert isinstance(data, dict), "Expected a dictionary of apartments"
        return {key: Apartment(**apartment) for key, apartment in data.items()}


class Tenant(BaseModel):
    name: str
    apartment: str
    room: str
    rent_pln: float
    deposit_pln: float
    date_agreement_from: str
    date_agreement_to: str

    @staticmethod
    def from_json_file(file_path: str) -> Dict[str, 'Tenant']:
        data = None
        with open(file_path, 'r') as file:
            data = json.load(file)
        assert isinstance(data, dict), "Expected a dictionary of tenants"
        return {key: Tenant(**tenant) for key, tenant in data.items()}


class Transfer(BaseModel):
    amount_pln: float
    date: str
    settlement_year: int | None
    settlement_month: int | None
    tenant: str

    @staticmethod
    def from_json_file(file_path: str) -> List['Transfer']:
        data = None
        with open(file_path, 'r') as file:
            data = json.load(file)
        assert isinstance(data, list), "Expected a list of transfers"
        return [Transfer(**transfer) for transfer in data]


class Bill(BaseModel):
    amount_pln: float
    date_due: str
    apartment: str
    settlement_year: int
    settlement_month: int
    type: str

    @staticmethod
    def from_json_file(file_path: str) -> List['Bill']:
        data = None
        with open(file_path, 'r') as file:
            data = json.load(file)
        assert isinstance(data, list), "Expected a list of bills"
        return [Bill(**bill) for bill in data]


class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters

        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []

        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(
            self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(
            self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)


class TenantSettlement(BaseModel):
    tenant: str
    settlement_year: int
    settlement_month: int
    apart: str
    rent_pln: float
    bills_share_pln: float
    transfers_total_pln: float

    @computed_field
    @property
    def total_due_pln(self) -> float:
        return round(self.rent_pln + self.bills_share_pln, 2)

    @computed_field
    @property
    def balance_pln(self) -> float:
        return round(self.transfers_total_pln - self.total_due_pln, 2)


if __name__ == '__main__':
    parameters = Parameters()
    manager = Manager(parameters)

    for apartment in manager.apartments.values():
        print("-"*50)
        print(apartment.key, apartment.name,
              apartment.location, apartment.area_m2)
        for room in apartment.rooms.values():
            print('  ', room.name, room.area_m2)

        for bill in manager.bills:
            if bill.apartment == apartment.key:
                print('  ', bill.amount_pln, bill.date_due,
                      bill.settlement_year, bill.settlement_month, bill.type)

    for tenant in manager.tenants.values():
        print("-"*50)
        print(tenant.name, tenant.apartment, tenant.room, tenant.rent_pln,
              tenant.deposit_pln, tenant.date_agreement_from, tenant.date_agreement_to)
        for transfer in manager.transfers:
            if transfer.tenant == tenant.name:
                print('  ', transfer.amount_pln, transfer.date,
                      transfer.settlement_year, transfer.settlement_month)
                print('  ', transfer.amount_pln, transfer.date,
                      transfer.settlement_year, transfer.settlement_month)
