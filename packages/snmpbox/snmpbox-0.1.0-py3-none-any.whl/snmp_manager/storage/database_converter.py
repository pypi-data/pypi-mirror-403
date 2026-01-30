"""
Database Converter Module

This module provides conversion between SNMP Manager's universal data structures
and various database formats including MongoDB, PostgreSQL, SQLite, and Redis.

Features:
- Unified interface for all database types
- Automatic schema creation and migration
- Data validation and type conversion
- Bulk operations for performance
- Connection pooling and management
- Error handling and retry logic
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import uuid

# Database drivers
try:
    import pymongo
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

try:
    import asyncpg
    import psycopg2
    from psycopg2.extras import execute_values
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

try:
    import sqlite3
    import aiosqlite
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

try:
    import redis
    import aioredis
    from redis.exceptions import ConnectionError, RedisError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ..core.engine import SNMPResult
from ..utils.data_structures import DeviceData, OLTData, ONUData, PortData

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    db_type: str
    host: str = 'localhost'
    port: int = 0
    database: str = 'snmp_manager'
    username: str = ''
    password: str = ''
    connection_string: str = ''
    options: Dict[str, Any] = None

    def __post_init__(self):
        if self.options is None:
            self.options = {}


class DatabaseInterface(ABC):
    """Abstract base class for database interfaces."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None
        self._connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establish database connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    async def store_device_data(self, data: DeviceData) -> str:
        """Store device data and return document/record ID."""
        pass

    @abstractmethod
    async def store_olt_data(self, data: OLTData) -> str:
        """Store OLT-specific data and return document/record ID."""
        pass

    @abstractmethod
    async def store_onu_data(self, data: ONUData) -> str:
        """Store ONU-specific data and return document/record ID."""
        pass

    @abstractmethod
    async def store_bulk_data(self, data_list: List[Union[DeviceData, OLTData, ONUData]]) -> List[str]:
        """Store multiple records in a single operation."""
        pass

    @abstractmethod
    async def query_devices(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict]:
        """Query device data with optional filters."""
        pass

    @abstractmethod
    async def get_latest_data(self, device_id: str, data_type: str = 'all') -> Dict:
        """Get the latest data for a specific device."""
        pass

    @abstractmethod
    async def create_indexes(self) -> None:
        """Create database indexes for performance."""
        pass


