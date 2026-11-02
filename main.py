from pydantic import BaseModel, Field, PositiveInt, NonNegativeFloat, computed_field
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

    print("=" * 60)
    print(" APARTMENTS & BILLS ")
    print("=" * 60)
    for apt in manager.apartments.values():
        print(f"\n🏠 [{apt.key}] {apt.name} ({apt.location}) - {apt.area_m2} m²")
        
        print("   Pokoje:")
        for r_key, room in apt.rooms.items():
            print(f"     - [{r_key}] {room.name}: {room.area_m2} m²")

        apt_bills = [b for b in manager.bills if b.apartment == apt.key]
        if apt_bills:
            print("   Rachunki:")
            for bill in apt_bills:
                print(f"     - {bill.type.upper():<12} | {bill.amount_pln:>7.2f} PLN | Okres: {bill.settlement_year}-{bill.settlement_month:02d} | Termin: {bill.date_due}")

    print("\n" + "=" * 60)
    print(" TENANTS & TRANSFERS ")
    print("=" * 60)
    for t_key, tenant in manager.tenants.items():
        print(f"\n👤 [{t_key}] {tenant.name}")
        print(f"   Mieszkanie: {tenant.apartment} | Pokój: {tenant.room}")
        print(f"   Czynsz: {tenant.rent_pln:.2f} PLN | Kaucja: {tenant.deposit_pln:.2f} PLN")
        print(f"   Umowa: od {tenant.date_agreement_from} do {tenant.date_agreement_to}")

        tenant_transfers = [tr for tr in manager.transfers if tr.tenant == t_key or tr.tenant == tenant.name]
        if tenant_transfers:
            print("   Przelewy:")
            for tr in tenant_transfers:
                period = f"{tr.settlement_year}-{tr.settlement_month:02d}" if tr.settlement_year and tr.settlement_month else "Brak okresu"
                print(f"     - {tr.amount_pln:>7.2f} PLN | Data: {tr.date} | Rozliczenie: {period}")