"""
Metrics service for CloudWatch/Datadog integration.
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Dict, Optional
from datetime import datetime


class MetricsService:
    """Service for emitting metrics to CloudWatch/Datadog."""
    
    def __init__(self):
        """Initialize metrics service."""
        self.metrics_provider = os.getenv('METRICS_PROVIDER', 'cloudwatch')  # 'cloudwatch' or 'datadog'
        self.namespace = os.getenv('METRICS_NAMESPACE', 'SMSBot')
        
        # Initialize provider-specific clients
        if self.metrics_provider == 'cloudwatch':
            try:
                import boto3
                self.cloudwatch = boto3.client('cloudwatch', region_name=os.getenv('AWS_REGION', 'us-east-1'))
                self.enabled = True
            except ImportError:
                print("⚠️  boto3 not available - metrics disabled")
                self.cloudwatch = None
                self.enabled = False
        elif self.metrics_provider == 'datadog':
            try:
                from datadog import initialize, statsd
                self.datadog_api_key = os.getenv('DATADOG_API_KEY')
                self.datadog_app_key = os.getenv('DATADOG_APP_KEY')
                if self.datadog_api_key:
                    initialize(api_key=self.datadog_api_key, app_key=self.datadog_app_key)
                    self.statsd = statsd
                    self.enabled = True
                else:
                    print("⚠️  DATADOG_API_KEY not set - metrics disabled")
                    self.enabled = False
            except ImportError:
                print("⚠️  datadog library not available - metrics disabled")
                self.enabled = False
        else:
            self.enabled = False
    
    def increment(
        self,
        metric_name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None
    ):
        """Increment a counter metric."""
        if not self.enabled:
            return
        
        if self.metrics_provider == 'cloudwatch':
            self._cloudwatch_put_metric(metric_name, value, 'Count', tags)
        elif self.metrics_provider == 'datadog':
            dd_tags = self._format_datadog_tags(tags)
            self.statsd.increment(metric_name, value, tags=dd_tags)
    
    def gauge(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Set a gauge metric."""
        if not self.enabled:
            return
        
        if self.metrics_provider == 'cloudwatch':
            self._cloudwatch_put_metric(metric_name, value, 'None', tags)
        elif self.metrics_provider == 'datadog':
            dd_tags = self._format_datadog_tags(tags)
            self.statsd.gauge(metric_name, value, tags=dd_tags)
    
    def histogram(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record a histogram metric."""
        if not self.enabled:
            return
        
        if self.metrics_provider == 'cloudwatch':
            self._cloudwatch_put_metric(metric_name, value, 'None', tags)
        elif self.metrics_provider == 'datadog':
            dd_tags = self._format_datadog_tags(tags)
            self.statsd.histogram(metric_name, value, tags=dd_tags)
    
    def timer(self, metric_name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        return TimerContext(self, metric_name, tags)
    
    def _cloudwatch_put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        tags: Optional[Dict[str, str]] = None
    ):
        """Put metric to CloudWatch."""
        if not self.cloudwatch:
            return
        
        dimensions = []
        if tags:
            # CloudWatch dimensions (max 10, key+value <= 250 chars)
            for key, val in list(tags.items())[:10]:
                if len(key) <= 250 and len(str(val)) <= 250:
                    dimensions.append({'Name': key, 'Value': str(val)})
        
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': unit,
                        'Dimensions': dimensions,
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
        except Exception as e:
            print(f"Error putting CloudWatch metric: {e}")
    
    def _format_datadog_tags(self, tags: Optional[Dict[str, str]]) -> Optional[list]:
        """Format tags for Datadog."""
        if not tags:
            return None
        return [f"{key}:{value}" for key, value in tags.items()]


class TimerContext:
    """Context manager for timing operations."""
    
    def __init__(self, metrics_service: MetricsService, metric_name: str, tags: Optional[Dict[str, str]]):
        self.metrics_service = metrics_service
        self.metric_name = metric_name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        self.metrics_service.histogram(self.metric_name, duration * 1000, self.tags)  # Convert to milliseconds


# Global metrics instance
metrics = MetricsService()


# Convenience functions
def increment_counter(metric_name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
    """Increment a counter metric."""
    metrics.increment(metric_name, value, tags)


def set_gauge(metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
    """Set a gauge metric."""
    metrics.gauge(metric_name, value, tags)


def record_histogram(metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
    """Record a histogram metric."""
    metrics.histogram(metric_name, value, tags)
