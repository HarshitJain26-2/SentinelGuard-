# Integration Phase 3 Report — Machine Learning Risk Engine

**Project:** SentinelGuard — AI-Driven Bot & Credential-Stuffing Defense System  
**Phase:** Integration Phase 3 — Machine Learning Risk Engine  
**Branch:** `integration`  
**Date:** 2026-09-24  
**Status:** COMPLETE & VERIFIED  

---

## 1. Objective

The objective of Integration Phase 3 is to construct an end-to-end, reproducible Machine Learning Risk Engine for SentinelGuard that transforms ingested browser behavioral telemetry into probabilistic bot risk scores.

Specifically, this phase:
- Develops a reproducible synthetic mouse behavioral dataset generator with realistic kinematic distributions and cross-over noise.
- Trains an explainable `RandomForestClassifier` on 10 derived mouse biometrics features without raw coordinates or PII.
- Evaluates the classifier using standard metrics (Accuracy, Precision, Recall, F1, ROC-AUC, and Confusion Matrix).
- Serializes the trained model to `backend/ml/model.joblib`.
- Builds a model loading and inference layer (`backend/ml/inference.py`) that loads the model as a cached singleton.
- Implements a fault-isolated Django service layer (`backend/detection/ml_scoring.py`) that scores events and persists results into the existing `Score` table.
- Integrates automatic scoring into `POST /api/events/` ingestion while preserving server resilience and idempotency.

---

## 2. Existing Architecture vs. Phase 3 Architecture

### Before Phase 3:
```text
Chrome Extension -> Service Worker -> POST /api/events/ -> Event table (Stored without scoring)
```
The database maintained scaffolded `Score` and `Decision` tables, but no ML scoring or model evaluation existed.

### After Phase 3:
```text
Chrome Extension
    ↓
Service Worker
    ↓ HTTP POST (application/json)
Django EventCreateView (/api/events/)
    ↓
Event model (SQLite detection_event table)
    ↓
Service Layer (detection/ml_scoring.py)
    ↓
Feature Extraction (ml/features.py: validates 10 features & zero-PII)
    ↓
Inference Singleton (ml/inference.py: loads model.joblib)
    ↓ predict_proba(X)[:, 1]
Risk Score (0.0 to 1.0, where 1.0 = Bot, 0.0 = Human)
    ↓ + Explainability reasons
Score model (SQLite detection_score table: session OneToOne, event FK)
```

---

## 3. Dataset Generation

