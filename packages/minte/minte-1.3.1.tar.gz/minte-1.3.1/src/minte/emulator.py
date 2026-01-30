"""
Neural network emulator for malaria scenario predictions.

This module provides functions for:
- Loading trained LSTM/GRU models
- Running batch predictions for multiple scenarios
- Feature preparation with schema-aware processing

Based on model_helpers_optimized.py from the original R package.
"""

from __future__ import annotations

import json
import logging
import pickle
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Literal

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler

from .cache import get_cached_model, set_cached_model, is_cached

logger = logging.getLogger(__name__)


# ---------------------------
# Target transforms (from model_helpers_optimized.py)
# ---------------------------

def _clip01(x: np.ndarray, eps: float) -> np.ndarray:
    """Clip values to (eps, 1-eps) range."""
    return np.clip(x, eps, 1.0 - eps)


def transform_targets_np(y: np.ndarray, predictor: str, eps: float = 1e-5) -> np.ndarray:
    """Transform targets for model training/inference."""
    if predictor == "prevalence":
        y = _clip01(y, eps)
        return np.log(y / (1.0 - y))  # logit
    else:
        return np.log1p(np.maximum(y, 0.0))


def inverse_transform_np(y: np.ndarray, predictor: str) -> np.ndarray:
    """
    Inverse transform model outputs to original scale.

    For prevalence: sigmoid transform (always in (0, 1)).
    For cases: expm1 clamped to non-negative values.

    Parameters
    ----------
    y : np.ndarray
        Model outputs in transformed space. Can be 1D [T] or 2D [B, T].
    predictor : str
        Type of predictor ("prevalence" or "cases").

    Returns
    -------
    np.ndarray
        Inverse-transformed predictions in original scale.
    """
    if predictor == "prevalence":
        return 1.0 / (1.0 + np.exp(-y))  # sigmoid, always in (0, 1)
    else:
        # Cases: expm1 clamped to non-negative (allows recovery after troughs)
        return np.maximum(np.expm1(y), 0.0)


# ---------------------------
# Schema dataclass
# ---------------------------

@dataclass
class ModelSchema:
    """Schema describing the expected input features for a model."""

    expected_in: int
    cyc: bool = True  # Use cyclical time encoding
    extra2: int = 2  # Extra post-intervention features (always 2 for new models)


@dataclass
class EmulatorModels:
    """Container for loaded emulator models and configuration."""

    lstm_model: nn.Module
    lstm_schema: ModelSchema
    static_scaler: StandardScaler
    static_covars: list[str]
    after9_covars: list[str]
    intervention_day: int
    use_cyclical_time: bool
    predictor: str
    device: torch.device
    training_args: dict
    models_dir: Path
    eps_prevalence: float = 1e-5


# Standard static covariates used by the models
STATIC_COVARS = [
    "eir",
    "dn0_use",
    "dn0_future",
    "Q0",
    "phi_bednets",
    "seasonal",
    "routine",
    "itn_use",
    "irs_use",
    "itn_future",
    "irs_future",
    "lsm",
]

# Covariates that only apply after year 9 (intervention day)
AFTER9_COVARS = ["dn0_future", "itn_future", "irs_future", "lsm", "routine"]


# ---------------------------
# Schema-aware LSTM Model (from model_helpers_optimized.py)
# ---------------------------

class SchemaAwareLSTM(nn.Module):
    """
    Simple LSTM model for time series prediction.

    CRITICAL: Uses batch_first=False, so input shape is [T, B, F]
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        output_size: int,
        dropout_prob: float,
        num_layers: int = 1,
        predictor: str = "prevalence",
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.predictor = predictor

        self.lstm = nn.LSTM(
            input_size,
            hidden_size,
            num_layers=num_layers,
            dropout=dropout_prob if num_layers > 1 else 0.0,
            batch_first=False,  # CRITICAL: sequence-first [T, B, F]
        )
        self.fc = nn.Linear(hidden_size, output_size)
        self.ln = nn.LayerNorm(hidden_size)
        self.dropout = nn.Dropout(dropout_prob)
        self.activation = nn.Identity()  # Train in transformed space -> identity activation

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Parameters
        ----------
        x : torch.Tensor
            Input tensor of shape [T, B, F] (sequence-first!)

        Returns
        -------
        torch.Tensor
            Output tensor of shape [T, B, 1]
        """
        out, _ = self.lstm(x)
        out = self.ln(out)
        out = self.dropout(out)
        out = self.fc(out)
        out = self.activation(out)
        return out


