"""
Experiment Manager
==================
Manages training experiments with automatic folder creation, configuration saving,
and experiment registry tracking.
"""

import csv
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import shutil


class ExperimentManager:
    """
    Manages training experiments with automatic folder creation and tracking.
    
    Each experiment gets its own folder with:
    - config.yaml (experiment configuration)
    - metadata.json (experiment metadata)
    - checkpoints/ (model checkpoints)
    - logs/ (TensorBoard logs)
    - plots/ (training plots)
    - training_history.json (training metrics per epoch)
    """
    
    def __init__(self, base_dir: str = "experiments"):
        """
        Initialize experiment manager.
        
        Args:
            base_dir: Base directory for experiments
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.base_dir / "experiments.csv"
        self._init_registry()
    
    def _init_registry(self):
        """Initialize experiments registry CSV file."""
        if not self.registry_path.exists():
            with open(self.registry_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'experiment_id',
                    'model',
                    'dataset',
                    'epochs',
                    'accuracy',
                    'precision',
                    'recall',
                    'f1',
                    'roc_auc',
                    'best_epoch',
                    'date',
                    'checkpoint_path',
                    'status'
                ])
    
    def _get_next_experiment_id(self) -> str:
        """
        Get the next experiment ID.
        
        Returns:
            Experiment ID in format experiment_XXX
        """
        existing_experiments = []
        for item in self.base_dir.iterdir():
            if item.is_dir() and item.name.startswith('experiment_'):
                try:
                    num = int(item.name.split('_')[1])
                    existing_experiments.append(num)
                except (ValueError, IndexError):
                    pass
        
        next_num = max(existing_experiments) + 1 if existing_experiments else 1
        return f"experiment_{next_num:03d}"
    
    def create_experiment(
        self,
        config: Dict[str, Any],
        experiment_name: Optional[str] = None
    ) -> str:
        """
        Create a new experiment folder and save configuration.
        
        Args:
            config: Training configuration dictionary
            experiment_name: Optional custom experiment name
        
        Returns:
            Experiment ID
        """
        experiment_id = experiment_name or self._get_next_experiment_id()
        experiment_dir = self.base_dir / experiment_id
        
        # Create experiment directory structure
        experiment_dir.mkdir(parents=True, exist_ok=True)
        (experiment_dir / "checkpoints").mkdir(exist_ok=True)
        (experiment_dir / "logs").mkdir(exist_ok=True)
        (experiment_dir / "plots").mkdir(exist_ok=True)
        
        # Save configuration
        config_path = experiment_dir / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # Save experiment metadata
        metadata = {
            'experiment_id': experiment_id,
            'created_at': datetime.now().isoformat(),
            'status': 'created',
            'model': config['model']['architecture'],
            'dataset': config['data'].get('dataset_dir', 'unknown'),
            'epochs': config['training']['epochs']
        }
        
        metadata_path = experiment_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Register experiment in CSV
        self._register_experiment(experiment_id, metadata)
        
        print(f"[ExperimentManager] Created experiment: {experiment_id}")
        print(f"[ExperimentManager] Experiment directory: {experiment_dir}")
        
        return experiment_id
    
    def _register_experiment(self, experiment_id: str, metadata: Dict[str, Any]):
        """
        Register experiment in the registry CSV.
        
        Args:
            experiment_id: Experiment ID
            metadata: Experiment metadata
        """
        with open(self.registry_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                experiment_id,
                metadata['model'],
                metadata['dataset'],
                metadata['epochs'],
                '',  # accuracy (filled later)
                '',  # precision (filled later)
                '',  # recall (filled later)
                '',  # f1 (filled later)
                '',  # roc_auc (filled later)
                '',  # best_epoch (filled later)
                metadata['created_at'],
                '',  # checkpoint_path (filled later)
                metadata['status']
            ])
    
    def get_experiment_dir(self, experiment_id: str) -> Path:
        """
        Get the directory for a specific experiment.
        
        Args:
            experiment_id: Experiment ID
        
        Returns:
            Path to experiment directory
        """
        experiment_dir = self.base_dir / experiment_id
        if not experiment_dir.exists():
            raise FileNotFoundError(f"Experiment directory not found: {experiment_dir}")
        return experiment_dir
    
    def load_config(self, experiment_id: str) -> Dict[str, Any]:
        """
        Load configuration from experiment directory.
        
        Args:
            experiment_id: Experiment ID
        
        Returns:
            Configuration dictionary
        """
        experiment_dir = self.get_experiment_dir(experiment_id)
        config_path = experiment_dir / "config.yaml"
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def update_experiment_status(
        self,
        experiment_id: str,
        status: str,
        metrics: Optional[Dict[str, float]] = None,
        best_epoch: Optional[int] = None
    ):
        """
        Update experiment status and metrics in registry.
        
        Args:
            experiment_id: Experiment ID
            status: New status ('running', 'completed', 'failed')
            metrics: Optional metrics dictionary
            best_epoch: Optional best epoch number
        """
        # Read all experiments
        experiments = []
        with open(self.registry_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['experiment_id'] == experiment_id:
                    row['status'] = status
                    if metrics:
                        row['accuracy'] = str(metrics.get('accuracy', ''))
                        row['precision'] = str(metrics.get('precision', ''))
                        row['recall'] = str(metrics.get('recall', ''))
                        row['f1'] = str(metrics.get('f1', ''))
                        row['roc_auc'] = str(metrics.get('roc_auc', ''))
                    if best_epoch is not None:
                        row['best_epoch'] = str(best_epoch)
                experiments.append(row)
        
        # Write back
        with open(self.registry_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=experiments[0].keys())
            writer.writeheader()
            writer.writerows(experiments)
    
    def update_checkpoint_path(self, experiment_id: str, checkpoint_path: str):
        """
        Update checkpoint path in registry.
        
        Args:
            experiment_id: Experiment ID
            checkpoint_path: Path to best checkpoint
        """
        # Read all experiments
        experiments = []
        with open(self.registry_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['experiment_id'] == experiment_id:
                    row['checkpoint_path'] = checkpoint_path
                experiments.append(row)
        
        # Write back
        with open(self.registry_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=experiments[0].keys())
            writer.writeheader()
            writer.writerows(experiments)
    
    def save_training_history(self, experiment_id: str, history: Dict[str, List[float]]):
        """
        Save training history to JSON file.
        
        Args:
            experiment_id: Experiment ID
            history: Training history dictionary
        """
        experiment_dir = self.get_experiment_dir(experiment_id)
        history_path = experiment_dir / "training_history.json"
        
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"[ExperimentManager] Saved training history to {history_path}")
    
    def load_training_history(self, experiment_id: str) -> Dict[str, List[float]]:
        """
        Load training history from JSON file.
        
        Args:
            experiment_id: Experiment ID
        
        Returns:
            Training history dictionary
        """
        experiment_dir = self.get_experiment_dir(experiment_id)
        history_path = experiment_dir / "training_history.json"
        
        with open(history_path, 'r') as f:
            return json.load(f)
    
    def get_checkpoint_dir(self, experiment_id: str) -> Path:
        """
        Get the checkpoints directory for an experiment.
        
        Args:
            experiment_id: Experiment ID
        
        Returns:
            Path to checkpoints directory
        """
        experiment_dir = self.get_experiment_dir(experiment_id)
        return experiment_dir / "checkpoints"
    
    def get_log_dir(self, experiment_id: str) -> Path:
        """
        Get the logs directory for an experiment.
        
        Args:
            experiment_id: Experiment ID
        
        Returns:
            Path to logs directory
        """
        experiment_dir = self.get_experiment_dir(experiment_id)
        return experiment_dir / "logs"
    
    def get_plots_dir(self, experiment_id: str) -> Path:
        """
        Get the plots directory for an experiment.
        
        Args:
            experiment_id: Experiment ID
        
        Returns:
            Path to plots directory
        """
        experiment_dir = self.get_experiment_dir(experiment_id)
        return experiment_dir / "plots"
    
    def list_experiments(self) -> List[Dict[str, Any]]:
        """
        List all experiments from registry.
        
        Returns:
            List of experiment dictionaries
        """
        experiments = []
        with open(self.registry_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                experiments.append(dict(row))
        return experiments
    
    def delete_experiment(self, experiment_id: str):
        """
        Delete an experiment directory and remove from registry.
        
        Args:
            experiment_id: Experiment ID
        """
        experiment_dir = self.get_experiment_dir(experiment_id)
        
        # Remove from registry
        experiments = []
        with open(self.registry_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['experiment_id'] != experiment_id:
                    experiments.append(row)
        
        with open(self.registry_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=experiments[0].keys())
            writer.writeheader()
            writer.writerows(experiments)
        
        # Delete directory
        shutil.rmtree(experiment_dir)
        print(f"[ExperimentManager] Deleted experiment: {experiment_id}")
