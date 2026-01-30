from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .wats_base import WATSBase
from ....core.validation import validate_serial_number, validate_part_number

class SubUnit(WATSBase):
    """
    A sub unit (e.g., sub-module with its own serial number).
    
    Serial Number and Part Number Validation:
        The sn (serial number) and pn (part number) fields are validated
        for problematic characters that can cause issues with WATS searches.
        
        Problematic characters: * % ? [] [^] ! / \\
        
        To bypass validation (when you intentionally need these characters):
        - Use the allow_problematic_characters() context manager
        - Prefix the value with 'SUPPRESS:' (e.g., 'SUPPRESS:SN*001')
        
        See: pywats.core.validation for details
    """
    pn: str = Field(..., max_length=100, min_length=1)
    """
    The partnumber of the sub unit.
    """
    rev: Optional[str] = Field(default=None, max_length=100, min_length=0)
    """
    The revision of the sub unit.
    """
    sn: str = Field(..., max_length=100, min_length=1)
    """
    The serial number of the sub unit.
    """
    part_type: Optional[str] = Field(default="Unknown", max_length=50, min_length=1, validation_alias="partType",serialization_alias="partType")
    """
    The type of sub unit.
    """

    # Validate serial number for problematic characters
    @field_validator('sn', mode='after')
    @classmethod
    def validate_sn(cls, v: str) -> str:
        """Validate serial number for problematic characters."""
        return validate_serial_number(v)
    
    # Validate part number for problematic characters
    @field_validator('pn', mode='after')
    @classmethod
    def validate_pn(cls, v: str) -> str:
        """Validate part number for problematic characters."""
        return validate_part_number(v)

    model_config = ConfigDict(populate_by_name=True)
    