# Alias for backwards compatibility
LSTMModel = SchemaAwareLSTM


def get_device(device: str | None = None) -> torch.device:
    """Get the appropriate torch device."""
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return torch.device(device)


# ---------------------------
# Schema inference from checkpoint (from model_helpers_optimized.py)
# ---------------------------

def safe_load_state(path: str | Path, device: torch.device) -> Dict[str, Any]:
    """Load checkpoint safely handling different formats."""
    try:
        ckpt = torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        ckpt = torch.load(path, map_location=device)

    if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
        state = ckpt["model_state_dict"]
    else:
        state = ckpt

    if not isinstance(state, dict):
        raise RuntimeError("Unsupported checkpoint format.")

    return state


def infer_schema_from_state(
    state: Dict[str, Any],
    static_n: int,
    use_cyclical_time: bool
) -> ModelSchema:
    """
    Infer the feature schema from checkpoint state dict.

    New simplified models have structure:
    - Time encoding (2 if cyclical, 1 if not)
    - Static covariates (static_n)
    - Extra 2 features (post9, t_since9_years)

    Parameters
    ----------
    state : dict
        Model state dictionary.
    static_n : int
        Number of static covariates.
    use_cyclical_time : bool
        Whether cyclical time encoding is expected.

    Returns
    -------
    ModelSchema
        Inferred schema with all feature flags.
    """
    # Infer input size from weight matrix
    if "lstm.weight_ih_l0" in state:
        expected_in = int(state["lstm.weight_ih_l0"].shape[1])
    else:
        keys = [k for k in state if k.endswith("weight_ih_l0")]
        if not keys:
            raise RuntimeError("Cannot infer input size: no *weight_ih_l0 in checkpoint.")
        expected_in = int(state[keys[0]].shape[1])

    # Try different feature combinations
    candidates = []
    for cyc in (True, False):
        time_dim = 2 if cyc else 1
        total = time_dim + static_n + 2  # Always 2 extra features
        if total == expected_in:
            score = 10 if cyc == use_cyclical_time else 0
            candidates.append((
                score,
                ModelSchema(
                    expected_in=expected_in,
                    cyc=cyc,
                    extra2=2,
                ),
            ))

    if not candidates:
        raise RuntimeError(
            f"Could not map checkpoint input size {expected_in} to any feature combination. "
            f"Expected {2 if use_cyclical_time else 1} + {static_n} + 2 = "
            f"{(2 if use_cyclical_time else 1) + static_n + 2}, got {expected_in}"
        )

    # Sort by score descending and return best match
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def load_model_from_checkpoint(
    checkpoint_path: str | Path,
    static_n: int,
    predictor: str,
    device: torch.device,
    use_cyclical_time: bool = True,
) -> tuple[nn.Module, ModelSchema]:
    """
    Load SchemaAwareLSTM from checkpoint with automatic schema inference.

    Parameters
    ----------
    checkpoint_path : str or Path
        Path to the model checkpoint file.
    static_n : int
        Number of static covariates.
    predictor : str
        Type of predictor ("prevalence" or "cases").
    device : torch.device
        Device to load model on.
    use_cyclical_time : bool
        Whether cyclical time encoding is expected.

    Returns
    -------
    tuple[nn.Module, ModelSchema]
        Loaded model and inferred schema.
    """
    state = safe_load_state(checkpoint_path, device)
    schema = infer_schema_from_state(state, static_n, use_cyclical_time)

    # Infer architecture from state dict
    if "lstm.weight_ih_l0" in state:
        hidden = state["lstm.weight_ih_l0"].shape[0] // 4
        layers = sum(1 for k in state if k.startswith("lstm.weight_ih_l"))
    else:
        wih0 = [k for k in state if k.endswith("weight_ih_l0")]
        hidden = state[wih0[0]].shape[0] // 4
        layers = len({k.split(".")[1] for k in state if k.startswith("lstm.weight_ih_l")})

    model = SchemaAwareLSTM(
        input_size=schema.expected_in,
        hidden_size=hidden,
        output_size=1,
        dropout_prob=0.0,  # No dropout at inference
        num_layers=layers,
        predictor=predictor,
    )

    model.load_state_dict(state, strict=True)
    model.to(device).eval()

    logger.info(f"Loaded LSTM: {layers} layers, hidden {hidden}")
    logger.info(f"Schema: {schema}")

    return model, schema


