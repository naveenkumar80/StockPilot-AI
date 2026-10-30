import sys
import os

# Add root and api service paths to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
api_dir = os.path.join(root_dir, "services", "api")
for p in [root_dir, api_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.db.session import SessionLocal
from services.ml.training.trainer import ModelTrainingPipeline


def main():
    db = SessionLocal()
    try:
        trainer = ModelTrainingPipeline()
        report = trainer.train_and_benchmark(db, lookback_days=180, n_splits=4)
        print("=" * 60)
        print(f"StockPilot AI — ML Training Pipeline Complete")
        print(f"Model Version: {report['model_version']}")
        print(f"Algorithm:     {report['algorithm']}")
        print(f"Artifact:      {report['artifact_path']}")
        print(f"Samples:       {report['samples_count']}")
        print(f"Duration:      {report['training_duration_ms']:.1f}ms")
        print("-" * 60)
        wf = report["walk_forward_evaluation"]
        print(f"Walk-Forward ROC-AUC:    {wf['roc_auc']:.4f}")
        print(f"Walk-Forward Brier:      {wf['brier_score']:.4f}")
        print(f"Walk-Forward Log Loss:   {wf['log_loss']:.4f}")
        print(f"Precision (BUY):         {wf['precision_buy']:.4f}")
        print(f"Recall (BUY):            {wf['recall_buy']:.4f}")
        print(f"Calibration ECE:         {wf['expected_calibration_error']:.4f}")
        print("-" * 60)
        comp = report["price_only_vs_news_comparison"]
        print(f"Model A (Price-Only)  ROC-AUC: {comp['model_a_price_only']['roc_auc']:.4f}")
        print(f"Model B (Price+News)  ROC-AUC: {comp['model_b_price_plus_news']['roc_auc']:.4f}")
        print(f"News Feature Uplift:           {comp['news_uplift_roc_auc']:+.4f} ROC-AUC")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    main()

