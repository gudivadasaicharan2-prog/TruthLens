"""
Model Comparison Script
=======================
Compare multiple trained models and generate consolidated comparison report.
"""

import argparse
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd


class ModelComparator:
    """
    Compare multiple trained models and generate comparison reports.
    """
    
    def __init__(self, experiment_dirs: List[str]):
        """
        Initialize model comparator.
        
        Args:
            experiment_dirs: List of experiment directories to compare
        """
        self.experiment_dirs = [Path(d) for d in experiment_dirs]
        self.comparison_data = []
    
    def load_experiment_results(self, experiment_dir: Path) -> Dict[str, Any]:
        """
        Load results from an experiment directory.
        
        Args:
            experiment_dir: Path to experiment directory
        
        Returns:
            Experiment results dictionary
        """
        results = {
            'experiment_id': experiment_dir.name,
            'config': {},
            'metrics': {},
            'benchmark': {},
            'error_analysis': {}
        }
        
        # Load config
        config_path = experiment_dir / 'config.yaml'
        if config_path.exists():
            with open(config_path, 'r') as f:
                results['config'] = yaml.safe_load(f)
        
        # Load training history
        history_path = experiment_dir / 'training_history.json'
        if history_path.exists():
            with open(history_path, 'r') as f:
                results['training_history'] = json.load(f)
        
        # Load evaluation results if available
        eval_results_path = experiment_dir / 'evaluation_results' / 'complete_results.json'
        if eval_results_path.exists():
            with open(eval_results_path, 'r') as f:
                eval_results = json.load(f)
                results['metrics'] = eval_results.get('metrics', {})
                results['benchmark'] = eval_results.get('benchmark', {})
                results['error_analysis'] = eval_results.get('error_analysis', {})
        
        return results
    
    def collect_comparison_data(self):
        """Collect comparison data from all experiments."""
        for exp_dir in self.experiment_dirs:
            if exp_dir.exists():
                results = self.load_experiment_results(exp_dir)
                self.comparison_data.append(results)
            else:
                print(f"[Warning] Experiment directory not found: {exp_dir}")
    
    def generate_comparison_table(self) -> pd.DataFrame:
        """
        Generate comparison table.
        
        Returns:
            Comparison DataFrame
        """
        comparison_rows = []
        
        for results in self.comparison_data:
            config = results.get('config', {})
            metrics = results.get('metrics', {})
            benchmark = results.get('benchmark', {})
            error_analysis = results.get('error_analysis', {})
            
            row = {
                'Experiment ID': results['experiment_id'],
                'Model': config.get('model', {}).get('architecture', 'unknown'),
                'Dataset': config.get('data', {}).get('dataset_dir', 'unknown'),
                'Epochs': config.get('training', {}).get('epochs', 'unknown'),
                'Accuracy': metrics.get('accuracy', 0.0),
                'Precision': metrics.get('precision', 0.0),
                'Recall': metrics.get('recall', 0.0),
                'F1 Score': metrics.get('f1', 0.0),
                'ROC-AUC': metrics.get('roc_auc', 0.0),
                'PR-AUC': metrics.get('pr_auc', 0.0),
                'Parameters (M)': benchmark.get('model_info', {}).get('total_parameters', 0) / 1e6,
                'Model Size (MB)': benchmark.get('size', {}).get('size_mb', 0.0),
                'Inference Speed (samples/s)': benchmark.get('inference', {}).get('samples_per_second', 0.0),
                'GPU Memory (GB)': benchmark.get('memory', {}).get('gpu_memory_max_allocated', 0.0),
                'Error Rate': error_analysis.get('error_rate', 0.0),
                'FP Rate': error_analysis.get('fp_rate', 0.0),
                'FN Rate': error_analysis.get('fn_rate', 0.0)
            }
            
            comparison_rows.append(row)
        
        return pd.DataFrame(comparison_rows)
    
    def generate_comparison_report(self, output_dir: Path):
        """
        Generate comprehensive comparison report.
        
        Args:
            output_dir: Directory to save report
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Collect data
        self.collect_comparison_data()
        
        if not self.comparison_data:
            print("[Error] No valid experiment directories found")
            return
        
        # Generate comparison table
        df = self.generate_comparison_table()
        
        # Save comparison table as CSV
        csv_path = output_dir / 'model_comparison.csv'
        df.to_csv(csv_path, index=False)
        print(f"[Comparison] Saved comparison table to {csv_path}")
        
        # Save comparison table as JSON
        json_path = output_dir / 'model_comparison.json'
        with open(json_path, 'w') as f:
            json.dump(df.to_dict(orient='records'), f, indent=2)
        print(f"[Comparison] Saved comparison JSON to {json_path}")
        
        # Generate text report
        text_report_path = output_dir / 'comparison_report.txt'
        self._generate_text_report(df, text_report_path)
        print(f"[Comparison] Saved text report to {text_report_path}")
        
        # Generate recommendation
        recommendation_path = output_dir / 'recommendation.txt'
        self._generate_recommendation(df, recommendation_path)
        print(f"[Comparison] Saved recommendation to {recommendation_path}")
        
        # Print summary
        self._print_summary(df)
    
    def _generate_text_report(self, df: pd.DataFrame, output_path: Path):
        """
        Generate text comparison report.
        
        Args:
            df: Comparison DataFrame
            output_path: Path to save report
        """
        with open(output_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("MODEL COMPARISON REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("Overview\n")
            f.write("-" * 80 + "\n")
            f.write(f"Number of models compared: {len(df)}\n")
            f.write(f"Models: {', '.join(df['Model'].unique())}\n\n")
            
            f.write("Performance Metrics\n")
            f.write("-" * 80 + "\n")
            f.write(df[['Model', 'Accuracy', 'Precision', 'Recall', 'F1 Score', 'ROC-AUC', 'PR-AUC']].to_string(index=False))
            f.write("\n\n")
            
            f.write("Efficiency Metrics\n")
            f.write("-" * 80 + "\n")
            f.write(df[['Model', 'Parameters (M)', 'Model Size (MB)', 'Inference Speed (samples/s)', 'GPU Memory (GB)']].to_string(index=False))
            f.write("\n\n")
            
            f.write("Error Analysis\n")
            f.write("-" * 80 + "\n")
            f.write(df[['Model', 'Error Rate', 'FP Rate', 'FN Rate']].to_string(index=False))
            f.write("\n\n")
            
            f.write("Detailed Comparison\n")
            f.write("-" * 80 + "\n")
            f.write(df.to_string(index=False))
            f.write("\n\n")
    
    def _generate_recommendation(self, df: pd.DataFrame, output_path: Path):
        """
        Generate production model recommendation.
        
        Args:
            df: Comparison DataFrame
            output_path: Path to save recommendation
        """
        with open(output_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("PRODUCTION MODEL RECOMMENDATION\n")
            f.write("=" * 80 + "\n\n")
            
            # Best accuracy
            best_acc_idx = df['Accuracy'].idxmax()
            best_acc_model = df.loc[best_acc_idx, 'Model']
            best_acc = df.loc[best_acc_idx, 'Accuracy']
            
            f.write(f"Best Accuracy: {best_acc_model} ({best_acc:.4f})\n\n")
            
            # Best F1
            best_f1_idx = df['F1 Score'].idxmax()
            best_f1_model = df.loc[best_f1_idx, 'Model']
            best_f1 = df.loc[best_f1_idx, 'F1 Score']
            
            f.write(f"Best F1 Score: {best_f1_model} ({best_f1:.4f})\n\n")
            
            # Best ROC-AUC
            best_roc_idx = df['ROC-AUC'].idxmax()
            best_roc_model = df.loc[best_roc_idx, 'Model']
            best_roc = df.loc[best_roc_idx, 'ROC-AUC']
            
            f.write(f"Best ROC-AUC: {best_roc_model} ({best_roc:.4f})\n\n")
            
            # Fastest inference
            fastest_idx = df['Inference Speed (samples/s)'].idxmax()
            fastest_model = df.loc[fastest_idx, 'Model']
            fastest_speed = df.loc[fastest_idx, 'Inference Speed (samples/s)']
            
            f.write(f"Fastest Inference: {fastest_model} ({fastest_speed:.2f} samples/s)\n\n")
            
            # Smallest model
            smallest_idx = df['Model Size (MB)'].idxmin()
            smallest_model = df.loc[smallest_idx, 'Model']
            smallest_size = df.loc[smallest_idx, 'Model Size (MB)']
            
            f.write(f"Smallest Model: {smallest_model} ({smallest_size:.2f} MB)\n\n")
            
            # Lowest error rate
            lowest_error_idx = df['Error Rate'].idxmin()
            lowest_error_model = df.loc[lowest_error_idx, 'Model']
            lowest_error = df.loc[lowest_error_idx, 'Error Rate']
            
            f.write(f"Lowest Error Rate: {lowest_error_model} ({lowest_error:.4f})\n\n")
            
            # Overall recommendation
            f.write("=" * 80 + "\n")
            f.write("OVERALL RECOMMENDATION\n")
            f.write("=" * 80 + "\n\n")
            
            # Calculate composite score (weighted average)
            weights = {
                'accuracy': 0.3,
                'f1': 0.2,
                'roc_auc': 0.2,
                'speed': 0.15,
                'size': 0.1,
                'error_rate': 0.05
            }
            
            # Normalize metrics
            df_norm = df.copy()
            df_norm['norm_accuracy'] = df['Accuracy'] / df['Accuracy'].max()
            df_norm['norm_f1'] = df['F1 Score'] / df['F1 Score'].max()
            df_norm['norm_roc_auc'] = df['ROC-AUC'] / df['ROC-AUC'].max()
            df_norm['norm_speed'] = df['Inference Speed (samples/s)'] / df['Inference Speed (samples/s)'].max()
            df_norm['norm_size'] = 1 - (df['Model Size (MB)'] / df['Model Size (MB)'].max())  # Lower is better
            df_norm['norm_error'] = 1 - (df['Error Rate'] / df['Error Rate'].max())  # Lower is better
            
            # Calculate composite score
            df_norm['composite_score'] = (
                weights['accuracy'] * df_norm['norm_accuracy'] +
                weights['f1'] * df_norm['norm_f1'] +
                weights['roc_auc'] * df_norm['norm_roc_auc'] +
                weights['speed'] * df_norm['norm_speed'] +
                weights['size'] * df_norm['norm_size'] +
                weights['error_rate'] * df_norm['norm_error']
            )
            
            best_overall_idx = df_norm['composite_score'].idxmax()
            best_overall_model = df.loc[best_overall_idx, 'Model']
            best_overall_score = df_norm.loc[best_overall_idx, 'composite_score']
            
            f.write(f"Recommended Production Model: {best_overall_model}\n")
            f.write(f"Composite Score: {best_overall_score:.4f}\n\n")
            
            f.write("Rationale:\n")
            f.write(f"- Accuracy: {df.loc[best_overall_idx, 'Accuracy']:.4f}\n")
            f.write(f"- F1 Score: {df.loc[best_overall_idx, 'F1 Score']:.4f}\n")
            f.write(f"- ROC-AUC: {df.loc[best_overall_idx, 'ROC-AUC']:.4f}\n")
            f.write(f"- Inference Speed: {df.loc[best_overall_idx, 'Inference Speed (samples/s)']:.2f} samples/s\n")
            f.write(f"- Model Size: {df.loc[best_overall_idx, 'Model Size (MB)']:.2f} MB\n")
            f.write(f"- Error Rate: {df.loc[best_overall_idx, 'Error Rate']:.4f}\n\n")
            
            f.write("Trade-offs:\n")
            for idx, row in df.iterrows():
                if idx != best_overall_idx:
                    f.write(f"\n{row['Model']}:\n")
                    if row['Accuracy'] > df.loc[best_overall_idx, 'Accuracy']:
                        f.write(f"  + Better accuracy ({row['Accuracy']:.4f} vs {df.loc[best_overall_idx, 'Accuracy']:.4f})\n")
                    if row['Inference Speed (samples/s)'] > df.loc[best_overall_idx, 'Inference Speed (samples/s)']:
                        f.write(f"  + Faster inference ({row['Inference Speed (samples/s)']:.2f} vs {df.loc[best_overall_idx, 'Inference Speed (samples/s)']:.2f})\n")
                    if row['Model Size (MB)'] < df.loc[best_overall_idx, 'Model Size (MB)']:
                        f.write(f"  + Smaller model ({row['Model Size (MB)']:.2f} vs {df.loc[best_overall_idx, 'Model Size (MB)']:.2f} MB)\n")
    
    def _print_summary(self, df: pd.DataFrame):
        """Print comparison summary."""
        print("\n" + "=" * 80)
        print("MODEL COMPARISON SUMMARY")
        print("=" * 80)
        
        print(f"\nModels compared: {len(df)}")
        print(f"Architectures: {', '.join(df['Model'].unique())}")
        
        print(f"\nTop Performers:")
        print(f"  Accuracy: {df.loc[df['Accuracy'].idxmax(), 'Model']} ({df['Accuracy'].max():.4f})")
        print(f"  F1 Score: {df.loc[df['F1 Score'].idxmax(), 'Model']} ({df['F1 Score'].max():.4f})")
        print(f"  ROC-AUC: {df.loc[df['ROC-AUC'].idxmax(), 'Model']} ({df['ROC-AUC'].max():.4f})")
        print(f"  Inference Speed: {df.loc[df['Inference Speed (samples/s)'].idxmax(), 'Model']} ({df['Inference Speed (samples/s)'].max():.2f} samples/s)")
        print(f"  Model Size: {df.loc[df['Model Size (MB)'].idxmin(), 'Model']} ({df['Model Size (MB)'].min():.2f} MB)")
        
        print("\n" + "=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Compare trained models')
    parser.add_argument('--experiments', type=str, nargs='+', required=True, 
                       help='List of experiment directories to compare')
    parser.add_argument('--output', type=str, default='model_comparison',
                       help='Output directory for comparison report')
    
    args = parser.parse_args()
    
    # Create comparator
    comparator = ModelComparator(args.experiments)
    
    # Generate comparison report
    comparator.generate_comparison_report(Path(args.output))


if __name__ == '__main__':
    main()