def load_emulator_models(
    models_base_dir: str | Path | None = None,
    predictor: Literal["prevalence", "cases"] = "prevalence",
    device: str | None = None,
    verbose: bool = True,
    force_reload: bool = False,
) -> EmulatorModels:
    """
    Load emulator models with caching support.

    Parameters
    ----------
    models_base_dir : str or Path, optional
        Base directory containing model files.
    predictor : str
        Type of predictor ("prevalence" or "cases").
    device : str, optional
        Device to load models on ("cpu" or "cuda").
    verbose : bool
        Print loading messages.
    force_reload : bool
        Force reload even if cached.

    Returns
    -------
    EmulatorModels
        Container with loaded models and configuration.
    """
    cache_key = f"nn_{predictor}"

    # Check cache
    if not force_reload and is_cached(cache_key):
        if verbose:
            logger.info(f"Using cached {predictor} models")
        return get_cached_model(cache_key)

    # Determine device
    device_obj = get_device(device)
    if verbose:
        logger.info(f"Loading {predictor} models on device: {device_obj}")

    # Find model directory
    if models_base_dir is None:
        package_dir = Path(__file__).parent
        candidates = [
            package_dir / "models",
            package_dir / "data" / "models",
            Path("models"),
        ]
        for path in candidates:
            if path.exists():
                models_base_dir = path
                break

        if models_base_dir is None:
            raise FileNotFoundError("Models directory not found")

    models_base_dir = Path(models_base_dir)
    predictor_models_dir = models_base_dir / predictor

    # Load training args
    args_path = predictor_models_dir / "args.json"
    if not args_path.exists():
        raise FileNotFoundError(f"Could not find args.json in {predictor_models_dir}")

    with open(args_path) as f:
        training_args = json.load(f)

    if verbose:
        logger.info(f"Loaded training parameters from {args_path}")

    # Load scaler
    scaler_path = predictor_models_dir / "static_scaler.pkl"
    with open(scaler_path, "rb") as f:
        static_scaler = pickle.load(f)

    # Model configuration
    use_cyclical_time = training_args.get("use_cyclical_time", True)
    eps_prevalence = training_args.get("eps_prevalence", 1e-5)

    # Load LSTM model
    lstm_path = predictor_models_dir / "lstm_best.pt"
    if verbose:
        logger.info(f"Loading LSTM model from {lstm_path}")

    lstm_model, lstm_schema = load_model_from_checkpoint(
        lstm_path,
        static_n=len(STATIC_COVARS),
        predictor=predictor,
        device=device_obj,
        use_cyclical_time=use_cyclical_time,
    )

    if verbose:
        logger.info(f"LSTM model loaded successfully")
        logger.info(f"Expected input features: {lstm_schema.expected_in}")
        logger.info(f"Schema: cyc={lstm_schema.cyc}, extra2={lstm_schema.extra2}")

    # Create models container
    models = EmulatorModels(
        lstm_model=lstm_model,
        lstm_schema=lstm_schema,
        static_scaler=static_scaler,
        static_covars=STATIC_COVARS,
        after9_covars=AFTER9_COVARS,
        intervention_day=9 * 365,
        use_cyclical_time=use_cyclical_time,
        predictor=predictor,
        device=device_obj,
        training_args=training_args,
        models_dir=predictor_models_dir,
        eps_prevalence=eps_prevalence,
    )

    # Cache the models
    set_cached_model(cache_key, models)

    if verbose:
        logger.info(f"{predictor} models loaded and cached")

    return models


