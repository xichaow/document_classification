"""
Performance metrics calculation for document classification evaluation.

This module provides comprehensive metrics calculation including precision,
recall, F1-score, confusion matrix, and other evaluation metrics.
"""

import numpy as np
import logging
from typing import Dict, List, Any, Optional
from sklearn.metrics import (
    precision_recall_fscore_support,
    accuracy_score,
    confusion_matrix,
)
from collections import defaultdict, Counter
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Calculator for classification performance metrics.

    Provides methods to calculate precision, recall, F1-score, confusion matrix,
    and generate comprehensive evaluation reports.
    """

    def __init__(self):
        """Initialize metrics calculator."""
        self.document_types = [
            "Government ID",
            "Payslip",
            "Bank Statement",
            "Employment Letter",
            "Utility Bill",
            "Savings Statement",
            "Unknown",
        ]

    def calculate_classification_metrics(
        self, y_true: List[str], y_pred: List[str], confidences: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive classification metrics.

        Args:
            y_true: True labels.
            y_pred: Predicted labels.
            confidences: Prediction confidence scores.

        Returns:
            Dict[str, Any]: Comprehensive metrics report.
        """
        if len(y_true) != len(y_pred):
            raise ValueError("y_true and y_pred must have same length")

        if not y_true or not y_pred:
            raise ValueError("Input lists cannot be empty")

        try:
            # Overall accuracy
            accuracy = accuracy_score(y_true, y_pred)

            # Per-class metrics
            precision, recall, f1, support = precision_recall_fscore_support(
                y_true,
                y_pred,
                average=None,
                labels=self.document_types,
                zero_division=0,
            )

            # Macro and weighted averages
            macro_precision, macro_recall, macro_f1, _ = (
                precision_recall_fscore_support(
                    y_true, y_pred, average="macro", zero_division=0
                )
            )

            weighted_precision, weighted_recall, weighted_f1, _ = (
                precision_recall_fscore_support(
                    y_true, y_pred, average="weighted", zero_division=0
                )
            )

            # Confusion matrix
            cm = confusion_matrix(y_true, y_pred, labels=self.document_types)

            # Per-class results
            per_class_metrics = []
            for i, doc_type in enumerate(self.document_types):
                per_class_metrics.append(
                    {
                        "document_type": doc_type,
                        "precision": float(precision[i]) if i < len(precision) else 0.0,
                        "recall": float(recall[i]) if i < len(recall) else 0.0,
                        "f1_score": float(f1[i]) if i < len(f1) else 0.0,
                        "support": int(support[i]) if i < len(support) else 0,
                    }
                )

            # Confidence-based metrics
            confidence_metrics = {}
            if confidences:
                confidence_metrics = self._calculate_confidence_metrics(
                    y_true, y_pred, confidences
                )

            return {
                "overall_accuracy": float(accuracy),
                "macro_avg": {
                    "precision": float(macro_precision),
                    "recall": float(macro_recall),
                    "f1_score": float(macro_f1),
                },
                "weighted_avg": {
                    "precision": float(weighted_precision),
                    "recall": float(weighted_recall),
                    "f1_score": float(weighted_f1),
                },
                "per_class_metrics": per_class_metrics,
                "confusion_matrix": cm.tolist(),
                "class_names": self.document_types,
                "total_samples": len(y_true),
                "confidence_metrics": confidence_metrics,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            raise

    def _calculate_confidence_metrics(
        self, y_true: List[str], y_pred: List[str], confidences: List[float]
    ) -> Dict[str, Any]:
        """
        Calculate confidence-based metrics.

        Args:
            y_true: True labels.
            y_pred: Predicted labels.
            confidences: Prediction confidences.

        Returns:
            Dict[str, Any]: Confidence-based metrics.
        """
        try:
            confidences = np.array(confidences)
            correct_predictions = np.array([t == p for t, p in zip(y_true, y_pred)])

            # Average confidence
            avg_confidence = float(np.mean(confidences))
            avg_confidence_correct = float(np.mean(confidences[correct_predictions]))
            avg_confidence_incorrect = (
                float(np.mean(confidences[~correct_predictions]))
                if np.sum(~correct_predictions) > 0
                else 0.0
            )

            # Confidence thresholds analysis
            thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
            threshold_analysis = []

            for threshold in thresholds:
                high_conf_mask = confidences >= threshold
                if np.sum(high_conf_mask) > 0:
                    high_conf_accuracy = float(
                        np.mean(correct_predictions[high_conf_mask])
                    )
                    high_conf_count = int(np.sum(high_conf_mask))
                    high_conf_percentage = float(
                        high_conf_count / len(confidences) * 100
                    )
                else:
                    high_conf_accuracy = 0.0
                    high_conf_count = 0
                    high_conf_percentage = 0.0

                threshold_analysis.append(
                    {
                        "threshold": threshold,
                        "accuracy": high_conf_accuracy,
                        "count": high_conf_count,
                        "percentage": high_conf_percentage,
                    }
                )

            return {
                "average_confidence": avg_confidence,
                "average_confidence_correct": avg_confidence_correct,
                "average_confidence_incorrect": avg_confidence_incorrect,
                "confidence_distribution": {
                    "min": float(np.min(confidences)),
                    "max": float(np.max(confidences)),
                    "std": float(np.std(confidences)),
                    "median": float(np.median(confidences)),
                },
                "threshold_analysis": threshold_analysis,
            }

        except Exception as e:
            logger.error(f"Error calculating confidence metrics: {e}")
            return {}

    def generate_confusion_matrix_data(
        self, y_true: List[str], y_pred: List[str]
    ) -> Dict[str, Any]:
        """
        Generate confusion matrix with normalized values.

        Args:
            y_true: True labels.
            y_pred: Predicted labels.

        Returns:
            Dict[str, Any]: Confusion matrix data.
        """
        try:
            # Raw confusion matrix
            cm = confusion_matrix(y_true, y_pred, labels=self.document_types)

            # Normalized confusion matrix
            cm_normalized = cm.astype("float") / (cm.sum(axis=1, keepdims=True) + 1e-10)

            # Convert to percentages
            cm_percentage = cm_normalized * 100

            return {
                "raw_matrix": cm.tolist(),
                "normalized_matrix": cm_normalized.tolist(),
                "percentage_matrix": cm_percentage.tolist(),
                "class_names": self.document_types,
                "total_samples": int(np.sum(cm)),
            }

        except Exception as e:
            logger.error(f"Error generating confusion matrix: {e}")
            return {}

    def calculate_performance_trends(
        self, results_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate performance trends over time.

        Args:
            results_history: List of historical evaluation results.

        Returns:
            Dict[str, Any]: Trend analysis.
        """
        if not results_history or len(results_history) < 2:
            return {"error": "Insufficient historical data for trend analysis"}

        try:
            # Extract metrics over time
            timestamps = [r.get("timestamp", "") for r in results_history]
            accuracies = [r.get("overall_accuracy", 0) for r in results_history]
            macro_f1s = [
                r.get("macro_avg", {}).get("f1_score", 0) for r in results_history
            ]

            # Calculate trends
            accuracy_trend = self._calculate_trend(accuracies)
            f1_trend = self._calculate_trend(macro_f1s)

            # Recent vs historical performance
            recent_window = min(5, len(results_history))
            recent_accuracy = np.mean(accuracies[-recent_window:])
            historical_accuracy = (
                np.mean(accuracies[:-recent_window])
                if len(accuracies) > recent_window
                else recent_accuracy
            )

            return {
                "timestamps": timestamps,
                "accuracy_history": accuracies,
                "f1_history": macro_f1s,
                "trends": {"accuracy_trend": accuracy_trend, "f1_trend": f1_trend},
                "performance_comparison": {
                    "recent_accuracy": float(recent_accuracy),
                    "historical_accuracy": float(historical_accuracy),
                    "improvement": float(recent_accuracy - historical_accuracy),
                },
                "total_evaluations": len(results_history),
            }

        except Exception as e:
            logger.error(f"Error calculating performance trends: {e}")
            return {"error": str(e)}

    def _calculate_trend(self, values: List[float]) -> str:
        """
        Calculate trend direction from a series of values.

        Args:
            values: List of numeric values.

        Returns:
            str: Trend direction ('improving', 'declining', 'stable').
        """
        if len(values) < 2:
            return "stable"

        try:
            # Simple linear trend
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]

            if slope > 0.01:  # 1% improvement threshold
                return "improving"
            elif slope < -0.01:  # 1% decline threshold
                return "declining"
            else:
                return "stable"
        except Exception:
            return "stable"

    def export_metrics_report(self, metrics: Dict[str, Any], filepath: str) -> None:
        """
        Export metrics report to JSON file.

        Args:
            metrics: Calculated metrics.
            filepath: Output file path.
        """
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)

            logger.info(f"Metrics report exported to {filepath}")

        except Exception as e:
            logger.error(f"Error exporting metrics report: {e}")
            raise

    def generate_classification_summary(
        self, y_true: List[str], y_pred: List[str]
    ) -> Dict[str, Any]:
        """
        Generate a high-level classification summary.

        Args:
            y_true: True labels.
            y_pred: Predicted labels.

        Returns:
            Dict[str, Any]: Classification summary.
        """
        try:
            # Label distribution
            true_distribution = dict(Counter(y_true))
            pred_distribution = dict(Counter(y_pred))

            # Correct predictions per class
            correct_per_class = defaultdict(int)
            for true_label, pred_label in zip(y_true, y_pred):
                if true_label == pred_label:
                    correct_per_class[true_label] += 1

            # Overall statistics
            total_samples = len(y_true)
            total_correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)

            return {
                "total_samples": total_samples,
                "total_correct": total_correct,
                "overall_accuracy": float(total_correct / total_samples),
                "label_distribution": {
                    "true": true_distribution,
                    "predicted": pred_distribution,
                },
                "correct_predictions_per_class": dict(correct_per_class),
                "most_common_true_label": max(
                    true_distribution.items(), key=lambda x: x[1]
                )[0],
                "most_common_predicted_label": max(
                    pred_distribution.items(), key=lambda x: x[1]
                )[0],
                "class_balance_score": self._calculate_class_balance_score(
                    true_distribution
                ),
            }

        except Exception as e:
            logger.error(f"Error generating classification summary: {e}")
            return {}

    def _calculate_class_balance_score(self, distribution: Dict[str, int]) -> float:
        """
        Calculate class balance score (1.0 = perfectly balanced, 0.0 = highly imbalanced).

        Args:
            distribution: Label distribution.

        Returns:
            float: Balance score.
        """
        if not distribution or len(distribution) < 2:
            return 1.0

        counts = list(distribution.values())
        min_count = min(counts)
        max_count = max(counts)

        if max_count == 0:
            return 1.0

        return float(min_count / max_count)
