"""
Adapter registry for ESG data ingestion.

Maps source_type strings to their corresponding adapter classes.
"""
from apps.ingestion.adapters.sap import SAPProcurementAdapter
from apps.ingestion.adapters.travel import CorporateTravelAdapter
from apps.ingestion.adapters.utility import UtilityElectricityAdapter

ADAPTER_REGISTRY = {
    'sap_procurement': SAPProcurementAdapter,
    'utility_electricity': UtilityElectricityAdapter,
    'corporate_travel': CorporateTravelAdapter,
}

__all__ = [
    'ADAPTER_REGISTRY',
    'SAPProcurementAdapter',
    'UtilityElectricityAdapter',
    'CorporateTravelAdapter',
]
