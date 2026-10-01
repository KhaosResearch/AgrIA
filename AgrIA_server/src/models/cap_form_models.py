from typing import Optional, List
from pydantic import BaseModel, Field


class BeneficiaryInfo(BaseModel):
    nif_cif: Optional[str] = Field(None, description="Tax ID of applicant")
    full_name: Optional[str] = Field(None, description="Name or company name")
    active_farmer_status: Optional[bool] = Field(
        None, description="Active farmer compliance status"
    )
    iban: Optional[str] = Field(None, description="Bank account number for payments")


class EntitlementDetail(BaseModel):
    region_code: str = Field(description="CAP Region code (e.g., Region 13)")
    num_entitlements: float = Field(description="Number of entitlement units held")
    unit_value_eur: Optional[float] = Field(None, description="Value per unit in Euros")


class SIGPACParcel(BaseModel):
    province_code: int = Field(description="Código de provincia")
    municipality_code: int = Field(description="Código de municipio")
    polygon: int = Field(description="Polígono")
    plot: int = Field(description="Parcela")
    enclosure: int = Field(description="Recinto SIGPAC")
    sigpac_use: str = Field(description="Uso SIGPAC oficial (e.g., OV, TA, PA)")
    declared_crop: str = Field(description="Cultivo o aprovechamiento real declarado")
    crop_variety: Optional[str] = Field(None, description="Variedad del cultivo")
    irrigation_type: str = Field(description="Régimen de hídrico: Secano / Regadío")
    declared_surface_ha: float = Field(
        description="Superficie determinada/declarada en ha"
    )
    slope_percentage: Optional[float] = Field(
        None, description="Pendiente media del recinto"
    )


class EcoSchemeAssignment(BaseModel):
    practice_code: str = Field(
        description="Eco-Régimen code (e.g., P6 - Cubierta vegetal espontánea)"
    )
    target_land_type: str = Field(
        description="Tierras de cultivo, Cultivos leñosos, Pastos"
    )
    slope_tier: Optional[str] = Field(
        None, description="Llano, Pendiente Media, Fuerte Pendiente"
    )
    applied_surface_ha: float = Field(
        description="Superficie solicitada para esta práctica"
    )


class LivestockDeclaration(BaseModel):
    rega_code: str = Field(description="Código de explotación REGA")
    species: str = Field(description="Especie (e.g., Bovino, Ovino, Caprino)")
    num_heads: int = Field(description="Número de cabezas de ganado")
    ugm_total: Optional[float] = Field(
        None, description="Unidades de Gran Ganado (UGM)"
    )


class CAPFullApplicationSchema(BaseModel):
    beneficiary: Optional[BeneficiaryInfo] = None
    requested_aid_lines: List[str] = Field(
        default_factory=list,
        description="Lista de líneas de ayuda solicitadas (ABRS, Redistributiva, etc.)",
    )
    entitlements: List[EntitlementDetail] = Field(default_factory=list)
    parcels: List[SIGPACParcel] = Field(default_factory=list)
    eco_schemes: List[EcoSchemeAssignment] = Field(default_factory=list)
    livestock: List[LivestockDeclaration] = Field(default_factory=list)
    total_declared_ha: float = Field(
        description="Superficie total computable declarada"
    )