- **Module**: `backend/ml/dataset.py`
- **Methodology**: Deterministic parametric generation using `np.random.RandomState(42)`.
- **Sample Count**: 1,400 samples (700 Human, 700 Bot).
- **Class 0 (Human-like)**:
  - Modeled after physiological motor control (Fitts's Law, bell-shaped velocity curves, micro-corrective tremor).
  - Bell-curved velocity: `maximum_velocity` is 1.4x to 2.4x `average_velocity`.
  - Natural acceleration variance: `velocity_variance` ~ 0.015 to 0.070.
  - Sub-movement curvature: `path_efficiency` ~ 0.70 to 0.90, `direction_change_count` ~ 2 to 7.
- **Class 1 (Bot-like)**:
  - Mixture of linear automation scripts (65%) and evasion jitter bots (35%).
  - Linear bots: Unnaturally straight trajectories (`path_efficiency` > 0.95), near-zero velocity variance (< 0.005), and 0–1 direction changes.
  - Jitter bots: Artificial random-walk noise with high angular deflection (`average_direction_change` > 0.6) and erratic spikes.
  - **Statistical Cross-over Noise**: ~8% of bot samples mimic human variance and ~5% of human samples execute straight flicks, preventing trivial separability.

---

## 4. Feature List

The classifier operates strictly on the 10 kinematic features extracted by the extension's content script:

| # | Feature Name | Description | Human Typical Range | Bot Typical Range |
| :-: | :--- | :--- | :--- | :--- |
| 1 | `movement_count` | Number of sampled points | 18 – 25 | 20 – 25 |
| 2 | `total_distance` | Cumulative path length (pixels) | 80 – 350 | 70 – 350 |
| 3 | `movement_duration` | Trajectory duration (ms) | 400 – 1100 | 150 – 850 |
| 4 | `average_velocity` | Mean speed (px/ms) | 0.15 – 0.40 | 0.25 – 0.70 |
| 5 | `maximum_velocity` | Peak instantaneous velocity (px/ms) | 0.35 – 0.75 | 0.30 – 1.20 |
| 6 | `velocity_variance` | Velocity variance over time | 0.015 – 0.070 | < 0.008 or > 0.06 |
| 7 | `direction_change_count` | Trajectory direction reversals | 2 – 7 | 0 – 2 or 6 – 14 |
| 8 | `average_direction_change`| Mean angular deflection (rad) | 0.25 – 0.50 | < 0.15 or > 0.60 |
| 9 | `path_efficiency` | Direct distance / Total distance | 0.65 – 0.90 | > 0.95 or < 0.65 |
| 10 | `straightness_ratio` | Chord length / Cumulative arc | 0.70 – 0.92 | > 0.96 or < 0.70 |

**Strict Zero-PII Policy**: No raw coordinates (`x`, `y`), timestamps, DOM text, passwords, or IP addresses are present in the feature space.

---

## 5. Model Choice

- **Selected Classifier**: `sklearn.ensemble.RandomForestClassifier`
- **Hyperparameters**:
  - `n_estimators`: 100
  - `max_depth`: 6 (constrained depth ensures smooth, calibrated class probabilities and prevents overfitting on synthetic noise)
  - `min_samples_split`: 4
  - `min_samples_leaf`: 2
  - `random_state`: 42 (deterministic)
- **Rationale**:
  - Non-linear multivariate decision boundaries: Effectively captures kinematic interactions (e.g. high efficiency + low variance = linear script).
  - Robustness to outliers and noise.
  - Explainable feature importances.
  - Reliable probability estimation (`predict_proba`) for risk scoring.

---

## 6. Training Procedure & Train/Test Split

- **Script**: `backend/ml/train_model.py`
- **Dataset Partitioning**: 80% Training (1,120 samples), 20% Testing (280 samples).
- **Stratification**: `stratify=y` ensures identical class distribution in train and test splits.
- **Random Seed**: `random_state=42`.

---

## 7. Evaluation Metrics

Evaluated on held-out 20% test partition (280 samples: 140 Human, 140 Bot):

| Metric | Score | Note |
| :--- | :---: | :--- |
| **Accuracy** | **0.9000** | 90.0% correct classifications on held-out test data |
| **Precision** | **0.9308** | Low false positive rate for bot identification |
| **Recall** | **0.8643** | Correctly catches 86.4% of bots despite overlap |
| **F1-Score** | **0.8963** | Harmonic mean of precision and recall |
| **ROC-AUC** | **0.9555** | Strong probabilistic ranking capability |

### Confusion Matrix:
```text
                 Predicted Human (0)   Predicted Bot (1)
Actual Human (0)        131 (TN)              9 (FP)
Actual Bot (1)           19 (FN)            121 (TP)
```

### Top Contributing Feature Importances:
1. `average_direction_change`: 27.50%
2. `velocity_variance`: 23.80%
3. `movement_duration`: 12.97%
4. `path_efficiency`: 9.01%
5. `straightness_ratio`: 8.52%
6. `maximum_velocity`: 6.68%
7. `direction_change_count`: 6.06%
8. `movement_count`: 2.48%
9. `average_velocity`: 2.36%
10. `total_distance`: 0.62%

---

## 8. Model Artifact Location

- **Trained Model**: `backend/ml/model.joblib` (375 KB)
- **Model Metadata**: `backend/ml/model_meta.json`
- **Synthetic Training Data**: `backend/ml/data/synthetic_mouse_telemetry.csv`

---

## 9. Django Inference Flow

1. An incoming JSON payload hits `POST /api/events/`.
2. `EventInSerializer` validates the envelope structure and creates the `Event` row.
3. `views.py` calls `score_event(event)` from `detection/ml_scoring.py`.
4. `ml_scoring.py`:
   - Checks `event.event_type == "MOUSE_BEHAVIOR"`.
   - Calls `extract_features_from_payload(event.payload)` in `ml/features.py`.
   - Queries `predict_risk(features)` via the cached singleton model in `ml/inference.py`.
   - Extracts human-readable explainability signals via `extract_reasons()`.
   - Persists or updates the `Score` row:
     ```python
     Score.objects.update_or_create(
         session=event.session,
         defaults={
             "event": event,
             "risk_score": risk_score,
             "reasons": reasons,
         }
     )
     ```
5. `EventCreateView` returns HTTP 201 `ACK` with `"risk_score": <float>`.
6. If inference fails, the error is logged; the original `Event` is preserved, and HTTP 201 is still returned.

---

## 10. Database Integration

### Modified Model (`backend/detection/models.py`):
```python
class Score(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name="score")
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name="scores")
    risk_score = models.FloatField()  # 0.0 - 1.0 (bot probability)
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, blank=True, null=True)
    reasons = models.JSONField(blank=True, null=True)
    scored_at = models.DateTimeField(auto_now_add=True)
```

### Migration:
- Generated: `backend/detection/migrations/0002_score_event_alter_score_tier.py`
- Operations: Added `event` foreign key; made `tier` nullable/optional so decision logic is not forced prior to Phase 4.

---

## 11. Tests Performed

Ran full test suite:
```powershell
python manage.py test detection
```
**Results: 23 tests, 0 failures, 0 errors (0.443s)**.

### Test Breakdown:
- **Phase 1 & 2 Tests (11 tests)**:
  - Health check endpoint (`200 OK`)
  - Valid event creation (`201 Created`)
  - Duplicate event rejection (`200 DUPLICATE`)
  - Validation guards: invalid session ID, invalid event ID, invalid event type
  - Non-numeric feature rejection & boolean feature rejection
  - Missing field rejection & forbidden privacy keys (`x`, `y`, `password`, `key`, `text`)
  - Legacy `TEST_EVENT` compatibility
- **Phase 3 ML Engine Tests (12 tests)**:
  - `test_1_synthetic_dataset_generation`: Determinism, balance, non-null features.
  - `test_2_feature_extraction`: 10 floats extracted cleanly.
  - `test_3_feature_ordering`: Guarantees exact feature index alignment regardless of dictionary insertion order.
  - `test_4_model_training`: Validates training script metrics (> 70% baseline).
  - `test_5_model_loading`: Validates cached model singleton and 10-feature input shape.
  - `test_6_risk_score_range`: Guarantees score is bounded in [0.0, 1.0].
  - `test_7_missing_feature_rejection`: Incomplete feature payload raises `FeatureExtractionError`.
  - `test_8_valid_mouse_behavior_gets_scored`: Live API returns `risk_score` in HTTP response.
  - `test_9_score_is_persisted_in_database`: Database row exists in `detection_score` with linked session and event.
  - `test_10_duplicate_event_does_not_create_duplicate_scores`: Idempotency guard prevents duplicate scores.
  - `test_11_non_mouse_event_not_scored`: Non-mouse events are not scored.
  - `test_12_ml_failure_does_not_destroy_original_event`: Fault isolation verifies Event persistence even if inference raises an exception.

---

## 12. Manual Verification Results

Verified live against running Django server:

1. **Human Event**:
   - Sample: `path_efficiency=0.79`, `velocity_variance=0.031`, `average_direction_change=0.38`.
   - Result: `HTTP 201 ACK`, `"risk_score": 0.0652` (Low bot risk).
   - Database: Saved to `detection_score` with `reasons: {"behavioral_profile": "Nominal human kinematic baseline"}`.

2. **Bot Event (Linear Automation Script)**:
   - Sample: `path_efficiency=0.99`, `velocity_variance=0.002`, `average_direction_change=0.03`.
   - Result: `HTTP 201 ACK`, `"risk_score": 1.0` (High bot risk).
   - Database: Saved to `detection_score` with `reasons: {"path_efficiency": "Extremely high path straightness...", "velocity_variance": "Unnaturally constant cursor velocity..."}`.

3. **Duplicate Submission**:
   - Re-sent the exact same bot event.
   - Result: `HTTP 200 DUPLICATE`.
   - Database: No duplicate score row created.

---

## 13. Limitations & Real-World Notice

> [!IMPORTANT]
> **Synthetic Data Baseline Notice:**
> - The current model was trained on mathematically modeled synthetic distributions.
> - While distributions intentionally incorporate noise and overlap, synthetic performance is strictly an engineering baseline and proof-of-concept.
> - Real-world deployment requires training on representative human and automated telemetry collected in the wild.
> - Mouse behavioral biometrics alone should be treated as a risk signal (0.0 to 1.0), not definitive proof of malicious intent.

---

## 14. Exact Commands to Retrain the Model

```powershell
# From the repository root:
python backend/ml/train_model.py

# Or from the backend directory:
cd backend
python ml/train_model.py
```

---

## 15. Example Risk-Scoring Flow

```python
# 1. Incoming payload from browser extension
payload = {
    "movement_count": 25,
    "total_distance": 160.0,
    "movement_duration": 350.0,
    "average_velocity": 0.457,
    "maximum_velocity": 0.490,
    "velocity_variance": 0.002,
    "direction_change_count": 0,
    "average_direction_change": 0.030,
    "path_efficiency": 0.990,
    "straightness_ratio": 0.995,
}

# 2. Extract feature vector
# features = [25.0, 160.0, 350.0, 0.457, 0.490, 0.002, 0.0, 0.030, 0.990, 0.995]

# 3. Model predict_proba(X)[:, 1]
# risk_score = 1.0 (Bot probability)

# 4. Result stored in Score table:
# session_id: 'sess_...'
# risk_score: 1.0
# reasons: {
#   "path_efficiency": "Extremely high path straightness (characteristic of linear scripting)",
#   "velocity_variance": "Unnaturally constant cursor velocity"
# }
```
