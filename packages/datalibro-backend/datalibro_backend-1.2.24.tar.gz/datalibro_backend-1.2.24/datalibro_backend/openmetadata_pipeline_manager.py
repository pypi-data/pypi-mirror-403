#!/usr/bin/env python3
"""
OpenMetadata Pipeline Manager

A Python library for managing OpenMetadata pipelines and lineage tracking with Spark integration.
Supports automatic Pipeline Service and Pipeline entity creation, data lineage management,
and OpenLineage integration for comprehensive data governance.

Author: OpenMetadata Pipeline Manager Team
License: Apache License 2.0
"""

import os
import time
import uuid
import re
import yaml
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum

# Pipeline状态枚举
class PipelineBusinessStatus(Enum):
    """Pipeline业务状态枚举"""
    TESTING = "测试中"      # 在测试环境验证中
    ONLINE = "已上线"       # 生产环境运行中  
    OFFLINE = "已下线"      # 已停用/下线
    
    def __str__(self):
        return self.value

# 尝试导入OpenMetadata依赖，如果失败则提供降级模式
OPENMETADATA_AVAILABLE = False
try:
    from metadata.generated.schema.entity.services.connections.metadata.openMetadataConnection import (
        OpenMetadataConnection,
    )
    from metadata.generated.schema.security.client.openMetadataJWTClientConfig import (
        OpenMetadataJWTClientConfig,
    )
    from metadata.ingestion.ometa.ometa_api import OpenMetadata
    from metadata.generated.schema.api.services.createPipelineService import CreatePipelineServiceRequest
    from metadata.generated.schema.entity.services.pipelineService import PipelineServiceType
    from metadata.generated.schema.entity.services.connections.pipeline.customPipelineConnection import CustomPipelineConnection
    from metadata.generated.schema.entity.services.pipelineService import PipelineConnection
    from metadata.generated.schema.api.data.createPipeline import CreatePipelineRequest
    from metadata.generated.schema.entity.data.pipeline import Task
    from metadata.generated.schema.type.entityReference import EntityReference
    from metadata.generated.schema.entity.teams.user import User
    from metadata.generated.schema.api.teams.createUser import CreateUserRequest
    from metadata.generated.schema.api.lineage.addLineage import AddLineageRequest
    from metadata.generated.schema.type.entityLineage import EntitiesEdge, LineageDetails
    from metadata.generated.schema.entity.data.table import Table
    from metadata.generated.schema.entity.data.pipeline import Pipeline
    from metadata.generated.schema.entity.services.pipelineService import PipelineService
    OPENMETADATA_AVAILABLE = True
    print("✅ OpenMetadata 依赖加载成功")
except ImportError as e:
    print(f"⚠️ OpenMetadata 依赖加载失败: {e}")
    print("📝 将使用简化模式，部分功能不可用")
    print("💡 要使用完整功能，请解决依赖问题")
    
    # 创建占位符类以保持API兼容性
    class MockOpenMetadata:
        def __init__(self, *args, **kwargs):
            pass
    
    class MockPipeline:
        def __init__(self, name="mock-pipeline"):
            self.name = name
            self.id = "mock-id"
            self.fullyQualifiedName = f"mock-service.{name}"
    
    # 设置占位符
    OpenMetadata = MockOpenMetadata
    Pipeline = MockPipeline


@dataclass
class PipelineConfig:
    """Pipeline configuration class"""
    name: str
    display_name: str
    description: str
    service_name: str
    tasks: Optional[List[Dict[str, Any]]] = None


@dataclass
class OwnerConfig:
    """Owner configuration class"""
    name: str
    email: str
    display_name: Optional[str] = None
    is_admin: bool = False


@dataclass
class OpenLineageConfig:
    """OpenLineage integration configuration"""
    namespace: str = "default-namespace"
    parent_job_name: str = "data-pipeline"
    spark_packages: str = "io.openlineage:openlineage-spark:1.7.0"
    spark_listener: str = "io.openlineage.spark.agent.OpenLineageSparkListener"


def load_openmetadata_config(config_file: str = "cfg.yaml", config_section: str = "openmetadata_test") -> Dict[str, Any]:
    """
    从cfg.yaml文件加载OpenMetadata配置，支持多环境配置
    
    Args:
        config_file: 配置文件路径，默认为cfg.yaml
        config_section: 配置节名称，默认为openmetadata_test
                       可选值: openmetadata_test, openmetadata_prod
    """
    try:
        # 完全复用get_tidb_config的读取逻辑
        with open(config_file, "r") as file:
            all_configs = yaml.safe_load(file)
        
        # 与get_tidb_config完全一致的错误处理
        if config_section not in all_configs:
            raise ValueError(f"配置名称 '{config_section}' 在cfg.yaml中不存在")
        
        config = all_configs[config_section]
        
        # 基础验证 - 适配新的配置字段名
        if 'host' not in config or not config['host']:
            raise ValueError("必需的配置项 'host' 缺失或为空")
        if 'token' not in config or not config['token']:
            raise ValueError("必需的配置项 'token' 缺失或为空")
        
        # 转换为标准格式
        standardized_config = {
            'host': config['host'],
            'jwt_token': config['token'],  # token -> jwt_token
        }
        
        # 自动修正host格式
        if not standardized_config['host'].endswith('/api'):
            standardized_config['host'] = standardized_config['host'].rstrip('/') + '/api'
        
        # 处理owner配置
        if all(key in config for key in ['pipeline_owner_name', 'pipeline_owner_email']):
            standardized_config['owner'] = {
                'name': config['pipeline_owner_name'],
                'email': config['pipeline_owner_email'],
                'display_name': config.get('pipeline_owner_display_name', config['pipeline_owner_name']),
                'is_admin': False
            }
        
        print(f"✅ 成功加载配置文件: {config_file} [{config_section}]")
        print(f"📋 OpenMetadata Host: {standardized_config['host']}")
        if 'owner' in standardized_config:
            print(f"👤 Pipeline Owner: {standardized_config['owner']['name']} ({standardized_config['owner']['email']})")
        
        return standardized_config
    
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        print(f"💡 请检查cfg.yaml中是否存在 '{config_section}' 配置节")
        return {
            'host': 'http://localhost:8585/api',
            'jwt_token': '',
            'owner': {'name': 'admin', 'email': 'admin@company.com', 'display_name': 'Admin'}
        }