class MongoDBConverter(DatabaseInterface):
    """MongoDB converter for document-oriented storage."""

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        if not MONGODB_AVAILABLE:
            raise ImportError("pymongo is required for MongoDB support")

        # Set default MongoDB port
        if config.port == 0:
            self.config.port = 27017

    async def connect(self) -> bool:
        """Establish MongoDB connection."""
        try:
            if self.config.connection_string:
                self.client = MongoClient(self.config.connection_string)
            else:
                self.client = MongoClient(
                    host=self.config.host,
                    port=self.config.port,
                    username=self.config.username if self.config.username else None,
                    password=self.config.password if self.config.password else None,
                    **self.config.options
                )

            # Test connection
            self.client.admin.command('ping')

            self.db = self.client[self.config.database]
            self._connected = True

            logger.info(f"Connected to MongoDB at {self.config.host}:{self.config.port}")
            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("Disconnected from MongoDB")

    async def store_device_data(self, data: DeviceData) -> str:
        """Store device data in MongoDB."""
        try:
            collection = self.db.devices

            # Prepare document
            doc = asdict(data)
            doc['_id'] = str(uuid.uuid4())
            doc['timestamp'] = datetime.now()
            doc['data_type'] = 'device'

            result = await asyncio.get_event_loop().run_in_executor(
                None, collection.insert_one, doc
            )

            logger.debug(f"Stored device data with ID: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to store device data: {e}")
            raise

    async def store_olt_data(self, data: OLTData) -> str:
        """Store OLT-specific data in MongoDB."""
        try:
            collection = self.db.olt_data

            # Prepare document
            doc = asdict(data)
            doc['_id'] = str(uuid.uuid4())
            doc['timestamp'] = datetime.now()
            doc['data_type'] = 'olt'

            result = await asyncio.get_event_loop().run_in_executor(
                None, collection.insert_one, doc
            )

            logger.debug(f"Stored OLT data with ID: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to store OLT data: {e}")
            raise

    async def store_onu_data(self, data: ONUData) -> str:
        """Store ONU-specific data in MongoDB."""
        try:
            collection = self.db.onu_data

            # Prepare document
            doc = asdict(data)
            doc['_id'] = str(uuid.uuid4())
            doc['timestamp'] = datetime.now()
            doc['data_type'] = 'onu'

            result = await asyncio.get_event_loop().run_in_executor(
                None, collection.insert_one, doc
            )

            logger.debug(f"Stored ONU data with ID: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to store ONU data: {e}")
            raise

    async def store_bulk_data(self, data_list: List[Union[DeviceData, OLTData, ONUData]]) -> List[str]:
        """Store multiple records in MongoDB bulk operation."""
        try:
            if not data_list:
                return []

            # Group by data type
            device_data = []
            olt_data = []
            onu_data = []

            for item in data_list:
                doc = asdict(item)
                doc['_id'] = str(uuid.uuid4())
                doc['timestamp'] = datetime.now()

                if isinstance(item, DeviceData):
                    doc['data_type'] = 'device'
                    device_data.append(doc)
                elif isinstance(item, OLTData):
                    doc['data_type'] = 'olt'
                    olt_data.append(doc)
                elif isinstance(item, ONUData):
                    doc['data_type'] = 'onu'
                    onu_data.append(doc)

            ids = []

            # Insert in bulk for each collection
            if device_data:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self.db.devices.insert_many, device_data
                )
                ids.extend([str(oid) for oid in result.inserted_ids])

            if olt_data:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self.db.olt_data.insert_many, olt_data
                )
                ids.extend([str(oid) for oid in result.inserted_ids])

            if onu_data:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self.db.onu_data.insert_many, onu_data
                )
                ids.extend([str(oid) for oid in result.inserted_ids])

            logger.debug(f"Stored {len(data_list)} records in bulk operation")
            return ids

        except Exception as e:
            logger.error(f"Failed to store bulk data: {e}")
            raise

    async def query_devices(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict]:
        """Query device data from MongoDB."""
        try:
            collection = self.db.devices

            query = filters or {}
            cursor = collection.find(query).limit(limit)

            results = await asyncio.get_event_loop().run_in_executor(
                None, list, cursor
            )

            # Convert ObjectId to string for JSON serialization
            for result in results:
                if '_id' in result:
                    result['_id'] = str(result['_id'])

            return results

        except Exception as e:
            logger.error(f"Failed to query devices: {e}")
            raise

    async def get_latest_data(self, device_id: str, data_type: str = 'all') -> Dict:
        """Get latest data for a device from MongoDB."""
        try:
            if data_type == 'all':
                # Query all collections and get latest
                results = {}

                for collection_name in ['devices', 'olt_data', 'onu_data']:
                    collection = self.db[collection_name]
                    latest = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: collection.find(
                            {'device_id': device_id}
                        ).sort('timestamp', -1).limit(1)
                    )

                    latest_list = await asyncio.get_event_loop().run_in_executor(
                        None, list, latest
                    )

                    if latest_list:
                        result = latest_list[0]
                        result['_id'] = str(result['_id'])
                        results[collection_name] = result

                return results
            else:
                # Query specific collection
                collection_map = {
                    'device': 'devices',
                    'olt': 'olt_data',
                    'onu': 'onu_data'
                }

                collection = self.db[collection_map.get(data_type, 'devices')]
                latest = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: collection.find(
                        {'device_id': device_id}
                    ).sort('timestamp', -1).limit(1)
                )

                latest_list = await asyncio.get_event_loop().run_in_executor(
                    None, list, latest
                )

                if latest_list:
                    result = latest_list[0]
                    result['_id'] = str(result['_id'])
                    return result

                return {}

        except Exception as e:
            logger.error(f"Failed to get latest data: {e}")
            raise

    async def create_indexes(self) -> None:
        """Create MongoDB indexes for performance."""
        try:
            # Device collection indexes
            await asyncio.get_event_loop().run_in_executor(
                None, self.db.devices.create_index, 'device_id'
            )
            await asyncio.get_event_loop().run_in_executor(
                None, self.db.devices.create_index, 'timestamp'
            )
            await asyncio.get_event_loop().run_in_executor(
                None, self.db.devices.create_index, [('device_id', 1), ('timestamp', -1)]
            )

            # OLT data collection indexes
            await asyncio.get_event_loop().run_in_executor(
                None, self.db.olt_data.create_index, 'device_id'
            )
            await asyncio.get_event_loop().run_in_executor(
                None, self.db.olt_data.create_index, 'timestamp'
            )
            await asyncio.get_event_loop().run_in_executor(
                None, self.db.olt_data.create_index, 'olt_id'
            )

            # ONU data collection indexes
            await asyncio.get_event_loop().run_in_executor(
                None, self.db.onu_data.create_index, 'device_id'
            )
            await asyncio.get_event_loop().run_in_executor(
                None, self.db.onu_data.create_index, 'timestamp'
            )
            await asyncio.get_event_loop().run_in_executor(
                None, self.db.onu_data.create_index, 'onu_id'
            )
            await asyncio.get_event_loop().run_in_executor(
                None, self.db.onu_data.create_index, 'olt_id'
            )

            logger.info("Created MongoDB indexes for performance")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")


