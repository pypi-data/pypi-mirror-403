"""
Simple Report Builder for pyWATS

A forgiving, LLM-friendly tool for building WATS reports with minimal complexity.
Perfect for converters and AI-generated code that just wants to add steps without
worrying about nested sequences, step types, or comparison operators.

Key Features:
- Smart add_step() that infers step type from data
- Automatic sequence management (flat or hierarchical)
- Flexible data handling (handles strings, dicts, objects)
- Sensible defaults for everything
- Built-in type inference and validation

Example:
    >>> from pywats.tools.report_builder import ReportBuilder
    >>> 
    >>> builder = ReportBuilder(
    ...     part_number="MODULE-001",
    ...     serial_number="SN12345"
    ... )
    >>> 
    >>> # Add whatever data you have - it figures it out
    >>> builder.add_step("Voltage Test", 5.02, unit="V", low_limit=4.5, high_limit=5.5)
    >>> builder.add_step("Power OK", True)
    >>> builder.add_step("Serial Read", "ABC123")
    >>> builder.add_step("Multi-point", [1.2, 1.3, 1.1], unit="mV")
    >>> 
    >>> # Build and submit
    >>> report = builder.build()
    >>> api.report.submit_report(report)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from ..domains.report.report_models.uut.uut_report import UUTReport
from ..domains.report.report_models.uut.uut_info import UUTInfo
from ..domains.report.report_models.uut.steps.sequence_call import SequenceCall
from pywats.shared.enums import CompOp


@dataclass
class StepData:
    """Internal representation of a step before building"""
    name: str
    value: Any
    unit: Optional[str] = None
    low_limit: Optional[float] = None
    high_limit: Optional[float] = None
    comp_op: Optional[CompOp] = None
    status: Optional[str] = None
    group: Optional[str] = None  # Sequence name
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReportBuilder:
    """
    Simple, forgiving report builder that intelligently handles messy data.
    
    This builder is designed for:
    - Converter scripts that parse test data
    - LLM-generated code
    - Quick prototyping
    - Situations where you don't want to think about report structure
    
    Philosophy:
    - If it can be inferred, it will be
    - If it's missing, use sensible defaults
    - Never fail on missing metadata - just do the best you can
    - Support both flat and hierarchical structures automatically
    
    Attributes:
        part_number: Part number (required)
        serial_number: Serial number (required)
        revision: Revision (default: "A")
        operator: Operator name (default: "Converter")
        station: Station name (optional)
        location: Location (optional)
        process_code: Operation type code (default: 10 = SW Debug)
        result: Overall result, set automatically from steps unless specified
        
    Example:
        >>> # Simple usage
        >>> builder = ReportBuilder("PN-001", "SN-001")
        >>> builder.add_step("Voltage", 5.0, unit="V", low_limit=4.5, high_limit=5.5)
        >>> builder.add_step("Status", True)
        >>> report = builder.build()
        >>>
        >>> # With grouping
        >>> builder = ReportBuilder("PN-001", "SN-002")
        >>> builder.add_step("VCC", 3.3, unit="V", group="Power Tests")
        >>> builder.add_step("VDD", 1.8, unit="V", group="Power Tests")
        >>> builder.add_step("UART", True, group="Communication")
        >>> report = builder.build()
        >>>
        >>> # From messy dict
        >>> test_data = {"TestName": "Voltage", "Value": "5.02", "Unit": "V", 
        ...              "Low": 4.5, "High": 5.5, "Result": "PASS"}
        >>> builder.add_step_from_dict(test_data)
    """
    
    def __init__(
        self,
        part_number: str,
        serial_number: str,
        revision: str = "A",
        operator: Optional[str] = None,
        station: Optional[str] = None,
        location: Optional[str] = None,
        process_code: int = 10,  # SW Debug
        result: Optional[str] = None,
        start_time: Optional[datetime] = None,
        purpose: Optional[str] = None,
    ):
        """
        Initialize report builder with basic header info.
        
        Args:
            part_number: Part number (required)
            serial_number: Serial number (required)
            revision: Revision (default: "A")
            operator: Operator name (default: "Converter")
            station: Station name (optional)
            location: Location (optional)
            process_code: Operation type code (default: 10 = SW Debug)
            result: Overall result "P" or "F" (auto-determined if None)
            start_time: Start time (defaults to now)
            purpose: Test purpose (optional)
        """
        self.part_number = part_number
        self.serial_number = serial_number
        self.revision = revision
        self.operator = operator or "Converter"
        self.station = station
        self.location = location
        self.process_code = process_code
        self._explicit_result = result  # User-specified result
        self.start_time = start_time or datetime.now().astimezone()
        self.purpose = purpose
        
        # Storage for steps
        self._steps: List[StepData] = []
        
        # Metadata storage
        self._misc_info: Dict[str, str] = {}
        self._sub_units: List[Dict[str, str]] = []
        
    def add_step(
        self,
        name: str,
        value: Any = None,
        unit: Optional[str] = None,
        low_limit: Optional[Union[float, str]] = None,
        high_limit: Optional[Union[float, str]] = None,
        status: Optional[str] = None,
        group: Optional[str] = None,
        comp_op: Optional[Union[CompOp, str]] = None,
        **kwargs
    ) -> "ReportBuilder":
        """
        Add a test step with automatic type inference.
        
        This is the main method - it figures out what kind of step to create
        based on the data you provide.
        
        Type inference:
        - bool/True/False/"PASS"/"FAIL" → Boolean step
        - float/int with limits → Numeric limit test
        - float/int without limits → Numeric log
        - str → String step
        - list[float]/list[int] → Multi-numeric step
        - list[bool] → Multi-boolean step
        - list[str] → Multi-string step
        
        Args:
            name: Step name (required)
            value: Measured value (can be anything)
            unit: Unit of measurement (e.g., "V", "A", "°C")
            low_limit: Lower limit (for numeric tests)
            high_limit: Upper limit (for numeric tests)
            status: Status override ("P", "F", "Passed", "Failed", etc.)
            group: Group/sequence name (creates hierarchy)
            comp_op: Comparison operator (auto-inferred if not specified)
            **kwargs: Additional metadata stored for debugging
            
        Returns:
            Self for method chaining
            
        Examples:
            >>> # Numeric test with limits
            >>> builder.add_step("Voltage", 5.02, unit="V", low_limit=4.5, high_limit=5.5)
            >>>
            >>> # Boolean test
            >>> builder.add_step("Power OK", True)
            >>>
            >>> # String value
            >>> builder.add_step("Serial Number", "ABC123")
            >>>
            >>> # Multi-numeric
            >>> builder.add_step("Calibration Points", [1.2, 1.3, 1.1], unit="mV")
            >>>
            >>> # Grouped steps
            >>> builder.add_step("VCC", 3.3, unit="V", group="Power Tests")
            >>> builder.add_step("VDD", 1.8, unit="V", group="Power Tests")
        """
        # Convert limits to floats if they're strings
        if low_limit is not None and isinstance(low_limit, str):
            try:
                low_limit = float(low_limit)
            except (ValueError, TypeError):
                low_limit = None
                
        if high_limit is not None and isinstance(high_limit, str):
            try:
                high_limit = float(high_limit)
            except (ValueError, TypeError):
                high_limit = None
        
        # Auto-infer comparison operator if not provided
        if comp_op is None:
            comp_op = self._infer_comp_op(value, low_limit, high_limit)
        elif isinstance(comp_op, str):
            # Convert string to CompOp enum
            comp_op = self._parse_comp_op(comp_op)
        
        # Auto-infer status if not provided
        if status is None:
            status = self._infer_status(value, low_limit, high_limit, comp_op)
        else:
            # Normalize status to "P" or "F"
            status = self._normalize_status(status)
        
        step = StepData(
            name=name,
            value=value,
            unit=unit,
            low_limit=low_limit,
            high_limit=high_limit,
            comp_op=comp_op,
            status=status,
            group=group,
            timestamp=kwargs.get("timestamp"),
            metadata=kwargs
        )
        
        self._steps.append(step)
        return self
    
    def add_step_from_dict(
        self,
        data: Dict[str, Any],
        name_key: str = "name",
        value_key: str = "value",
        unit_key: str = "unit",
        low_limit_key: str = "low_limit",
        high_limit_key: str = "high_limit",
        status_key: str = "status",
        group_key: str = "group"
    ) -> "ReportBuilder":
        """
        Add a step from a dictionary with flexible key mapping.
        
        Handles common variations in key names:
        - name/Name/TestName/test_name/Step
        - value/Value/MeasuredValue/measured_value/Result
        - unit/Unit/Units/UOM
        - low_limit/LowLimit/Low/MinLimit/min
        - high_limit/HighLimit/High/MaxLimit/max
        - status/Status/Result/Pass/result
        - group/Group/Sequence/TestGroup
        
        Args:
            data: Dictionary containing step data
            name_key: Key for step name (default: "name")
            value_key: Key for value (default: "value")
            unit_key: Key for unit (default: "unit")
            low_limit_key: Key for low limit (default: "low_limit")
            high_limit_key: Key for high limit (default: "high_limit")
            status_key: Key for status (default: "status")
            group_key: Key for group name (default: "group")
            
        Returns:
            Self for method chaining
            
        Example:
            >>> # Standard format
            >>> data = {"name": "Voltage", "value": 5.0, "unit": "V"}
            >>> builder.add_step_from_dict(data)
            >>>
            >>> # Custom keys
            >>> data = {"TestName": "Voltage", "MeasuredValue": 5.0}
            >>> builder.add_step_from_dict(data, name_key="TestName", value_key="MeasuredValue")
            >>>
            >>> # Auto-detect common variations
            >>> data = {"Step": "Voltage", "Value": "5.0", "Unit": "V", "Low": 4.5, "High": 5.5}
            >>> builder.add_step_from_dict(data)  # Will find keys automatically
        """
        # Try to extract values using flexible key matching
        name = self._extract_value(data, name_key, ["name", "Name", "TestName", "test_name", "Step", "StepName"])
        value = self._extract_value(data, value_key, ["value", "Value", "MeasuredValue", "measured_value", "Result", "result"])
        unit = self._extract_value(data, unit_key, ["unit", "Unit", "Units", "UOM", "uom"])
        low_limit = self._extract_value(data, low_limit_key, ["low_limit", "LowLimit", "Low", "MinLimit", "min", "lowlimit"])
        high_limit = self._extract_value(data, high_limit_key, ["high_limit", "HighLimit", "High", "MaxLimit", "max", "highlimit"])
        status = self._extract_value(data, status_key, ["status", "Status", "Result", "result", "Pass", "pass", "Passed"])
        group = self._extract_value(data, group_key, ["group", "Group", "Sequence", "TestGroup", "Category"])
        
        if name is None:
            raise ValueError(f"Could not find step name in dictionary. Tried keys: {name_key}, name, Name, TestName, etc.")
        
        return self.add_step(
            name=str(name),
            value=value,
            unit=unit,
            low_limit=low_limit,
            high_limit=high_limit,
            status=status,
            group=group,
            **{k: v for k, v in data.items() if k not in [name_key, value_key, unit_key, low_limit_key, high_limit_key, status_key, group_key]}
        )
    
    def add_misc_info(self, description: str, text: str) -> "ReportBuilder":
        """
        Add miscellaneous information to report header.
        
        Args:
            description: Info description/name
            text: Info value
            
        Returns:
            Self for method chaining
        """
        self._misc_info[description] = text
        return self
    
    def add_sub_unit(
        self,
        part_type: str,
        part_number: Optional[str] = None,
        serial_number: Optional[str] = None,
        revision: Optional[str] = None
    ) -> "ReportBuilder":
        """
        Add a sub-unit (component) to the report.
        
        Args:
            part_type: Type of component (e.g., "CPU", "Memory", "Power Supply")
            part_number: Part number of component
            serial_number: Serial number of component
            revision: Revision of component
            
        Returns:
            Self for method chaining
        """
        self._sub_units.append({
            "part_type": part_type,
            "pn": part_number,
            "sn": serial_number,
            "rev": revision
        })
        return self
    
    def build(self) -> UUTReport:
        """
        Build the final UUTReport from collected step data.
        
        This method:
        1. Creates the UUTReport with header info
        2. Groups steps by sequence (if groups specified)
        3. Adds all steps in the correct order
        4. Sets overall result based on step statuses
        5. Adds misc info and sub-units
        
        Returns:
            UUTReport ready to submit
            
        Example:
            >>> builder = ReportBuilder("PN-001", "SN-001")
            >>> builder.add_step("Test1", 5.0)
            >>> builder.add_step("Test2", True)
            >>> report = builder.build()
            >>> api.report.submit_report(report)
        """
        # Determine overall result
        if self._explicit_result:
            result = self._normalize_status(self._explicit_result)
        else:
            result = self._calculate_overall_result()
        
        # Create report
        report = UUTReport(
            pn=self.part_number,
            sn=self.serial_number,
            rev=self.revision,
            process_code=self.process_code,
            station_name=self.station or "Station",
            location=self.location or "Default",
            purpose=self.purpose or "Test",
            result=result,
            start=self.start_time
        )
        
        # Set UUT info
        report.info = UUTInfo(
            operator=self.operator,
        )
        
        # Add misc info
        from ..domains.report.report_models.misc_info import MiscInfo
        for desc, text in self._misc_info.items():
            report.misc_infos.append(MiscInfo(description=desc, text=text))
        
        # Add sub-units
        from ..domains.report.report_models.sub_unit import SubUnit
        for sub in self._sub_units:
            report.sub_units.append(SubUnit(**{k: v for k, v in sub.items() if v is not None}))
        
        # Get root sequence
        root = report.get_root_sequence_call()
        
        # Group steps by sequence
        grouped_steps = self._group_steps_by_sequence()
        
        # Add steps to sequences
        for group_name, steps in grouped_steps.items():
            if group_name is None:
                # Add to root
                sequence = root
            else:
                # Create sub-sequence
                sequence = root.add_sequence_call(
                    name=group_name
                )
            
            # Add steps to sequence
            for step_data in steps:
                self._add_step_to_sequence(sequence, step_data)
        
        return report
    
    # =========================================================================
    # Internal Helper Methods
    # =========================================================================
    
    def _infer_comp_op(
        self,
        value: Any,
        low_limit: Optional[float],
        high_limit: Optional[float]
    ) -> CompOp:
        """Infer comparison operator from value and limits"""
        # For boolean, always LOG (no comparison needed)
        if isinstance(value, bool):
            return CompOp.LOG
        
        # For numeric with both limits
        if low_limit is not None and high_limit is not None:
            return CompOp.GELE  # Greater than or equal low, less than or equal high
        
        # For numeric with only low limit
        if low_limit is not None:
            return CompOp.GE  # Greater than or equal
        
        # For numeric with only high limit
        if high_limit is not None:
            return CompOp.LE  # Less than or equal
        
        # Default: LOG (just log the value)
        return CompOp.LOG
    
    def _infer_status(
        self,
        value: Any,
        low_limit: Optional[float],
        high_limit: Optional[float],
        comp_op: CompOp
    ) -> str:
        """Infer status from value and limits"""
        # Boolean value
        if isinstance(value, bool):
            return "P" if value else "F"
        
        # String that looks like a status
        if isinstance(value, str):
            normalized = self._normalize_status(value)
            if normalized in ["P", "F"]:
                return normalized
        
        # Numeric with limits
        if isinstance(value, (int, float)) and (low_limit is not None or high_limit is not None):
            try:
                value_float = float(value)
                
                if comp_op == CompOp.GELE:
                    if low_limit is not None and high_limit is not None:
                        return "P" if low_limit <= value_float <= high_limit else "F"
                elif comp_op == CompOp.GE:
                    if low_limit is not None:
                        return "P" if value_float >= low_limit else "F"
                elif comp_op == CompOp.LE:
                    if high_limit is not None:
                        return "P" if value_float <= high_limit else "F"
                elif comp_op == CompOp.GT:
                    if low_limit is not None:
                        return "P" if value_float > low_limit else "F"
                elif comp_op == CompOp.LT:
                    if high_limit is not None:
                        return "P" if value_float < high_limit else "F"
                elif comp_op == CompOp.EQ:
                    if low_limit is not None:
                        return "P" if abs(value_float - low_limit) < 0.0001 else "F"
            except (ValueError, TypeError):
                pass
        
        # Default: assume pass if no limits
        return "P"
    
    def _normalize_status(self, status: Any) -> str:
        """Normalize various status representations to 'P' or 'F'"""
        if status is None:
            return "P"
        
        status_str = str(status).upper().strip()
        
        # Pass variations
        if status_str in ["P", "PASS", "PASSED", "TRUE", "1", "SUCCESS", "OK"]:
            return "P"
        
        # Fail variations
        if status_str in ["F", "FAIL", "FAILED", "FALSE", "0", "ERROR", "ERR"]:
            return "F"
        
        # Default
        return "P"
    
    def _parse_comp_op(self, comp_op_str: str) -> CompOp:
        """Parse comparison operator string to CompOp enum"""
        comp_op_map = {
            "LOG": CompOp.LOG,
            "EQ": CompOp.EQ,
            "NE": CompOp.NE,
            "LT": CompOp.LT,
            "LE": CompOp.LE,
            "GT": CompOp.GT,
            "GE": CompOp.GE,
            "GELE": CompOp.GELE,
            "GTLT": CompOp.GTLT,
            "GELT": CompOp.GELT,
            "GTLE": CompOp.GTLE,
        }
        
        comp_op_upper = comp_op_str.upper()
        return comp_op_map.get(comp_op_upper, CompOp.LOG)
    
    def _extract_value(self, data: Dict[str, Any], primary_key: str, alternatives: List[str]) -> Any:
        """Extract value from dict using primary key or alternatives"""
        # Try primary key first
        if primary_key in data:
            return data[primary_key]
        
        # Try alternatives
        for alt_key in alternatives:
            if alt_key in data:
                return data[alt_key]
        
        return None
    
    def _calculate_overall_result(self) -> str:
        """Calculate overall result from step statuses"""
        if not self._steps:
            return "P"
        
        # If any step failed, overall is fail
        for step in self._steps:
            if step.status == "F":
                return "F"
        
        return "P"
    
    def _calculate_sequence_result(self, steps: List[StepData]) -> str:
        """Calculate sequence result from its steps"""
        if not steps:
            return "P"
        
        for step in steps:
            if step.status == "F":
                return "F"
        
        return "P"
    
    def _group_steps_by_sequence(self) -> Dict[Optional[str], List[StepData]]:
        """Group steps by their sequence/group name"""
        grouped: Dict[Optional[str], List[StepData]] = {}
        
        for step in self._steps:
            group_name = step.group
            if group_name not in grouped:
                grouped[group_name] = []
            grouped[group_name].append(step)
        
        return grouped
    
    def _add_step_to_sequence(self, sequence: SequenceCall, step_data: StepData):
        """Add a step to a sequence, automatically determining step type"""
        value = step_data.value
        
        # Determine step type and add accordingly
        if isinstance(value, bool):
            # Boolean step - status is derived from boolean value
            bool_status = "P" if value else "F"
            sequence.add_boolean_step(
                name=step_data.name,
                status=step_data.status or bool_status
            )
        
        elif isinstance(value, (int, float)):
            # Numeric step
            sequence.add_numeric_step(
                name=step_data.name,
                value=float(value),
                unit=step_data.unit,
                comp_op=step_data.comp_op or CompOp.LOG,
                low_limit=step_data.low_limit,
                high_limit=step_data.high_limit,
                status=step_data.status
            )
        
        elif isinstance(value, str):
            # String step
            sequence.add_string_step(
                name=step_data.name,
                value=value,
                comp_op=step_data.comp_op or CompOp.LOG,
                status=step_data.status
            )
        
        elif isinstance(value, list) and value:
            # Multi-value step - determine type from first element
            first_elem = value[0]
            
            if isinstance(first_elem, bool):
                # Multi-boolean - convert to status
                multi_bool_status = "P" if all(value) else "F"
                step = sequence.add_multi_boolean_step(
                    name=step_data.name,
                    status=step_data.status or multi_bool_status
                )
                # Add individual boolean measurements
                for i, v in enumerate(value):
                    step.add_measurement(name=f"Value {i+1}", status="P" if v else "F")
            
            elif isinstance(first_elem, (int, float)):
                # Multi-numeric - create step and add measurements
                step = sequence.add_multi_numeric_step(
                    name=step_data.name,
                    status=step_data.status or "P"
                )
                # Add individual numeric measurements
                for i, v in enumerate(value):
                    step.add_measurement(
                        name=f"Value {i+1}",
                        value=float(v),
                        unit=step_data.unit or "NA",
                        comp_op=step_data.comp_op or CompOp.LOG,
                        low_limit=step_data.low_limit,
                        high_limit=step_data.high_limit
                    )
            
            elif isinstance(first_elem, str):
                # Multi-string - create step and add measurements
                step = sequence.add_multi_string_step(
                    name=step_data.name,
                    status=step_data.status or "P"
                )
                # Add individual string measurements
                for i, v in enumerate(value):
                    step.add_measurement(
                        name=f"Value {i+1}",
                        value=v,
                        status=step_data.status or "P",
                        comp_op=step_data.comp_op or CompOp.LOG
                    )
        
        else:
            # Unknown type - log as string
            sequence.add_string_step(
                name=step_data.name,
                value=str(value) if value is not None else "N/A",
                comp_op=CompOp.LOG,
                status=step_data.status
            )


# =============================================================================
# Convenience Functions
# =============================================================================

def quick_report(
    part_number: str,
    serial_number: str,
    steps: List[Dict[str, Any]],
    **kwargs
) -> UUTReport:
    """
    Create a report from a list of step dictionaries in one call.
    
    Perfect for LLM-generated code or quick prototyping.
    
    Args:
        part_number: Part number
        serial_number: Serial number
        steps: List of step dictionaries with keys like 'name', 'value', 'unit', etc.
        **kwargs: Additional arguments passed to ReportBuilder constructor
        
    Returns:
        UUTReport ready to submit
        
    Example:
        >>> steps = [
        ...     {"name": "Voltage", "value": 5.0, "unit": "V", "low_limit": 4.5, "high_limit": 5.5},
        ...     {"name": "Current", "value": 1.2, "unit": "A"},
        ...     {"name": "Status", "value": True}
        ... ]
        >>> report = quick_report("PN-001", "SN-001", steps)
        >>> api.report.submit_report(report)
    """
    builder = ReportBuilder(part_number, serial_number, **kwargs)
    
    for step_dict in steps:
        builder.add_step_from_dict(step_dict)
    
    return builder.build()