class OpenMetadataPipelineManager:
    """
    OpenMetadata Pipeline Manager
    
    A comprehensive manager for OpenMetadata pipelines, services, and lineage tracking
    with built-in Spark OpenLineage integration.
    
    Features:
    - Automatic Pipeline Service creation and management
    - Pipeline entity creation with customizable tasks
    - Data lineage tracking and management
    - User management and ownership assignment
    - Spark OpenLineage integration
    - Comprehensive error handling and logging
    
    Example:
        >>> config = {
        ...     'host': 'http://localhost:8585/api',
        ...     'jwt_token': 'your-jwt-token'
        ... }
        >>> manager = OpenMetadataPipelineManager(config)
        >>> 
        >>> # Create pipeline with lineage
        >>> pipeline_config = PipelineConfig(
        ...     name="data-processing-pipeline",
        ...     display_name="Data Processing Pipeline",
        ...     description="Processes raw data into analytics-ready format",
        ...     service_name="spark-pipeline-service"
        ... )
        >>> 
        >>> owner_config = OwnerConfig(
        ...     name="john.doe",
        ...     email="john.doe@company.com",
        ...     display_name="John Doe"
        ... )
        >>> 
        >>> pipeline = manager.create_complete_pipeline(
        ...     pipeline_config=pipeline_config,
        ...     owner_config=owner_config
        ... )
        >>> 
        >>> # Add data lineage
        >>> manager.add_table_lineage(
        ...     from_table_fqn="source.database.table1",
        ...     to_table_fqn="target.database.table2",
        ...     pipeline_fqn=pipeline.fullyQualifiedName
        ... )
    """
    
    def __init__(
        self,
        openmetadata_config: Optional[Dict[str, Any]] = None,
        openlineage_config: Optional[OpenLineageConfig] = None,
        enable_logging: bool = True,
        config_file: str = "cfg.yaml",
        config_section: str = "openmetadata_test"
    ):
        """
        Initialize OpenMetadata Pipeline Manager
        
        Args:
            openmetadata_config: OpenMetadata connection configuration (可选，如果不提供将从cfg.yaml读取)
                Required keys:
                - 'host': OpenMetadata server URL (e.g., 'http://localhost:8585/api')
                - 'jwt_token': JWT authentication token
                Optional keys:
                - 'auth_provider': Authentication provider (default: 'openmetadata')
                - 'verify_ssl': SSL verification (default: True)
            openlineage_config: OpenLineage configuration for Spark integration
            enable_logging: Enable console logging (default: True)
            config_file: 配置文件路径 (default: 'cfg.yaml')
            config_section: 配置节名称 (default: 'openmetadata_test')
                           可选值: 'openmetadata_test', 'openmetadata_prod'
        """
        # 如果没有提供配置，从cfg.yaml读取
        if openmetadata_config is None:
            self.config = load_openmetadata_config(config_file, config_section)
        else:
            self.config = openmetadata_config
            
        # 处理OpenLineage配置
        if openlineage_config is None and 'openlineage' in self.config:
            ol_config = self.config['openlineage']
            self.openlineage_config = OpenLineageConfig(
                namespace=ol_config.get('namespace', 'default-namespace'),
                parent_job_name=ol_config.get('parent_job_name', 'data-pipeline'),
                spark_packages=ol_config.get('spark_packages', 'io.openlineage:openlineage-spark:1.7.0'),
                spark_listener=ol_config.get('spark_listener', 'io.openlineage.spark.agent.OpenLineageSparkListener')
            )
        else:
            self.openlineage_config = openlineage_config or OpenLineageConfig()
            
        self.enable_logging = enable_logging
        self.metadata = None
        self.run_id = self._generate_run_id()
        self.current_pipeline = None  # 存储当前创建的pipeline
        
        # Initialize OpenMetadata connection
        self._initialize_connection()
    
    def _log(self, message: str, level: str = "INFO"):
        """Internal logging method"""
        if self.enable_logging:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def _generate_run_id(self) -> str:
        """Generate unique run ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"pipeline-run-{timestamp}-{str(uuid.uuid4())[:8]}"
    
    def _initialize_connection(self):
        """Initialize OpenMetadata connection"""
        if not OPENMETADATA_AVAILABLE:
            self._log("⚠️ OpenMetadata 依赖不可用，使用简化模式")
            self.metadata = None
            return
            
        try:
            # Extract configuration with defaults
            host_port = self.config.get('host', 'http://localhost:8585/api')
            jwt_token = self.config.get('jwt_token')
            auth_provider = self.config.get('auth_provider', 'openmetadata')
            
            if not jwt_token:
                raise ValueError("JWT token is required for OpenMetadata connection")
            
            # Create OpenMetadata connection
            server_config = OpenMetadataConnection(
                hostPort=host_port,
                authProvider=auth_provider,
                securityConfig=OpenMetadataJWTClientConfig(jwtToken=jwt_token),
            )
            
            self.metadata = OpenMetadata(server_config)
            self._log(f"✅ OpenMetadata connection established successfully")
            self._log(f"📋 Pipeline Run ID: {self.run_id}")
            
        except Exception as e:
            self._log(f"❌ OpenMetadata connection failed: {e}", "ERROR")
            self._log("📝 将继续使用简化模式")
            self.metadata = None
    
    def _extract_uuid(self, obj: Any) -> str:
        """Extract UUID string from OpenMetadata objects"""
        if hasattr(obj, '__root__'):
            uuid_str = str(obj.__root__)
        else:
            uuid_str = str(obj)
        
        # Handle various UUID formats
        if 'root=UUID(' in uuid_str:
            match = re.search(r"root=UUID\('([^']+)'\)", uuid_str)
            if match:
                return match.group(1)
        elif 'UUID(' in uuid_str:
            match = re.search(r"UUID\('([^']+)'\)", uuid_str)
            if match:
                return match.group(1)
        
        return uuid_str.replace("root=", "").replace("'", "")
    
    def _clean_name_format(self, name_obj: Any) -> str:
        """Clean name format from OpenMetadata objects"""
        name_str = name_obj.__root__ if hasattr(name_obj, '__root__') else str(name_obj)
        
        if 'root=' in str(name_str):
            match = re.search(r"root='([^']+)'", str(name_str))
            if match:
                return match.group(1)
            else:
                return str(name_str).replace("root=", "").replace("'", "")
        
        return str(name_str)
    
    def get_or_create_user(self, owner_config: OwnerConfig) -> Optional[User]:
        """
        Get or create user in OpenMetadata
        
        Args:
            owner_config: User configuration
        
        Returns:
            User object or None if failed
        """
        if not self.metadata:
            self._log("❌ OpenMetadata connection not available", "ERROR")
            return None
        
        try:
            # First, let's diagnose what users exist and their formats
            self._log(f"🔍 Diagnosing user system for: {owner_config.email}")
            
            try:
                users = self.metadata.list_entities(entity=User, limit=100)  # Get more users
                self._log(f"📋 Found {len(users.entities) if hasattr(users, 'entities') and users.entities else 0} total users")
                
                if hasattr(users, 'entities') and users.entities:
                    for i, existing_user in enumerate(users.entities):  # Show all users
                        try:
                            user_name = self._clean_name_format(existing_user.name) if hasattr(existing_user, 'name') else 'NO_NAME'
                            user_email = existing_user.email if hasattr(existing_user, 'email') else 'NO_EMAIL'
                            user_id = self._extract_uuid(existing_user.id) if hasattr(existing_user, 'id') else 'NO_ID'
                            self._log(f"  User {i+1}: name='{user_name}', email='{user_email}', id='{user_id}'")
                            
                            # Check if this is our target user by email (handle root= prefix)
                            if user_email == owner_config.email or user_email == f"root={owner_config.email}":
                                self._log(f"🎯 Found target user by email match!")
                                return existing_user
                            
                            # Also check by name match (including partial matches)
                            if (user_name == owner_config.name or 
                                user_name == owner_config.display_name or
                                user_name.startswith(owner_config.name) or
                                owner_config.name in user_name):
                                self._log(f"🎯 Found target user by name match!")
                                return existing_user
                        except Exception as debug_error:
                            self._log(f"  User {i+1}: Could not parse user info: {debug_error}")
                
                # If we didn't find by email, try by name
                for existing_user in users.entities:
                    try:
                        if hasattr(existing_user, 'name'):
                            user_name = self._clean_name_format(existing_user.name)
                            if user_name == owner_config.name:
                                self._log(f"🎯 Found target user by name match!")
                                return existing_user
                    except Exception as name_check_error:
                        continue
                        
            except Exception as list_error:
                self._log(f"⚠️ User listing failed: {list_error}", "WARNING")
            
            # If we still haven't found the user, try direct lookup
            try:
                user = self.metadata.get_by_name(entity=User, fqn=owner_config.name)
                if user:
                    self._log(f"🎯 Found user by direct lookup: {user}")
                    return user
            except Exception as direct_error:
                self._log(f"⚠️ Direct user lookup failed: {direct_error}", "WARNING")
                
            self._log(f"❌ Could not find user {owner_config.name} ({owner_config.email})", "ERROR")
            return None
            
        except Exception as e:
            self._log(f"❌ User retrieval failed: {e}", "ERROR")
            return None
    
    def create_pipeline_service(self, service_name: str, service_description: Optional[str] = None) -> Optional[str]:
        """
        Create or get Pipeline Service
        
        Args:
            service_name: Name of the pipeline service
            service_description: Optional description
        
        Returns:
            Service ID or None if failed
        """
        if not self.metadata:
            self._log("❌ OpenMetadata connection not available", "ERROR")
            return None
        
        try:
            # Try to get existing service first
            try:
                existing_service = self.metadata.get_by_name(entity=PipelineService, fqn=service_name)
                service_id = self._extract_uuid(existing_service.id)
                self._log(f"🔧 Found existing Pipeline Service: {self._clean_name_format(existing_service.name)}")
                return service_id
            except:
                pass
            
            # Create new service
            description = service_description or f"Pipeline service for {service_name}"
            
            # Create proper PipelineConnection structure
            custom_config = CustomPipelineConnection(
                type="CustomPipeline",
                sourcePythonClass=f"{service_name.replace('-', '_')}_service"
            )
            
            pipeline_connection = PipelineConnection(config=custom_config)
            
            service_request = CreatePipelineServiceRequest(
                name=service_name,
                displayName=service_name.replace('-', ' ').title(),
                description=description,
                serviceType=PipelineServiceType.CustomPipeline,
                connection=pipeline_connection
            )
            
            service = self.metadata.create_or_update(service_request)
            service_id = self._extract_uuid(service.id)
            
            self._log(f"🔧 Created Pipeline Service: {self._clean_name_format(service.name)} (ID: {service_id})")
            return service_id
            
        except Exception as e:
            self._log(f"❌ Pipeline Service creation failed: {e}", "ERROR")
            return None
    
    def create_pipeline_entity(
        self,
        pipeline_config: PipelineConfig,
        owner_config: Optional[OwnerConfig] = None
    ) -> Optional[Pipeline]:
        """
        Create Pipeline entity
        
        Args:
            pipeline_config: Pipeline configuration
            owner_config: Optional owner configuration
        
        Returns:
            Pipeline object or None if failed
        """
        if not OPENMETADATA_AVAILABLE:
            self._log("📝 简化模式：创建模拟Pipeline对象")
            mock_pipeline = Pipeline(name=pipeline_config.name)
            self.current_pipeline = mock_pipeline
            self._log(f"🚀 模拟Pipeline创建成功: {pipeline_config.name}")
            return mock_pipeline
            
        if not self.metadata:
            self._log("❌ OpenMetadata connection not available", "ERROR")
            return None
        
        # First check if pipeline already exists
        try:
            service_fqn = pipeline_config.service_name
            pipeline_fqn = f"{service_fqn}.{pipeline_config.name}"
            existing_pipeline = self.metadata.get_by_name(entity=Pipeline, fqn=pipeline_fqn)
            if existing_pipeline:
                self._log(f"📋 Found existing Pipeline: {self._clean_name_format(existing_pipeline.name)}")
                self.current_pipeline = existing_pipeline
                
                # Process owner assignment for existing Pipeline if provided
                if owner_config:
                    self._log(f"🔍 Processing owner for existing Pipeline: {owner_config.name} ({owner_config.email})")
                    owner_user = self.get_or_create_user(owner_config)
                    if owner_user:
                        owner_id = self._extract_uuid(owner_user.id) if hasattr(owner_user, 'id') else str(owner_user.id)
                        # Try to update existing pipeline with new owner - recreate it with proper owner
                        try:
                            from metadata.generated.schema.api.data.createPipeline import CreatePipelineRequest
                            
                            owner_ref = EntityReference(id=owner_id, type="user")
                            
                            # Extract service name from service EntityReference
                            service_name = None
                            if hasattr(existing_pipeline.service, 'name'):
                                service_name = existing_pipeline.service.name
                            elif hasattr(existing_pipeline, 'service'):
                                # If service is an EntityReference, get the name from it
                                try:
                                    service_entity = self.metadata.get_by_name(entity=PipelineService, fqn=existing_pipeline.service.name)
                                    service_name = service_entity.name
                                except:
                                    # Fallback - extract from FQN
                                    service_name = str(existing_pipeline.service.name) if hasattr(existing_pipeline.service, 'name') else pipeline_config.service_name
                            
                            if not service_name:
                                service_name = pipeline_config.service_name
                            
                            self._log(f"🔄 Recreating Pipeline with owner. Service: {service_name}")
                            
                            # Extract and convert existing tasks properly
                            tasks_list = []
                            # 首先检查是否提供了自定义tasks配置
                            if pipeline_config.tasks:
                                self._log(f"📋 Using provided custom tasks ({len(pipeline_config.tasks)} tasks)")
                                tasks_list = pipeline_config.tasks.copy()
                            elif hasattr(existing_pipeline, 'tasks') and existing_pipeline.tasks:
                                self._log(f"📋 Found {len(existing_pipeline.tasks)} existing tasks to preserve")
                                for task in existing_pipeline.tasks:
                                    # Convert task to proper format
                                    task_dict = {
                                        'name': task.name if hasattr(task, 'name') else 'default-task',
                                        'taskType': task.taskType if hasattr(task, 'taskType') else 'TRANSFORM',
                                        'description': task.description if hasattr(task, 'description') else '',
                                        'displayName': task.displayName if hasattr(task, 'displayName') else (task.name if hasattr(task, 'name') else 'Default Task')
                                    }
                                    tasks_list.append(task_dict)
                            else:
                                self._log(f"📋 No existing tasks found, creating default tasks")
                                # Create default tasks for data pipeline
                                tasks_list = [
                                    {
                                        'name': 'data-extraction',
                                        'taskType': 'TRANSFORM',
                                        'description': '从MySQL dl_cloud数据库提取设备档案数据',
                                        'displayName': 'Data Extraction'
                                    },
                                    {
                                        'name': 'data-transformation',
                                        'taskType': 'TRANSFORM', 
                                        'description': '数据清洗和转换处理',
                                        'displayName': 'Data Transformation'
                                    },
                                    {
                                        'name': 'data-loading',
                                        'taskType': 'TRANSFORM',
                                        'description': '将处理后的数据加载到TiDB ods_device_profile_detail_di表',
                                        'displayName': 'Data Loading'
                                    }
                                ]
                            
                            # Create Task objects
                            from metadata.generated.schema.entity.data.pipeline import Task
                            task_objects = []
                            for task_config in tasks_list:
                                task = Task(
                                    name=task_config['name'],
                                    taskType=task_config['taskType'],
                                    description=task_config.get('description', ''),
                                    displayName=task_config.get('displayName', task_config['name'])
                                )
                                task_objects.append(task)
                            
                            # Create new Pipeline request with owner and preserved tasks
                            create_request = CreatePipelineRequest(
                                name=existing_pipeline.name,
                                displayName=existing_pipeline.displayName or existing_pipeline.name,
                                description=existing_pipeline.description or f"Pipeline managed by {owner_user.name}",
                                service=service_name,  # Use service name as string, not EntityReference
                                tasks=task_objects,  # Use properly formatted Task objects
                                owners=[owner_ref]
                            )
                            
                            updated_pipeline = self.metadata.create_or_update(create_request)
                            self._log(f"✅ Recreated Pipeline with owner: {owner_user.name} ({owner_id})")
                            self.current_pipeline = updated_pipeline
                            return updated_pipeline
                            
                        except Exception as update_error:
                            self._log(f"⚠️ Could not recreate Pipeline with owner: {update_error}", "WARNING")
                            # Fallback - continue with existing pipeline
                            self._log(f"🔄 Continuing with existing Pipeline without persistent owner")
                            self.current_pipeline = existing_pipeline
                    else:
                        self._log("❌ Owner user is None, existing Pipeline owner unchanged")
                
                return existing_pipeline
        except Exception as check_error:
            self._log(f"📝 Pipeline does not exist, will create new one: {check_error}")
        
        try:
            # Create or get pipeline service
            service_id = self.create_pipeline_service(
                service_name=pipeline_config.service_name,
                service_description=f"Service for {pipeline_config.display_name}"
            )
            
            if not service_id:
                self._log("❌ Failed to create Pipeline Service", "ERROR")
                return None
            
            # Verify service exists and get clean name
            try:
                pipeline_service = self.metadata.get_by_name(entity=PipelineService, fqn=pipeline_config.service_name)
                service_reference = self._clean_name_format(pipeline_service.name)
                self._log(f"✅ Verified Pipeline Service: {service_reference}")
            except Exception as e:
                self._log(f"❌ Service verification failed: {e}", "ERROR")
                return None
            
            # Handle owner - only for new pipelines
            owners = []
            if owner_config:
                self._log(f"🔍 Setting up owner for new Pipeline: {owner_config.name} ({owner_config.email})")
                # Use proper user retrieval method with diagnostic logging
                owner_user = self.get_or_create_user(owner_config)
                if owner_user:
                    owner_id = self._extract_uuid(owner_user.id) if hasattr(owner_user, 'id') else str(owner_user.id)
                    owners.append(EntityReference(id=owner_id, type="user"))
                    self._log(f"✅ Added Pipeline owner: {owner_user.name} ({owner_id})")
                else:
                    self._log("❌ Owner user is None, no owner will be assigned")
            else:
                self._log("📝 No owner config provided")
            
            # Create tasks
            from metadata.generated.schema.entity.data.pipeline import Task
            tasks = []
            if pipeline_config.tasks:
                for task_config in pipeline_config.tasks:
                    task = Task(
                        name=task_config.get('name', 'default-task'),
                        displayName=task_config.get('displayName', task_config.get('display_name', task_config.get('name', 'Default Task'))),
                        description=task_config.get('description', ''),
                        taskType=task_config.get('taskType', task_config.get('task_type', 'TRANSFORM')),
                        owners=owners if owners else None
                    )
                    tasks.append(task)
            else:
                # Default tasks
                default_tasks = [
                    {
                        'name': 'extract-data',
                        'display_name': 'Extract Data',
                        'description': 'Extract data from source systems',
                        'task_type': 'EXTRACT'
                    },
                    {
                        'name': 'transform-data',
                        'display_name': 'Transform Data',
                        'description': 'Transform and process data',
                        'task_type': 'TRANSFORM'
                    },
                    {
                        'name': 'load-data',
                        'display_name': 'Load Data',
                        'description': 'Load data to target systems',
                        'task_type': 'LOAD'
                    }
                ]
                
                for task_config in default_tasks:
                    task = Task(
                        name=task_config['name'],
                        displayName=task_config['display_name'],
                        description=task_config['description'],
                        taskType=task_config['task_type'],
                        owners=owners if owners else None
                    )
                    tasks.append(task)
            
            # Create pipeline request
            from metadata.generated.schema.api.data.createPipeline import CreatePipelineRequest
            pipeline_request = CreatePipelineRequest(
                name=pipeline_config.name,
                displayName=pipeline_config.display_name,
                description=pipeline_config.description,
                service=service_reference,
                owners=owners,
                tasks=tasks
            )
            
            # Create pipeline
            pipeline = self.metadata.create_or_update(pipeline_request)
            self._log(f"🚀 Pipeline created successfully: {self._clean_name_format(pipeline.name)}")
            
            # 保存当前创建的pipeline以供血缘关系使用
            self.current_pipeline = pipeline
            
            # Display owner info
            if hasattr(pipeline, 'owners') and pipeline.owners:
                try:
                    owner_count = len(pipeline.owners) if hasattr(pipeline.owners, '__len__') else len(list(pipeline.owners))
                    self._log(f"👥 Pipeline Owners: {owner_count} assigned")
                except:
                    self._log("👥 Pipeline Owners: assigned (count unknown)")
            else:
                self._log("👥 Pipeline has no owners assigned")
            
            return pipeline
            
        except Exception as e:
            self._log(f"❌ Pipeline creation failed: {e}", "ERROR")
            return None
    
    def add_table_lineage(self, from_table_fqn, to_table_fqn, description="", pipeline_fqn=None, auto_associate_pipeline=True):
        """添加表血缘关系 - 包含Pipeline关联
        
        Args:
            from_table_fqn: 源表FQN
            to_table_fqn: 目标表FQN  
            description: 血缘关系描述
            pipeline_fqn: 指定的Pipeline FQN
            auto_associate_pipeline: 是否自动关联最近创建的pipeline
        """
        if not OPENMETADATA_AVAILABLE:
            self._log(f"📝 简化模式：记录血缘关系 {from_table_fqn} → {to_table_fqn}")
            self._log(f"📋 描述: {description}")
            return True
            
        if not self.metadata:
            self._log("❌ OpenMetadata connection not available", "ERROR")
            return False
            
        try:
            # 获取源表和目标表
            from metadata.generated.schema.entity.data.table import Table
            from metadata.generated.schema.type.entityLineage import EntitiesEdge, LineageDetails
            
            # 获取源表
            try:
                from_table = self.metadata.get_by_name(entity=Table, fqn=from_table_fqn)
            except Exception as e:
                self._log(f"❌ 源表不存在: {from_table_fqn} - {e}", "ERROR")
                return False
            
            # 获取目标表
            try:
                to_table = self.metadata.get_by_name(entity=Table, fqn=to_table_fqn)
            except Exception as e:
                self._log(f"❌ 目标表不存在: {to_table_fqn} - {e}", "ERROR")
                return False
            
            from_table_id = self._extract_uuid(from_table.id)
            to_table_id = self._extract_uuid(to_table.id)
            
            # 获取pipeline实体用于血缘关系（优先使用pipeline_fqn，否则尝试获取当前pipeline）
            pipeline_ref = None
            if pipeline_fqn:
                # 如果提供了pipeline_fqn，使用指定的Pipeline
                try:
                    pipeline_entity = self.metadata.get_by_name(entity=Pipeline, fqn=pipeline_fqn)
                    pipeline_id = self._extract_uuid(pipeline_entity.id)
                    pipeline_ref = EntityReference(id=pipeline_id, type="pipeline")
                    self._log(f"🔗 将指定Pipeline关联到血缘关系: {pipeline_id}")
                except Exception as pe:
                    self._log(f"⚠️ 指定Pipeline关联失败: {pe}", "WARNING")
            elif auto_associate_pipeline and self.current_pipeline:
                # 如果没有提供pipeline_fqn但启用了自动关联，使用当前创建的pipeline
                try:
                    pipeline_id = self._extract_uuid(self.current_pipeline.id)
                    pipeline_ref = EntityReference(id=pipeline_id, type="pipeline")
                    self._log(f"🔗 自动关联当前Pipeline到血缘关系: {pipeline_id}")
                except Exception as pe:
                    self._log(f"⚠️ 自动Pipeline关联失败: {pe}", "WARNING")
            else:
                self._log("🔗 未关联Pipeline，创建简单血缘关系")
            
            # 创建血缘关系 - 包含Pipeline上下文（如果可用）
            edge = EntitiesEdge(
                fromEntity=EntityReference(id=from_table_id, type="table"),
                toEntity=EntityReference(id=to_table_id, type="table"),
                lineageDetails=LineageDetails(
                    description=description or f"数据血缘: {from_table_fqn} → {to_table_fqn}",
                    pipeline=pipeline_ref
                )
            )
            
            lineage_request = AddLineageRequest(edge=edge)
            self.metadata.add_lineage(lineage_request)
            
            if pipeline_ref:
                self._log(f"✅ 血缘关系添加成功(含Pipeline): {from_table_fqn} → {to_table_fqn}")
            else:
                self._log(f"✅ 血缘关系添加成功: {from_table_fqn} → {to_table_fqn}")
            return True
            
        except Exception as e:
            self._log(f"❌ 添加血缘关系失败: {e}", "ERROR")
            return False
    
    def get_pipeline_info(self, pipeline_name: str) -> Optional[Dict[str, Any]]:
        """
        Get pipeline information
        
        Args:
            pipeline_name: Pipeline name
        
        Returns:
            Pipeline information dictionary or None
        """
        if not self.metadata:
            self._log("❌ OpenMetadata connection not available", "ERROR")
            return None
        
        try:
            pipeline = self.metadata.get_by_name(entity=Pipeline, fqn=pipeline_name)
            
            info = {
                'name': self._clean_name_format(pipeline.name),
                'id': self._extract_uuid(pipeline.id),
                'description': self._clean_name_format(pipeline.description) if pipeline.description else None,
                'status': pipeline.pipelineStatus,
                'service': self._clean_name_format(pipeline.service.name) if pipeline.service else None,
                'owners': [
                    {
                        'id': self._extract_uuid(owner.id),
                        'name': self._clean_name_format(owner.name),
                        'type': owner.type
                    }
                    for owner in (list(pipeline.owners) if pipeline.owners else [])
                    if hasattr(owner, 'id') and hasattr(owner, 'name') and hasattr(owner, 'type')
                ],
                'tasks': [
                    {
                        'name': self._clean_name_format(task.name),
                        'type': task.taskType,
                        'description': task.description
                    }
                    for task in (list(pipeline.tasks) if pipeline.tasks else [])
                ]
            }
            
            self._log(f"📋 Pipeline info retrieved: {info['name']}")
            return info
            
        except Exception as e:
            self._log(f"❌ Failed to get pipeline info: {e}", "ERROR")
            return None
    
    def get_pipeline(self, pipeline_name, service_name=""):
        """获取已存在的Pipeline"""
        if not self.metadata:
            self._log("❌ OpenMetadata connection not available", "ERROR")
            return None
            
        try:
            # 如果没有提供service_name，尝试从pipeline_name构建FQN
            if not service_name:
                # 尝试直接使用pipeline_name作为FQN
                fqn = pipeline_name
            else:
                fqn = f"{service_name}.{pipeline_name}"
            
            # 通过名称获取Pipeline
            pipeline = self.metadata.get_by_name(entity=Pipeline, fqn=fqn)
            
            self._log(f"📋 获取到Pipeline: {self._clean_name_format(pipeline.name)}")
            self._log(f"Pipeline ID: {self._extract_uuid(pipeline.id)}")
            self._log(f"Pipeline描述: {pipeline.description or 'N/A'}")
            
            # 显示Pipeline的任务
            if hasattr(pipeline, 'tasks') and pipeline.tasks:
                self._log("Pipeline任务:")
                for i, task in enumerate(pipeline.tasks, 1):
                    self._log(f"  {i}. {self._clean_name_format(task.name)} ({task.taskType}): {task.description}")
            
            return pipeline
        except Exception as e:
            self._log(f"❌ 获取Pipeline失败: {e}", "ERROR")
            return None

    def get_pipeline_lineage(self, pipeline_name, service_name=""):
        """获取Pipeline的血缘关系"""
        if not self.metadata:
            self._log("❌ OpenMetadata connection not available", "ERROR")
            return None
            
        try:
            pipeline = self.get_pipeline(pipeline_name, service_name)
            if not pipeline:
                return None
                
            # 构建FQN
            if not service_name:
                fqn = pipeline_name
            else:
                fqn = f"{service_name}.{pipeline_name}"
                
            # 获取血缘关系
            lineage = self.metadata.get_lineage_by_name(
                entity=Pipeline,
                fqn=fqn,
                up_depth=3,
                down_depth=3
            )
            
            self._log("📊 Pipeline血缘关系:")
            if lineage and lineage.get('edges'):
                for edge in lineage['edges']:
                    from_entity = edge.get('fromEntity', {})
                    to_entity = edge.get('toEntity', {})
                    self._log(f"  {from_entity.get('name', 'Unknown')} -> {to_entity.get('name', 'Unknown')}")
            else:
                self._log("  未找到血缘关系")
                
            return lineage
        except Exception as e:
            self._log(f"❌ 获取Pipeline血缘关系失败: {e}", "ERROR")
            return None

    def track_pipeline_execution(self, status="success", start_time=None, end_time=None, metrics=None):
        """跟踪管道执行状态"""
        if not self.metadata:
            return
            
        try:
            execution_info = {
                "run_id": self.run_id,
                "status": status,
                "start_time": start_time or datetime.now(),
                "end_time": end_time or datetime.now(),
                "metrics": metrics or {}
            }
            self._log(f"📈 管道执行跟踪: {execution_info}")
        except Exception as e:
            self._log(f"❌ 跟踪管道执行失败: {e}", "ERROR")

    def update_pipeline_custom_properties(
        self, 
        pipeline_fqn: str, 
        custom_properties: Dict[str, Any]
    ) -> bool:
        """
        更新Pipeline的自定义属性
        
        注意: 当前版本暂时将自定义属性记录到日志中，
        等待OpenMetadata Python SDK更新支持扩展属性更新功能
        
        Args:
            pipeline_fqn: Pipeline的完全限定名称
            custom_properties: 要更新的自定义属性字典
                例如: {
                    "pipelineStatus": "测试中",
                    "lastUpdate": "2024-01-15T10:30:00Z",
                    "pipelineDuration": "30分钟"
                }
        
        Returns:
            bool: 更新是否成功
        """
        if not self.metadata:
            self._log("❌ OpenMetadata connection not available", "ERROR")
            return False
            
        try:
            # 获取现有的Pipeline实体
            pipeline = self.metadata.get_by_name(entity=Pipeline, fqn=pipeline_fqn)
            if not pipeline:
                self._log(f"❌ Pipeline not found: {pipeline_fqn}", "ERROR")
                return False
            
            # 记录自定义属性到日志中
            self._log(f"📊 Pipeline自定义属性记录 [{pipeline_fqn}]:")
            for key, value in custom_properties.items():
                self._log(f"   • {key}: {value}")
            
            # 将属性保存到内存中供后续使用
            if not hasattr(self, '_pipeline_properties'):
                self._pipeline_properties = {}
            
            if pipeline_fqn not in self._pipeline_properties:
                self._pipeline_properties[pipeline_fqn] = {}
                
            self._pipeline_properties[pipeline_fqn].update(custom_properties)
            
            # 尝试实际更新OpenMetadata中的自定义属性
            success = self._update_pipeline_extension_via_api(pipeline, custom_properties)
            if success:
                self._log(f"✅ Pipeline自定义属性已更新到OpenMetadata: {pipeline_fqn}")
            else:
                self._log(f"✅ Pipeline自定义属性已记录到日志: {pipeline_fqn}")
            
            return True
                
        except Exception as e:
            self._log(f"❌ 更新Pipeline自定义属性时出错: {e}", "ERROR")
            return False

    def _update_pipeline_extension_via_api(self, pipeline, custom_properties: Dict[str, Any]) -> bool:
        """
        通过REST API直接更新Pipeline的扩展属性
        
        Args:
            pipeline: Pipeline实体对象
            custom_properties: 自定义属性字典
            
        Returns:
            bool: 更新是否成功
        """
        try:
            import json
            import requests
            from datetime import datetime
            
            # 准备API请求 - 使用_extract_uuid方法正确提取UUID
            pipeline_id = self._extract_uuid(pipeline.id)
            api_url = f"{self.config.get('host')}/v1/pipelines/{pipeline_id}"
            headers = {
                "Authorization": f"Bearer {self.config.get('jwt_token')}",
                "Content-Type": "application/json-patch+json"
            }
            
            # 定义已知的自定义字段（根据OpenMetadata UI中的定义）
            known_custom_fields = {
                "pipelineStatus", "lastUpdate", "pipelineDuration","executionStatus"
            }
            
            # 格式化扩展数据以符合OpenMetadata的要求
            formatted_extension = {}
            for key, value in custom_properties.items():
                # 只处理已知的自定义字段
                if key not in known_custom_fields:
                    self._log(f"⚠️ 跳过未定义的自定义字段: {key}", "WARNING")
                    continue
                    
                if key == "pipelineStatus":
                    # pipelineStatus是枚举类型，需要使用正确的值
                    if value in ["测试中", "已上线", "已下线"]:
                        status_mapping = {
                            "测试中": "Testing",
                            "已上线": "Online", 
                            "已下线": "Offline"
                        }
                        formatted_extension[key] = [status_mapping[value]]
                    else:
                        formatted_extension[key] = [value]
                elif key == "lastUpdate":
                    # 确保日期时间格式正确
                    if isinstance(value, str):
                        try:
                            # 尝试解析ISO格式并转换为OpenMetadata要求的格式
                            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            formatted_extension[key] = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            formatted_extension[key] = value
                    else:
                        formatted_extension[key] = value
                elif key == "executionStatus":
                    formatted_extension[key] = [value]
                else:
                    # 其他字段直接使用原值
                    formatted_extension[key] = value
            
            # 准备PATCH请求体
            patch_data = [
                {
                    "op": "add",
                    "path": "/extension",
                    "value": formatted_extension
                }
            ]
            
            # 发送PATCH请求
            response = requests.patch(api_url, headers=headers, json=patch_data)
            
            if response.status_code == 200:
                self._log(f"🎯 REST API更新成功: {response.status_code}")
                return True
            else:
                self._log(f"⚠️ REST API更新失败: {response.status_code} - {response.text}", "WARNING")
                return False
                
        except Exception as e:
            self._log(f"⚠️ REST API更新出错: {e}", "WARNING")
            return False

    def update_pipeline_status(
        self, 
        pipeline_fqn: str, 
        status: Union[PipelineBusinessStatus, str],
        duration: Optional[str] = None,
        last_update: Optional[datetime] = None
    ) -> bool:
        """
        更新Pipeline的业务状态和相关信息
        
        Args:
            pipeline_fqn: Pipeline的完全限定名称
            status: Pipeline状态 (可以是枚举或字符串)
            duration: 脚本运行时长 (可选)
            last_update: 最后更新时间 (可选，默认为当前时间)
        
        Returns:
            bool: 更新是否成功
        """
        # 处理状态值
        if isinstance(status, PipelineBusinessStatus):
            status_value = status.value
        else:
            status_value = str(status)
        
        # 准备自定义属性
        custom_properties = {
            "pipelineStatus": status_value,
            "lastUpdate": (last_update or datetime.now()).isoformat()
        }
        
        # 添加可选属性
        if duration:
            custom_properties["pipelineDuration"] = duration
            
        return self.update_pipeline_custom_properties(pipeline_fqn, custom_properties)

    def update_pipeline_properties_with_lifecycle(
        self, 
        pipeline_fqn: str, 
        status: str = "Testing", 
        duration: str = None, 
        error_message: str = None
    ) -> bool:
        """
        更新Pipeline的自定义属性（生命周期管理版本）
        
        Args:
            pipeline_fqn: Pipeline完全限定名
            status: Pipeline状态 ("测试中", "已上线", "已下线")
            duration: 执行时长 (可选)，如"4.6秒"
            error_message: 错误信息 (可选)
            
        Returns:
            bool: 更新是否成功
        """
        try:
            self._log(f"📝 更新Pipeline属性: {status}")
            
            # 准备自定义属性
            custom_props = {
                "pipelineStatus": status,
                "lastUpdate": datetime.now().isoformat()
            }
            
            # 添加可选属性
            if duration:
                custom_props["pipelineDuration"] = duration
            if error_message:
                custom_props["errorMessage"] = error_message
                custom_props["executionStatus"] = "Failed"
            else:
                custom_props["executionStatus"] = "Successful"
            
            # 更新属性
            success = self.update_pipeline_custom_properties(
                pipeline_fqn=pipeline_fqn,
                custom_properties=custom_props
            )
            
            if success:
                self._log("✅ Pipeline属性更新成功")
            else:
                self._log("❌ Pipeline属性更新失败", "ERROR")
                
            return success
                
        except Exception as e:
            self._log(f"⚠️ 更新Pipeline属性时出错: {e}", "ERROR")
            return False

    def add_data_lineage_simple(
        self, 
        source_table_fqn: str, 
        target_table_fqn: str, 
        description: str = ""
    ) -> bool:
        """
        添加数据血缘关系（简化版本）
        
        Args:
            source_table_fqn: 源表完全限定名
            target_table_fqn: 目标表完全限定名
            description: 血缘关系描述
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self._log(f"🔗 添加数据血缘关系: {source_table_fqn} → {target_table_fqn}")
            
            # 使用现有的血缘关系方法
            success = self.add_table_lineage(
                from_table_fqn=source_table_fqn,
                to_table_fqn=target_table_fqn,
                description=description or f"数据处理血缘: {source_table_fqn} → {target_table_fqn}"
            )
            
            if success:
                self._log("✅ 数据血缘关系添加成功")
            else:
                self._log("❌ 数据血缘关系添加失败", "ERROR")
                
            return success
            
        except Exception as e:
            self._log(f"⚠️ 添加血缘关系时出错: {e}", "ERROR")
            return False

    def get_pipeline_custom_properties(self, pipeline_fqn: str) -> Optional[Dict[str, Any]]:
        """
        获取Pipeline的自定义属性
        
        Args:
            pipeline_fqn: Pipeline的完全限定名称
            
        Returns:
            Dict[str, Any]: 自定义属性字典，如果失败返回None
        """
        if not self.metadata:
            self._log("❌ OpenMetadata connection not available", "ERROR")
            return None
            
        try:
            # 首先尝试从内存中获取
            if hasattr(self, '_pipeline_properties') and pipeline_fqn in self._pipeline_properties:
                self._log(f"📋 从内存获取Pipeline自定义属性: {pipeline_fqn}")
                return self._pipeline_properties[pipeline_fqn]
            
            # 如果内存中没有，尝试从OpenMetadata获取
            pipeline = self.metadata.get_by_name(entity=Pipeline, fqn=pipeline_fqn)
            if not pipeline:
                self._log(f"❌ Pipeline not found: {pipeline_fqn}", "ERROR")
                return None
                
            extension_data = pipeline.extension or {}
            self._log(f"📋 从OpenMetadata获取Pipeline自定义属性: {pipeline_fqn}")
            return extension_data
            
        except Exception as e:
            self._log(f"❌ 获取Pipeline自定义属性时出错: {e}", "ERROR")
            return None

    def configure_spark_openlineage(self, spark_session_or_builder) -> Any:
        """
        Configure Spark session with OpenLineage integration
        
        Args:
            spark_session_or_builder: SparkSession.builder object or existing SparkSession
        
        Returns:
            Configured SparkSession.builder or SparkSession
        """
        try:
            # Extract OpenMetadata host for OpenLineage
            om_host = self.config.get('host', 'http://localhost:8585')
            if om_host.endswith('/api'):
                om_host = om_host[:-4]  # Remove /api suffix
            
            # Check if it's a SparkSession or SparkSession.builder
            if hasattr(spark_session_or_builder, 'sparkContext'):
                # It's an existing SparkSession
                self._log("⚡ Configuring existing SparkSession with OpenLineage")
                spark_context = spark_session_or_builder.sparkContext
                
                # Configure runtime properties
                spark_context.setLocalProperty("spark.openlineage.namespace", self.openlineage_config.namespace)
                spark_context.setLocalProperty("spark.openlineage.parentJobName", self.openlineage_config.parent_job_name)
                
                # Log configuration (runtime configuration is limited for existing sessions)
                self._log("⚡ Spark session configured with OpenLineage integration")
                self._log("ℹ️ Note: Some OpenLineage configurations require restart for existing sessions")
                return spark_session_or_builder
                
            else:
                # It's a SparkSession.builder
                self._log("⚡ Configuring SparkSession.builder with OpenLineage")
                configured_builder = spark_session_or_builder \
                    .config("spark.openlineage.namespace", self.openlineage_config.namespace) \
                    .config("spark.openlineage.parentJobName", self.openlineage_config.parent_job_name) \
                    .config("spark.jars.packages", self.openlineage_config.spark_packages) \
                    .config("spark.extraListeners", self.openlineage_config.spark_listener) \
                    .config("spark.openlineage.transport.type", "http") \
                    .config("spark.openlineage.transport.url", f"{om_host}/api/v1/lineage") \
                    .config("spark.openlineage.transport.auth.type", "api_key") \
                    .config("spark.openlineage.transport.auth.apiKey", self.config.get('jwt_token', ''))
                
                self._log("⚡ Spark session configured with OpenLineage integration")
                return configured_builder
            
        except Exception as e:
            self._log(f"⚠️ Spark OpenLineage configuration warning: {e}", "WARNING")
            return spark_session_or_builder
    
    def create_complete_pipeline(
        self,
        pipeline_config: PipelineConfig,
        owner_config: Optional[OwnerConfig] = None,
        lineage_mappings: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Pipeline]:
        """
        Create a complete pipeline with service, entity, and optional lineage
        
        Args:
            pipeline_config: Pipeline configuration
            owner_config: Optional owner configuration
            lineage_mappings: Optional list of lineage mappings
                Each mapping should have 'from_table_fqn' and 'to_table_fqn' keys
        
        Returns:
            Pipeline object or None if failed
        """
        self._log("🚀 Creating complete pipeline setup...")
        
        # Create pipeline entity
        pipeline = self.create_pipeline_entity(pipeline_config, owner_config)
        if not pipeline:
            return None
        
        # Add lineage if provided
        if lineage_mappings:
            self._log(f"🔗 Adding {len(lineage_mappings)} lineage relationships...")
            # Use pipeline fullyQualifiedName for proper lineage association
            pipeline_fqn = self._clean_name_format(pipeline.fullyQualifiedName) if hasattr(pipeline, 'fullyQualifiedName') else self._clean_name_format(pipeline.name)
            
            for mapping in lineage_mappings:
                from_table = mapping.get('from_table_fqn')
                to_table = mapping.get('to_table_fqn')
                description = mapping.get('description')
                
                if from_table and to_table:
                    self.add_table_lineage(
                        from_table_fqn=from_table,
                        to_table_fqn=to_table,
                        description=description or f"数据血缘: {from_table} → {to_table}",
                        pipeline_fqn=pipeline_fqn,
                        auto_associate_pipeline=True  # 启用自动关联
                    )
        
        self._log("✅ Complete pipeline setup finished successfully!")
        return pipeline