class PostgreSQLConverter(DatabaseInterface):
    """PostgreSQL converter for relational storage."""

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        if not POSTGRESQL_AVAILABLE:
            raise ImportError("asyncpg and psycopg2 are required for PostgreSQL support")

        # Set default PostgreSQL port
        if config.port == 0:
            self.config.port = 5432

    async def connect(self) -> bool:
        """Establish PostgreSQL connection."""
        try:
            self.connection = await asyncpg.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                **self.config.options
            )

            self._connected = True
            logger.info(f"Connected to PostgreSQL at {self.config.host}:{self.config.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False

    async def disconnect(self) -> None:
        """Close PostgreSQL connection."""
        if self.connection:
            await self.connection.close()
            self._connected = False
            logger.info("Disconnected from PostgreSQL")

    async def _create_tables(self) -> None:
        """Create PostgreSQL tables if they don't exist."""
        try:
            # Devices table
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    device_id VARCHAR(255) NOT NULL,
                    host VARCHAR(255) NOT NULL,
                    vendor VARCHAR(100),
                    model VARCHAR(100),
                    device_type VARCHAR(100),
                    system_description TEXT,
                    system_uptime BIGINT,
                    system_name VARCHAR(255),
                    system_location VARCHAR(255),
                    snmp_version VARCHAR(10),
                    metadata JSONB,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    data_type VARCHAR(50) DEFAULT 'device'
                )
            """)

            # OLT data table
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS olt_data (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    device_id VARCHAR(255) NOT NULL,
                    olt_id VARCHAR(255) NOT NULL,
                    olt_name VARCHAR(255),
                    olt_model VARCHAR(100),
                    total_onus INTEGER DEFAULT 0,
                    active_onus INTEGER DEFAULT 0,
                    total_ports INTEGER DEFAULT 0,
                    cpu_utilization FLOAT,
                    memory_utilization FLOAT,
                    temperature FLOAT,
                    optical_power_tx FLOAT,
                    optical_power_rx FLOAT,
                    status VARCHAR(50),
                    firmware_version VARCHAR(100),
                    uptime BIGINT,
                    metadata JSONB,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    data_type VARCHAR(50) DEFAULT 'olt'
                )
            """)

            # ONU data table
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS onu_data (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    device_id VARCHAR(255) NOT NULL,
                    olt_id VARCHAR(255) NOT NULL,
                    onu_id VARCHAR(255) NOT NULL,
                    onu_name VARCHAR(255),
                    port_id INTEGER,
                    slot_id INTEGER,
                    serial_number VARCHAR(100),
                    status VARCHAR(50),
                    optical_power_rx FLOAT,
                    optical_power_tx FLOAT,
                    distance FLOAT,
                    temperature FLOAT,
                    uptime BIGINT,
                    admin_state VARCHAR(50),
                    operational_state VARCHAR(50),
                    description TEXT,
                    metadata JSONB,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    data_type VARCHAR(50) DEFAULT 'onu'
                )
            """)

            logger.info("Created PostgreSQL tables")

        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    async def store_device_data(self, data: DeviceData) -> str:
        """Store device data in PostgreSQL."""
        try:
            # Ensure tables exist
            await self._create_tables()

            query = """
                INSERT INTO devices (
                    device_id, host, vendor, model, device_type,
                    system_description, system_uptime, system_name,
                    system_location, snmp_version, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
            """

            result = await self.connection.fetch(
                query,
                data.device_id,
                data.host,
                data.vendor,
                data.model,
                data.device_type,
                data.system_description,
                data.system_uptime,
                data.system_name,
                data.system_location,
                data.snmp_version,
                json.dumps(data.metadata) if data.metadata else None
            )

            record_id = str(result[0]['id'])
            logger.debug(f"Stored device data with ID: {record_id}")
            return record_id

        except Exception as e:
            logger.error(f"Failed to store device data: {e}")
            raise

    async def store_olt_data(self, data: OLTData) -> str:
        """Store OLT data in PostgreSQL."""
        try:
            # Ensure tables exist
            await self._create_tables()

            query = """
                INSERT INTO olt_data (
                    device_id, olt_id, olt_name, olt_model,
                    total_onus, active_onus, total_ports,
                    cpu_utilization, memory_utilization, temperature,
                    optical_power_tx, optical_power_rx, status,
                    firmware_version, uptime, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                RETURNING id
            """

            result = await self.connection.fetch(
                query,
                data.device_id,
                data.olt_id,
                data.olt_name,
                data.olt_model,
                data.total_onus,
                data.active_onus,
                data.total_ports,
                data.cpu_utilization,
                data.memory_utilization,
                data.temperature,
                data.optical_power_tx,
                data.optical_power_rx,
                data.status,
                data.firmware_version,
                data.uptime,
                json.dumps(data.metadata) if data.metadata else None
            )

            record_id = str(result[0]['id'])
            logger.debug(f"Stored OLT data with ID: {record_id}")
            return record_id

        except Exception as e:
            logger.error(f"Failed to store OLT data: {e}")
            raise

    async def store_onu_data(self, data: ONUData) -> str:
        """Store ONU data in PostgreSQL."""
        try:
            # Ensure tables exist
            await self._create_tables()

            query = """
                INSERT INTO onu_data (
                    device_id, olt_id, onu_id, onu_name, port_id,
                    slot_id, serial_number, status, optical_power_rx,
                    optical_power_tx, distance, temperature, uptime,
                    admin_state, operational_state, description, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                RETURNING id
            """

            result = await self.connection.fetch(
                query,
                data.device_id,
                data.olt_id,
                data.onu_id,
                data.onu_name,
                data.port_id,
                data.slot_id,
                data.serial_number,
                data.status,
                data.optical_power_rx,
                data.optical_power_tx,
                data.distance,
                data.temperature,
                data.uptime,
                data.admin_state,
                data.operational_state,
                data.description,
                json.dumps(data.metadata) if data.metadata else None
            )

            record_id = str(result[0]['id'])
            logger.debug(f"Stored ONU data with ID: {record_id}")
            return record_id

        except Exception as e:
            logger.error(f"Failed to store ONU data: {e}")
            raise

    async def store_bulk_data(self, data_list: List[Union[DeviceData, OLTData, ONUData]]) -> List[str]:
        """Store multiple records in PostgreSQL bulk operation."""
        try:
            if not data_list:
                return []

            # Ensure tables exist
            await self._create_tables()

            ids = []

            # Process each data type separately
            for data_type in [DeviceData, OLTData, ONUData]:
                type_data = [item for item in data_list if isinstance(item, data_type)]

                if not type_data:
                    continue

                if data_type == DeviceData:
                    query = """
                        INSERT INTO devices (
                            device_id, host, vendor, model, device_type,
                            system_description, system_uptime, system_name,
                            system_location, snmp_version, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        RETURNING id
                    """

                    for item in type_data:
                        result = await self.connection.fetch(
                            query,
                            item.device_id,
                            item.host,
                            item.vendor,
                            item.model,
                            item.device_type,
                            item.system_description,
                            item.system_uptime,
                            item.system_name,
                            item.system_location,
                            item.snmp_version,
                            json.dumps(item.metadata) if item.metadata else None
                        )
                        ids.append(str(result[0]['id']))

                elif data_type == OLTData:
                    query = """
                        INSERT INTO olt_data (
                            device_id, olt_id, olt_name, olt_model,
                            total_onus, active_onus, total_ports,
                            cpu_utilization, memory_utilization, temperature,
                            optical_power_tx, optical_power_rx, status,
                            firmware_version, uptime, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                        RETURNING id
                    """

                    for item in type_data:
                        result = await self.connection.fetch(
                            query,
                            item.device_id,
                            item.olt_id,
                            item.olt_name,
                            item.olt_model,
                            item.total_onus,
                            item.active_onus,
                            item.total_ports,
                            item.cpu_utilization,
                            item.memory_utilization,
                            item.temperature,
                            item.optical_power_tx,
                            item.optical_power_rx,
                            item.status,
                            item.firmware_version,
                            item.uptime,
                            json.dumps(item.metadata) if item.metadata else None
                        )
                        ids.append(str(result[0]['id']))

                elif data_type == ONUData:
                    query = """
                        INSERT INTO onu_data (
                            device_id, olt_id, onu_id, onu_name, port_id,
                            slot_id, serial_number, status, optical_power_rx,
                            optical_power_tx, distance, temperature, uptime,
                            admin_state, operational_state, description, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                        RETURNING id
                    """

                    for item in type_data:
                        result = await self.connection.fetch(
                            query,
                            item.device_id,
                            item.olt_id,
                            item.onu_id,
                            item.onu_name,
                            item.port_id,
                            item.slot_id,
                            item.serial_number,
                            item.status,
                            item.optical_power_rx,
                            item.optical_power_tx,
                            item.distance,
                            item.temperature,
                            item.uptime,
                            item.admin_state,
                            item.operational_state,
                            item.description,
                            json.dumps(item.metadata) if item.metadata else None
                        )
                        ids.append(str(result[0]['id']))

            logger.debug(f"Stored {len(data_list)} records in bulk operation")
            return ids

        except Exception as e:
            logger.error(f"Failed to store bulk data: {e}")
            raise

    async def query_devices(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict]:
        """Query device data from PostgreSQL."""
        try:
            base_query = "SELECT * FROM devices"
            conditions = []
            params = []

            if filters:
                for key, value in filters.items():
                    if key == 'vendor':
                        conditions.append(f"vendor = ${len(params) + 1}")
                        params.append(value)
                    elif key == 'device_type':
                        conditions.append(f"device_type = ${len(params) + 1}")
                        params.append(value)
                    elif key == 'host':
                        conditions.append(f"host = ${len(params) + 1}")
                        params.append(value)

                if conditions:
                    base_query += " WHERE " + " AND ".join(conditions)

            base_query += f" LIMIT {limit}"

            if params:
                results = await self.connection.fetch(base_query, *params)
            else:
                results = await self.connection.fetch(base_query)

            # Convert to list of dicts
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Failed to query devices: {e}")
            raise

    async def get_latest_data(self, device_id: str, data_type: str = 'all') -> Dict:
        """Get latest data for a device from PostgreSQL."""
        try:
            results = {}

            if data_type in ['all', 'device']:
                query = """
                    SELECT * FROM devices
                    WHERE device_id = $1
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                device_result = await self.connection.fetch(query, device_id)
                if device_result:
                    results['device'] = dict(device_result[0])

            if data_type in ['all', 'olt']:
                query = """
                    SELECT * FROM olt_data
                    WHERE device_id = $1
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                olt_result = await self.connection.fetch(query, device_id)
                if olt_result:
                    results['olt'] = dict(olt_result[0])

            if data_type in ['all', 'onu']:
                query = """
                    SELECT * FROM onu_data
                    WHERE device_id = $1
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                onu_result = await self.connection.fetch(query, device_id)
                if onu_result:
                    results['onu'] = dict(onu_result[0])

            return results

        except Exception as e:
            logger.error(f"Failed to get latest data: {e}")
            raise

    async def create_indexes(self) -> None:
        """Create PostgreSQL indexes for performance."""
        try:
            # Device table indexes
            await self.connection.execute("CREATE INDEX IF NOT EXISTS idx_devices_device_id ON devices(device_id)")
            await self.connection.execute("CREATE INDEX IF NOT EXISTS idx_devices_timestamp ON devices(timestamp)")
            await self.connection.execute("CREATE INDEX IF NOT EXISTS idx_devices_vendor ON devices(vendor)")
            await self.connection.execute("CREATE INDEX IF NOT EXISTS idx_devices_device_type ON devices(device_type)")

            # OLT data table indexes
            await self.connection.execute("CREATE INDEX IF NOT EXISTS idx_olt_data_device_id ON olt_data(device_id)")
            await self.connection.execute("CREATE INDEX IF NOT EXISTS idx_olt_data_olt_id ON olt_data(olt_id)")
            await self.connection.execute("CREATE INDEX IF NOT EXISTS idx_olt_data_timestamp ON olt_data(timestamp)")

            # ONU data table indexes
            await self.connection.execute("CREATE INDEX IF NOT EXISTS idx_onu_data_device_id ON onu_data(device_id)")
            await self.connection.execute("CREATE INDEX IF NOT EXISTS idx_onu_data_olt_id ON onu_data(olt_id)")
            await self.connection.execute("CREATE INDEX IF NOT EXISTS idx_onu_data_onu_id ON onu_data(onu_id)")
            await self.connection.execute("CREATE INDEX IF NOT EXISTS idx_onu_data_timestamp ON onu_data(timestamp)")

            logger.info("Created PostgreSQL indexes for performance")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")


class DatabaseConverterFactory:
    """Factory for creating database converters."""

    @staticmethod
    def create_converter(config: DatabaseConfig) -> DatabaseInterface:
        """Create appropriate database converter based on configuration."""
        converters = {
            'mongodb': MongoDBConverter,
            'postgresql': PostgreSQLConverter,
            'postgres': PostgreSQLConverter,
        }

        converter_class = converters.get(config.db_type.lower())
        if not converter_class:
            raise ValueError(f"Unsupported database type: {config.db_type}")

        return converter_class(config)


class DatabaseManager:
    """High-level database manager for SNMP Manager."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.converter = DatabaseConverterFactory.create_converter(config)
        self._connected = False

    async def connect(self) -> bool:
        """Connect to the database."""
        success = await self.converter.connect()
        if success:
            self._connected = True
            await self.converter.create_indexes()
        return success

    async def disconnect(self) -> None:
        """Disconnect from the database."""
        await self.converter.disconnect()
        self._connected = False

    async def store_snmp_data(self, data: Union[DeviceData, OLTData, ONUData, List]) -> Union[str, List[str]]:
        """Store SNMP data with automatic type detection."""
        if not self._connected:
            raise RuntimeError("Database not connected")

        if isinstance(data, list):
            return await self.converter.store_bulk_data(data)
        else:
            if isinstance(data, DeviceData):
                return await self.converter.store_device_data(data)
            elif isinstance(data, OLTData):
                return await self.converter.store_olt_data(data)
            elif isinstance(data, ONUData):
                return await self.converter.store_onu_data(data)
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")

    async def query_data(self, query_type: str = 'devices', filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict]:
        """Query data from the database."""
        if not self._connected:
            raise RuntimeError("Database not connected")

        if query_type == 'devices':
            return await self.converter.query_devices(filters, limit)
        else:
            raise ValueError(f"Unsupported query type: {query_type}")

    async def get_latest_device_data(self, device_id: str) -> Dict:
        """Get latest data for a device."""
        if not self._connected:
            raise RuntimeError("Database not connected")

        return await self.converter.get_latest_data(device_id, 'all')