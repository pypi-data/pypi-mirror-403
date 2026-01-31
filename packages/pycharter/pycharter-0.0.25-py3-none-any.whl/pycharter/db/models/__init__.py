"""
SQLAlchemy Models for PyCharter Database Schema

Core models based on template data structure:
1. metadata_record - Comprehensive metadata storage
2. coercion_rule - Data type coercion rules
3. validation_rule - Business logic validation rules
4. data_contract - Central table linking all components
5. schema - JSON Schema definitions
6. owner - Ownership information
7. governance_rule - Governance rules
8. system - System information
9. domain - Domain information

Naming convention:
- Tables: plural (schemas, coercion_rules, etc.)
- Files: singular (schema.py, coercion_rule.py, etc.)
- Classes: singular with Model suffix (SchemaModel, CoercionRuleModel, etc.)
"""

from pycharter.db.models.base import Base
from pycharter.db.models.coercion_rule import CoercionRuleModel

# GovernanceRuleModel removed - governance rules are stored as JSON in metadata_records
from pycharter.db.models.data_contract import DataContractModel, DataContractTag
from pycharter.db.models.data_dependency import DataDependencyModel
from pycharter.db.models.data_feed import DataFeedModel
from pycharter.db.models.domain import DomainModel
from pycharter.db.models.environment import EnvironmentModel
from pycharter.db.models.storage_location import StorageLocationModel
from pycharter.db.models.compliance_framework import ComplianceFrameworkModel
from pycharter.db.models.tag import TagModel
from pycharter.db.models.api_endpoint import APIEndpointModel
from pycharter.db.models.metadata_record import (
    MetadataRecordBusinessOwner,
    MetadataRecordBUSME,
    MetadataRecordComplianceFramework,
    MetadataRecordDataFeed,
    MetadataRecordDomain,
    MetadataRecordEnvironment,
    MetadataRecordITApplicationOwner,
    MetadataRecordITSME,
    MetadataRecordModel,
    MetadataRecordStorageLocation,
    MetadataRecordSupportLead,
    MetadataRecordSystemPull,
    MetadataRecordSystemPush,
    MetadataRecordSystemSource,
)
from pycharter.db.models.owner import OwnerModel
from pycharter.db.models.dlq import DeadLetterQueueModel
from pycharter.db.models.quality_metric import QualityMetricModel
from pycharter.db.models.quality_violation import QualityViolationModel
from pycharter.db.models.schema import SchemaModel
from pycharter.db.models.system import SystemModel
from pycharter.db.models.validation_rule import ValidationRuleModel

__all__ = [
    "Base",
    # Core component models
    "SchemaModel",
    "CoercionRuleModel",
    "ValidationRuleModel",
    "MetadataRecordModel",
    "OwnerModel",
    # GovernanceRuleModel removed - governance rules stored in metadata_records
    "DataContractModel",
    # Entity models
    "SystemModel",
    "DomainModel",
    # New Tier 2 & 3 entities
    "DataDependencyModel",
    "EnvironmentModel",
    "DataFeedModel",
    "StorageLocationModel",
    "ComplianceFrameworkModel",
    "TagModel",
    "APIEndpointModel",
    # Quality assurance models
    "QualityMetricModel",
    "QualityViolationModel",
    # Dead Letter Queue
    "DeadLetterQueueModel",
    # Join tables - Systems and Domains
    "MetadataRecordSystemPull",
    "MetadataRecordSystemPush",
    "MetadataRecordSystemSource",
    "MetadataRecordDomain",
    # Join tables - New entities
    "MetadataRecordEnvironment",
    "MetadataRecordDataFeed",
    "MetadataRecordStorageLocation",
    "MetadataRecordComplianceFramework",
    "DataContractTag",
    # Join tables - Owners
    "MetadataRecordBusinessOwner",
    "MetadataRecordBUSME",
    "MetadataRecordITApplicationOwner",
    "MetadataRecordITSME",
    "MetadataRecordSupportLead",
]
