"""
constec.db.models - All Django models for the Constec platform.

Usage:
    from constec.db.models import Company, User, Session, Message

    # ERP models (from erp schema, no prefix needed):
    from constec.db.models import System, Connection, Entity

    # Or import from specific modules:
    from constec.db.models.organization import Organization
    from constec.db.models.erp import System, Connection
    from constec.db.models.erp_entity import Role, Entity, EntityAuth
"""

# Base
from .base import UUIDModel

# Core models (core schema)
from .organization import Organization, OrganizationRole, OrganizationUser
from .company import Company
from .user import User, UserRole, UserCompanyAccess
from .person import Person
from .group import UserGroup
from .contact import ContactType, Contact, PersonContact
from .tag import TagCategory, PersonTag, PersonTagged
from .module import Module, CompanyModule, OrganizationModule

# ERP models (erp schema)
from .erp import System, CompanySystem, Connection
from .erp_entity import Role, Entity, EntityAuth

# Aliases for backward compatibility
ErpSystem = System
CompanyErpSystem = CompanySystem
ErpConnection = Connection
ErpRole = Role
ErpEntity = Entity

# Constancia models (constancia schema)
from .flow import FlowTemplate, Flow
from .session import Session, Message


__all__ = [
    # Base
    'UUIDModel',
    # Organization
    'Organization',
    'OrganizationRole',
    'OrganizationUser',
    # Company
    'Company',
    # User
    'User',
    'UserRole',
    'UserCompanyAccess',
    # Person
    'Person',
    # Group
    'UserGroup',
    # Contact
    'ContactType',
    'Contact',
    'PersonContact',
    # Tag
    'TagCategory',
    'PersonTag',
    'PersonTagged',
    # Module
    'Module',
    'CompanyModule',
    'OrganizationModule',
    # ERP (erp schema)
    'System',
    'CompanySystem',
    'Connection',
    'Role',
    'Entity',
    'EntityAuth',
    # ERP aliases (backward compatibility)
    'ErpSystem',
    'CompanyErpSystem',
    'ErpConnection',
    'ErpRole',
    'ErpEntity',
    # Constancia (constancia schema)
    'FlowTemplate',
    'Flow',
    'Session',
    'Message',
]
