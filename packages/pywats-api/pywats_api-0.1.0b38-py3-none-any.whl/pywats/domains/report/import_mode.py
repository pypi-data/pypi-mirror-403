"""
ImportMode functionality for the Report domain.

This module provides the ImportMode context and helper functions for
automatic status calculation and failure propagation in Active mode.
"""
from typing import TYPE_CHECKING, Optional
from contextvars import ContextVar

from .enums import ImportMode

if TYPE_CHECKING:
    from .report_models.uut.step import Step
    from .report_models.uut.uut_report import UUTReport

# Context variable to hold the current ImportMode
# This allows nested contexts and thread-safe operation
_current_import_mode: ContextVar[ImportMode] = ContextVar(
    'import_mode', 
    default=ImportMode.Import
)


def get_import_mode() -> ImportMode:
    """
    Get the current import mode from context.
    
    Returns:
        The current ImportMode (Import or Active)
    """
    return _current_import_mode.get()


def set_import_mode(mode: ImportMode) -> None:
    """
    Set the current import mode in context.
    
    Args:
        mode: ImportMode.Import or ImportMode.Active
    """
    if not isinstance(mode, ImportMode):
        raise TypeError(f"mode must be ImportMode, not {type(mode).__name__}")
    _current_import_mode.set(mode)


def is_active_mode() -> bool:
    """
    Check if currently in Active mode.
    
    Returns:
        True if ImportMode.Active, False if ImportMode.Import
    """
    return _current_import_mode.get() == ImportMode.Active


def apply_failure_propagation(step: "Step") -> None:
    """
    Apply failure propagation for a step in Active mode.
    
    If the step's status is Failed and fail_parent_on_failure is True,
    this will propagate the failure up the step hierarchy.
    
    This is a no-op in Import mode.
    
    Args:
        step: The step to potentially propagate failure from
    """
    from .report_models.uut.step import StepStatus
    
    if not is_active_mode():
        return
    
    # Handle both enum and string status (NumericStep uses use_enum_values=True)
    status_is_failed = (
        step.status == StepStatus.Failed or 
        step.status == "F" or 
        (hasattr(step.status, 'value') and step.status.value == "F")
    )
    
    if status_is_failed and step.fail_parent_on_failure:
        # Propagate to parent
        if step.parent is not None:
            step.parent.propagate_failure()


def apply_measurement_auto_status(step: "Step") -> None:
    """
    Apply automatic status calculation for measurement steps in Active mode.
    
    For NumericStep and MultiNumericStep, calculates status based on
    comparison operator and limits. Only applies when status has not been
    explicitly set (is default Passed).
    
    This is a no-op in Import mode.
    
    Args:
        step: The step to potentially calculate status for
    """
    from .report_models.uut.step import StepStatus
    from .report_models.uut.steps.numeric_step import NumericStep, MultiNumericStep
    
    if not is_active_mode():
        return
    
    # Only process numeric steps with measurements
    if isinstance(step, NumericStep):
        if step.measurement is not None:
            calculated_status = step.measurement.calculate_status()
            if calculated_status == "F":
                step.status = StepStatus.Failed
                # Trigger propagation
                apply_failure_propagation(step)
    
    elif isinstance(step, MultiNumericStep):
        if step.measurements:
            for meas in step.measurements:
                calculated_status = meas.calculate_status()
                if calculated_status == "F":
                    step.status = StepStatus.Failed
                    # Trigger propagation
                    apply_failure_propagation(step)
                    break  # One failure is enough


def propagate_failure_to_report(step: "Step", report: "UUTReport") -> None:
    """
    Propagate failure from a step to the report level.
    
    This is called when failure propagation reaches the root sequence call.
    It sets the UUTReport.result to Failed.
    
    Args:
        step: The failing step
        report: The UUTReport to update
    """
    if not is_active_mode():
        return
    
    report.result = "F"