# Convenience functions for quick usage
def create_pipeline_manager(
    openmetadata_host: str = None,
    jwt_token: str = None,
    config_file: str = "cfg.yaml",
    config_section: str = "openmetadata_test",
    **kwargs
) -> OpenMetadataPipelineManager:
    """
    便捷函数创建pipeline manager
    
    Args:
        openmetadata_host: OpenMetadata server URL (可选，优先从cfg.yaml读取)
        jwt_token: JWT authentication token (可选，优先从cfg.yaml读取)
        config_file: 配置文件路径 (default: 'cfg.yaml')
        config_section: 配置节名称 (default: 'openmetadata_test')
        **kwargs: Additional configuration options
    
    Returns:
        OpenMetadataPipelineManager instance
    """
    if openmetadata_host and jwt_token:
        # 如果提供了参数，使用传统方式
        config = {
            'host': openmetadata_host,
            'jwt_token': jwt_token,
            **kwargs
        }
        return OpenMetadataPipelineManager(config)
    else:
        # 使用cfg.yaml配置
        return OpenMetadataPipelineManager(
            config_file=config_file,
            config_section=config_section
        )


def create_simple_pipeline_manager(config_file: str = "cfg.yaml", config_section: str = None) -> OpenMetadataPipelineManager:
    """
    最简单的方式创建pipeline manager - 直接从cfg.yaml读取所有配置
    
    Args:
        config_file: 配置文件路径 (default: 'cfg.yaml')
        config_section: 配置节名称 (default: 根据环境变量OPENMETADATA_ENV自动选择)
                       可选值: 'openmetadata_test', 'openmetadata_prod'
    
    Returns:
        OpenMetadataPipelineManager instance
    """
    # 如果没有指定配置节，根据环境变量自动选择
    if config_section is None:
        env = os.getenv("OPENMETADATA_ENV", "test").lower()
        if env in ["prod", "production"]:
            config_section = "openmetadata_prod"
        else:
            config_section = "openmetadata_test"
        print(f"🌍 自动选择环境: {config_section} (基于OPENMETADATA_ENV={env})")
    
    return OpenMetadataPipelineManager(config_file=config_file, config_section=config_section)


