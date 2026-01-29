"""
Configuration management for AE optimization.

This module handles loading, validation, and management of configuration
parameters for the AE optimization system.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Union

def get_project_root() -> Path:
    """Get the project root directory.
    
    When installed as a package, this should be the current working directory
    where the user is running the command from, not the package installation directory.
    """
    return Path.cwd()

class AEConfig:
    """Configuration class for Automated Ensemble optimization"""
    
    def __init__(self, project_root: Path = None):
        """Initialize with default directory paths and empty values for JSON loading"""
        if project_root is None:
            project_root = get_project_root()
            
        # Output configuration - use new structure
        self.OUTPUT_DIR: str = str(project_root / "outputs" / "runs")
        self.BEST_TRIAL_DIR: str = str(project_root / "outputs" / "best_trials")
        self.LOGS_DIR: str = str(project_root / "outputs" / "logs")
        self.VISUALIZATIONS_DIR: str = str(project_root / "outputs" / "visualizations")
        
        # Create all necessary directories automatically
        self._create_directories()
        
        # Initialize all other attributes that will be loaded from JSON
        # Prediction thresholds
        self.HARD_VOTING_THRESHOLD: float = 0.5 # Default: 0.5
        self.ACCEPTANCE_THRESHOLD: float = 0.0      # Default: No minimum threshold
        self.ACCEPTANCE_METRIC: str = "soft_recall" # Default: Qualify based on recall
        self.MODEL_TYPE: str = "lightgbm"  # Default model type
        self.OPTIMIZATION_METRICS: str = "soft_recall"  # Default optimization metric
        self.BEST_TRIAL_FILE_SUFFIX: str = ""  # Optional suffix for best trial file names
        self.DATA_PATH: str = None
        self.HYPERPARAMETER_PATH: str = None
        self.FEATURES: List[str] = None
        self.CATEGORICAL_FEATURES: List[str] = [] # Native categorical support
        self.LABEL_COLUMN: str = None
        self.CLASS_WEIGHT: Dict[int, int] = None
        self.UNDER_SAMPLE_MAJORITY_RATIO: float = None
        self.N_ENSEMBLE_GROUP_NUMBER: int = None
        self.AE_NUM_TRIALS: int = None
        self.NUM_SOBOL_TRIALS: int = None
        self.RANDOM_SEED: int = None
        self.PARALLEL_TRAINING: bool = None
        self.N_JOBS: int = None
        self.CROSS_VALIDATION_FOLDS: int = 1 # Default: 1 (No Cross-Validation)
        self.EARLY_STOPPING_PATIENCE: int = 0 # Default: 0 (Disabled)
        self.NUM_PARALLEL_TRIALS: int = 1   # Default: 1 (Batch size for Ax)
        
        # Data preprocessing options
        self.TEST_SIZE: float = 0.2        # Default: 20% test split
        self.ENABLE_DATA_IMPUTATION: bool = False  # Default: LightGBM handles nulls
        self.IMPUTE_TARGET_NULLS: bool = True      # Target nulls should still be handled
        self.ENABLE_PLOTS: bool = False            # Default: Plots disabled
        self.TOP_FEATURE_IMPORTANCE_PLOT: int = 20 # Default: Top 20 features in plot
        
        # Threshold-based trial selection options
        self.SAVE_THRESHOLD_ENABLED: bool = False            # Enable threshold mode
        self.SAVE_THRESHOLD_METRIC: str = "soft_recall"      # Metric to threshold on
        self.SAVE_THRESHOLD_VALUE: float = 0.85              # Save trials >= this value
    
    @classmethod
    def from_file(cls, config_path: str, project_root: Path = None) -> 'AEConfig':
        """Load configuration from JSON file"""
        try:
            if project_root is None:
                project_root = get_project_root()
                
            # If path is relative, make it relative to project root
            if not os.path.isabs(config_path):
                config_path = project_root / config_path
            
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
            
            config = cls(project_root)
            
            # Helper to map values
            def map_value(key, value):
                if hasattr(config, key):
                    # Handle ENABLE_PLOTS show/hide strings
                    if key == "ENABLE_PLOTS" and isinstance(value, str):
                        if value.lower() == "hide":
                            value = False
                        elif value.lower() == "show":
                            value = True

                    # Handle CLASS_WEIGHT dictionary conversion
                    if key == "CLASS_WEIGHT" and isinstance(value, dict):
                        # Convert string keys to int keys for CLASS_WEIGHT
                        value = {int(k): v for k, v in value.items()}
                    setattr(config, key, value)
                elif key.startswith('_'):
                    pass
            
            # Check if it's a nested config (by checking for standard top-level keys)
            is_nested = any(k in config_dict for k in ['meta', 'data', 'model', 'training', 'selection', 'output'])
            
            if is_nested:
                # Map nested structure to flat structure
                mapping = {
                    # Data section
                    ('data', 'path'): 'DATA_PATH',
                    ('data', 'label_column'): 'LABEL_COLUMN',
                    ('data', 'features'): 'FEATURES',
                    ('data', 'categorical_features'): 'CATEGORICAL_FEATURES',
                    ('data', 'class_weight'): 'CLASS_WEIGHT',
                    ('data', 'under_sample_majority_ratio'): 'UNDER_SAMPLE_MAJORITY_RATIO',
                    ('data', 'test_size'): 'TEST_SIZE',
                    ('data', 'enable_imputation'): 'ENABLE_DATA_IMPUTATION',
                    ('data', 'impute_target_nulls'): 'IMPUTE_TARGET_NULLS',
                    
                    # Model section
                    ('model', 'hyperparameter_path'): 'HYPERPARAMETER_PATH',
                    ('model', 'ensemble_size'): 'N_ENSEMBLE_GROUP_NUMBER',
                    ('model', 'type'): 'MODEL_TYPE',

                    # Thresholds section
                    ('thresholds', 'hard_voting_threshold'): 'HARD_VOTING_THRESHOLD',
                    ('thresholds', 'acceptance_threshold'): 'ACCEPTANCE_THRESHOLD',
                    ('thresholds', 'acceptance_metric'): 'ACCEPTANCE_METRIC',
                    
                    # Training section
                    ('training', 'total_trials'): 'AE_NUM_TRIALS',
                    ('training', 'sobol_trials'): 'NUM_SOBOL_TRIALS',
                    ('training', 'random_seed'): 'RANDOM_SEED',
                    ('training', 'parallel'): 'PARALLEL_TRAINING',
                    ('training', 'n_jobs'): 'N_JOBS',
                    ('training', 'metric'): 'OPTIMIZATION_METRICS',
                    ('training', 'cross_validation_subsets'): 'CROSS_VALIDATION_FOLDS',
                    ('training', 'early_stopping_patience'): 'EARLY_STOPPING_PATIENCE',
                    ('training', 'parallel_trials'): 'NUM_PARALLEL_TRIALS',
                    
                    # Selection section
                    ('selection', 'threshold_saving_enabled'): 'SAVE_THRESHOLD_ENABLED',
                    ('selection', 'metric'): 'SAVE_THRESHOLD_METRIC',
                    ('selection', 'threshold_value'): 'SAVE_THRESHOLD_VALUE',
                    
                    # Output section
                    ('output', 'dir'): 'OUTPUT_DIR',
                    ('output', 'best_trial_dir'): 'BEST_TRIAL_DIR',
                    ('output', 'best_trial_suffix'): 'BEST_TRIAL_FILE_SUFFIX',
                    ('output', 'plots'): 'ENABLE_PLOTS',
                    ('output', 'top_feature_importance_plot'): 'TOP_FEATURE_IMPORTANCE_PLOT'
                }
                
                for path, attr_name in mapping.items():
                    section, key = path
                    if section in config_dict and key in config_dict[section]:
                        map_value(attr_name, config_dict[section][key])
                        
            else:
                # Legacy flat structure
                logging.info("Detected legacy, flat configuration structure. Consider upgrading to the new nested format.")
                for key, value in config_dict.items():
                    map_value(key, value)
            
            # Post-process: Load external features if defined as path
            if isinstance(config.FEATURES, str):
                features_path = Path(config.FEATURES)
                if not features_path.is_absolute():
                     # Resolve relative to config directory if possible, or cwd
                     features_path = Path.cwd() / features_path
                
                logging.info(f"Loading external features from {features_path}")
                try:
                    if features_path.suffix.lower() in ['.yaml', '.yml']:
                         import yaml
                         with open(features_path, 'r') as f:
                             loaded_features = yaml.safe_load(f)
                             # Support both list or {"features": [...]} format
                             if isinstance(loaded_features, dict) and 'features' in loaded_features:
                                 config.FEATURES = loaded_features['features']
                             elif isinstance(loaded_features, list):
                                 config.FEATURES = loaded_features
                             else:
                                 raise ValueError("YAML feature file must contain a list or a 'features' key")
                    elif features_path.suffix.lower() == '.json':
                        with open(features_path, 'r') as f:
                            loaded_features = json.load(f)
                            if isinstance(loaded_features, list):
                                config.FEATURES = loaded_features
                            elif isinstance(loaded_features, dict) and 'features' in loaded_features:
                                config.FEATURES = loaded_features['features']
                            else:
                                raise ValueError("JSON feature file must contain a list or a 'features' key")
                    else:
                         # Assume text file with one feature per line
                         with open(features_path, 'r') as f:
                             config.FEATURES = [line.strip() for line in f if line.strip()]
                             
                except Exception as e:
                    logging.error(f"Failed to load external features from {features_path}: {e}")
                    raise
            
            # Validate that all required parameters are loaded
            config._validate_config()
            
            logging.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logging.error(f"Config file {config_path} not found. Cannot proceed without configuration.")
            raise
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing config file: {e}")
            raise
    
    def _validate_config(self) -> None:
        """Validate that all required configuration parameters are set"""
        required_params = [
            'HARD_VOTING_THRESHOLD', 'ACCEPTANCE_THRESHOLD',
            'DATA_PATH', 'FEATURES', 'LABEL_COLUMN',
            'CLASS_WEIGHT', 'UNDER_SAMPLE_MAJORITY_RATIO', 'N_ENSEMBLE_GROUP_NUMBER',
            'AE_NUM_TRIALS', 'NUM_SOBOL_TRIALS', 'RANDOM_SEED', 'PARALLEL_TRAINING', 'N_JOBS',
            'MODEL_TYPE'
        ]
        
        missing_params = []
        for param in required_params:
            if getattr(self, param, None) is None:
                missing_params.append(param)
        
        if missing_params:
            raise ValueError(f"Missing required configuration parameters: {missing_params}")
        
        valid_metrics = [
            "soft_recall", "hard_recall", "soft_f1_score", "hard_f1_score", 
            "soft_precision", "hard_precision", "cross_entropy", "neg_log_loss",
            "soft_roc_auc"
        ]
        if self.OPTIMIZATION_METRICS not in valid_metrics:
            raise ValueError(f"Invalid OPTIMIZATION_METRICS '{self.OPTIMIZATION_METRICS}'. "
                           f"Must be one of: {valid_metrics}")
        
        # Validate model type
        valid_models = ["lightgbm", "xgboost", "random_forest", "rf"]
        if self.MODEL_TYPE.lower() not in valid_models:
             raise ValueError(f"Invalid MODEL_TYPE '{self.MODEL_TYPE}'. Must be one of: {valid_models}")
    
    def save_to_file(self, config_path: str) -> None:
        """Save current configuration to JSON file"""
        # If path is relative, make it relative to project root
        if not os.path.isabs(config_path):
            config_path = get_project_root() / config_path
        
        config_dict = {
            attr: getattr(self, attr) 
            for attr in dir(self) 
            if not attr.startswith('_') and not callable(getattr(self, attr))
        }
        
        # Convert Path objects to strings for JSON serialization
        for key, value in config_dict.items():
            if isinstance(value, Path):
                config_dict[key] = str(value)
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=4)
        
        logging.info(f"Configuration saved to {config_path}")
    
    def _create_directories(self) -> None:
        """Create all necessary output directories"""
        directories_to_create = [
            self.OUTPUT_DIR,
            self.BEST_TRIAL_DIR, 
            self.LOGS_DIR,
            self.VISUALIZATIONS_DIR,
            # Also create the parent outputs directory
            str(Path(self.OUTPUT_DIR).parent)
        ]
        
        for dir_path in directories_to_create:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                logging.debug(f"Created directory: {dir_path}")
            except Exception as e:
                logging.warning(f"Could not create directory {dir_path}: {e}")