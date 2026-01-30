from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseCmfRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    value: float = Field(alias="Valor")
    date: datetime = Field(alias="Fecha")

    @field_validator('value', mode='before')
    @classmethod
    def convert_value(cls, v):
        return float(v.replace('.', '').replace(',', '.'))

    @field_validator('date', mode='before')
    @classmethod
    def convert_date(cls, v):
        return datetime.strptime(v, '%Y-%m-%d')


class IpcRecord(BaseCmfRecord):
    @field_validator('value', mode='before')
    @classmethod
    def convert_value(cls, v):
        return round(float(v.replace('.', '').replace(',', '.')) / 100, 5)


class UsdRecord(BaseCmfRecord): ...


class EurRecord(BaseCmfRecord): ...


class UFRecord(BaseCmfRecord): ...


class UTMRecord(BaseCmfRecord): ...