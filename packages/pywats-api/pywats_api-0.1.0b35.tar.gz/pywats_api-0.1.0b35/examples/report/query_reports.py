"""
Report Domain: Query Reports

This example demonstrates querying and filtering reports using OData filters.
The report query API uses OData syntax for filtering, not WATSFilter.
"""
import os
from datetime import datetime, timedelta
from pywats import pyWATS
from pywats.domains.report import ReportType

# =============================================================================
# Setup
# =============================================================================

api = pyWATS(
    base_url=os.environ.get("WATS_BASE_URL", "https://demo.wats.com"),
    token=os.environ.get("WATS_TOKEN", "")
)


# =============================================================================
# Get Report Headers (List)
# =============================================================================

# Get recent report headers using helper method
headers = api.report.get_recent_headers(count=10)

print(f"Found {len(headers)} reports")
for header in headers[:5]:
    print(f"  {header.serial_number}: {header.result} ({header.start})")


# =============================================================================
# Filter by Date Range
# =============================================================================

# Using helper method
start_date = datetime.now() - timedelta(days=7)
end_date = datetime.now()

headers = api.report.get_headers_by_date_range(
    start_date=start_date,
    end_date=end_date
)
print(f"\nReports from last 7 days: {len(headers)}")


# =============================================================================
# Filter by Part Number
# =============================================================================

# Using helper method
headers = api.report.get_headers_by_part_number("WIDGET-001")
print(f"\nReports for WIDGET-001: {len(headers)}")

# Or using OData filter directly
headers = api.report.query_uut_headers(
    odata_filter="partNumber eq 'WIDGET-001'"
)


# =============================================================================
# Filter by Serial Number
# =============================================================================

# Using helper method
headers = api.report.get_headers_by_serial("SN-2024-001234")
print(f"\nReports for serial SN-2024-001234: {len(headers)}")

# Or using OData filter directly
headers = api.report.query_uut_headers(
    odata_filter="serialNumber eq 'SN-2024-001234'"
)


# =============================================================================
# Filter by Result
# =============================================================================

# Get failed reports only using OData filter
headers = api.report.query_uut_headers(
    odata_filter="result eq 'Failed'",
    top=100
)
print(f"\nFailed reports: {len(headers)}")

for header in headers[:5]:
    print(f"  {header.serial_number}: {header.part_number}")


# =============================================================================
# Get Full Report
# =============================================================================

# Get a report by ID
report_id = "some-report-uuid"  # Replace with actual ID
report = api.report.get_report(report_id)

if report:
    print(f"\nFull Report:")
    print(f"  Serial: {report.sn}")
    print(f"  Part: {report.pn}")
    print(f"  Result: {report.result}")
    print(f"  Steps: {len(report.root.steps) if report.root else 0}")


# =============================================================================
# Get Serial Number History
# =============================================================================

# Get all reports for a serial number (Analytics API - still uses WATSFilter)
history = api.analytics.get_sn_history("SN-2024-001234")

print(f"\nHistory for SN-2024-001234:")
for report in history:
    print(f"  {report.start}: {report.result} ({report.processCode})")


# =============================================================================
# Combined OData Filters
# =============================================================================

# Combine multiple conditions with 'and'
headers = api.report.query_uut_headers(
    odata_filter="partNumber eq 'WIDGET-001' and result eq 'Failed'",
    top=100
)
print(f"\nFailed WIDGET-001 reports: {len(headers)}")


# =============================================================================
# Report Query with Pagination
# =============================================================================

# Get reports in batches using skip and top
all_headers = []
page = 0
page_size = 100

while True:
    headers = api.report.query_uut_headers(
        top=page_size,
        skip=page * page_size,
        orderby="start desc"
    )
    
    if not headers:
        break
    
    all_headers.extend(headers)
    page += 1
    
    if len(headers) < page_size:
        break

print(f"\nTotal reports (paginated): {len(all_headers)}")


# =============================================================================
# Query with Expanded Fields
# =============================================================================

# Expand sub-units
headers = api.report.query_uut_headers(
    odata_filter="serialNumber eq 'W12345'",
    expand=["subUnits"]
)

for header in headers:
    if header.sub_units:
        for sub in header.sub_units:
            print(f"  Sub-unit: {sub.serial_number}")


# =============================================================================
# Unified Query for UUT/UUR
# =============================================================================

# Query UUT headers
uut_headers = api.report.query_headers(
    report_type=ReportType.UUT,
    odata_filter="serialNumber eq 'W12345'"
)

# Query UUR (repair) headers
uur_headers = api.report.query_headers(
    report_type=ReportType.UUR,
    odata_filter="serialNumber eq 'W12345'"
)

print(f"\nUUT reports: {len(uut_headers)}")
print(f"UUR reports: {len(uur_headers)}")
