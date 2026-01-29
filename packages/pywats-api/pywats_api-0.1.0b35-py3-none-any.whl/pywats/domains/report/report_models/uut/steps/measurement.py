import json
from typing import Any, Literal, Optional, Union, Generic, TypeVar
from uuid import UUID
from pydantic import Field, model_validator, root_validator
from pydantic_core.core_schema import FieldPlainInfoSerializerFunction

from ...wats_base import WATSBase
from .comp_operator import CompOp

class Measurement(WATSBase):
    parent_step: Optional[Any] = Field(default=None, exclude=True)

    model_config = {
        "populate_by_name": True,          # Use alias for serializatio / deserialization
        "arbitrary_types_allowed": True,    # Fixes StepList issue
        "use_enum_values": True,
        "json_encoders": {CompOp: lambda c: c.name},  # Serialize enums as their names
        "allow_inf_nan": True,
        "ser_json_inf_nan": 'strings'
    }

class BooleanMeasurement(Measurement):    
    status: str = Field(default="P", max_length=1, min_length=1, pattern='^[PFS]$')

class MultiBooleanMeasurement(BooleanMeasurement):    
    name: str = Field(..., description="The name of the measurement - required for MultiStepTypes")

# ------------------------------------------------------------------------------------------
# LimitMeasurement 
class LimitMeasurement(BooleanMeasurement):
    value: Union[str,float] = Field(...)
    value_format: str | None = Field(default=None, validation_alias="valueFormat", serialization_alias="valueFormat")

    comp_op: Optional[CompOp] = Field(default=CompOp.LOG, validation_alias="compOp", serialization_alias="compOp")
    
    high_limit: float | str | None = Field(default=None, validation_alias="highLimit", serialization_alias="highLimit")
    high_limit_format: str | None = Field(default=None, validation_alias="highLimitFormat", serialization_alias="highLimitFormat")
    low_limit: float | str | None = Field(default=None, validation_alias="lowLimit", serialization_alias="lowLimit")
    low_limit_format: str | None = Field(default=None, validation_alias="lowLimitFormat", serialization_alias="lowLimitFormat")
        
    model_config = {
        "populate_by_name": True,          # Use alias for serializatio / deserialization
        "arbitrary_types_allowed": True,    # Fixes StepList issue
        "use_enum_values": True,
        "json_encoders": {CompOp: lambda c: c.name},  # Serialize enums as their names
        "allow_inf_nan": True,
        "ser_json_inf_nan": 'strings'
    }

    def calculate_status(self) -> str:
        """
        Calculate status based on comparison operator and limits.
        
        Used by ImportMode.Active for automatic status determination.
        
        Returns:
            "P" if measurement passes, "F" if it fails
            
        Note:
            - Returns "P" for LOG (no comparison)
            - Returns "P" if value is not numeric
            - Returns "P" if required limits are missing
        """
        # Get the comp_op - handle both enum and string forms
        comp_op = self.comp_op
        if isinstance(comp_op, str):
            try:
                comp_op = CompOp[comp_op]
            except (KeyError, ValueError):
                return "P"  # Unknown comp_op - default to pass
        
        if comp_op is None:
            return "P"
        
        # LOG always passes
        if comp_op == CompOp.LOG:
            return "P"
        
        # Try to convert value to float for comparison
        try:
            numeric_value = float(self.value)
        except (TypeError, ValueError):
            return "P"  # Non-numeric value - default to pass
        
        # Convert limits to float if present
        low = None
        high = None
        try:
            if self.low_limit is not None:
                low = float(self.low_limit)
        except (TypeError, ValueError):
            pass
        try:
            if self.high_limit is not None:
                high = float(self.high_limit)
        except (TypeError, ValueError):
            pass
        
        # Evaluate using CompOp's evaluate method
        if comp_op.evaluate(numeric_value, low, high):
            return "P"
        else:
            return "F"

    # Validate limits and comOp
    # @model_validator(mode="after")
    # def check_comp_op_limits(self):  
    #     if not self.comp_op.validate_limits(self.low_limit, self.high_limit):
    #         raise ValueError("Invalid limits")
    #     return self  
    
    # Using a Pydantic parsing method that supports current functionalities
    # @classmethod
    # def parse_obj(cls, obj):
    #     if isinstance(obj.get('comp_op'), str):
    #         obj['comp_op'] = CompOp[obj['comp_op']].value
    #     return super().model_validate(obj)

