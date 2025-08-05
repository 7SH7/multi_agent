import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    name: str
    condition: Callable[[float], bool]
    level: AlertLevel
    message: str
    cooldown_seconds: int = 300


@dataclass
class Alert:
    rule_name: str
    level: AlertLevel
    message: str
    value: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class SystemMonitor:
    def __init__(self, max_metrics_history: int = 10000):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_metrics_history))
        self.alerts: List[Alert] = []
        self.alert_rules: Dict[str, AlertRule] = {}
        self.last_alert_times: Dict[str, datetime] = {}
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self._start_time = datetime.now()

    def record_metric(self, name: str, value: float, metric_type: MetricType,
                      labels: Optional[Dict[str, str]] = None, metadata: Optional[Dict[str, Any]] = None):
        metric = PerformanceMetric(
            name=name,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {},
            metadata=metadata or {}
        )

        self.metrics[name].append(metric)

        # Update internal counters
        if metric_type == MetricType.COUNTER:
            self.counters[name] += value
        elif metric_type == MetricType.GAUGE:
            self.gauges[name] = value
        elif metric_type == MetricType.HISTOGRAM:
            self.histograms[name].append(value)

        # Check alert rules
        self._check_alerts(name, value)

    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        self.record_metric(name, value, MetricType.COUNTER, labels)

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        self.record_metric(name, value, MetricType.GAUGE, labels)

    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        self.record_metric(name, value, MetricType.HISTOGRAM, labels)

    def time_function(self, name: str, labels: Optional[Dict[str, str]] = None):
        def decorator(func):
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    self.record_metric(f"{name}_duration", duration, MetricType.TIMER, labels)

            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    self.record_metric(f"{name}_duration", duration, MetricType.TIMER, labels)

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    def add_alert_rule(self, rule: AlertRule):
        self.alert_rules[rule.name] = rule

    def _check_alerts(self, metric_name: str, value: float):
        current_time = datetime.now()

        for rule_name, rule in self.alert_rules.items():
            if rule_name in self.last_alert_times:
                time_since_last = current_time - self.last_alert_times[rule_name]
                if time_since_last.total_seconds() < rule.cooldown_seconds:
                    continue

            if rule.condition(value):
                alert = Alert(
                    rule_name=rule_name,
                    level=rule.level,
                    message=rule.message.format(value=value, metric=metric_name),
                    value=value,
                    timestamp=current_time
                )
                self.alerts.append(alert)
                self.last_alert_times[rule_name] = current_time

                # Log alert (in production, send to alerting system)
                print(f"ALERT [{alert.level.value.upper()}] {alert.message}")

    def get_metric_summary(self, name: str, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        if name not in self.metrics:
            return {}

        metrics = list(self.metrics[name])

        if time_window:
            cutoff_time = datetime.now() - time_window
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]

        if not metrics:
            return {}

        values = [m.value for m in metrics]

        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'sum': sum(values),
            'latest': values[-1],
            'first_timestamp': metrics[0].timestamp.isoformat(),
            'latest_timestamp': metrics[-1].timestamp.isoformat()
        }

    def get_all_metrics_summary(self, time_window: Optional[timedelta] = None) -> Dict[str, Dict[str, Any]]:
        return {
            name: self.get_metric_summary(name, time_window)
            for name in self.metrics.keys()
        }

    def get_active_alerts(self) -> List[Alert]:
        return [alert for alert in self.alerts if not alert.resolved]

    def resolve_alert(self, rule_name: str):
        for alert in self.alerts:
            if alert.rule_name == rule_name and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()

    def get_system_health(self) -> Dict[str, Any]:
        current_time = datetime.now()
        uptime = current_time - self._start_time

        # Agent health metrics
        agent_metrics = {}
        for agent in ['gpt', 'gemini', 'clova']:
            success_count = self.counters.get(f'agent_{agent}_success', 0)
            error_count = self.counters.get(f'agent_{agent}_error', 0)
            total = success_count + error_count
            success_rate = (success_count / total * 100) if total > 0 else 0

            agent_metrics[agent] = {
                'success_count': success_count,
                'error_count': error_count,
                'success_rate': round(success_rate, 2)
            }

        # System metrics
        active_alerts = self.get_active_alerts()

        return {
            'uptime_seconds': uptime.total_seconds(),
            'uptime_human': str(uptime),
            'total_requests': self.counters.get('total_requests', 0),
            'active_sessions': self.gauges.get('active_sessions', 0),
            'agent_health': agent_metrics,
            'active_alerts_count': len(active_alerts),
            'active_alerts': [
                {
                    'rule': alert.rule_name,
                    'level': alert.level.value,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat()
                }
                for alert in active_alerts
            ],
            'memory_usage_mb': self.gauges.get('memory_usage_mb', 0),
            'cpu_usage_percent': self.gauges.get('cpu_usage_percent', 0)
        }


class AlertManager:
    def __init__(self, monitor: SystemMonitor):
        self.monitor = monitor
        self._setup_default_rules()

    def _setup_default_rules(self):
        # Agent error rate alerts
        self.monitor.add_alert_rule(AlertRule(
            name="high_agent_error_rate",
            condition=lambda x: x > 0.1,  # More than 10% error rate
            level=AlertLevel.WARNING,
            message="Agent error rate is high: {value:.2%}",
            cooldown_seconds=300
        ))

        # Response time alerts
        self.monitor.add_alert_rule(AlertRule(
            name="slow_response_time",
            condition=lambda x: x > 30.0,  # More than 30 seconds
            level=AlertLevel.WARNING,
            message="Response time is slow: {value:.2f} seconds",
            cooldown_seconds=120
        ))

        # Memory usage alerts
        self.monitor.add_alert_rule(AlertRule(
            name="high_memory_usage",
            condition=lambda x: x > 1000,  # More than 1GB
            level=AlertLevel.WARNING,
            message="Memory usage is high: {value:.2f} MB",
            cooldown_seconds=600
        ))

        # Session count alerts
        self.monitor.add_alert_rule(AlertRule(
            name="too_many_sessions",
            condition=lambda x: x > 100,  # More than 100 active sessions
            level=AlertLevel.WARNING,
            message="Too many active sessions: {value}",
            cooldown_seconds=300
        ))

    def send_alert(self, alert: Alert):
        # In production, this would send to Slack, email, PagerDuty, etc.
        print(f"🚨 ALERT: [{alert.level.value.upper()}] {alert.message}")

    def check_and_send_alerts(self):
        for alert in self.monitor.get_active_alerts():
            self.send_alert(alert)


# Global monitor instance
_system_monitor = None


def get_system_monitor() -> SystemMonitor:
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor