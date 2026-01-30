"""
Data Validation and Quality Assurance Module

This module provides comprehensive validation and quality assurance for SNMP data collection.
It ensures data integrity, consistency, and reliability across different vendors and database types.

Features:
- Data type validation and range checking
- Consistency validation across related metrics
- Anomaly detection and outlier identification
- Data quality scoring and reporting
- Automatic data cleaning and correction
- Trend analysis and pattern validation
- Performance monitoring and alerting
- Custom validation rules engine
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
import math
from collections import defaultdict, deque

from ..utils.data_structures import (
    OLTData, ONUData, PortData, DeviceData,
    ONUStatus, PortStatus, DeviceStatus
)

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DataQualityLevel(Enum):
    """Data quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"


@dataclass
class ValidationIssue:
    """Validation issue description."""
    issue_id: str
    severity: ValidationSeverity
    category: str
    description: str
    field_name: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    recommendation: Optional[str] = None
    auto_correctable: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    quality_level: DataQualityLevel
    quality_score: float  # 0.0 to 1.0
    issues: List[ValidationIssue] = field(default_factory=list)
    corrected_fields: Dict[str, Any] = field(default_factory=dict)
    validation_time: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0


@dataclass
class ValidationRule:
    """Validation rule definition."""
    rule_id: str
    name: str
    description: str
    data_types: List[str]  # ['olt', 'onu', 'port', 'device']
    field_name: Optional[str] = None
    validation_function: Callable = None
    severity: ValidationSeverity = ValidationSeverity.WARNING
    auto_correct: bool = False
    correction_function: Callable = None
    enabled: bool = True


class ValidationMetrics:
    """Validation metrics tracking."""

    def __init__(self):
        self.total_validations = 0
        self.successful_validations = 0
        self.failed_validations = 0
        self.issues_by_severity = defaultdict(int)
        self.issues_by_category = defaultdict(int)
        self.average_quality_score = 0.0
        self.validation_history = deque(maxlen=1000)
        self.field_error_rates = defaultdict(int)
        self.trend_data = defaultdict(lambda: deque(maxlen=100))

    def record_validation(self, result: ValidationResult):
        """Record validation result metrics."""
        self.total_validations += 1

        if result.is_valid:
            self.successful_validations += 1
        else:
            self.failed_validations += 1

        # Count issues by severity and category
        for issue in result.issues:
            self.issues_by_severity[issue.severity.value] += 1
            self.issues_by_category[issue.category] += 1

            if issue.field_name:
                self.field_error_rates[issue.field_name] += 1

        # Update average quality score
        total_score = self.average_quality_score * (self.total_validations - 1) + result.quality_score
        self.average_quality_score = total_score / self.total_validations

        # Store in history
        self.validation_history.append({
            'timestamp': result.validation_time,
            'quality_score': result.quality_score,
            'issues_count': len(result.issues),
            'processing_time': result.processing_time
        })


