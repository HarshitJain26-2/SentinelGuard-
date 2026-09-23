"""
SentinelGuard — Synthetic Mouse Telemetry Dataset Generator

Generates realistic, overlapping kinematic distributions for:
  Class 0: Human-like behavior (natural acceleration, corrective curvature, physiological tremor)
  Class 1: Bot-like behavior (linear interpolation, unnaturally rigid paths, or synthetic jitter)

Designed to be statistically non-trivial with realistic overlapping distributions and noise.
Deterministic via fixed random_state.
"""

import os
from pathlib import Path
from typing import Tuple
import numpy as np
import pandas as pd
from .features import FEATURE_NAMES


def generate_synthetic_data(
    n_samples: int = 1200,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Generates a balanced, realistic synthetic dataset of mouse telemetry features.
    
    Args:
        n_samples: Total number of samples (split 50/50 between human and bot).
        random_state: Random seed for deterministic generation.
        
    Returns:
        pd.DataFrame with 10 feature columns plus 'label' (0 = human, 1 = bot).
    """
    rng = np.random.RandomState(random_state)
    n_class = n_samples // 2

    # ========================================================
    # 1. Human Telemetry Generation (Class 0)
    # Characterized by bell-shaped velocity profiles and natural sub-movement curvature.
    # ========================================================
    human_movement_count = rng.randint(18, 26, size=n_class)
    human_distance = rng.normal(loc=175.0, scale=45.0, size=n_class).clip(50.0, 450.0)
    human_duration = rng.normal(loc=680.0, scale=140.0, size=n_class).clip(350.0, 1200.0)
    human_avg_vel = human_distance / human_duration
    # Human peak velocity is naturally 1.5x - 2.5x the average velocity
    human_max_vel = human_avg_vel * rng.uniform(1.4, 2.4, size=n_class) + rng.normal(0, 0.02, size=n_class)
    human_max_vel = np.maximum(human_max_vel, human_avg_vel)
    # Velocity variance reflecting continuous acceleration & deceleration phases
    human_vel_var = rng.normal(loc=0.030, scale=0.012, size=n_class).clip(0.008, 0.090)
    # Direction changes from sub-movement target corrections
    human_dir_changes = rng.poisson(lam=3.8, size=n_class).clip(1, 9)
    human_avg_dir_change = rng.normal(loc=0.38, scale=0.08, size=n_class).clip(0.15, 0.65)
    # Smooth curves, efficiency typically 0.70 - 0.90, occasionally higher on straight flicks
    human_path_eff = rng.normal(loc=0.80, scale=0.07, size=n_class).clip(0.55, 0.96)
    human_straightness = human_path_eff * rng.uniform(0.95, 1.05, size=n_class)
    human_straightness = human_straightness.clip(0.50, 0.98)

    human_df = pd.DataFrame({
        "movement_count": human_movement_count,
        "total_distance": np.round(human_distance, 2),
        "movement_duration": np.round(human_duration, 1),
        "average_velocity": np.round(human_avg_vel, 4),
        "maximum_velocity": np.round(human_max_vel, 4),
        "velocity_variance": np.round(human_vel_var, 4),
        "direction_change_count": human_dir_changes,
        "average_direction_change": np.round(human_avg_dir_change, 4),
        "path_efficiency": np.round(human_path_eff, 4),
        "straightness_ratio": np.round(human_straightness, 4),
        "label": 0
    })

    # ========================================================
    # 2. Bot Telemetry Generation (Class 1)
    # Mixture of:
    #   - Linear/scripted bots (65%): high path efficiency (~0.98), low velocity variance
    #   - Jitter/evasion bots (35%): noisy erratic direction changes, artificial variance
    # Both types include noise and overlap with edge human behaviors.
    # ========================================================
    n_linear = int(n_class * 0.65)
    n_jitter = n_class - n_linear

    # 2A: Linear / Scripted Bots
    linear_movement_count = rng.randint(20, 26, size=n_linear)
    linear_distance = rng.normal(loc=170.0, scale=40.0, size=n_linear).clip(60.0, 400.0)
    # Often faster duration than human, but overlaps
    linear_duration = rng.normal(loc=420.0, scale=120.0, size=n_linear).clip(150.0, 850.0)
    linear_avg_vel = linear_distance / linear_duration
    # Constant speed scripts have maximum velocity very close to average velocity
    linear_max_vel = linear_avg_vel * rng.uniform(1.02, 1.25, size=n_linear)
    # Very small velocity variance
    linear_vel_var = rng.normal(loc=0.003, scale=0.002, size=n_linear).clip(0.0002, 0.012)
    # Zero or few direction changes
    linear_dir_changes = rng.choice([0, 1, 2], p=[0.55, 0.35, 0.10], size=n_linear)
    linear_avg_dir_change = rng.uniform(0.01, 0.18, size=n_linear)
    # Unnaturally high straightness and path efficiency
    linear_path_eff = rng.normal(loc=0.965, scale=0.025, size=n_linear).clip(0.89, 0.999)
    linear_straightness = rng.normal(loc=0.975, scale=0.020, size=n_linear).clip(0.91, 0.999)

    # 2B: Jitter / Artificial Random Walk Bots
    jitter_movement_count = rng.randint(20, 26, size=n_jitter)
    jitter_distance = rng.normal(loc=180.0, scale=45.0, size=n_jitter).clip(70.0, 400.0)
    jitter_duration = rng.normal(loc=580.0, scale=120.0, size=n_jitter).clip(250.0, 950.0)
    jitter_avg_vel = jitter_distance / jitter_duration
    jitter_max_vel = jitter_avg_vel * rng.uniform(2.0, 3.2, size=n_jitter)
    jitter_vel_var = rng.normal(loc=0.045, scale=0.018, size=n_jitter).clip(0.015, 0.120)
    jitter_dir_changes = rng.poisson(lam=6.5, size=n_jitter).clip(3, 12)
    jitter_avg_dir_change = rng.normal(loc=0.52, scale=0.12, size=n_jitter).clip(0.25, 0.95)
    jitter_path_eff = rng.normal(loc=0.68, scale=0.10, size=n_jitter).clip(0.40, 0.88)
    jitter_straightness = rng.normal(loc=0.72, scale=0.10, size=n_jitter).clip(0.42, 0.90)

    # 2C: Realistic Cross-over Noise (Mimicry & Edge Cases)
    # A small fraction (~7%) of bots generate trajectory features that intentionally mimic human motor variance
    n_mimic = int(n_class * 0.08)
    mimic_indices = rng.choice(n_class, size=n_mimic, replace=False)
    
    bot_movement_count = np.concatenate([linear_movement_count, jitter_movement_count])
    bot_distance = np.concatenate([linear_distance, jitter_distance])
    bot_duration = np.concatenate([linear_duration, jitter_duration])
    bot_avg_vel = np.concatenate([linear_avg_vel, jitter_avg_vel])
    bot_max_vel = np.concatenate([linear_max_vel, jitter_max_vel])
    bot_vel_var = np.concatenate([linear_vel_var, jitter_vel_var])
    bot_dir_changes = np.concatenate([linear_dir_changes, jitter_dir_changes])
    bot_avg_dir_change = np.concatenate([linear_avg_dir_change, jitter_avg_dir_change])
    bot_path_eff = np.concatenate([linear_path_eff, jitter_path_eff])
    bot_straightness = np.concatenate([linear_straightness, jitter_straightness])

    # Inject human-like values for mimic bots to create genuine non-trivial overlap
    for idx in mimic_indices:
        bot_vel_var[idx] = rng.normal(0.028, 0.008)
        bot_avg_dir_change[idx] = rng.normal(0.36, 0.06)
        bot_path_eff[idx] = rng.normal(0.82, 0.05)
        bot_straightness[idx] = rng.normal(0.85, 0.05)
        bot_dir_changes[idx] = rng.randint(3, 6)

    bot_df = pd.DataFrame({
        "movement_count": bot_movement_count,
        "total_distance": np.round(bot_distance, 2),
        "movement_duration": np.round(bot_duration, 1),
        "average_velocity": np.round(bot_avg_vel, 4),
        "maximum_velocity": np.round(bot_max_vel, 4),
        "velocity_variance": np.round(bot_vel_var, 4),
        "direction_change_count": bot_dir_changes,
        "average_direction_change": np.round(bot_avg_dir_change, 4),
        "path_efficiency": np.round(bot_path_eff, 4),
        "straightness_ratio": np.round(bot_straightness, 4),
        "label": 1
    })


    # Combine and shuffle
    df = pd.concat([human_df, bot_df], ignore_index=True)
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

    # Ensure all feature columns match FEATURE_NAMES order
    cols = FEATURE_NAMES + ["label"]
    return df[cols]


def save_synthetic_dataset(output_path: Path, n_samples: int = 1200, random_state: int = 42) -> Path:
    """Generates and writes synthetic telemetry dataset to CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_synthetic_data(n_samples=n_samples, random_state=random_state)
    df.to_csv(output_path, index=False)
    return output_path
