"""
Standard Converters Module

This module provides converters for common test data formats,
including WATS standard formats and third-party equipment formats.

WATS Standard Formats:
- WATSStandardTextConverter: WATS Standard Text Format (tab-delimited)
- WATSStandardJSONConverter: WATS Standard JSON Format (WSJF)
- WATSStandardXMLConverter: WATS Standard XML Format (WSXF/WRML)

Industry Standard Formats:
- ATMLConverter: IEEE ATML (IEEE 1671/1636.1) test results with TestStand AddOn support

Test Equipment Converters:
- SeicaXMLConverter: Seica Flying Probe XML format
- TeradyneICTConverter: Teradyne i3070 ICT format (classic and new)
- TeradyneSpectrumICTConverter: Teradyne Spectrum ICT format
- KeysightTestExecSLConverter: Keysight TestExec SL functional test format
- KlippelConverter: Klippel audio/acoustic test equipment
- SPEAConverter: SPEA automated test equipment
- XJTAGConverter: XJTAG boundary scan test equipment

Special Converters:
- AIConverter: Auto-selection converter that detects file type and delegates
"""

from .atml_converter import ATMLConverter
from .seica_xml_converter import SeicaXMLConverter
from .teradyne_ict_converter import TeradyneICTConverter
from .teradyne_spectrum_ict_converter import TeradyneSpectrumICTConverter
from .keysight_testexec_sl_converter import KeysightTestExecSLConverter
from .wats_standard_text_converter import WATSStandardTextConverter
from .wats_standard_json_converter import WATSStandardJsonConverter
from .wats_standard_xml_converter import WATSStandardXMLConverter
from .klippel_converter import KlippelConverter
from .spea_converter import SPEAConverter
from .xjtag_converter import XJTAGConverter
from .ai_converter import AIConverter

__all__ = [
    # WATS Standard Formats
    "WATSStandardTextConverter",
    "WATSStandardJsonConverter",
    "WATSStandardXMLConverter",
    # Industry Standards
    "ATMLConverter",
    # Test Equipment
    "SeicaXMLConverter",
    "TeradyneICTConverter",
    "TeradyneSpectrumICTConverter",
    "KeysightTestExecSLConverter",
    "KlippelConverter",
    "SPEAConverter",
    "XJTAGConverter",
    # Special
    "AIConverter",
]