def prepare_input_features_schema(
    df: pd.DataFrame,
    models: EmulatorModels,
    window_size: int = 14,
) -> np.ndarray:
    """
    Prepare input features matching the new simplified model structure.

    Features are:
    - Time encoding (sin/cos if cyclical, normalized timesteps if not)
    - Static covariates (scaled)
    - Extra 2 features: post9 flag and time_since9_years

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with timesteps and covariate values.
    models : EmulatorModels
        Loaded models container.
    window_size : int
        Window size in days.

    Returns
    -------
    np.ndarray
        Prepared input features array of shape (T, n_features).
    """
    T_len = len(df)
    abs_t = df["abs_timesteps"].values.astype(np.float32)
    rel_t = df["timesteps"].values.astype(np.float32)
    schema = models.lstm_schema

    # Base static features
    row0 = df.iloc[0]
    base_static = np.array([row0[cov] for cov in models.static_covars], dtype=np.float32)
    raw_matrix = np.tile(base_static, (T_len, 1))

    # Gate future-only covariates before intervention
    post_mask = abs_t >= models.intervention_day
    for cov in models.after9_covars:
        j = models.static_covars.index(cov)
        raw_matrix[~post_mask, j] = 0.0

    # Scale static features
    scaled_matrix = models.static_scaler.transform(raw_matrix)

    # Build feature columns
    cols = []

    # Time encoding
    if schema.cyc:
        day_of_year = abs_t % 365.0
        sin_t = np.sin(2 * np.pi * day_of_year / 365.0)
        cos_t = np.cos(2 * np.pi * day_of_year / 365.0)
        cols.append(np.column_stack([sin_t, cos_t]))
    else:
        t_min, t_max = rel_t.min(), rel_t.max()
        t_norm = (rel_t - t_min) / (t_max - t_min) if t_max > t_min else rel_t
        cols.append(t_norm.reshape(-1, 1))

    # Static covariates
    cols.append(scaled_matrix)

    # Extra post-intervention features (always included in new models)
    post9 = (abs_t >= models.intervention_day).astype(np.float32)
    t_since9_years = np.maximum(0.0, abs_t - models.intervention_day) / 365.0
    cols.append(np.column_stack([post9, t_since9_years]))

    # Combine all features
    X = np.hstack(cols)

    # Verify dimensions
    if X.shape[1] != schema.expected_in:
        raise ValueError(
            f"Feature width {X.shape[1]} != checkpoint expected {schema.expected_in}. "
            f"Schema: cyc={schema.cyc}, static_n={len(models.static_covars)}, extra2={schema.extra2}"
        )

    return X.astype(np.float32)


