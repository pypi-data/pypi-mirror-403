"""
Main entry point for pyWATS Client Application
"""
from pywats import pyWATS
from pywats.domains.report import ReportType


def main():
    """Launch the pyWATS client application"""
    
    # 1. Initialize the pywats-api
    # 2. Connect to python.wats.com (credentials from conftest.py)
    api = pyWATS(
        base_url="https://python.wats.com",
        token="cHlXQVRTX0FQSV9BVVRPVEVTVDo2cGhUUjg0ZTVIMHA1R3JUWGtQZlY0UTNvbmk2MiM="
    )
    
    # 3. Query all UUT headers for serial number 244650023099
    serial_number = "244650023099"
    print(f"Querying UUT headers for serial number: {serial_number}")
    print("-" * 60)
    
    # Method 1: Using the helper method (simplest)
    headers = api.report.get_headers_by_serial(serial_number)
    
    # Method 2: Using query_headers with ReportType enum
    # headers = api.report.query_headers(
    #     report_type=ReportType.UUT,
    #     odata_filter=f"serialNumber eq '{serial_number}'"
    # )
    
    # Method 3: Using query_uut_headers with OData filter
    # headers = api.report.query_uut_headers(
    #     odata_filter=f"serialNumber eq '{serial_number}'"
    # )
    
    # 4. Print the results to console
    if not headers:
        print(f"No reports found for serial number: {serial_number}")
    else:
        print(f"Found {len(headers)} report(s):\n")
        for i, header in enumerate(headers, 1):
            print(f"Report {i}:")
            print(f"  UUID: {header.uuid}")
            print(f"  Part Number: {header.part_number}")
            print(f"  Serial Number: {header.serial_number}")
            print(f"  Revision: {header.revision}")
            print(f"  Status: {header.status}")
            print(f"  Start (UTC): {header.start_utc}")
            print(f"  Station: {header.station_name}")
            print(f"  Test Operation: {header.test_operation}")
            print(f"  Operator: {header.operator}")
            print()


if __name__ == "__main__":
    main()