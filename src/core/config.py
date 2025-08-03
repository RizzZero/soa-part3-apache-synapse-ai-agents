"""
Configuration Management for Synapse MCP Server

This module handles configuration loading, validation, and management
for the Apache Synapse MCP server.
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    enabled: bool = True
    auth_type: str = "jwt"  # jwt, oauth2, api_key
    jwt_secret: str = ""
    oauth2_client_id: str = ""
    oauth2_client_secret: str = ""
    api_key_header: str = "X-API-Key"
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration."""
    enabled: bool = True
    metrics_port: int = 9090
    log_level: str = "INFO"
    log_format: str = "json"
    prometheus_enabled: bool = True
    health_check_interval: int = 30  # seconds


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    type: str = "sqlite"  # sqlite, postgresql, mysql
    url: str = "sqlite:///synapse_mcp.db"
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False


@dataclass
class CacheConfig:
    """Cache configuration settings."""
    type: str = "redis"  # redis, memory
    redis_url: str = "redis://localhost:6379"
    ttl: int = 3600  # seconds
    max_size: int = 1000


@dataclass
class SynapseMCPConfig:
    """Main configuration class for Synapse MCP Server."""
    
    # Server settings
    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    
    # Security
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Monitoring
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Database
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    # Cache
    cache: CacheConfig = field(default_factory=CacheConfig)
    
    # Synapse specific settings
    synapse_home: str = "/opt/synapse"
    synapse_config_dir: str = "/opt/synapse/conf"
    synapse_repository_dir: str = "/opt/synapse/repository"
    
    # MCP settings
    mcp_server_name: str = "synapse-mcp-server"
    mcp_server_version: str = "1.0.0"
    mcp_tools_enabled: bool = True
    mcp_resources_enabled: bool = True
    
    @classmethod
    def from_file(cls, config_path: str) -> "SynapseMCPConfig":
        """Load configuration from YAML file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return cls.from_dict(config_data)
    
    @classmethod
    def from_dict(cls, config_data: Dict[str, Any]) -> "SynapseMCPConfig":
        """Create configuration from dictionary."""
        config = cls()
        
        # Update server settings
        if "server" in config_data:
            server_config = config_data["server"]
            config.host = server_config.get("host", config.host)
            config.port = server_config.get("port", config.port)
            config.debug = server_config.get("debug", config.debug)
        
        # Update security settings
        if "security" in config_data:
            security_data = config_data["security"]
            config.security.enabled = security_data.get("enabled", config.security.enabled)
            config.security.auth_type = security_data.get("auth_type", config.security.auth_type)
            config.security.jwt_secret = security_data.get("jwt_secret", config.security.jwt_secret)
            config.security.oauth2_client_id = security_data.get("oauth2_client_id", config.security.oauth2_client_id)
            config.security.oauth2_client_secret = security_data.get("oauth2_client_secret", config.security.oauth2_client_secret)
            config.security.api_key_header = security_data.get("api_key_header", config.security.api_key_header)
            config.security.rate_limit_requests = security_data.get("rate_limit_requests", config.security.rate_limit_requests)
            config.security.rate_limit_window = security_data.get("rate_limit_window", config.security.rate_limit_window)
        
        # Update monitoring settings
        if "monitoring" in config_data:
            monitoring_data = config_data["monitoring"]
            config.monitoring.enabled = monitoring_data.get("enabled", config.monitoring.enabled)
            config.monitoring.metrics_port = monitoring_data.get("metrics_port", config.monitoring.metrics_port)
            config.monitoring.log_level = monitoring_data.get("log_level", config.monitoring.log_level)
            config.monitoring.log_format = monitoring_data.get("log_format", config.monitoring.log_format)
            config.monitoring.prometheus_enabled = monitoring_data.get("prometheus_enabled", config.monitoring.prometheus_enabled)
            config.monitoring.health_check_interval = monitoring_data.get("health_check_interval", config.monitoring.health_check_interval)
        
        # Update database settings
        if "database" in config_data:
            database_data = config_data["database"]
            config.database.type = database_data.get("type", config.database.type)
            config.database.url = database_data.get("url", config.database.url)
            config.database.pool_size = database_data.get("pool_size", config.database.pool_size)
            config.database.max_overflow = database_data.get("max_overflow", config.database.max_overflow)
            config.database.echo = database_data.get("echo", config.database.echo)
        
        # Update cache settings
        if "cache" in config_data:
            cache_data = config_data["cache"]
            config.cache.type = cache_data.get("type", config.cache.type)
            config.cache.redis_url = cache_data.get("redis_url", config.cache.redis_url)
            config.cache.ttl = cache_data.get("ttl", config.cache.ttl)
            config.cache.max_size = cache_data.get("max_size", config.cache.max_size)
        
        # Update Synapse settings
        if "synapse" in config_data:
            synapse_data = config_data["synapse"]
            config.synapse_home = synapse_data.get("home", config.synapse_home)
            config.synapse_config_dir = synapse_data.get("config_dir", config.synapse_config_dir)
            config.synapse_repository_dir = synapse_data.get("repository_dir", config.synapse_repository_dir)
        
        # Update MCP settings
        if "mcp" in config_data:
            mcp_data = config_data["mcp"]
            config.mcp_server_name = mcp_data.get("server_name", config.mcp_server_name)
            config.mcp_server_version = mcp_data.get("server_version", config.mcp_server_version)
            config.mcp_tools_enabled = mcp_data.get("tools_enabled", config.mcp_tools_enabled)
            config.mcp_resources_enabled = mcp_data.get("resources_enabled", config.mcp_resources_enabled)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "server": {
                "host": self.host,
                "port": self.port,
                "debug": self.debug
            },
            "security": {
                "enabled": self.security.enabled,
                "auth_type": self.security.auth_type,
                "jwt_secret": self.security.jwt_secret,
                "oauth2_client_id": self.security.oauth2_client_id,
                "oauth2_client_secret": self.security.oauth2_client_secret,
                "api_key_header": self.security.api_key_header,
                "rate_limit_requests": self.security.rate_limit_requests,
                "rate_limit_window": self.security.rate_limit_window
            },
            "monitoring": {
                "enabled": self.monitoring.enabled,
                "metrics_port": self.monitoring.metrics_port,
                "log_level": self.monitoring.log_level,
                "log_format": self.monitoring.log_format,
                "prometheus_enabled": self.monitoring.prometheus_enabled,
                "health_check_interval": self.monitoring.health_check_interval
            },
            "database": {
                "type": self.database.type,
                "url": self.database.url,
                "pool_size": self.database.pool_size,
                "max_overflow": self.database.max_overflow,
                "echo": self.database.echo
            },
            "cache": {
                "type": self.cache.type,
                "redis_url": self.cache.redis_url,
                "ttl": self.cache.ttl,
                "max_size": self.cache.max_size
            },
            "synapse": {
                "home": self.synapse_home,
                "config_dir": self.synapse_config_dir,
                "repository_dir": self.synapse_repository_dir
            },
            "mcp": {
                "server_name": self.mcp_server_name,
                "server_version": self.mcp_server_version,
                "tools_enabled": self.mcp_tools_enabled,
                "resources_enabled": self.mcp_resources_enabled
            }
        }
    
    def save_to_file(self, config_path: str):
        """Save configuration to YAML file."""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        errors = []
        
        # Validate security settings
        if self.security.enabled:
            if self.security.auth_type == "jwt" and not self.security.jwt_secret:
                errors.append("JWT secret is required when JWT authentication is enabled")
            elif self.security.auth_type == "oauth2":
                if not self.security.oauth2_client_id:
                    errors.append("OAuth2 client ID is required")
                if not self.security.oauth2_client_secret:
                    errors.append("OAuth2 client secret is required")
        
        # Validate database settings
        if self.database.type not in ["sqlite", "postgresql", "mysql"]:
            errors.append("Invalid database type")
        
        # Validate cache settings
        if self.cache.type not in ["redis", "memory"]:
            errors.append("Invalid cache type")
        
        # Validate Synapse paths
        if not os.path.exists(self.synapse_home):
            errors.append(f"Synapse home directory does not exist: {self.synapse_home}")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
        
        return True


def load_config(config_path: Optional[str] = None) -> SynapseMCPConfig:
    """Load configuration from file or environment."""
    if config_path:
        return SynapseMCPConfig.from_file(config_path)
    
    # Try to load from environment variable
    config_env = os.getenv("SYNAPSE_MCP_CONFIG")
    if config_env:
        return SynapseMCPConfig.from_file(config_env)
    
    # Try default locations
    default_paths = [
        "config/synapse-mcp.yaml",
        "synapse-mcp.yaml",
        "~/.synapse-mcp/config.yaml"
    ]
    
    for path in default_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            return SynapseMCPConfig.from_file(expanded_path)
    
    # Return default configuration
    return SynapseMCPConfig() 