class OLTDataValidator:
    """Comprehensive OLT data validator."""

    def __init__(self):
        self.validation_rules = self._create_validation_rules()
        self.metrics = ValidationMetrics()
        self.historical_data = defaultdict(lambda: deque(maxlen=100))

    def _create_validation_rules(self) -> List[ValidationRule]:
        """Create built-in validation rules."""
        rules = []

        # OLT-specific rules
        rules.extend([
            ValidationRule(
                rule_id="olt_001",
                name="OLT ID Validation",
                description="OLT ID must be present and non-empty",
                data_types=["olt"],
                field_name="olt_id",
                validation_function=lambda data: bool(getattr(data, 'olt_id', None) and getattr(data, 'olt_id', '').strip()),
                severity=ValidationSeverity.ERROR,
                auto_correct=False
            ),
            ValidationRule(
                rule_id="olt_002",
                name="CPU Utilization Range",
                description="CPU utilization must be between 0 and 100",
                data_types=["olt"],
                field_name="cpu_utilization",
                validation_function=lambda data: getattr(data, 'cpu_utilization', None) is None or 0 <= getattr(data, 'cpu_utilization', 0) <= 100,
                severity=ValidationSeverity.ERROR,
                auto_correct=True,
                correction_function=lambda data: self._correct_range(data, 'cpu_utilization', 0, 100)
            ),
            ValidationRule(
                rule_id="olt_003",
                name="Memory Utilization Range",
                description="Memory utilization must be between 0 and 100",
                data_types=["olt"],
                field_name="memory_utilization",
                validation_function=lambda data: getattr(data, 'memory_utilization', None) is None or 0 <= getattr(data, 'memory_utilization', 0) <= 100,
                severity=ValidationSeverity.ERROR,
                auto_correct=True,
                correction_function=lambda data: self._correct_range(data, 'memory_utilization', 0, 100)
            ),
            ValidationRule(
                rule_id="olt_004",
                name="Temperature Range",
                description="Temperature must be within reasonable operating range (-40 to 85°C)",
                data_types=["olt"],
                field_name="temperature",
                validation_function=lambda data: getattr(data, 'temperature', None) is None or -40 <= getattr(data, 'temperature', 0) <= 85,
                severity=ValidationSeverity.WARNING,
                auto_correct=False
            ),
            ValidationRule(
                rule_id="olt_005",
                name="ONU Count Consistency",
                description="Active ONUs cannot exceed total ONUs",
                data_types=["olt"],
                validation_function=self._validate_onu_count_consistency,
                severity=ValidationSeverity.ERROR,
                auto_correct=True,
                correction_function=self._correct_onu_count
            ),
            ValidationRule(
                rule_id="olt_006",
                name="Optical Power Range",
                description="Optical power must be within typical range (-50 to +30 dBm)",
                data_types=["olt"],
                validation_function=self._validate_optical_power_range,
                severity=ValidationSeverity.WARNING,
                auto_correct=False
            ),
        ])

        # ONU-specific rules
        rules.extend([
            ValidationRule(
                rule_id="onu_001",
                name="ONU ID Validation",
                description="ONU ID must be present and follow proper format",
                data_types=["onu"],
                field_name="onu_id",
                validation_function=lambda data: bool(getattr(data, 'onu_id', None) and getattr(data, 'onu_id', '').strip()),
                severity=ValidationSeverity.ERROR,
                auto_correct=False
            ),
            ValidationRule(
                rule_id="onu_002",
                name="ONU Distance Range",
                description="ONU distance must be positive and within reasonable range (0-100km)",
                data_types=["onu"],
                field_name="distance",
                validation_function=lambda data: getattr(data, 'distance', None) is None or (0 <= getattr(data, 'distance', 0) <= 100000),
                severity=ValidationSeverity.WARNING,
                auto_correct=True,
                correction_function=lambda data: self._correct_range(data, 'distance', 0, 100000)
            ),
            ValidationRule(
                rule_id="onu_003",
                name="ONU Optical Power Range",
                description="ONU optical power must be within typical range (-50 to +10 dBm)",
                data_types=["onu"],
                validation_function=self._validate_onu_optical_power,
                severity=ValidationSeverity.WARNING,
                auto_correct=False
            ),
            ValidationRule(
                rule_id="onu_004",
                name="ONU Status Consistency",
                description="ONU status should be consistent with operational state",
                data_types=["onu"],
                validation_function=self._validate_onu_status_consistency,
                severity=ValidationSeverity.WARNING,
                auto_correct=False
            ),
        ])

        # Port-specific rules
        rules.extend([
            ValidationRule(
                rule_id="port_001",
                name="Port ID Validation",
                description="Port ID must be non-negative",
                data_types=["port"],
                field_name="port_id",
                validation_function=lambda data: getattr(data, 'port_id', -1) >= 0,
                severity=ValidationSeverity.ERROR,
                auto_correct=False
            ),
            ValidationRule(
                rule_id="port_002",
                name="Port Speed Consistency",
                description="Current speed cannot exceed maximum speed",
                data_types=["port"],
                validation_function=self._validate_port_speed_consistency,
                severity=ValidationSeverity.WARNING,
                auto_correct=True,
                correction_function=self._correct_port_speed
            ),
        ])

        return rules

    async def validate_olt_data(self, olt_data: OLTData, historical_context: bool = True) -> ValidationResult:
        """
        Validate OLT data comprehensively.

        Args:
            olt_data: OLT data to validate
            historical_context: Whether to use historical data for validation

        Returns:
            ValidationResult with detailed findings
        """
        start_time = datetime.now()
        issues = []
        corrected_fields = {}

        try:
            # Get applicable rules
            applicable_rules = [rule for rule in self.validation_rules if 'olt' in rule.data_types and rule.enabled]

            # Apply each rule
            for rule in applicable_rules:
                try:
                    rule_result = await self._apply_rule(olt_data, rule)
                    if rule_result:
                        issue, correction = rule_result
                        issues.append(issue)
                        if correction:
                            corrected_fields.update(correction)

                except Exception as e:
                    logger.error(f"Error applying rule {rule.rule_id}: {e}")

            # Historical context validation
            if historical_context:
                historical_issues = await self._validate_historical_context(olt_data)
                issues.extend(historical_issues)

            # Cross-field validation
            cross_field_issues = await self._validate_cross_fields(olt_data)
            issues.extend(cross_field_issues)

            # Anomaly detection
            anomaly_issues = await self._detect_anomalies(olt_data)
            issues.extend(anomaly_issues)

            # Calculate quality score
            quality_score = self._calculate_quality_score(issues, len(applicable_rules))
            quality_level = self._determine_quality_level(quality_score)

            # Store historical data
            self.historical_data[olt_data.olt_id].append({
                'timestamp': datetime.now(),
                'data': olt_data,
                'quality_score': quality_score
            })

            # Create result
            processing_time = (datetime.now() - start_time).total_seconds()
            result = ValidationResult(
                is_valid=quality_level != DataQualityLevel.INVALID,
                quality_level=quality_level,
                quality_score=quality_score,
                issues=issues,
                corrected_fields=corrected_fields,
                processing_time=processing_time
            )

            # Record metrics
            self.metrics.record_validation(result)

            return result

        except Exception as e:
            logger.error(f"Error during OLT data validation: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()

            return ValidationResult(
                is_valid=False,
                quality_level=DataQualityLevel.INVALID,
                quality_score=0.0,
                issues=[ValidationIssue(
                    issue_id="validation_error",
                    severity=ValidationSeverity.CRITICAL,
                    category="system",
                    description=f"Validation system error: {str(e)}"
                )],
                processing_time=processing_time
            )

    async def validate_onu_data(self, onu_data: ONUData, olt_context: Optional[OLTData] = None) -> ValidationResult:
        """Validate ONU data with OLT context."""
        start_time = datetime.now()
        issues = []
        corrected_fields = {}

        try:
            # Get applicable rules
            applicable_rules = [rule for rule in self.validation_rules if 'onu' in rule.data_types and rule.enabled]

            # Apply each rule
            for rule in applicable_rules:
                try:
                    rule_result = await self._apply_rule(onu_data, rule)
                    if rule_result:
                        issue, correction = rule_result
                        issues.append(issue)
                        if correction:
                            corrected_fields.update(correction)

                except Exception as e:
                    logger.error(f"Error applying rule {rule.rule_id}: {e}")

            # OLT context validation
            if olt_context:
                context_issues = await self._validate_onu_olt_context(onu_data, olt_context)
                issues.extend(context_issues)

            # Calculate quality score
            quality_score = self._calculate_quality_score(issues, len(applicable_rules))
            quality_level = self._determine_quality_level(quality_score)

            processing_time = (datetime.now() - start_time).total_seconds()
            result = ValidationResult(
                is_valid=quality_level != DataQualityLevel.INVALID,
                quality_level=quality_level,
                quality_score=quality_score,
                issues=issues,
                corrected_fields=corrected_fields,
                processing_time=processing_time
            )

            self.metrics.record_validation(result)
            return result

        except Exception as e:
            logger.error(f"Error during ONU data validation: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()

            return ValidationResult(
                is_valid=False,
                quality_level=DataQualityLevel.INVALID,
                quality_score=0.0,
                issues=[ValidationIssue(
                    issue_id="validation_error",
                    severity=ValidationSeverity.CRITICAL,
                    category="system",
                    description=f"Validation system error: {str(e)}"
                )],
                processing_time=processing_time
            )

    async def validate_port_data(self, port_data: PortData) -> ValidationResult:
        """Validate port data."""
        start_time = datetime.now()
        issues = []
        corrected_fields = {}

        try:
            # Get applicable rules
            applicable_rules = [rule for rule in self.validation_rules if 'port' in rule.data_types and rule.enabled]

            # Apply each rule
            for rule in applicable_rules:
                try:
                    rule_result = await self._apply_rule(port_data, rule)
                    if rule_result:
                        issue, correction = rule_result
                        issues.append(issue)
                        if correction:
                            corrected_fields.update(correction)

                except Exception as e:
                    logger.error(f"Error applying rule {rule.rule_id}: {e}")

            # Calculate quality score
            quality_score = self._calculate_quality_score(issues, len(applicable_rules))
            quality_level = self._determine_quality_level(quality_score)

            processing_time = (datetime.now() - start_time).total_seconds()
            result = ValidationResult(
                is_valid=quality_level != DataQualityLevel.INVALID,
                quality_level=quality_level,
                quality_score=quality_score,
                issues=issues,
                corrected_fields=corrected_fields,
                processing_time=processing_time
            )

            self.metrics.record_validation(result)
            return result

        except Exception as e:
            logger.error(f"Error during port data validation: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()

            return ValidationResult(
                is_valid=False,
                quality_level=DataQualityLevel.INVALID,
                quality_score=0.0,
                issues=[ValidationIssue(
                    issue_id="validation_error",
                    severity=ValidationSeverity.CRITICAL,
                    category="system",
                    description=f"Validation system error: {str(e)}"
                )],
                processing_time=processing_time
            )

    async def _apply_rule(self, data: Union[OLTData, ONUData, PortData], rule: ValidationRule) -> Optional[Tuple[ValidationIssue, Dict[str, Any]]]:
        """Apply a validation rule to data."""
        try:
            # Execute validation function
            is_valid = rule.validation_function(data)

            if not is_valid:
                # Create issue
                actual_value = str(getattr(data, rule.field_name, 'N/A')) if rule.field_name else 'N/A'
                expected_value = "Valid value"  # Could be customized per rule

                issue = ValidationIssue(
                    issue_id=rule.rule_id,
                    severity=rule.severity,
                    category=rule.field_name or "general",
                    description=rule.description,
                    field_name=rule.field_name,
                    expected_value=expected_value,
                    actual_value=actual_value,
                    recommendation=self._get_rule_recommendation(rule),
                    auto_correctable=rule.auto_correct
                )

                # Apply correction if possible
                correction = {}
                if rule.auto_correct and rule.correction_function:
                    correction = rule.correction_function(data)

                return issue, correction

            return None

        except Exception as e:
            logger.error(f"Error applying rule {rule.rule_id}: {e}")
            return None

    async def _validate_historical_context(self, olt_data: OLTData) -> List[ValidationIssue]:
        """Validate data against historical context."""
        issues = []

        try:
            historical = self.historical_data.get(olt_data.olt_id, [])
            if len(historical) < 2:
                return issues  # Not enough historical data

            # Get recent historical data
            recent_data = list(historical)[-10:]  # Last 10 records

            # Check for unusual changes
            if len(recent_data) >= 2:
                latest = recent_data[-1]['data']
                previous = recent_data[-2]['data']

                # Check for CPU utilization spikes
                if latest.cpu_utilization and previous.cpu_utilization:
                    change = abs(latest.cpu_utilization - previous.cpu_utilization)
                    if change > 50:  # More than 50% change
                        issues.append(ValidationIssue(
                            issue_id="hist_cpu_spike",
                            severity=ValidationSeverity.WARNING,
                            category="performance",
                            description=f"Large CPU utilization change detected: {change:.1f}%",
                            actual_value=f"{latest.cpu_utilization:.1f}%",
                            expected_value=f"Similar to previous: {previous.cpu_utilization:.1f}%"
                        ))

                # Check for memory utilization spikes
                if latest.memory_utilization and previous.memory_utilization:
                    change = abs(latest.memory_utilization - previous.memory_utilization)
                    if change > 40:  # More than 40% change
                        issues.append(ValidationIssue(
                            issue_id="hist_memory_spike",
                            severity=ValidationSeverity.WARNING,
                            category="performance",
                            description=f"Large memory utilization change detected: {change:.1f}%",
                            actual_value=f"{latest.memory_utilization:.1f}%",
                            expected_value=f"Similar to previous: {previous.memory_utilization:.1f}%"
                        ))

                # Check for ONU count changes
                onu_change = latest.total_onus - previous.total_onus
                if abs(onu_change) > 10:  # More than 10 ONUs added/removed
                    issues.append(ValidationIssue(
                        issue_id="hist_onu_count_change",
                        severity=ValidationSeverity.INFO,
                        category="inventory",
                        description=f"ONU count changed significantly: {onu_change:+d} ONUs",
                        actual_value=str(latest.total_onus),
                        expected_value=f"Similar to previous: {previous.total_onus}"
                    ))

        except Exception as e:
            logger.error(f"Error in historical validation: {e}")

        return issues

    async def _validate_cross_fields(self, olt_data: OLTData) -> List[ValidationIssue]:
        """Validate cross-field consistency."""
        issues = []

        try:
            # Validate that active ONUs <= total ONUs
            if olt_data.active_onus and olt_data.total_onus:
                if olt_data.active_onus > olt_data.total_onus:
                    issues.append(ValidationIssue(
                        issue_id="cross_onu_count",
                        severity=ValidationSeverity.ERROR,
                        category="consistency",
                        description="Active ONUs cannot exceed total ONUs",
                        actual_value=f"Active: {olt_data.active_onus}, Total: {olt_data.total_onus}",
                        recommendation="Check ONU counting logic or data collection"
                    ))

            # Validate temperature vs performance correlation
            if olt_data.temperature and olt_data.cpu_utilization:
                if olt_data.temperature > 75 and olt_data.cpu_utilization < 30:
                    issues.append(ValidationIssue(
                        issue_id="cross_temp_performance",
                        severity=ValidationSeverity.INFO,
                        category="correlation",
                        description="High temperature with low CPU utilization may indicate cooling issues",
                        actual_value=f"Temp: {olt_data.temperature}°C, CPU: {olt_data.cpu_utilization}%",
                        recommendation="Check device cooling system"
                    ))

        except Exception as e:
            logger.error(f"Error in cross-field validation: {e}")

        return issues

    async def _detect_anomalies(self, olt_data: OLTData) -> List[ValidationIssue]:
        """Detect anomalies in the data."""
        issues = []

        try:
            # Get historical data for anomaly detection
            historical = self.historical_data.get(olt_data.olt_id, [])
            if len(historical) < 5:
                return issues  # Not enough data for anomaly detection

            # Extract metric history
            cpu_history = [h['data'].cpu_utilization for h in historical if h['data'].cpu_utilization is not None]
            memory_history = [h['data'].memory_utilization for h in historical if h['data'].memory_utilization is not None]
            temp_history = [h['data'].temperature for h in historical if h['data'].temperature is not None]

            # Detect CPU anomalies
            if cpu_history and olt_data.cpu_utilization:
                mean_cpu = statistics.mean(cpu_history)
                stdev_cpu = statistics.stdev(cpu_history) if len(cpu_history) > 1 else 0

                if stdev_cpu > 0:
                    z_score = abs(olt_data.cpu_utilization - mean_cpu) / stdev_cpu
                    if z_score > 3:  # More than 3 standard deviations
                        issues.append(ValidationIssue(
                            issue_id="anomaly_cpu",
                            severity=ValidationSeverity.WARNING,
                            category="anomaly",
                            description=f"CPU utilization anomaly detected (z-score: {z_score:.1f})",
                            actual_value=f"{olt_data.cpu_utilization:.1f}%",
                            expected_value=f"Typical range: {mean_cpu:.1f}% ± {stdev_cpu:.1f}%"
                        ))

            # Detect memory anomalies
            if memory_history and olt_data.memory_utilization:
                mean_mem = statistics.mean(memory_history)
                stdev_mem = statistics.stdev(memory_history) if len(memory_history) > 1 else 0

                if stdev_mem > 0:
                    z_score = abs(olt_data.memory_utilization - mean_mem) / stdev_mem
                    if z_score > 3:
                        issues.append(ValidationIssue(
                            issue_id="anomaly_memory",
                            severity=ValidationSeverity.WARNING,
                            category="anomaly",
                            description=f"Memory utilization anomaly detected (z-score: {z_score:.1f})",
                            actual_value=f"{olt_data.memory_utilization:.1f}%",
                            expected_value=f"Typical range: {mean_mem:.1f}% ± {stdev_mem:.1f}%"
                        ))

        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")

        return issues

    def _calculate_quality_score(self, issues: List[ValidationIssue], total_rules: int) -> float:
        """Calculate overall data quality score."""
        if total_rules == 0:
            return 1.0

        # Weight issues by severity
        severity_weights = {
            ValidationSeverity.INFO: 0.1,
            ValidationSeverity.WARNING: 0.3,
            ValidationSeverity.ERROR: 0.6,
            ValidationSeverity.CRITICAL: 1.0
        }

        total_penalty = sum(severity_weights.get(issue.severity, 0.3) for issue in issues)
        max_penalty = total_rules * 1.0

        # Calculate score (0.0 to 1.0)
        score = max(0.0, 1.0 - (total_penalty / max_penalty))
        return score

    def _determine_quality_level(self, score: float) -> DataQualityLevel:
        """Determine data quality level from score."""
        if score >= 0.95:
            return DataQualityLevel.EXCELLENT
        elif score >= 0.85:
            return DataQualityLevel.GOOD
        elif score >= 0.70:
            return DataQualityLevel.FAIR
        elif score >= 0.50:
            return DataQualityLevel.POOR
        else:
            return DataQualityLevel.INVALID

    def _get_rule_recommendation(self, rule: ValidationRule) -> str:
        """Get recommendation for a validation rule."""
        recommendations = {
            "cpu_utilization": "Check device load and investigate performance issues",
            "memory_utilization": "Monitor memory usage and consider device restart if needed",
            "temperature": "Check device cooling and environmental conditions",
            "onu_id": "Verify ONU configuration and data collection process",
            "distance": "Check ONU physical distance and fiber connection",
            "optical_power": "Verify optical connections and signal levels",
        }
        return recommendations.get(rule.field_name, "Review data source and collection process")

    # Validation rule functions
    def _validate_onu_count_consistency(self, data: OLTData) -> bool:
        """Validate ONU count consistency."""
        if not data.active_onus or not data.total_onus:
            return True  # No data to validate
        return data.active_onus <= data.total_onus

    def _correct_onu_count(self, data: OLTData) -> Dict[str, Any]:
        """Correct ONU count inconsistency."""
        correction = {}
        if data.active_onus and data.total_onus and data.active_onus > data.total_onus:
            correction['active_onus'] = data.total_onus
            data.active_onus = data.total_onus
        return correction

    def _validate_optical_power_range(self, data: OLTData) -> bool:
        """Validate optical power range."""
        if data.optical_power_tx is None and data.optical_power_rx is None:
            return True  # No optical power data to validate

        if data.optical_power_tx is not None:
            if not -50 <= data.optical_power_tx <= 30:
                return False

        if data.optical_power_rx is not None:
            if not -50 <= data.optical_power_rx <= 30:
                return False

        return True

    def _validate_onu_optical_power(self, data: ONUData) -> bool:
        """Validate ONU optical power range."""
        if data.optical_power_tx is None and data.optical_power_rx is None:
            return True

        if data.optical_power_tx is not None:
            if not -50 <= data.optical_power_tx <= 10:
                return False

        if data.optical_power_rx is not None:
            if not -50 <= data.optical_power_rx <= 10:
                return False

        return True

    def _validate_onu_status_consistency(self, data: ONUData) -> bool:
        """Validate ONU status consistency."""
        # This is a simplified validation - could be more sophisticated
        if data.status == ONUStatus.ACTIVE:
            return data.optical_power_rx is not None and data.optical_power_rx > -40
        return True

    def _validate_port_speed_consistency(self, data: PortData) -> bool:
        """Validate port speed consistency."""
        if data.current_speed is None or data.max_speed is None:
            return True
        return data.current_speed <= data.max_speed

    def _correct_port_speed(self, data: PortData) -> Dict[str, Any]:
        """Correct port speed inconsistency."""
        correction = {}
        if data.current_speed and data.max_speed and data.current_speed > data.max_speed:
            correction['current_speed'] = data.max_speed
            data.current_speed = data.max_speed
        return correction

    def _correct_range(self, data: Any, field_name: str, min_val: float, max_val: float) -> Dict[str, Any]:
        """Correct value to be within range."""
        correction = {}
        current_value = getattr(data, field_name, None)

        if current_value is not None:
            if current_value < min_val:
                correction[field_name] = min_val
                setattr(data, field_name, min_val)
            elif current_value > max_val:
                correction[field_name] = max_val
                setattr(data, field_name, max_val)

        return correction

    async def _validate_onu_olt_context(self, onu_data: ONUData, olt_data: OLTData) -> List[ValidationIssue]:
        """Validate ONU data in OLT context."""
        issues = []

        try:
            # Check if ONU belongs to OLT
            if onu_data.olt_id != olt_data.olt_id:
                issues.append(ValidationIssue(
                    issue_id="context_olt_mismatch",
                    severity=ValidationSeverity.ERROR,
                    category="consistency",
                    description="ONU OLT ID does not match OLT data",
                    actual_value=onu_data.olt_id,
                    expected_value=olt_data.olt_id
                ))

            # Check port validity
            if onu_data.port_id and olt_data.ports:
                port_exists = any(p.port_id == onu_data.port_id for p in olt_data.ports)
                if not port_exists:
                    issues.append(ValidationIssue(
                        issue_id="context_port_not_found",
                        severity=ValidationSeverity.WARNING,
                        category="consistency",
                        description=f"ONU port {onu_data.port_id} not found in OLT port list",
                        actual_value=str(onu_data.port_id)
                    ))

        except Exception as e:
            logger.error(f"Error in ONU-OLT context validation: {e}")

        return issues

    def get_validation_metrics(self) -> Dict[str, Any]:
        """Get validation performance metrics."""
        return {
            'total_validations': self.metrics.total_validations,
            'successful_validations': self.metrics.successful_validations,
            'failed_validations': self.metrics.failed_validations,
            'success_rate': self.metrics.successful_validations / max(self.metrics.total_validations, 1),
            'average_quality_score': self.metrics.average_quality_score,
            'issues_by_severity': dict(self.metrics.issues_by_severity),
            'issues_by_category': dict(self.metrics.issues_by_category),
            'field_error_rates': dict(self.metrics.field_error_rates),
            'enabled_rules': len([r for r in self.validation_rules if r.enabled]),
            'total_rules': len(self.validation_rules)
        }

    def add_custom_rule(self, rule: ValidationRule) -> bool:
        """Add a custom validation rule."""
        try:
            # Validate rule structure
            if not rule.rule_id or not rule.validation_function:
                logger.error("Invalid rule structure")
                return False

            # Check for duplicate rule ID
            if any(r.rule_id == rule.rule_id for r in self.validation_rules):
                logger.error(f"Rule ID {rule.rule_id} already exists")
                return False

            self.validation_rules.append(rule)
            logger.info(f"Added custom validation rule: {rule.rule_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding custom rule: {e}")
            return False

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a validation rule by ID."""
        try:
            for i, rule in enumerate(self.validation_rules):
                if rule.rule_id == rule_id:
                    del self.validation_rules[i]
                    logger.info(f"Removed validation rule: {rule_id}")
                    return True

            logger.warning(f"Rule {rule_id} not found")
            return False

        except Exception as e:
            logger.error(f"Error removing rule: {e}")
            return False

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a validation rule."""
        for rule in self.validation_rules:
            if rule.rule_id == rule_id:
                rule.enabled = True
                logger.info(f"Enabled validation rule: {rule_id}")
                return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a validation rule."""
        for rule in self.validation_rules:
            if rule.rule_id == rule_id:
                rule.enabled = False
                logger.info(f"Disabled validation rule: {rule_id}")
                return True
        return False