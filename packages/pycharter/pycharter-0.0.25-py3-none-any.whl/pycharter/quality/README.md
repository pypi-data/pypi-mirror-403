# Quality Assurance Module

The Quality Assurance module provides comprehensive data quality checking, metrics calculation, violation tracking, and reporting capabilities for PyCharter.

## Overview

The quality module enables you to:
- **Run quality checks** against data contracts
- **Calculate quality metrics** (scores, accuracy, completeness, violation rates)
- **Track violations** for audit and remediation
- **Check thresholds** and get alerts when quality degrades
- **Generate reports** with detailed quality insights

## Core Components

### QualityCheck

The main class for running quality checks. It's orchestrator-agnostic and can be used:
- Standalone (CLI, API, Python scripts)
- Within orchestrators (Airflow, Prefect, Dagster)
- Via API calls

```python
from pycharter import QualityCheck, QualityCheckOptions

# Create quality check instance
check = QualityCheck(store=store)  # Optional: pass metadata store

# Run quality check
report = check.run(
    schema_id="user_schema_v1",  # Or use contract=...
    data="data/users.json",  # File path, list, or callable
    options=QualityCheckOptions(
        record_violations=True,
        calculate_metrics=True,
        check_thresholds=True,
    )
)

print(f"Quality Score: {report.quality_score.overall_score:.2f}/100")
print(f"Passed: {report.passed}")
```

### QualityMetrics

Calculates quality scores and metrics from validation results:

```python
from pycharter.quality import QualityMetrics

metrics = QualityMetrics()
quality_score = metrics.calculate_quality_score(validation_results)

print(f"Overall Score: {quality_score.overall_score}")
print(f"Accuracy: {quality_score.accuracy:.2%}")
print(f"Completeness: {quality_score.completeness:.2%}")
```

### ViolationTracker

Tracks and manages data quality violations:

```python
from pycharter.quality import ViolationTracker

tracker = ViolationTracker(store=store)
violation = tracker.record_violation(
    schema_id="user_schema_v1",
    record_id="user_123",
    record_data={"name": "Alice", "age": "invalid"},
    validation_result=result,
    severity="warning"
)

# Query violations
violations = tracker.get_violations(
    schema_id="user_schema_v1",
    status="open"
)
```

## Usage Examples

### Standalone Quality Check

```python
from pycharter import QualityCheck, QualityCheckOptions, QualityThresholds

# Define thresholds
thresholds = QualityThresholds(
    min_overall_score=95.0,
    max_violation_rate=0.05,
    min_accuracy=0.95
)

# Run check
check = QualityCheck()
report = check.run(
    contract="contracts/user_contract.yaml",
    data="data/users.json",
    options=QualityCheckOptions(
        check_thresholds=True,
        thresholds=thresholds
    )
)

if not report.passed:
    print("⚠ Quality check failed!")
    for breach in report.threshold_breaches:
        print(f"  - {breach}")
```

### CLI Usage

```bash
# Run quality check
pycharter quality check \
    --schema-id user_schema_v1 \
    --data data/users.json \
    --database-url postgresql://user:pass@localhost/db \
    --check-thresholds \
    --output quality_report.json

# Query violations
pycharter quality violations \
    --schema-id user_schema_v1 \
    --status open \
    --output violations.json
```

### API Usage

```bash
# Run quality check via API
curl -X POST http://localhost:8000/api/v1/quality/check \
  -H "Content-Type: application/json" \
  -d '{
    "schema_id": "user_schema_v1",
    "data": [{"name": "Alice", "age": 30}],
    "calculate_metrics": true,
    "record_violations": true
  }'
```

## Quality Metrics

The quality module calculates several metrics:

- **Overall Score** (0-100): Weighted combination of accuracy and completeness
- **Accuracy** (0-1): Percentage of records that pass validation
- **Completeness** (0-1): Percentage of required fields present
- **Violation Rate** (0-1): Percentage of records with violations
- **Field Scores**: Per-field quality scores

## Thresholds and Alerting

Define quality thresholds to get alerts when quality degrades:

```python
thresholds = QualityThresholds(
    min_overall_score=95.0,
    max_violation_rate=0.05,
    min_completeness=0.95,
    min_accuracy=0.95,
    field_thresholds={
        "email": {"min_score": 98.0},
        "phone": {"min_score": 90.0}
    }
)
```

## Integration with Orchestrators

The quality module works seamlessly with orchestrators:

### Airflow

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from pycharter import QualityCheck

def quality_check_task():
    check = QualityCheck(store=store)
    report = check.run(schema_id="user_schema_v1", data=extract_data())
    if not report.passed:
        raise ValueError("Quality check failed")

with DAG("data_pipeline") as dag:
    quality_check = PythonOperator(
        task_id="quality_check",
        python_callable=quality_check_task
    )
```

### Prefect

```python
from prefect import flow, task
from pycharter import QualityCheck

@task
def quality_check_task(schema_id: str, data):
    check = QualityCheck(store=store)
    return check.run(schema_id=schema_id, data=data)

@flow
def data_pipeline():
    data = extract_data()
    report = quality_check_task("user_schema_v1", data)
    return report
```

### Dagster

```python
from dagster import asset, op
from pycharter import QualityCheck

@op
def quality_check_op(context, data):
    check = QualityCheck(store=store)
    report = check.run(schema_id="user_schema_v1", data=data)
    context.log.info(f"Quality score: {report.quality_score.overall_score}")
    return report
```

## Future Enhancements

- Database persistence for violations and metrics
- Scheduled quality monitoring jobs
- Quality dashboards and visualizations
- Data profiling capabilities
- Remediation workflows

