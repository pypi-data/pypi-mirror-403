"""
AI Converter - Auto-Selection Converter

This converter watches a folder and automatically selects the best matching
converter from all installed converters based on validation confidence scores.

How it works:
1. File arrives in the watch folder
2. AI Converter runs validate() on ALL installed converters
3. Selects the converter with highest confidence score
4. Delegates conversion to that converter
5. Returns the result

This enables a "drop any file here" workflow where the system automatically
determines the correct converter to use.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type

# ═══════════════════════════════════════════════════════════════════════════════
# PyWATS Report Model API Imports
# ═══════════════════════════════════════════════════════════════════════════════
from pywats.domains.report.report_models import UUTReport

# ═══════════════════════════════════════════════════════════════════════════════
# Converter Infrastructure Imports
# ═══════════════════════════════════════════════════════════════════════════════
from pywats_client.converters.file_converter import FileConverter
from pywats_client.converters.context import ConverterContext
from pywats_client.converters.models import (
    ConverterSource,
    ConverterResult,
    ValidationResult,
    ConversionStatus,
    PostProcessAction,
    ArgumentDefinition,
    ArgumentType,
)

logger = logging.getLogger(__name__)


class AIConverter(FileConverter):
    """
    Intelligent auto-selection converter.
    
    This converter doesn't convert files itself - instead it:
    1. Validates files against ALL registered converters
    2. Selects the converter with the highest confidence score
    3. Delegates the actual conversion to that converter
    
    Use this converter when you want a "smart" drop folder that
    automatically routes files to the correct converter.
    
    Configuration:
        min_confidence: Minimum confidence required (default: 0.5)
        log_all_scores: Log all converter confidence scores (default: True)
    """
    
    # Registry of available converters (populated on first use)
    _converter_registry: Dict[str, FileConverter] = {}
    _registry_initialized: bool = False
    
    @property
    def name(self) -> str:
        return "AI Converter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Automatically selects the best converter for each file based on content analysis"
    
    @property
    def file_patterns(self) -> List[str]:
        """Accept all file types - we'll let the sub-converters decide"""
        return ["*.*"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        return {
            "minConfidence": ArgumentDefinition(
                arg_type=ArgumentType.FLOAT,
                default=0.5,
                description="Minimum confidence score required to accept a converter match",
            ),
            "logAllScores": ArgumentDefinition(
                arg_type=ArgumentType.BOOLEAN,
                default=True,
                description="Log confidence scores from all converters for debugging",
            ),
        }
    
    @classmethod
    def register_converter(cls, converter: FileConverter) -> None:
        """
        Register a converter for auto-selection.
        
        Call this to add converters to the AI Converter's registry.
        """
        cls._converter_registry[converter.name] = converter
        logger.info(f"AI Converter: Registered '{converter.name}' v{converter.version}")
    
    @classmethod
    def register_converters(cls, converters: List[FileConverter]) -> None:
        """Register multiple converters at once"""
        for converter in converters:
            cls.register_converter(converter)
    
    @classmethod
    def get_registered_converters(cls) -> Dict[str, FileConverter]:
        """Get all registered converters"""
        return cls._converter_registry.copy()
    
    @classmethod
    def clear_registry(cls) -> None:
        """Clear the converter registry"""
        cls._converter_registry.clear()
        cls._registry_initialized = False
    
    @classmethod
    def initialize_default_converters(cls) -> None:
        """
        Initialize with all available converters from the converters folder.
        
        This is called automatically on first use if the registry is empty.
        """
        if cls._registry_initialized:
            return
        
        cls._registry_initialized = True
        
        # Import all known converters that use the UUTReport API
        try:
            from spea_converter import SPEAConverter
            cls.register_converter(SPEAConverter())
        except ImportError as e:
            logger.debug(f"Could not import SPEAConverter: {e}")
        
        try:
            from xjtag_converter import XJTAGConverter
            cls.register_converter(XJTAGConverter())
        except ImportError as e:
            logger.debug(f"Could not import XJTAGConverter: {e}")
        
        try:
            from xml_converter import XMLConverter
            cls.register_converter(XMLConverter())
        except ImportError as e:
            logger.debug(f"Could not import XMLConverter: {e}")
        
        try:
            from ict_converter import ICTConverter
            cls.register_converter(ICTConverter())
        except ImportError as e:
            logger.debug(f"Could not import ICTConverter: {e}")
        
        try:
            from json_converter import JSONConverter
            cls.register_converter(JSONConverter())
        except ImportError as e:
            logger.debug(f"Could not import JSONConverter: {e}")
        
        try:
            from klippel_converter import KlippelConverter
            cls.register_converter(KlippelConverter())
        except ImportError as e:
            logger.debug(f"Could not import KlippelConverter: {e}")
        
        try:
            from csv_converter import CsvConverter
            cls.register_converter(CsvConverter())
        except ImportError as e:
            logger.debug(f"Could not import CsvConverter: {e}")
        
        logger.info(f"AI Converter: Initialized with {len(cls._converter_registry)} converters")
    
    def _find_best_converter(
        self,
        source: ConverterSource,
        context: ConverterContext
    ) -> Tuple[Optional[FileConverter], Optional[ValidationResult], List[Dict[str, Any]]]:
        """
        Find the best converter for a source file.
        
        Returns:
            Tuple of (best_converter, best_validation, all_scores)
        """
        # Ensure converters are registered
        if not self._converter_registry:
            self.initialize_default_converters()
        
        min_confidence = context.get_argument("minConfidence", 0.5)
        log_all = context.get_argument("logAllScores", True)
        
        best_converter: Optional[FileConverter] = None
        best_validation: Optional[ValidationResult] = None
        best_score: float = 0.0
        all_scores: List[Dict[str, Any]] = []
        
        for name, converter in self._converter_registry.items():
            # Skip self to avoid infinite recursion
            if name == self.name:
                continue
            
            try:
                validation = converter.validate(source, context)
                
                score_entry = {
                    "converter": name,
                    "version": converter.version,
                    "can_convert": validation.can_convert,
                    "confidence": validation.confidence,
                    "message": validation.message,
                    "detected_sn": validation.detected_serial_number,
                    "detected_pn": validation.detected_part_number,
                }
                all_scores.append(score_entry)
                
                if not validation.can_convert:
                    continue
                
                # Use confidence directly as score
                if validation.confidence > best_score:
                    best_score = validation.confidence
                    best_converter = converter
                    best_validation = validation
                    
            except Exception as e:
                logger.warning(f"Error validating with {name}: {e}")
                all_scores.append({
                    "converter": name,
                    "can_convert": False,
                    "confidence": 0.0,
                    "message": f"Error: {e}",
                })
        
        # Sort scores for logging
        all_scores.sort(key=lambda x: x["confidence"], reverse=True)
        
        if log_all and all_scores:
            logger.info(f"AI Converter scores for {source.primary_name}:")
            for entry in all_scores[:5]:  # Top 5
                status = "✓" if entry["can_convert"] else "✗"
                logger.info(
                    f"  {status} {entry['converter']}: {entry['confidence']:.2f} - {entry['message']}"
                )
        
        # Check minimum confidence
        if best_validation and best_validation.confidence < min_confidence:
            logger.warning(
                f"Best match '{best_converter.name}' has confidence {best_validation.confidence:.2f} "
                f"below minimum {min_confidence}"
            )
            return None, None, all_scores
        
        return best_converter, best_validation, all_scores
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """
        Validate by checking if ANY registered converter can handle this file.
        
        Returns the validation result from the best matching converter.
        """
        best_converter, best_validation, all_scores = self._find_best_converter(source, context)
        
        if best_converter and best_validation:
            return ValidationResult(
                can_convert=True,
                confidence=best_validation.confidence,
                message=f"AI selected: {best_converter.name} ({best_validation.confidence:.2f})",
                detected_serial_number=best_validation.detected_serial_number,
                detected_part_number=best_validation.detected_part_number,
                detected_result=best_validation.detected_result,
            )
        
        # No converter found
        if all_scores:
            top_scores = ", ".join(
                f"{s['converter']}={s['confidence']:.2f}"
                for s in all_scores[:3]
            )
            return ValidationResult.no_match(
                f"No converter matched with sufficient confidence. Top scores: {top_scores}"
            )
        
        return ValidationResult.no_match("No converters registered")
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """
        Convert by delegating to the best matching converter.
        """
        best_converter, best_validation, all_scores = self._find_best_converter(source, context)
        
        if not best_converter:
            return ConverterResult.failed_result(
                error="No suitable converter found for this file"
            )
        
        logger.info(
            f"AI Converter delegating to '{best_converter.name}' "
            f"(confidence: {best_validation.confidence:.2f})"
        )
        
        try:
            # Delegate conversion
            result = best_converter.convert(source, context)
            
            # Add AI Converter metadata to the result
            if result.status == ConversionStatus.SUCCESS and result.report:
                # If it's a UUTReport, add misc info about AI selection
                if isinstance(result.report, UUTReport):
                    result.report.add_misc_info(
                        description="AI Converter Selected",
                        value=best_converter.name
                    )
                    result.report.add_misc_info(
                        description="AI Confidence Score",
                        value=f"{best_validation.confidence:.2f}"
                    )
                # If it's a dict (legacy), add metadata
                elif isinstance(result.report, dict):
                    if "miscInfo" not in result.report:
                        result.report["miscInfo"] = []
                    result.report["miscInfo"].append({
                        "description": "AI Converter Selected",
                        "value": best_converter.name
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error during delegated conversion: {e}", exc_info=True)
            return ConverterResult.failed_result(
                error=f"Conversion failed ({best_converter.name}): {e}"
            )
    
    def on_load(self, context: ConverterContext) -> None:
        """Initialize converter registry on load"""
        self.initialize_default_converters()
        logger.info(
            f"AI Converter loaded with {len(self._converter_registry)} registered converters"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Test/Demo Code
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    import tempfile
    
    # Add src to path
    src_path = str(Path(__file__).parent.parent / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    converters_path = str(Path(__file__).parent)
    if converters_path not in sys.path:
        sys.path.insert(0, converters_path)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    # Create test files
    test_files = []
    
    # CSV test file
    csv_content = """serial_number,part_number,result,test_name,measured_value,unit,pass
SN001,PN-123,PASSED,Voltage Test,12.5,V,TRUE
SN001,PN-123,PASSED,Current Test,1.2,A,TRUE"""
    
    csv_file = Path(tempfile.gettempdir()) / "test_results.csv"
    csv_file.write_text(csv_content)
    test_files.append(csv_file)
    
    # XML test file
    xml_content = """<?xml version="1.0"?>
<test>
    <header>
        <tester>TestOp</tester>
        <article_number>PN-XML-001</article_number>
        <sernum>SN-XML-001</sernum>
        <test_file>XMLTest</test_file>
        <test_existed>true</test_existed>
    </header>
    <meas>
        <name>Voltage</name>
        <val>5.1</val>
        <unit>V</unit>
        <in_range>true</in_range>
    </meas>
</test>"""
    
    xml_file = Path(tempfile.gettempdir()) / "test_result.xml"
    xml_file.write_text(xml_content)
    test_files.append(xml_file)
    
    # JSON test file
    json_content = """{
    "header": {
        "operator": "JsonOp",
        "partNumber": "PN-JSON-001",
        "serialNumber": "SN-JSON-001",
        "testFile": "JSONTest",
        "result": "Passed"
    },
    "tests": [
        {"name": "Test1", "value": 10.5, "unit": "V", "passed": true}
    ]
}"""
    
    json_file = Path(tempfile.gettempdir()) / "test_result.json"
    json_file.write_text(json_content)
    test_files.append(json_file)
    
    try:
        # Initialize AI Converter
        ai_converter = AIConverter()
        context = ConverterContext()
        
        # Force initialize converters
        AIConverter.initialize_default_converters()
        
        print("=" * 70)
        print("AI CONVERTER AUTO-SELECTION TEST")
        print("=" * 70)
        print(f"\nRegistered converters: {list(AIConverter.get_registered_converters().keys())}")
        print()
        
        for test_file in test_files:
            print(f"\n{'─' * 70}")
            print(f"Testing: {test_file.name}")
            print(f"{'─' * 70}")
            
            source = ConverterSource.from_file(test_file)
            
            # Validate
            validation = ai_converter.validate(source, context)
            print(f"Validation: can_convert={validation.can_convert}")
            print(f"  Message: {validation.message}")
            print(f"  Detected SN: {validation.detected_serial_number}")
            print(f"  Detected PN: {validation.detected_part_number}")
            
            # Convert
            if validation.can_convert:
                result = ai_converter.convert(source, context)
                print(f"\nConversion: {result.status.value}")
                if result.report:
                    if isinstance(result.report, UUTReport):
                        print(f"  Part Number: {result.report.pn}")
                        print(f"  Serial Number: {result.report.sn}")
                        print(f"  Result: {result.report.result}")
                    elif isinstance(result.report, dict):
                        print(f"  Part Number: {result.report.get('partNumber')}")
                        print(f"  Serial Number: {result.report.get('serialNumber')}")
                if result.error:
                    print(f"  Error: {result.error}")
    
    finally:
        # Cleanup
        for f in test_files:
            if f.exists():
                f.unlink()
