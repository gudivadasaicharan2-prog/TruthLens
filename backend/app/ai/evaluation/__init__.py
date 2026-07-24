"""
Evaluation Module
=================
Provides automated evaluation framework for image detection performance.
"""

from .evaluator import run_evaluation, evaluate_with_ground_truth

__all__ = ["run_evaluation", "evaluate_with_ground_truth"]
