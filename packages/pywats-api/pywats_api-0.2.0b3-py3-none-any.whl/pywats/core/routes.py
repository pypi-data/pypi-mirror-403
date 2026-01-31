"""
API Routes - Centralized endpoint definitions for WATS API.

This module provides standardized route definitions to eliminate
hardcoded strings throughout the codebase and ensure consistency.

Usage:
    from pywats.core.routes import Routes
    
    url = Routes.Production.unit(sn="SN001", pn="PN001")
    # Returns: "/api/Production/Unit/SN001/PN001"

Coverage:
    - Production: Unit management, batches, serial numbers, phases
    - Product: Products, revisions, groups, BOM, vendors
    - Asset: Asset tracking, calibration, maintenance
    - Report: UUT/UUR reports, attachments
    - Software: Package distribution
    - Analytics: Yield, FPY, measurements, OEE
    - RootCause: Ticketing system
    - Process: Test processes and operations
    - SCIM: User provisioning
    - App: Server metadata (version, processes, levels)
"""


class Routes:
    """Centralized API route definitions for all WATS domains."""
    
    # =========================================================================
    # App / Server Metadata
    # =========================================================================
    
    class App:
        """Application/Server metadata routes."""
        BASE = "/api/App"
        VERSION = f"{BASE}/Version"
        PROCESSES = f"{BASE}/Processes"
        LEVELS = f"{BASE}/Levels"
        PRODUCT_GROUPS = f"{BASE}/ProductGroups"
        
        # Analytics endpoints under /api/App
        DYNAMIC_YIELD = f"{BASE}/DynamicYield"
        VOLUME_YIELD = f"{BASE}/VolumeYield"
        HIGH_VOLUME = f"{BASE}/HighVolume"
        HIGH_VOLUME_BY_GROUP = f"{BASE}/HighVolumeByProductGroup"
        WORST_YIELD = f"{BASE}/WorstYield"
        WORST_YIELD_BY_GROUP = f"{BASE}/WorstYieldByProductGroup"
        DYNAMIC_REPAIR = f"{BASE}/DynamicRepair"
        RELATED_REPAIR_HISTORY = f"{BASE}/RelatedRepairHistory"
        TOP_FAILED = f"{BASE}/TopFailed"
        TEST_STEP_ANALYSIS = f"{BASE}/TestStepAnalysis"
        MEASUREMENTS = f"{BASE}/Measurements"
        AGGREGATED_MEASUREMENTS = f"{BASE}/AggregatedMeasurements"
        OEE_ANALYSIS = f"{BASE}/OeeAnalysis"
        SERIAL_NUMBER_HISTORY = f"{BASE}/SerialNumberHistory"
        UUT_REPORT = f"{BASE}/UutReport"
        UUR_REPORT = f"{BASE}/UurReport"
    
    # =========================================================================
    # Production Domain
    # =========================================================================
    
    class Production:
        """Production domain routes."""
        BASE = "/api/Production"
        
        # Unit endpoints
        UNIT = f"{BASE}/Unit"
        UNITS = f"{BASE}/Units"
        UNITS_CHANGES = f"{BASE}/Units/Changes"
        UNIT_VERIFICATION = f"{BASE}/UnitVerification"
        SET_UNIT_PHASE = f"{BASE}/SetUnitPhase"
        SET_UNIT_PROCESS = f"{BASE}/SetUnitProcess"
        ADD_CHILD_UNIT = f"{BASE}/AddChildUnit"
        REMOVE_CHILD_UNIT = f"{BASE}/RemoveChildUnit"
        CHECK_CHILD_UNITS = f"{BASE}/CheckChildUnits"
        
        # Serial number endpoints
        SERIAL_NUMBERS = f"{BASE}/SerialNumbers"
        SERIAL_NUMBER_TYPES = f"{BASE}/SerialNumbers/Types"
        SERIAL_NUMBERS_TAKE = f"{BASE}/SerialNumbers/Take"
        SERIAL_NUMBERS_BY_RANGE = f"{BASE}/SerialNumbers/ByRange"
        SERIAL_NUMBERS_BY_REFERENCE = f"{BASE}/SerialNumbers/ByReference"
        
        # Batch endpoints
        BATCH = f"{BASE}/Batch"
        BATCHES = f"{BASE}/Batches"
        
        # Phase/Shift endpoints
        PHASES = f"{BASE}/Phases"
        SHIFT = f"{BASE}/Shift"
        SHIFTS = f"{BASE}/Shifts"
        OPERATORS = f"{BASE}/Operators"
        OPERATOR = f"{BASE}/Operator"
        
        @staticmethod
        def unit(serial_number: str, part_number: str) -> str:
            """GET /api/Production/Unit/{sn}/{pn}"""
            return f"{Routes.Production.UNIT}/{serial_number}/{part_number}"
        
        @staticmethod
        def unit_change(change_id: str) -> str:
            """DELETE /api/Production/Units/Changes/{id}"""
            return f"{Routes.Production.UNITS_CHANGES}/{change_id}"
        
        @staticmethod
        def shift(shift_id: str) -> str:
            """GET /api/Production/Shift/{id}"""
            return f"{Routes.Production.SHIFT}/{shift_id}"
        
        @staticmethod
        def batch(batch_id: str) -> str:
            """GET /api/Production/Batch/{id}"""
            return f"{Routes.Production.BATCH}/{batch_id}"
        
        @staticmethod
        def operator(operator_id: str) -> str:
            """GET /api/Production/Operator/{id}"""
            return f"{Routes.Production.OPERATOR}/{operator_id}"
        
        # Internal API routes
        class Internal:
            """⚠️ Internal Production API routes."""
            BASE = "/api/internal/Production"
            MES_BASE = "/api/internal/Mes"
            
            IS_CONNECTED = f"{BASE}/isConnected"
            GET_UNIT = f"{BASE}/GetUnit"
            GET_UNIT_INFO = f"{BASE}/GetUnitInfo"
            GET_UNIT_HIERARCHY = f"{BASE}/GetUnitHierarchy"
            GET_UNIT_STATE_HISTORY = f"{BASE}/GetUnitStateHistory"
            GET_UNIT_PHASE = f"{BASE}/GetUnitPhase"
            GET_UNIT_PROCESS = f"{BASE}/GetUnitProcess"
            GET_UNIT_CONTENTS = f"{BASE}/GetUnitContents"
            CREATE_UNIT = f"{BASE}/CreateUnit"
            ADD_CHILD_UNIT = f"{BASE}/AddChildUnit"
            REMOVE_CHILD_UNIT = f"{BASE}/RemoveChildUnit"
            REMOVE_ALL_CHILD_UNITS = f"{BASE}/RemoveAllChildUnits"
            CHECK_CHILD_UNITS = f"{BASE}/CheckChildUnits"
            SERIAL_NUMBERS = f"{BASE}/SerialNumbers"
            SERIAL_NUMBERS_COUNT = f"{BASE}/SerialNumbers/Count"
            SERIAL_NUMBERS_FREE = f"{BASE}/SerialNumbers/Free"
            SERIAL_NUMBERS_RANGES = f"{BASE}/SerialNumbers/Ranges"
            SERIAL_NUMBERS_STATISTICS = f"{BASE}/SerialNumbers/Statistics"
            GET_SITES = f"{BASE}/GetSites"
            GET_UNIT_PHASES = f"{MES_BASE}/GetUnitPhases"
    
    # =========================================================================
    # Product Domain
    # =========================================================================
    
    class Product:
        """Product domain routes."""
        BASE = "/api/Product"
        
        QUERY = f"{BASE}/Query"
        PRODUCTS = f"{BASE}/Products"
        REVISION = f"{BASE}/Revision"
        REVISIONS = f"{BASE}/Revisions"
        GROUPS = f"{BASE}/Groups"
        GROUP = f"{BASE}/Group"
        BOM = f"{BASE}/BOM"
        VENDORS = f"{BASE}/Vendors"
        
        @staticmethod
        def product(part_number: str) -> str:
            """GET/PUT /api/Product/{partNumber}"""
            return f"{Routes.Product.BASE}/{part_number}"
        
        @staticmethod
        def revisions(part_number: str) -> str:
            """GET /api/Product/{partNumber}/Revisions"""
            return f"{Routes.Product.BASE}/{part_number}/Revisions"
        
        @staticmethod
        def revision(part_number: str, revision: str) -> str:
            """GET /api/Product/{partNumber}/{revision}"""
            return f"{Routes.Product.BASE}/{part_number}/{revision}"
        
        @staticmethod
        def bom(part_number: str, revision: str) -> str:
            """GET /api/Product/{partNumber}/{revision}/BOM"""
            return f"{Routes.Product.BASE}/{part_number}/{revision}/BOM"
        
        @staticmethod
        def vendor(vendor_id: str) -> str:
            """DELETE /api/Product/Vendors/{id}"""
            return f"{Routes.Product.VENDORS}/{vendor_id}"
        
        # Internal API routes
        class Internal:
            """⚠️ Internal Product API routes."""
            BASE = "/api/internal/Product"
            
            BOM = f"{BASE}/Bom"
            BOM_UPLOAD = f"{BASE}/BOM"
            GET_PRODUCT_INFO = f"{BASE}/GetProductInfo"
            GET_PRODUCT_BY_PN = f"{BASE}/GetProductByPN"
            POST_REVISION_RELATION = f"{BASE}/PostProductRevisionRelation"
            PUT_REVISION_RELATION = f"{BASE}/PutProductRevisionRelation"
            DELETE_REVISION_RELATION = f"{BASE}/DeleteProductRevisionRelation"
            GET_CATEGORIES = f"{BASE}/GetProductCategories"
            PUT_CATEGORIES = f"{BASE}/PutProductCategories"
            GET_PRODUCT_TAGS = f"{BASE}/GetProductTags"
            PUT_PRODUCT_TAGS = f"{BASE}/PutProductTags"
            GET_REVISION_TAGS = f"{BASE}/GetRevisionTags"
            PUT_REVISION_TAGS = f"{BASE}/PutRevisionTags"
            GET_GROUPS_FOR_PRODUCT = f"{BASE}/GetGroupsForProduct"
    
    # =========================================================================
    # Asset Domain
    # =========================================================================
    
    class Asset:
        """Asset domain routes."""
        BASE = "/api/Asset"
        ASSETS = "/api/Assets"
        
        TYPES = f"{BASE}/Types"
        STATUS = f"{BASE}/Status"
        STATE = f"{BASE}/State"
        COUNT = f"{BASE}/Count"
        RESET_RUNNING_COUNT = f"{BASE}/ResetRunningCount"
        SET_RUNNING_COUNT = f"{BASE}/SetRunningCount"
        SET_TOTAL_COUNT = f"{BASE}/SetTotalCount"
        CALIBRATION = f"{BASE}/Calibration"
        CALIBRATION_EXTERNAL = f"{BASE}/Calibration/External"
        MAINTENANCE = f"{BASE}/Maintenance"
        MAINTENANCE_EXTERNAL = f"{BASE}/Maintenance/External"
        LOG = f"{BASE}/Log"
        MESSAGE = f"{BASE}/Message"
        SUB_ASSETS = f"{BASE}/SubAssets"
        
        @staticmethod
        def asset(identifier: str) -> str:
            """GET/PUT/DELETE /api/Asset/{id_or_serial}"""
            return f"{Routes.Asset.BASE}/{identifier}"
        
        @staticmethod
        def asset_status(serial_number: str) -> str:
            """GET /api/Asset/{serialNumber}/Status"""
            return f"{Routes.Asset.BASE}/{serial_number}/Status"
        
        @staticmethod
        def calibrations(serial_number: str) -> str:
            """GET /api/Asset/{serialNumber}/Calibrations"""
            return f"{Routes.Asset.BASE}/{serial_number}/Calibrations"
        
        @staticmethod
        def maintenance(serial_number: str) -> str:
            """GET /api/Asset/{serialNumber}/Maintenance"""
            return f"{Routes.Asset.BASE}/{serial_number}/Maintenance"
        
        # Internal API routes
        class Internal:
            """⚠️ Internal Asset API routes."""
            BLOB_BASE = "/api/internal/Blob/Asset"
            
            @staticmethod
            def upload(asset_id: str) -> str:
                """POST /api/internal/Blob/Asset/{id}"""
                return f"{Routes.Asset.Internal.BLOB_BASE}/{asset_id}"
            
            @staticmethod
            def download(asset_id: str, file_name: str) -> str:
                """GET /api/internal/Blob/Asset/{id}/{fileName}"""
                return f"{Routes.Asset.Internal.BLOB_BASE}/{asset_id}/{file_name}"
            
            @staticmethod
            def list_files(asset_id: str) -> str:
                """GET /api/internal/Blob/Asset/List/{id}"""
                return f"{Routes.Asset.Internal.BLOB_BASE}/List/{asset_id}"
            
            DELETE_FILES = "/api/internal/Blob/Assets"
    
    # =========================================================================
    # Report Domain
    # =========================================================================
    
    class Report:
        """Report domain routes."""
        BASE = "/api/Report"
        
        QUERY_HEADER = f"{BASE}/Query/Header"
        QUERY_HEADER_BY_MISC = f"{BASE}/Query/HeaderByMiscInfo"
        WSJF = f"{BASE}/WSJF"
        WSXF = f"{BASE}/WSXF"
        ATTACHMENT = f"{BASE}/Attachment"
        
        # UUT endpoints
        UUT = f"{BASE}/UUT"
        UUT_HEADERS = f"{UUT}/Headers"
        
        # UUR endpoints
        UUR = f"{BASE}/UUR"
        UUR_HEADERS = f"{UUR}/Headers"
        
        @staticmethod
        def wsjf(report_id: str) -> str:
            """GET /api/Report/Wsjf/{id}"""
            return f"{Routes.Report.BASE}/Wsjf/{report_id}"
        
        @staticmethod
        def wsxf(report_id: str) -> str:
            """GET /api/Report/Wsxf/{id}"""
            return f"{Routes.Report.BASE}/Wsxf/{report_id}"
        
        @staticmethod
        def uut(report_id: str) -> str:
            """GET /api/Report/UUT/{id}"""
            return f"{Routes.Report.UUT}/{report_id}"
        
        @staticmethod
        def uur(report_id: str) -> str:
            """GET /api/Report/UUR/{id}"""
            return f"{Routes.Report.UUR}/{report_id}"
        
        @staticmethod
        def attachments(report_id: str) -> str:
            """GET /api/Report/Attachments/{id}"""
            return f"{Routes.Report.BASE}/Attachments/{report_id}"
        
        @staticmethod
        def certificate(report_id: str) -> str:
            """GET /api/Report/Certificate/{id}"""
            return f"{Routes.Report.BASE}/Certificate/{report_id}"
    
    # =========================================================================
    # Software Domain
    # =========================================================================
    
    class Software:
        """Software distribution routes."""
        BASE = "/api/Software"
        
        PACKAGES = f"{BASE}/Packages"
        PACKAGE = f"{BASE}/Package"
        PACKAGE_BY_NAME = f"{BASE}/PackageByName"
        PACKAGES_BY_TAG = f"{BASE}/PackagesByTag"
        VIRTUAL_FOLDERS = f"{BASE}/VirtualFolders"
        FILE = f"{BASE}/File"
        
        @staticmethod
        def package(package_id: str) -> str:
            """GET/PUT/DELETE /api/Software/Package/{id}"""
            return f"{Routes.Software.PACKAGE}/{package_id}"
        
        @staticmethod
        def package_status(package_id: str) -> str:
            """POST /api/Software/PackageStatus/{id}"""
            return f"{Routes.Software.BASE}/PackageStatus/{package_id}"
        
        @staticmethod
        def package_files(package_id: str) -> str:
            """GET /api/Software/PackageFiles/{id}"""
            return f"{Routes.Software.BASE}/PackageFiles/{package_id}"
        
        @staticmethod
        def upload_zip(package_id: str) -> str:
            """POST /api/Software/Package/UploadZip/{id}"""
            return f"{Routes.Software.PACKAGE}/UploadZip/{package_id}"
        
        @staticmethod
        def file_attribute(package_id: str) -> str:
            """POST /api/Software/Package/FileAttribute/{id}"""
            return f"{Routes.Software.PACKAGE}/FileAttribute/{package_id}"
        
        # Internal API routes
        class Internal:
            """⚠️ Internal Software API routes."""
            BASE = "/api/internal/Software"
            
            IS_CONNECTED = f"{BASE}/isConnected"
            CHECK_FILE = f"{BASE}/CheckFile"
            POST_FOLDER = f"{BASE}/PostPackageFolder"
            UPDATE_FOLDER = f"{BASE}/UpdatePackageFolder"
            DELETE_FOLDER = f"{BASE}/DeletePackageFolder"
            DELETE_FOLDER_FILES = f"{BASE}/DeletePackageFolderFiles"
            GET_HISTORY = f"{BASE}/GetPackageHistory"
            GET_DOWNLOAD_HISTORY = f"{BASE}/GetPackageDownloadHistory"
            GET_REVOKED = f"{BASE}/GetRevokedPackages"
            GET_AVAILABLE = f"{BASE}/GetAvailablePackages"
            GET_DETAILS = f"{BASE}/GetSoftwareEntityDetails"
            LOG = f"{BASE}/Log"
            
            @staticmethod
            def file(file_id: str) -> str:
                """GET /api/internal/Software/File/{id}"""
                return f"{Routes.Software.Internal.BASE}/File/{file_id}"
    
    # =========================================================================
    # Analytics Domain
    # =========================================================================
    
    class Analytics:
        """Analytics domain routes (uses /api/App endpoints)."""
        # Most analytics endpoints are under /api/App, accessed via Routes.App
        BASE = "/api/Analytics"
        
        YIELD = f"{BASE}/Yield"
        FPY = f"{BASE}/FPY"
        STEPS = f"{BASE}/Steps"
        MEASUREMENTS = f"{BASE}/Measurements"
        PARETO = f"{BASE}/Pareto"
        
        @staticmethod
        def test_statistics(part_number: str = None) -> str:
            """GET /api/Analytics/TestStatistics[/{partNumber}]"""
            if part_number:
                return f"{Routes.Analytics.BASE}/TestStatistics/{part_number}"
            return f"{Routes.Analytics.BASE}/TestStatistics"
        
        # Internal API routes
        class Internal:
            """⚠️ Internal Analytics API routes."""
            UNIT_FLOW = "/api/internal/UnitFlow"
            UNIT_FLOW_LINKS = f"{UNIT_FLOW}/Links"
            UNIT_FLOW_NODES = f"{UNIT_FLOW}/Nodes"
            UNIT_FLOW_SN = f"{UNIT_FLOW}/SN"
            UNIT_FLOW_SPLIT_BY = f"{UNIT_FLOW}/SplitBy"
            UNIT_FLOW_UNIT_ORDER = f"{UNIT_FLOW}/UnitOrder"
            UNIT_FLOW_UNITS = f"{UNIT_FLOW}/Units"
            
            APP_BASE = "/api/internal/App"
            MEASUREMENT_LIST = f"{APP_BASE}/MeasurementList"
            STEP_STATUS_LIST = f"{APP_BASE}/StepStatusList"
            TOP_FAILED = f"{APP_BASE}/TopFailed"
            
            # Alarm/Notification routes (uses Trigger controller internally)
            TRIGGER_BASE = "/api/internal/Trigger"
            ALARM_LOGS = f"{TRIGGER_BASE}/GetAlarmAndNotificationLogs"
    
    # =========================================================================
    # RootCause Domain
    # =========================================================================
    
    class RootCause:
        """RootCause/Ticketing routes."""
        BASE = "/api/RootCause"
        
        TICKETS = f"{BASE}/Tickets"
        TICKET = f"{BASE}/Ticket"
        ARCHIVE_TICKETS = f"{BASE}/ArchiveTickets"
        ATTACHMENT = f"{BASE}/Attachment"
        TEAMS = f"{BASE}/Teams"
        
        @staticmethod
        def ticket(ticket_id: str) -> str:
            """GET/PUT /api/RootCause/Ticket/{id}"""
            return f"{Routes.RootCause.TICKET}/{ticket_id}"
        
        @staticmethod
        def ticket_comment(ticket_id: str) -> str:
            """POST /api/RootCause/Ticket/{id}/Comment"""
            return f"{Routes.RootCause.TICKET}/{ticket_id}/Comment"
        
        @staticmethod
        def ticket_status(ticket_id: str) -> str:
            """PUT /api/RootCause/Ticket/{id}/Status"""
            return f"{Routes.RootCause.TICKET}/{ticket_id}/Status"
    
    # =========================================================================
    # Process Domain
    # =========================================================================
    
    class Process:
        """Process routes."""
        BASE = "/api/Process"
        PROCESSES = f"{BASE}/Processes"
        
        @staticmethod
        def process(process_id: str) -> str:
            """GET /api/Process/{id}"""
            return f"{Routes.Process.BASE}/{process_id}"
        
        # Internal API routes
        class Internal:
            """⚠️ Internal Process API routes."""
            BASE = "/api/internal/Process"
            
            GET_PROCESSES = f"{BASE}/GetProcesses"
            GET_REPAIR_OPERATIONS = f"{BASE}/GetRepairOperations"
            
            @staticmethod
            def get_process(process_id: str) -> str:
                """GET /api/internal/Process/GetProcess/{id}"""
                return f"{Routes.Process.Internal.BASE}/GetProcess/{process_id}"
            
            @staticmethod
            def get_repair_operation(operation_id: str) -> str:
                """GET /api/internal/Process/GetRepairOperation/{id}"""
                return f"{Routes.Process.Internal.BASE}/GetRepairOperation/{operation_id}"
    
    # =========================================================================
    # SCIM Domain
    # =========================================================================
    
    class SCIM:
        """SCIM (User provisioning) routes."""
        BASE = "/api/SCIM/v2"
        
        TOKEN = f"{BASE}/Token"
        USERS = f"{BASE}/Users"
        GROUPS = f"{BASE}/Groups"
        
        @staticmethod
        def user(user_id: str) -> str:
            """GET/PATCH/DELETE /api/SCIM/v2/Users/{id}"""
            return f"{Routes.SCIM.USERS}/{user_id}"
        
        @staticmethod
        def user_by_name(username: str) -> str:
            """GET /api/SCIM/v2/Users/userName={userName}"""
            return f"{Routes.SCIM.USERS}/userName={username}"
        
        @staticmethod
        def group(group_id: str) -> str:
            """GET /api/SCIM/v2/Groups/{id}"""
            return f"{Routes.SCIM.GROUPS}/{group_id}"


# Convenience alias
API = Routes
