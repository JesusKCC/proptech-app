from pydantic import BaseModel, ConfigDict


class PlanoCentroBase(BaseModel):
    centro_comercial_id: str
    nombre_piso: str
    archivo_pdf_url: str
    ancho_unscaled_pt: float = 2384.0
    alto_unscaled_pt: float = 1684.0


class PlanoCentroCreate(PlanoCentroBase):
    pass


class PlanoCentroResponse(PlanoCentroBase):
    id: str

    model_config = ConfigDict(from_attributes=True)
