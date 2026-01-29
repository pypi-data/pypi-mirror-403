import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from pylibs.database_manager import get_session_context
from db.schema import Connector, ConnectorStatus


class ConnectorManager:
  
    
    def list_connectors(self) -> List[Dict[str, Any]]:
        
        with get_session_context() as session:
            connectors = session.query(Connector).order_by(Connector.created_at.desc()).all()
            return [self._connector_to_dict(c) for c in connectors]
    
    def get_connector(self, name: str) -> Optional[Dict[str, Any]]:
      
        with get_session_context() as session:
            connector = session.query(Connector).filter(
                Connector.name == name
            ).first()
            
            if not connector:
                return None
            
            return self._connector_to_dict(connector)
    
    def create_connector(
        self,
        name: str,
        provider: str,
        config: Optional[Dict[str, Any]] = None,
        status: str = "ACTIVE"
    ) -> Dict[str, Any]:
       
        with get_session_context() as session:
            # Check if connector with name already exists
            existing = session.query(Connector).filter(
                Connector.name == name
            ).first()
            
            if existing:
                raise ValueError(f"Connector with name '{name}' already exists")
            
            connector = Connector(
                name=name,
                provider=provider,
                config=config or {},
                status=ConnectorStatus[status]
            )
            
            session.add(connector)
            session.flush()
            
            return self._connector_to_dict(connector)
    
    def update_connector(
        self,
        connector_id: str,
        name: Optional[str] = None,
        provider: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
      
        try:
            parsed_id = uuid.UUID(connector_id)
        except ValueError:
            raise ValueError(f"Invalid connector ID format: '{connector_id}'")
        
        with get_session_context() as session:
            connector = session.query(Connector).filter(
                Connector.id == parsed_id
            ).first()
            
            if not connector:
                return None
            
            if name and name != connector.name:
                existing = session.query(Connector).filter(
                    Connector.name == name
                ).first()
                if existing:
                    raise ValueError(f"Connector with name '{name}' already exists")
                connector.name = name
            
            if provider:
                connector.provider = provider
            
            if config is not None:
                connector.config = config
            
            if status:
                connector.status = ConnectorStatus[status]
            
            connector.updated_at = datetime.now(timezone.utc)
            
            return self._connector_to_dict(connector)
    
    def delete_connector(self, connector_id: str) -> bool:
       
        try:
            parsed_id = uuid.UUID(connector_id)
        except ValueError:
            raise ValueError(f"Invalid connector ID format: '{connector_id}'")
        
        with get_session_context() as session:
            connector = session.query(Connector).filter(
                Connector.id == parsed_id
            ).first()
            
            if not connector:
                return False
            
            session.delete(connector)
            return True
    
    def _connector_to_dict(self, connector: Connector) -> Dict[str, Any]:
        """Convert a Connector ORM object to a dictionary."""
        return {
            "id": str(connector.id),
            "name": connector.name,
            "provider": connector.provider,
            "config": connector.config or {},
            "status": connector.status.value if connector.status else "ACTIVE",
            "created_at": connector.created_at.isoformat() if connector.created_at else None,
            "updated_at": connector.updated_at.isoformat() if connector.updated_at else None
        }


# Global connector manager instance (singleton)
_connector_manager: Optional[ConnectorManager] = None


def _get_manager() -> ConnectorManager:
    """Get singleton ConnectorManager instance."""
    global _connector_manager
    if _connector_manager is None:
        _connector_manager = ConnectorManager()
    return _connector_manager
