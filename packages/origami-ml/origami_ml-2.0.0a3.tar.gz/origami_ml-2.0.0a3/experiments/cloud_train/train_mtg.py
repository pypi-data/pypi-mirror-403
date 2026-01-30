#!/usr/bin/env python
"""Train Origami on MTG card dataset.

Predicts card rarity from other attributes like mana cost, colors, types, etc.

Usage:
    uv run python experiments/cloud_train/train_mtg.py
    uv run python experiments/cloud_train/train_mtg.py --epochs 1 --workers 4
"""

import argparse
import json
import random

from origami import DataConfig, ModelConfig, OrigamiConfig, OrigamiPipeline, TrainingConfig
from origami.training import ProgressCallback, accuracy


def load_mtg_data(path: str, max_samples: int | None = None) -> list[dict]:
    """Load MTG data from JSONL file."""
    data = []
    with open(path) as f:
        for line in f:
            data.append(json.loads(line))
            if max_samples and len(data) >= max_samples:
                break
    return data


def main():
    parser = argparse.ArgumentParser(description="Train Origami on MTG dataset")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--workers", type=int, default=0, help="DataLoader workers")
    args = parser.parse_args()

    print("Loading MTG data...")
    data = load_mtg_data("experiments/cloud_train/mtg_data.jsonl")
    print(f"Loaded {len(data)} cards")

    # Show rarity distribution
    rarities = {}
    for card in data:
        r = card["rarity"]
        rarities[r] = rarities.get(r, 0) + 1
    print(f"Rarity distribution: {rarities}")

    # Shuffle and split
    random.seed(42)
    random.shuffle(data)
    split_idx = int(len(data) * 0.9)
    train_data = data[:split_idx]
    eval_data = data[split_idx:]
    print(f"Train: {len(train_data)}, Eval: {len(eval_data)}")

    # Configure model - moderate size for multi-GPU
    config = OrigamiConfig(
        model=ModelConfig(
            d_model=256,
            n_heads=8,
            n_layers=8,
            d_ff=512,
            dropout=0.0,
        ),
        training=TrainingConfig(
            batch_size=args.batch_size,
            learning_rate=8e-4,
            num_epochs=args.epochs,
            warmup_steps=2000,
            eval_strategy="epoch",
            eval_metrics={"accuracy": accuracy},
            eval_sample_size=1000,
            target_key="rarity",
            use_accelerate=True,
            mixed_precision="bf16",  # Use bfloat16 for faster training on A100s
            dataloader_num_workers=args.workers,
        ),
        data=DataConfig(
            numeric_mode="discretize",  # Bin mana values
            cat_threshold=50,
        ),
    )

    print(f"\nConfig:\n{config}")

    # Train
    pipeline = OrigamiPipeline(config)
    pipeline.fit(train_data, eval_data=eval_data, callbacks=[ProgressCallback()])
    pipeline.save("origami_mtg_model.pt")

    # Final evaluation
    print("\n--- Final Evaluation ---")
    results = pipeline.evaluate(
        eval_data,
        target_key="rarity",
        metrics={"accuracy": accuracy}
    )
    print(f"Results: {results}")

    # Sample predictions
    print("\n--- Sample Predictions ---")
    for card in eval_data[:5]:
        pred = pipeline.predict(card, target_key="rarity")
        actual = card["rarity"]
        print(f"  Predicted: {pred}, Actual: {actual}, {'✓' if pred == actual else '✗'}")


if __name__ == "__main__":
    main()