def quick_pipeline_setup(
    pipeline_name: str,
    pipeline_description: str,
    config_file: str = "cfg.yaml",
    service_name: Optional[str] = None,
    lineage_mappings: Optional[List[Dict[str, str]]] = None,
    tasks: Optional[List[Dict[str, Any]]] = None,
    **kwargs
) -> Optional[Pipeline]:
    """
    快速Pipeline设置 - 从cfg.yaml读取配置
    
    Args:
        pipeline_name: Pipeline名称
        pipeline_description: Pipeline描述
        config_file: 配置文件路径 (default: 'cfg.yaml')
        service_name: 服务名称 (可选，默认从cfg.yaml读取或使用pipeline_name-service)
        lineage_mappings: 可选的血缘关系映射
        tasks: 可选的自定义任务列表
        **kwargs: 其他配置选项
    
    Returns:
        Pipeline object or None if failed
    """
    # Create manager from cfg.yaml
    manager = create_simple_pipeline_manager(config_file)
    
    # 如果没有指定服务名称，使用pipeline名称生成
    if not service_name:
        service_name = f"{pipeline_name}-service"
    
    # Configure pipeline
    pipeline_config = PipelineConfig(
        name=pipeline_name,
        display_name=pipeline_name.replace('-', ' ').replace('_', ' ').title(),
        description=pipeline_description,
        service_name=service_name,
        tasks=tasks  # 添加tasks支持
    )
    
    # Configure owner from cfg.yaml
    owner_config = None
    if 'owner' in manager.config:
        owner_info = manager.config['owner']
        owner_config = OwnerConfig(
            name=owner_info.get('name', 'admin'),
            email=owner_info.get('email', 'admin@company.com'),
            display_name=owner_info.get('display_name', owner_info.get('name', 'Admin')),
            is_admin=owner_info.get('is_admin', False)
        )
    
    # Create pipeline
    return manager.create_complete_pipeline(
        pipeline_config=pipeline_config,
        owner_config=owner_config,
        lineage_mappings=lineage_mappings
    )