def batch_predict_scenarios(
    model: nn.Module,
    X: np.ndarray,
    device: torch.device,
    predictor: str,
    batch_size: int = 32,
    use_amp: bool = False,
) -> np.ndarray:
    """
    Run batch predictions with the LSTM model.
    
    IMPORTANT: The SchemaAwareLSTM expects input in [T, B, F] format (sequence-first),
    so we need to transpose from the [B, T, F] input format.

    Parameters
    ----------
    model : nn.Module
        Loaded LSTM model.
    X : np.ndarray
        Input features of shape (n_scenarios, n_timesteps, n_features) = [B, T, F].
    device : torch.device
        Device to run inference on.
    predictor : str
        Type of predictor ("prevalence" or "cases").
    batch_size : int
        Batch size for inference.
    use_amp : bool
        Use automatic mixed precision.

    Returns
    -------
    np.ndarray
        Predictions of shape (n_scenarios, n_timesteps).
    """
    model.eval()
    n_scenarios = X.shape[0]
    all_predictions = []

    with torch.no_grad():
        for i in range(0, n_scenarios, batch_size):
            batch_end = min(i + batch_size, n_scenarios)
            batch_data = X[i:batch_end]  # [B, T, F]
            
            # CRITICAL: Transpose to [T, B, F] for sequence-first LSTM
            batch_data = np.transpose(batch_data, (1, 0, 2))  # [T, B, F]
            
            x_batch = torch.tensor(batch_data, dtype=torch.float32).to(device)

            if use_amp and device.type == "cuda":
                with torch.autocast(device_type="cuda", dtype=torch.float16):
                    batch_pred = model(x_batch)
            else:
                batch_pred = model(x_batch)

            # Output is [T, B, 1], need to convert to [B, T]
            batch_pred = batch_pred.squeeze(-1).permute(1, 0).cpu().numpy()  # [B, T]
            all_predictions.append(batch_pred)

    predictions = np.concatenate(all_predictions, axis=0)
    
    # Apply inverse transform
    return inverse_transform_np(predictions, predictor)


def predict_full_sequence(
    model: nn.Module,
    full_ts: np.ndarray,
    device: torch.device,
    predictor: str,
    use_amp: bool = False,
) -> np.ndarray:
    """
    Predict on a single sequence.
    
    Parameters
    ----------
    full_ts : np.ndarray
        Input array of shape [T, F].
    device : torch.device
        Device to run inference on.
    predictor : str
        Type of predictor.
    use_amp : bool
        Use automatic mixed precision.
        
    Returns
    -------
    np.ndarray
        Predictions of shape [T] (inverse transformed).
    """
    model.eval()
    with torch.no_grad():
        # Add batch dimension: [T, F] -> [T, 1, F]
        x_torch = torch.tensor(full_ts, dtype=torch.float32).unsqueeze(1).to(device)
        
        if device.type == "cuda" and use_amp:
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                pred = model(x_torch).squeeze(-1).squeeze(-1).cpu().numpy()
        else:
            pred = model(x_torch).squeeze(-1).squeeze(-1).cpu().numpy()
            
    return inverse_transform_np(pred, predictor)


def generate_scenario_predictions_batched(
    scenarios: pd.DataFrame,
    models: EmulatorModels,
    model_types: list[str] = ["LSTM"],
    time_steps: int = 2190,
    window_size: int = 14,
    benchmark: bool = False,
    use_amp: bool = False,
) -> list[dict]:
    """
    Generate predictions for multiple scenarios with batching.

    Parameters
    ----------
    scenarios : pd.DataFrame
        DataFrame with scenario parameters.
    models : EmulatorModels
        Loaded models container.
    model_types : list[str]
        List of model types to use (currently only "LSTM").
    time_steps : int
        Number of time steps in days.
    window_size : int
        Window size in days.
    benchmark : bool
        Track timing information.
    use_amp : bool
        Use automatic mixed precision.

    Returns
    -------
    list[dict]
        List of prediction dictionaries for each scenario.
    """
    bench = {} if benchmark else None
    if benchmark:
        t_start = time.time()

    n_scenarios = len(scenarios)
    n_timesteps = time_steps // window_size

    # Pre-allocate array for all scenarios
    X_all = np.zeros((n_scenarios, n_timesteps, models.lstm_schema.expected_in), dtype=np.float32)

    # Process each scenario
    for i in range(n_scenarios):
        # Create time series
        last_6_years_day = 6 * 365
        abs_t = last_6_years_day + np.arange(n_timesteps) * window_size
        rel_t = np.arange(1, n_timesteps + 1)

        # Build dataframe for this scenario
        df = pd.DataFrame({
            "abs_timesteps": abs_t,
            "timesteps": rel_t,
        })

        # Add static covariates
        for cov in models.static_covars:
            df[cov] = scenarios.iloc[i][cov]

        # Add dummy target for feature prep
        if models.predictor == "prevalence":
            df["prevalence"] = 0.1
        else:
            df["cases"] = 1.0

        # Prepare features
        X_i = prepare_input_features_schema(df, models, window_size)
        X_all[i] = X_i

    if benchmark:
        bench["data_prep"] = time.time() - t_start
        t_start = time.time()

    # Batch predict
    predictions_lstm = batch_predict_scenarios(
        models.lstm_model,
        X_all,
        models.device,
        models.predictor,
        use_amp=use_amp,
    )

    if benchmark:
        bench["python_inference"] = time.time() - t_start

    # Convert to list format
    predictions = []
    for i in range(n_scenarios):
        scenario_preds = {
            "scenario_index": i,
            "timesteps": list(range(1, n_timesteps + 1)),
            "parameters": scenarios.iloc[i].to_dict(),
            "lstm": predictions_lstm[i].tolist(),
        }
        predictions.append(scenario_preds)

    if benchmark:
        # Attach benchmark info
        for p in predictions:
            p["_benchmark"] = bench

    return predictions


