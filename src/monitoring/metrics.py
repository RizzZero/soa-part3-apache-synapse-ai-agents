"""
Monitoring and Metrics Collection

This module provides monitoring and metrics collection capabilities for Apache Synapse MCP,
including performance metrics, health checks, and observability features.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class ServiceMetrics:
    """Metrics for a specific service."""
    service_name: str
    request_count: int = 0
    error_count: int = 0
    total_response_time: float = 0.0
    avg_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    last_error_time: Optional[datetime] = None


class MetricsCollector:
    """
    Metrics collector that gathers and stores performance metrics
    for the Apache Synapse MCP server and its services.
    """
    
    def __init__(self):
        """Initialize the metrics collector."""
        # Service-specific metrics
        self.service_metrics: Dict[str, ServiceMetrics] = defaultdict(ServiceMetrics)
        
        # Global metrics
        self.global_metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "uptime_start": datetime.now(),
            "last_request": None,
            "last_error": None
        }
        
        # Prometheus metrics
        self._init_prometheus_metrics()
        
        # Historical data (last 24 hours)
        self.historical_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1440))  # 24 hours * 60 minutes
        
        # Health check results
        self.health_checks: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Metrics collector initialized")
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics."""
        # Request metrics
        self.request_counter = Counter(
            'synapse_mcp_requests_total',
            'Total number of requests',
            ['service', 'method', 'status']
        )
        
        self.request_duration = Histogram(
            'synapse_mcp_request_duration_seconds',
            'Request duration in seconds',
            ['service', 'method']
        )
        
        # Error metrics
        self.error_counter = Counter(
            'synapse_mcp_errors_total',
            'Total number of errors',
            ['service', 'error_type']
        )
        
        # Service metrics
        self.service_uptime = Gauge(
            'synapse_mcp_service_uptime_seconds',
            'Service uptime in seconds',
            ['service']
        )
        
        self.active_services = Gauge(
            'synapse_mcp_active_services',
            'Number of active services'
        )
        
        # System metrics
        self.memory_usage = Gauge(
            'synapse_mcp_memory_bytes',
            'Memory usage in bytes'
        )
        
        self.cpu_usage = Gauge(
            'synapse_mcp_cpu_percent',
            'CPU usage percentage'
        )
    
    def record_request(self, service_name: str, method: str = "unknown", duration: float = 0.0, status: str = "200"):
        """Record a request metric."""
        # Update service metrics
        if service_name not in self.service_metrics:
            self.service_metrics[service_name] = ServiceMetrics(service_name=service_name)
        
        metrics = self.service_metrics[service_name]
        metrics.request_count += 1
        metrics.total_response_time += duration
        metrics.avg_response_time = metrics.total_response_time / metrics.request_count
        metrics.min_response_time = min(metrics.min_response_time, duration)
        metrics.max_response_time = max(metrics.max_response_time, duration)
        metrics.last_request_time = datetime.now()
        
        # Update global metrics
        self.global_metrics["total_requests"] += 1
        self.global_metrics["last_request"] = datetime.now()
        
        # Update Prometheus metrics
        self.request_counter.labels(service=service_name, method=method, status=status).inc()
        self.request_duration.labels(service=service_name, method=method).observe(duration)
        
        # Record historical data
        self._record_historical_data(service_name, "requests", 1)
        self._record_historical_data(service_name, "response_time", duration)
        
        logger.debug(f"Recorded request for service '{service_name}': {duration:.3f}s")
    
    def record_error(self, service_name: str, error_type: str = "unknown", error_message: str = ""):
        """Record an error metric."""
        # Update service metrics
        if service_name not in self.service_metrics:
            self.service_metrics[service_name] = ServiceMetrics(service_name=service_name)
        
        metrics = self.service_metrics[service_name]
        metrics.error_count += 1
        metrics.last_error_time = datetime.now()
        
        # Update global metrics
        self.global_metrics["total_errors"] += 1
        self.global_metrics["last_error"] = datetime.now()
        
        # Update Prometheus metrics
        self.error_counter.labels(service=service_name, error_type=error_type).inc()
        
        # Record historical data
        self._record_historical_data(service_name, "errors", 1)
        
        logger.warning(f"Recorded error for service '{service_name}': {error_type} - {error_message}")
    
    def record_service_creation(self, service_name: str):
        """Record service creation."""
        if service_name not in self.service_metrics:
            self.service_metrics[service_name] = ServiceMetrics(service_name=service_name)
        
        # Update Prometheus metrics
        self.active_services.inc()
        self.service_uptime.labels(service=service_name).set(0)
        
        logger.info(f"Recorded service creation: '{service_name}'")
    
    def record_service_deletion(self, service_name: str):
        """Record service deletion."""
        if service_name in self.service_metrics:
            del self.service_metrics[service_name]
        
        # Update Prometheus metrics
        self.active_services.dec()
        
        logger.info(f"Recorded service deletion: '{service_name}'")
    
    def record_health_check(self, service_name: str, status: str, details: Dict[str, Any] = None):
        """Record a health check result."""
        self.health_checks[service_name] = {
            "status": status,
            "timestamp": datetime.now(),
            "details": details or {}
        }
        
        logger.debug(f"Recorded health check for service '{service_name}': {status}")
    
    def _record_historical_data(self, service_name: str, metric_type: str, value: float):
        """Record historical data point."""
        timestamp = datetime.now()
        data_point = MetricPoint(
            timestamp=timestamp,
            value=value,
            labels={"service": service_name, "type": metric_type}
        )
        
        key = f"{service_name}_{metric_type}"
        self.historical_data[key].append(data_point)
    
    def get_service_metrics(self, service_name: str) -> Dict[str, Any]:
        """Get metrics for a specific service."""
        if service_name not in self.service_metrics:
            return {"error": f"Service '{service_name}' not found"}
        
        metrics = self.service_metrics[service_name]
        
        # Calculate error rate
        error_rate = 0.0
        if metrics.request_count > 0:
            error_rate = (metrics.error_count / metrics.request_count) * 100
        
        # Calculate uptime
        uptime = 0.0
        if metrics.last_request_time:
            uptime = (datetime.now() - metrics.last_request_time).total_seconds()
        
        return {
            "service_name": service_name,
            "request_count": metrics.request_count,
            "error_count": metrics.error_count,
            "error_rate_percent": error_rate,
            "avg_response_time": metrics.avg_response_time,
            "min_response_time": metrics.min_response_time if metrics.min_response_time != float('inf') else 0.0,
            "max_response_time": metrics.max_response_time,
            "last_request_time": metrics.last_request_time.isoformat() if metrics.last_request_time else None,
            "last_error_time": metrics.last_error_time.isoformat() if metrics.last_error_time else None,
            "uptime_seconds": uptime
        }
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """Get global metrics."""
        uptime = (datetime.now() - self.global_metrics["uptime_start"]).total_seconds()
        
        # Calculate overall error rate
        error_rate = 0.0
        if self.global_metrics["total_requests"] > 0:
            error_rate = (self.global_metrics["total_errors"] / self.global_metrics["total_requests"]) * 100
        
        return {
            "total_requests": self.global_metrics["total_requests"],
            "total_errors": self.global_metrics["total_errors"],
            "error_rate_percent": error_rate,
            "uptime_seconds": uptime,
            "active_services": len(self.service_metrics),
            "last_request": self.global_metrics["last_request"].isoformat() if self.global_metrics["last_request"] else None,
            "last_error": self.global_metrics["last_error"].isoformat() if self.global_metrics["last_error"] else None
        }
    
    def get_all_service_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all services."""
        return {
            service_name: self.get_service_metrics(service_name)
            for service_name in self.service_metrics.keys()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        health_checks = {}
        overall_status = "healthy"
        
        for service_name, health_data in self.health_checks.items():
            health_checks[service_name] = {
                "status": health_data["status"],
                "timestamp": health_data["timestamp"].isoformat(),
                "details": health_data["details"]
            }
            
            if health_data["status"] != "healthy":
                overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": health_checks,
            "total_services": len(self.service_metrics),
            "healthy_services": len([h for h in health_checks.values() if h["status"] == "healthy"])
        }
    
    def get_historical_data(self, service_name: str, metric_type: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical data for a service and metric type."""
        key = f"{service_name}_{metric_type}"
        if key not in self.historical_data:
            return []
        
        # Filter data for the specified time range
        cutoff_time = datetime.now() - timedelta(hours=hours)
        filtered_data = [
            {
                "timestamp": point.timestamp.isoformat(),
                "value": point.value,
                "labels": point.labels
            }
            for point in self.historical_data[key]
            if point.timestamp >= cutoff_time
        ]
        
        return filtered_data
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics."""
        return generate_latest()
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in the specified format."""
        if format.lower() == "json":
            return json.dumps({
                "global": self.get_global_metrics(),
                "services": self.get_all_service_metrics(),
                "health": self.get_health_status()
            }, indent=2)
        elif format.lower() == "prometheus":
            return self.get_prometheus_metrics()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def reset_metrics(self, service_name: Optional[str] = None):
        """Reset metrics for a specific service or all services."""
        if service_name:
            if service_name in self.service_metrics:
                del self.service_metrics[service_name]
            logger.info(f"Reset metrics for service '{service_name}'")
        else:
            self.service_metrics.clear()
            self.global_metrics = {
                "total_requests": 0,
                "total_errors": 0,
                "uptime_start": datetime.now(),
                "last_request": None,
                "last_error": None
            }
            logger.info("Reset all metrics")
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """Clean up old historical data."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for key, data_queue in self.historical_data.items():
            # Remove old data points
            while data_queue and data_queue[0].timestamp < cutoff_time:
                data_queue.popleft()
        
        logger.debug(f"Cleaned up historical data older than {max_age_hours} hours")
    
    def close(self):
        """Clean up resources."""
        logger.info("Metrics collector closed")


class HealthChecker:
    """
    Health checker that performs health checks on services and components.
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize the health checker."""
        self.metrics = metrics_collector
        self.check_interval = 30  # seconds
        self.running = False
        self._check_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the health checker."""
        if self.running:
            return
        
        self.running = True
        self._check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Health checker started")
    
    async def stop(self):
        """Stop the health checker."""
        if not self.running:
            return
        
        self.running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health checker stopped")
    
    async def _health_check_loop(self):
        """Main health check loop."""
        while self.running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _perform_health_checks(self):
        """Perform health checks on all services."""
        for service_name in self.metrics.service_metrics.keys():
            try:
                health_status = await self._check_service_health(service_name)
                self.metrics.record_health_check(service_name, health_status["status"], health_status["details"])
            except Exception as e:
                logger.error(f"Error checking health for service '{service_name}': {e}")
                self.metrics.record_health_check(service_name, "error", {"error": str(e)})
    
    async def _check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service."""
        # This is a simplified health check implementation
        # In a real implementation, you would perform actual health checks
        
        metrics = self.metrics.service_metrics.get(service_name)
        if not metrics:
            return {"status": "unknown", "details": {"reason": "Service not found"}}
        
        # Check if service has recent activity
        if metrics.last_request_time:
            time_since_last_request = (datetime.now() - metrics.last_request_time).total_seconds()
            if time_since_last_request > 300:  # 5 minutes
                return {
                    "status": "warning",
                    "details": {
                        "reason": "No recent activity",
                        "last_request_seconds_ago": time_since_last_request
                    }
                }
        
        # Check error rate
        if metrics.request_count > 0:
            error_rate = (metrics.error_count / metrics.request_count) * 100
            if error_rate > 10:  # 10% error rate threshold
                return {
                    "status": "unhealthy",
                    "details": {
                        "reason": "High error rate",
                        "error_rate_percent": error_rate
                    }
                }
        
        return {"status": "healthy", "details": {}} 