def simple_lineage_setup(
    from_table_fqn: str,
    to_table_fqn: str,
    pipeline_name: str,
    description: str = "",
    config_file: str = "cfg.yaml"
) -> bool:
    """
    简单的血缘关系设置
    
    Args:
        from_table_fqn: 源表FQN
        to_table_fqn: 目标表FQN
        pipeline_name: Pipeline名称
        description: 血缘关系描述
        config_file: 配置文件路径
    
    Returns:
        是否成功
    """
    try:
        manager = create_simple_pipeline_manager(config_file)
        return manager.add_table_lineage(
            from_table_fqn=from_table_fqn,
            to_table_fqn=to_table_fqn,
            description=description or f"数据血缘: {from_table_fqn} → {to_table_fqn}",
            pipeline_fqn=pipeline_name,
            auto_associate_pipeline=True
        )
    except Exception as e:
        print(f"❌ 血缘关系设置失败: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    print("OpenMetadata Pipeline Manager - 简化版本")
    print("=" * 60)
    
    print("🔧 配置文件示例 (cfg.yaml):")
    print("""
# 测试环境配置 (默认)
openmetadata_test:
    token: "your_test_jwt_token_here"
    host: "https://test-openmetadata.dl-aiot.com/api"
    pipeline_owner_name: "adward"
    pipeline_owner_email: "adward.chen@designlibro.com"
    pipeline_owner_display_name: "adward.chen"

# 生产环境配置
openmetadata_prod:
    token: "your_prod_jwt_token_here"
    host: "https://us-openmetadata.dl-aiot.com/api"
    pipeline_owner_name: "adward"
    pipeline_owner_email: "adward.chen@designlibro.com"
    pipeline_owner_display_name: "adward.chen"
""")
    
    print("\n📖 使用示例:")
    print("""
# 方式1: 最简单的使用方式 - 所有配置从cfg.yaml读取
from datalibro_backend.openmetadata_pipeline_manager import (
    create_simple_pipeline_manager,
    quick_pipeline_setup,
    simple_lineage_setup
)

# 1. 创建Pipeline Manager (默认使用测试环境)
manager = create_simple_pipeline_manager()

# 或者使用生产环境
# manager = create_simple_pipeline_manager(config_section="openmetadata_prod")

# 2. 快速创建Pipeline (指定服务名称)
pipeline = quick_pipeline_setup(
    pipeline_name="data-sync-pc001-active-stats",
    pipeline_description="PC001设备活跃统计数据同步",
    service_name="pc001-spark-pipeline-service"  # 根据项目需求指定
)

# 3. 添加数据血缘关系
simple_lineage_setup(
    from_table_fqn="aiot_internal.dl_cloud.ods_device_profile_detail_di",
    to_table_fqn="aiot_internal.dl_cloud.ads_pc001_active_bound_device_stats_di",
    pipeline_name="pc001-spark-pipeline-service.data-sync-pc001-active-stats",
    description="PC001设备数据处理血缘"
)

# 方式2: 传统方式 - 手动配置
from datalibro_backend.openmetadata_pipeline_manager import (
    OpenMetadataPipelineManager,
    PipelineConfig, 
    OwnerConfig
)

# 创建管理器 (仍然可以从cfg.yaml读取)
manager = OpenMetadataPipelineManager()

# 或者手动配置
manager = OpenMetadataPipelineManager(
    openmetadata_config={
        'host': 'http://10.52.178.223:59693/api',
        'jwt_token': 'your-jwt-token'
    }
)

# 方式3: 在现有脚本中集成
def initialize_openmetadata_manager():
    \"\"\"初始化 OpenMetadata Pipeline Manager\"\"\"
    try:
        # 最简单的方式 - 一行代码
        manager = create_simple_pipeline_manager()
        
        # 创建Pipeline (指定服务名称)
        pipeline = quick_pipeline_setup(
            pipeline_name=os.path.basename(__file__).replace('.py', ''),
            pipeline_description=f"数据同步脚本: {os.path.basename(__file__)}",
            service_name="pc001-spark-pipeline-service"  # 根据项目统一使用
        )
        
        return manager, pipeline
    except Exception as e:
        print(f"⚠️ OpenMetadata 初始化失败: {e}")
        return None, None

# 在main函数中使用
def main():
    # 初始化OpenMetadata
    om_manager, om_pipeline = initialize_openmetadata_manager()
    
    # 你的数据处理逻辑...
    
    # 添加血缘关系
    if om_manager:
        om_manager.add_table_lineage(
            from_table_fqn="source.db.table",
            to_table_fqn="target.db.table",
            description="数据处理血缘"
        )

# 方式4: Spark集成 (可选配置OpenLineage)
from pyspark.sql import SparkSession
from datalibro_backend.openmetadata_pipeline_manager import OpenLineageConfig

# 如果需要OpenLineage集成，可以单独配置
openlineage_config = OpenLineageConfig(
    namespace="datalibro-namespace",
    parent_job_name="data-pipeline"
)

manager = OpenMetadataPipelineManager(openlineage_config=openlineage_config)
spark_builder = SparkSession.builder.appName("my-app")

# 配置OpenLineage集成
spark = manager.configure_spark_openlineage(spark_builder).getOrCreate()
""")