def run_malaria_emulator(
    scenarios: pd.DataFrame,
    predictor: Literal["prevalence", "cases"] = "prevalence",
    models_base_dir: str | Path | None = None,
    window_size: int = 14,
    device: str | None = None,
    model_types: list[str] = ["LSTM"],
    time_steps: int = 2190,
    use_cache: bool = True,
    benchmark: bool = False,
    precision: Literal["fp32", "amp"] = "fp32",
) -> pd.DataFrame:
    """
    Run the malaria emulator on a set of scenarios.

    Parameters
    ----------
    scenarios : pd.DataFrame
        DataFrame with scenario parameters.
    predictor : str
        Type of predictor ("prevalence" or "cases").
    models_base_dir : str or Path, optional
        Base directory containing model files.
    window_size : int
        Window size for rolling average in days.
    device : str, optional
        Device to use ("cpu" or "cuda").
    model_types : list[str]
        List of model types to use.
    time_steps : int
        Number of time steps in days.
    use_cache : bool
        Use cached models.
    benchmark : bool
        Track timing information.
    precision : str
        Precision control ("fp32" or "amp").

    Returns
    -------
    pd.DataFrame
        DataFrame with predictions containing columns:
        - index: scenario index
        - timestep: time step number
        - prevalence/cases: predicted value
        - model_type: model type used
    """
    bench = {} if benchmark else None
    if benchmark:
        t_total = time.time()
        t_start = time.time()

    # Validate inputs
    if not isinstance(scenarios, pd.DataFrame):
        raise ValueError("Scenarios must be a DataFrame")
    if len(scenarios) == 0:
        raise ValueError("Scenarios DataFrame is empty")
    if predictor not in ["prevalence", "cases"]:
        raise ValueError("Predictor must be 'prevalence' or 'cases'")

    valid_models = ["LSTM"]
    if not all(m in valid_models for m in model_types):
        raise ValueError(f"Invalid model types. Must be: {', '.join(valid_models)}")

    use_amp = precision == "amp"

    # Load models
    if use_cache:
        cache_key = f"nn_{predictor}"
        models = get_cached_model(cache_key)
        if models is None:
            logger.info(f"Loading and caching {predictor} emulator models...")
            models = load_emulator_models(
                models_base_dir,
                predictor,
                device,
                verbose=False,
            )
        else:
            logger.info(f"Using cached {predictor} models")
    else:
        logger.info("Loading emulator models (cache disabled)...")
        models = load_emulator_models(
            models_base_dir,
            predictor,
            device,
            verbose=False,
            force_reload=True,
        )

    if benchmark:
        bench["model_loading"] = time.time() - t_start

    # Check required columns
    missing_cols = set(models.static_covars) - set(scenarios.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in scenarios: {missing_cols}")

    logger.info(f"Processing {len(scenarios)} scenarios")
    logger.info(f"Using model types: {', '.join(model_types)}")
    logger.info(f"Generating predictions for {time_steps / 365:.1f} years")

    # Run batched prediction
    if benchmark:
        t_start = time.time()

    predictions = generate_scenario_predictions_batched(
        scenarios=scenarios,
        models=models,
        model_types=model_types,
        time_steps=time_steps,
        window_size=window_size,
        benchmark=benchmark,
        use_amp=use_amp,
    )

    if benchmark:
        bench["neural_network"] = time.time() - t_start
        if predictions and "_benchmark" in predictions[0]:
            bench["nn_details"] = predictions[0]["_benchmark"]

    # Convert to DataFrame
    if benchmark:
        t_start = time.time()

    results_list = []
    for i, pred in enumerate(predictions):
        if "lstm" in pred:
            lstm_df = pd.DataFrame({
                "index": i,
                "timestep": pred["timesteps"],
                predictor: pred["lstm"],
                "model_type": "LSTM",
            })
            results_list.append(lstm_df)

    results = pd.concat(results_list, ignore_index=True)

    if benchmark:
        bench["data_conversion"] = time.time() - t_start
        bench["total"] = time.time() - t_total

        logger.info("\n--- Emulator Performance ---")
        logger.info(f"  Model loading: {bench['model_loading']:.3f} seconds")
        logger.info(f"  Neural network: {bench['neural_network']:.3f} seconds")
        if "nn_details" in bench:
            logger.info(f"    - Data prep: {bench['nn_details']['data_prep']:.3f} seconds")
            logger.info(f"    - Python inference: {bench['nn_details']['python_inference']:.3f} seconds")
        logger.info(f"  Data conversion: {bench['data_conversion']:.3f} seconds")
        logger.info(f"  Total: {bench['total']:.3f} seconds")

    logger.info(f"\nSummary:")
    logger.info(f"  - Mode: Scenario")
    logger.info(f"  - Predictor type: {predictor}")
    logger.info(f"  - Number of scenarios: {len(scenarios)}")
    logger.info(f"  - Model types: {', '.join(model_types)}")
    logger.info(f"  - Time period: {time_steps / 365:.1f} years")
    logger.info(f"  - Total predictions: {len(results)} rows")

    return results


def create_scenarios(**kwargs) -> pd.DataFrame:
    """
    Create a scenarios DataFrame from parameter vectors.

    All parameters must have the same length.

    Parameters
    ----------
    **kwargs
        Named parameter vectors.

    Returns
    -------
    pd.DataFrame
        DataFrame with one row per scenario.

    Examples
    --------
    >>> scenarios = create_scenarios(
    ...     eir=[10, 20],
    ...     dn0_use=[0.5, 0.6],
    ...     # ... other parameters
    ... )
    """
    lengths = [len(v) for v in kwargs.values()]
    if len(set(lengths)) != 1:
        raise ValueError("All scenario parameters must have the same length")

    return pd.DataFrame(kwargs)


def generate_scenario_predictions(
    scenarios: pd.DataFrame,
    models: EmulatorModels,
    model_types: list[str] = ["LSTM"],
    time_steps: int = 2190,
) -> list[dict]:
    """
    Generate predictions for scenarios (convenience wrapper).

    Parameters
    ----------
    scenarios : pd.DataFrame
        DataFrame with scenario parameters.
    models : EmulatorModels
        Loaded models container.
    model_types : list[str]
        List of model types to use.
    time_steps : int
        Number of time steps in days.

    Returns
    -------
    list[dict]
        List of prediction dictionaries.
    """
    return generate_scenario_predictions_batched(
        scenarios=scenarios,
        models=models,
        model_types=model_types,
        time_steps=time_steps,
    )
