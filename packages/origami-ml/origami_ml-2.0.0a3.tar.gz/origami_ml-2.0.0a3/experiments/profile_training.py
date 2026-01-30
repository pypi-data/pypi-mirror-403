#!/usr/bin/env python
"""Comprehensive Origami training profiler.

Note: Set OMP_NUM_THREADS=1 before running with --compare-workers to avoid
fork() + OpenMP conflicts:
    OMP_NUM_THREADS=1 python experiments/profile_training.py --compare-workers

Profiles training performance across different configurations to identify
bottlenecks and optimization opportunities.

Usage:
    # Quick profile (default settings)
    uv run python experiments/profile_training.py

    # Full profile with torch.profiler traces
    uv run python experiments/profile_training.py --full

    # Custom configuration
    uv run python experiments/profile_training.py --batch-size 64 --d-model 256

    # Compare num_workers settings
    uv run python experiments/profile_training.py --compare-workers

    # Save results to JSON for comparison
    uv run python experiments/profile_training.py --output results.json
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import statistics
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader

from origami import DataConfig, ModelConfig, OrigamiConfig, OrigamiPipeline, TrainingConfig
from origami.training import OrigamiDataCollator, OrigamiDataset

# ============================================================================
# Timing Utilities
# ============================================================================

@dataclass
class TimingResult:
    """Statistics for a timed operation."""
    name: str
    count: int
    total_ms: float
    mean_ms: float
    std_ms: float
    min_ms: float
    max_ms: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TimingStats:
    """Collect and analyze timing statistics."""
    times: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def add(self, name: str, elapsed_seconds: float):
        self.times[name].append(elapsed_seconds * 1000)  # Store in ms

    def get_result(self, name: str) -> TimingResult | None:
        if name not in self.times or not self.times[name]:
            return None
        times = self.times[name]
        return TimingResult(
            name=name,
            count=len(times),
            total_ms=sum(times),
            mean_ms=statistics.mean(times),
            std_ms=statistics.stdev(times) if len(times) > 1 else 0,
            min_ms=min(times),
            max_ms=max(times),
        )

    def all_results(self) -> list[TimingResult]:
        results = []
        for name in self.times:
            result = self.get_result(name)
            if result:
                results.append(result)
        return sorted(results, key=lambda r: -r.total_ms)

    def summary(self, title: str = "TIMING SUMMARY") -> str:
        results = self.all_results()
        if not results:
            return "No timing data collected"

        total_time = sum(r.total_ms for r in results)
        lines = [
            "",
            "=" * 80,
            title.center(80),
            "=" * 80,
            f"{'Operation':<35} {'Mean':>10} {'Std':>10} {'Min':>10} {'Max':>10} {'%':>6}",
            "-" * 80,
        ]

        for r in results:
            pct = 100 * r.total_ms / total_time if total_time > 0 else 0
            lines.append(
                f"{r.name:<35} {r.mean_ms:>9.2f}ms {r.std_ms:>9.2f}ms "
                f"{r.min_ms:>9.2f}ms {r.max_ms:>9.2f}ms {pct:>5.1f}%"
            )

        lines.append("=" * 80)
        return "\n".join(lines)


def sync_device():
    """Synchronize GPU if available."""
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    elif torch.backends.mps.is_available():
        torch.mps.synchronize()


@contextmanager
def timed(stats: TimingStats, name: str, sync: bool = True):
    """Context manager for timing code blocks."""
    if sync:
        sync_device()
    start = time.perf_counter()
    yield
    if sync:
        sync_device()
    stats.add(name, time.perf_counter() - start)


# ============================================================================
# System Information
# ============================================================================

@dataclass
class SystemInfo:
    """System and environment information."""
    platform: str
    python_version: str
    torch_version: str
    device_type: str
    device_name: str
    device_count: int
    cuda_version: str | None
    cudnn_version: int | None
    cudnn_benchmark: bool
    memory_gb: float | None
    numba_available: bool
    accelerate_available: bool

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        lines = [
            "",
            "=" * 80,
            "SYSTEM INFORMATION".center(80),
            "=" * 80,
            f"Platform:          {self.platform}",
            f"Python:            {self.python_version}",
            f"PyTorch:           {self.torch_version}",
            f"Device:            {self.device_type} ({self.device_name})",
            f"Device count:      {self.device_count}",
        ]

        if self.cuda_version:
            lines.append(f"CUDA version:      {self.cuda_version}")
        if self.cudnn_version:
            lines.append(f"cuDNN version:     {self.cudnn_version}")
            lines.append(f"cuDNN benchmark:   {self.cudnn_benchmark}")
        if self.memory_gb:
            lines.append(f"GPU memory:        {self.memory_gb:.1f} GB")

        lines.extend([
            f"Numba available:   {self.numba_available}",
            f"Accelerate:        {self.accelerate_available}",
            "=" * 80,
        ])

        return "\n".join(lines)


def get_system_info() -> SystemInfo:
    """Gather system information."""
    # Check for numba
    try:
        import numba
        numba_available = True
    except ImportError:
        numba_available = False

    # Check for accelerate
    try:
        import accelerate
        accelerate_available = True
    except ImportError:
        accelerate_available = False

    # Determine device info
    if torch.cuda.is_available():
        device_type = "cuda"
        device_name = torch.cuda.get_device_name(0)
        device_count = torch.cuda.device_count()
        cuda_version = torch.version.cuda
        cudnn_version = torch.backends.cudnn.version()
        cudnn_benchmark = torch.backends.cudnn.benchmark
        memory_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
    elif torch.backends.mps.is_available():
        device_type = "mps"
        device_name = "Apple Silicon"
        device_count = 1
        cuda_version = None
        cudnn_version = None
        cudnn_benchmark = False
        memory_gb = None  # MPS doesn't expose this easily
    else:
        device_type = "cpu"
        device_name = platform.processor() or "Unknown"
        device_count = 0
        cuda_version = None
        cudnn_version = None
        cudnn_benchmark = False
        memory_gb = None

    return SystemInfo(
        platform=f"{platform.system()} {platform.release()}",
        python_version=platform.python_version(),
        torch_version=torch.__version__,
        device_type=device_type,
        device_name=device_name,
        device_count=device_count,
        cuda_version=cuda_version,
        cudnn_version=cudnn_version,
        cudnn_benchmark=cudnn_benchmark,
        memory_gb=memory_gb,
        numba_available=numba_available,
        accelerate_available=accelerate_available,
    )


# ============================================================================
# Data Generation
# ============================================================================

def generate_sample_data(n: int = 5000, complexity: str = "medium") -> list[dict]:
    """Generate sample JSON data for profiling.

    Args:
        n: Number of samples
        complexity: "simple", "medium", or "complex" - affects nesting depth
    """
    data = []
    categories = ["A", "B", "C", "D", "E"]

    for i in range(n):
        if complexity == "simple":
            obj = {
                "id": i,
                "category": random.choice(categories),
                "value": random.randint(0, 100),
            }
        elif complexity == "medium":
            obj = {
                "id": i,
                "category": random.choice(categories),
                "value1": random.randint(0, 100),
                "value2": random.random() * 1000,
                "nested": {
                    "field1": random.choice(["x", "y", "z"]),
                    "field2": random.randint(0, 50),
                },
                "tags": random.sample(["tag1", "tag2", "tag3", "tag4"], k=random.randint(1, 3)),
            }
        else:  # complex
            obj = {
                "id": i,
                "category": random.choice(categories),
                "value1": random.randint(0, 100),
                "value2": random.random() * 1000,
                "nested": {
                    "level1": {
                        "level2": {
                            "field": random.choice(["a", "b", "c"]),
                        }
                    },
                    "array": [random.randint(0, 10) for _ in range(3)],
                },
                "metadata": {
                    "created": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                    "tags": random.sample(["t1", "t2", "t3", "t4", "t5"], k=random.randint(2, 4)),
                },
            }
        data.append(obj)

    return data


# ============================================================================
# Profiling Functions
# ============================================================================

def profile_grammar_comparison(
    pipeline: OrigamiPipeline,
    data: list[dict],
    batch_size: int = 32,
    num_iterations: int = 20,
) -> dict[str, TimingResult]:
    """Compare Numba vs PyTorch grammar implementations."""
    print("\n" + "=" * 80)
    print("GRAMMAR IMPLEMENTATION COMPARISON".center(80))
    print("=" * 80)

    tokenizer = pipeline._tokenizer
    model = pipeline._model
    grammar_pda = getattr(model, "_grammar_pda", None)

    if grammar_pda is None:
        print("Grammar constraints disabled, skipping.")
        return {}

    # Check if Numba is available
    try:
        from origami.constraints.json_grammar import NUMBA_AVAILABLE
    except ImportError:
        NUMBA_AVAILABLE = False

    # Create a batch (on CPU for grammar comparison)
    dataset = OrigamiDataset(data[:batch_size], tokenizer, shuffle=False)
    collator = OrigamiDataCollator(tokenizer, max_length=512, grammar_pda=None)
    batch = collator([dataset[i] for i in range(min(batch_size, len(dataset)))])

    token_ids = batch.input_ids  # Already on CPU
    batch_size_actual, seq_len = token_ids.shape
    vocab_size = tokenizer.vocab.size
    mask_size_mb = batch_size_actual * seq_len * vocab_size / 1e6

    print(f"Batch shape: ({batch_size_actual}, {seq_len})")
    print(f"Vocab size: {vocab_size}")
    print(f"Grammar mask size: {mask_size_mb:.1f} MB per batch")
    print(f"Numba available: {NUMBA_AVAILABLE}")

    results = {}

    # Warmup
    _ = grammar_pda.compute_valid_mask(token_ids, use_numba=False)

    # Time Numba (if available)
    if NUMBA_AVAILABLE:
        # Warmup Numba JIT
        _ = grammar_pda.compute_valid_mask(token_ids, use_numba=True)

        stats = TimingStats()
        for _ in range(num_iterations):
            with timed(stats, "numba", sync=False):
                _ = grammar_pda.compute_valid_mask(token_ids, use_numba=True)
        result = stats.get_result("numba")
        if result:
            results["numba"] = result
            print(f"Numba:   {result.mean_ms:.2f}ms ± {result.std_ms:.2f}ms")

    # Time PyTorch
    stats = TimingStats()
    for _ in range(num_iterations):
        with timed(stats, "pytorch", sync=False):
            _ = grammar_pda.compute_valid_mask(token_ids, use_numba=False)
    result = stats.get_result("pytorch")
    if result:
        results["pytorch"] = result
        print(f"PyTorch: {result.mean_ms:.2f}ms ± {result.std_ms:.2f}ms")

    if "numba" in results and "pytorch" in results:
        speedup = results["pytorch"].mean_ms / results["numba"].mean_ms
        print(f"Numba speedup: {speedup:.2f}x")

    return results


def profile_data_loading(
    pipeline: OrigamiPipeline,
    data: list[dict],
    batch_size: int = 32,
    num_batches: int = 50,
) -> dict[str, Any]:
    """Profile data loading and collation overhead."""
    print("\n" + "=" * 80)
    print("DATA LOADING PROFILE".center(80))
    print("=" * 80)

    tokenizer = pipeline._tokenizer
    model = pipeline._model
    grammar_pda = getattr(model, "_grammar_pda", None)

    dataset = OrigamiDataset(data, tokenizer, shuffle=True)

    # Profile tokenization
    stats = TimingStats()
    for _ in range(num_batches):
        batch_indices = [random.randint(0, len(dataset) - 1) for _ in range(batch_size)]
        with timed(stats, "tokenization", sync=False):
            instances = [dataset[idx] for idx in batch_indices]

    # Profile collation WITHOUT grammar
    collator_no_grammar = OrigamiDataCollator(tokenizer, max_length=512, grammar_pda=None)
    for _ in range(num_batches):
        batch_indices = [random.randint(0, len(dataset) - 1) for _ in range(batch_size)]
        instances = [dataset[idx] for idx in batch_indices]
        with timed(stats, "collation_no_grammar", sync=False):
            _ = collator_no_grammar(instances)

    # Profile collation WITH grammar
    if grammar_pda:
        collator_with_grammar = OrigamiDataCollator(tokenizer, max_length=512, grammar_pda=grammar_pda)
        for _ in range(num_batches):
            batch_indices = [random.randint(0, len(dataset) - 1) for _ in range(batch_size)]
            instances = [dataset[idx] for idx in batch_indices]
            with timed(stats, "collation_with_grammar", sync=False):
                _ = collator_with_grammar(instances)

    print(stats.summary("DATA LOADING BREAKDOWN"))

    # Calculate grammar overhead
    result = {"stats": {r.name: r.to_dict() for r in stats.all_results()}}

    if grammar_pda:
        no_grammar = stats.get_result("collation_no_grammar")
        with_grammar = stats.get_result("collation_with_grammar")
        if no_grammar and with_grammar:
            overhead_ms = with_grammar.mean_ms - no_grammar.mean_ms
            overhead_pct = 100 * overhead_ms / with_grammar.mean_ms
            result["grammar_overhead_ms"] = overhead_ms
            result["grammar_overhead_pct"] = overhead_pct
            print(f"\nGrammar overhead: {overhead_ms:.2f}ms ({overhead_pct:.1f}% of collation time)")

    return result


def profile_training_step(
    pipeline: OrigamiPipeline,
    data: list[dict],
    batch_size: int = 32,
    num_steps: int = 100,
    num_workers: int = 0,
) -> dict[str, Any]:
    """Profile individual training step components."""
    print("\n" + "=" * 80)
    print(f"TRAINING STEP PROFILE (num_workers={num_workers})".center(80))
    print("=" * 80)

    device = next(pipeline._model.parameters()).device
    tokenizer = pipeline._tokenizer
    model = pipeline._model
    grammar_pda = getattr(model, "_grammar_pda", None)

    dataset = OrigamiDataset(data, tokenizer, shuffle=True)
    collator = OrigamiDataCollator(tokenizer, max_length=512, grammar_pda=grammar_pda)

    # Use spawn context to avoid fork() + OpenMP conflicts with Numba
    mp_context = "spawn" if num_workers > 0 else None

    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collator,
        num_workers=num_workers,
        persistent_workers=num_workers > 0,
        multiprocessing_context=mp_context,
    )

    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

    stats = TimingStats()
    step_times = []

    # Warmup
    for batch in dataloader:
        batch = batch.to(device)
        output = model(
            input_ids=batch.input_ids,
            path_types=batch.path_types,
            path_ids=batch.path_ids,
            path_lengths=batch.path_lengths,
            attention_mask=batch.attention_mask,
            labels=batch.labels,
            numeric_values=batch.numeric_values,
            numeric_mask=batch.numeric_mask,
            grammar_mask=batch.grammar_mask,
        )
        output.loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        break

    # Profile
    for step, batch in enumerate(dataloader):
        if step >= num_steps:
            break

        step_start = time.perf_counter()

        with timed(stats, "device_transfer"):
            batch = batch.to(device)

        with timed(stats, "zero_grad"):
            optimizer.zero_grad()

        with timed(stats, "forward"):
            output = model(
                input_ids=batch.input_ids,
                path_types=batch.path_types,
                path_ids=batch.path_ids,
                path_lengths=batch.path_lengths,
                attention_mask=batch.attention_mask,
                labels=batch.labels,
                numeric_values=batch.numeric_values,
                numeric_mask=batch.numeric_mask,
                grammar_mask=batch.grammar_mask,
            )

        with timed(stats, "backward"):
            output.loss.backward()

        with timed(stats, "clip_grad"):
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        with timed(stats, "optimizer_step"):
            optimizer.step()

        sync_device()
        step_times.append((time.perf_counter() - step_start) * 1000)

    print(stats.summary("TRAINING STEP BREAKDOWN"))

    # Throughput calculation
    if step_times:
        mean_step_ms = statistics.mean(step_times)
        std_step_ms = statistics.stdev(step_times) if len(step_times) > 1 else 0
        steps_per_sec = 1000 / mean_step_ms
        samples_per_sec = batch_size * steps_per_sec

        print(f"\nTotal step time: {mean_step_ms:.2f}ms ± {std_step_ms:.2f}ms")
        print(f"Throughput: {steps_per_sec:.1f} steps/sec, {samples_per_sec:.0f} samples/sec")

    return {
        "stats": {r.name: r.to_dict() for r in stats.all_results()},
        "total_step_ms": mean_step_ms if step_times else None,
        "samples_per_sec": samples_per_sec if step_times else None,
    }


def profile_forward_breakdown(
    pipeline: OrigamiPipeline,
    data: list[dict],
    batch_size: int = 32,
    num_iterations: int = 50,
) -> dict[str, Any]:
    """Profile forward pass component breakdown."""
    print("\n" + "=" * 80)
    print("FORWARD PASS BREAKDOWN".center(80))
    print("=" * 80)

    device = next(pipeline._model.parameters()).device
    tokenizer = pipeline._tokenizer
    model = pipeline._model
    grammar_pda = getattr(model, "_grammar_pda", None)

    dataset = OrigamiDataset(data, tokenizer, shuffle=False)
    collator = OrigamiDataCollator(tokenizer, max_length=512, grammar_pda=grammar_pda)
    batch = collator([dataset[i] for i in range(min(batch_size, len(dataset)))])
    batch = batch.to(device)

    model.eval()
    stats = TimingStats()

    # Get model components
    embeddings = model.embeddings
    backbone = model.backbone
    discrete_head = model.discrete_head

    with torch.no_grad():
        for _ in range(num_iterations):
            # Embeddings (includes KVPE)
            with timed(stats, "embeddings"):
                hidden = embeddings(
                    input_ids=batch.input_ids,
                    path_types=batch.path_types,
                    path_ids=batch.path_ids,
                    path_lengths=batch.path_lengths,
                    numeric_values=batch.numeric_values,
                )

            # Backbone
            with timed(stats, "backbone"):
                hidden = backbone(hidden, attention_mask=batch.attention_mask)

            # Discrete head
            with timed(stats, "discrete_head"):
                logits = discrete_head(hidden)

            # Grammar masking (if applicable)
            if batch.grammar_mask is not None:
                with timed(stats, "grammar_masking"):
                    logits = logits.masked_fill(~batch.grammar_mask, float("-inf"))

    print(stats.summary("FORWARD PASS COMPONENTS"))
    return {"stats": {r.name: r.to_dict() for r in stats.all_results()}}


def profile_memory_usage(
    pipeline: OrigamiPipeline,
    data: list[dict],
    batch_sizes: list[int] = [16, 32, 64, 128],
) -> dict[str, Any]:
    """Profile GPU memory usage at different batch sizes."""
    if not torch.cuda.is_available():
        print("\nMemory profiling requires CUDA. Skipping.")
        return {}

    print("\n" + "=" * 80)
    print("GPU MEMORY PROFILE".center(80))
    print("=" * 80)

    device = next(pipeline._model.parameters()).device
    tokenizer = pipeline._tokenizer
    model = pipeline._model
    grammar_pda = getattr(model, "_grammar_pda", None)

    dataset = OrigamiDataset(data, tokenizer, shuffle=False)

    results = {}

    for batch_size in batch_sizes:
        if batch_size > len(dataset):
            continue

        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

        try:
            collator = OrigamiDataCollator(tokenizer, max_length=512, grammar_pda=grammar_pda)
            batch = collator([dataset[i] for i in range(batch_size)])
            batch = batch.to(device)

            model.train()
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
            optimizer.zero_grad()

            output = model(
                input_ids=batch.input_ids,
                path_types=batch.path_types,
                path_ids=batch.path_ids,
                path_lengths=batch.path_lengths,
                attention_mask=batch.attention_mask,
                labels=batch.labels,
                numeric_values=batch.numeric_values,
                numeric_mask=batch.numeric_mask,
                grammar_mask=batch.grammar_mask,
            )
            output.loss.backward()
            optimizer.step()

            peak_memory_mb = torch.cuda.max_memory_allocated() / 1e6
            results[batch_size] = peak_memory_mb
            print(f"Batch size {batch_size:3d}: {peak_memory_mb:,.0f} MB peak memory")

        except RuntimeError as e:
            if "out of memory" in str(e):
                print(f"Batch size {batch_size:3d}: OOM")
                results[batch_size] = "OOM"
            else:
                raise

    return {"memory_by_batch_size": results}


def profile_compare_workers(
    pipeline: OrigamiPipeline,
    data: list[dict],
    batch_size: int = 32,
    num_steps: int = 50,
    worker_counts: list[int] = [0, 2, 4],
) -> dict[str, Any]:
    """Compare performance with different num_workers settings."""
    print("\n" + "=" * 80)
    print("DATALOADER WORKERS COMPARISON".center(80))
    print("=" * 80)

    results = {}

    for num_workers in worker_counts:
        print(f"\nProfiling with num_workers={num_workers}...")
        result = profile_training_step(
            pipeline, data, batch_size=batch_size,
            num_steps=num_steps, num_workers=num_workers
        )
        results[num_workers] = {
            "total_step_ms": result["total_step_ms"],
            "samples_per_sec": result["samples_per_sec"],
        }

    # Summary comparison
    print("\n" + "-" * 60)
    print("WORKERS COMPARISON SUMMARY".center(60))
    print("-" * 60)
    for num_workers, data in results.items():
        if data["samples_per_sec"]:
            print(f"num_workers={num_workers}: {data['samples_per_sec']:.0f} samples/sec")

    return results


def run_torch_profiler(
    pipeline: OrigamiPipeline,
    data: list[dict],
    batch_size: int = 32,
    output_dir: str = "./tb_logs",
):
    """Run detailed torch.profiler analysis."""
    from torch.profiler import ProfilerActivity, profile, schedule, tensorboard_trace_handler

    print("\n" + "=" * 80)
    print("TORCH PROFILER (TensorBoard Trace)".center(80))
    print("=" * 80)

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    device = next(pipeline._model.parameters()).device
    tokenizer = pipeline._tokenizer
    model = pipeline._model
    grammar_pda = getattr(model, "_grammar_pda", None)

    dataset = OrigamiDataset(data, tokenizer, shuffle=True)
    collator = OrigamiDataCollator(tokenizer, max_length=512, grammar_pda=grammar_pda)

    dataloader = DataLoader(
        dataset, batch_size=batch_size, shuffle=True, collate_fn=collator, num_workers=0
    )

    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

    # Profile schedule
    prof_schedule = schedule(
        skip_first=3,
        wait=1,
        warmup=1,
        active=5,
        repeat=2
    )

    activities = [ProfilerActivity.CPU]
    if torch.cuda.is_available():
        activities.append(ProfilerActivity.CUDA)

    with profile(
        activities=activities,
        schedule=prof_schedule,
        on_trace_ready=tensorboard_trace_handler(str(output_path)),
        record_shapes=True,
        profile_memory=True,
        with_stack=True,
    ) as prof:
        for step, batch in enumerate(dataloader):
            if step >= 15:
                break

            batch = batch.to(device)
            optimizer.zero_grad()

            output = model(
                input_ids=batch.input_ids,
                path_types=batch.path_types,
                path_ids=batch.path_ids,
                path_lengths=batch.path_lengths,
                attention_mask=batch.attention_mask,
                labels=batch.labels,
                numeric_values=batch.numeric_values,
                numeric_mask=batch.numeric_mask,
                grammar_mask=batch.grammar_mask,
            )
            output.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            prof.step()

    # Print summary table
    sort_key = "cuda_time_total" if torch.cuda.is_available() else "cpu_time_total"
    print(f"\nTop 15 operations by {sort_key}:")
    print(prof.key_averages().table(sort_by=sort_key, row_limit=15))

    print(f"\nFull trace saved to {output_path}/")
    print(f"View with: tensorboard --logdir={output_path}")


# ============================================================================
# Main Entry Point
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="Origami Training Profiler")

    # Model configuration
    parser.add_argument("--d-model", type=int, default=128, help="Model dimension")
    parser.add_argument("--n-layers", type=int, default=4, help="Number of transformer layers")
    parser.add_argument("--n-heads", type=int, default=4, help="Number of attention heads")

    # Profiling configuration
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--num-samples", type=int, default=3000, help="Number of samples to generate")
    parser.add_argument("--complexity", choices=["simple", "medium", "complex"], default="medium",
                        help="JSON complexity level")
    parser.add_argument("--num-steps", type=int, default=100, help="Number of training steps to profile")

    # Profile modes
    parser.add_argument("--full", action="store_true", help="Run full profiling including torch.profiler")
    parser.add_argument("--compare-workers", action="store_true", help="Compare different num_workers settings")
    parser.add_argument("--memory", action="store_true", help="Profile memory usage at different batch sizes")
    parser.add_argument("--quick", action="store_true", help="Quick profile with fewer iterations")

    # Output
    parser.add_argument("--output", "-o", type=str, help="Save results to JSON file")
    parser.add_argument("--tb-dir", type=str, default="./tb_logs", help="TensorBoard output directory")

    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 80)
    print("ORIGAMI TRAINING PROFILER".center(80))
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")

    # System info
    sys_info = get_system_info()
    print(sys_info.summary())

    # Generate data
    print(f"\nGenerating {args.num_samples} samples (complexity={args.complexity})...")
    data = generate_sample_data(args.num_samples, complexity=args.complexity)
    random.shuffle(data)

    # Create pipeline
    config = OrigamiConfig(
        model=ModelConfig(
            d_model=args.d_model,
            n_heads=args.n_heads,
            n_layers=args.n_layers,
            d_ff=args.d_model * 4,
        ),
        training=TrainingConfig(
            batch_size=args.batch_size,
            num_epochs=1,
            dataloader_num_workers=0,
        ),
        data=DataConfig(numeric_mode="discretize"),
    )

    print(f"\nModel configuration:")
    print(f"  d_model={args.d_model}, n_layers={args.n_layers}, n_heads={args.n_heads}")
    print(f"  batch_size={args.batch_size}")

    pipeline = OrigamiPipeline(config)

    # Initialize pipeline (preprocess data, fit tokenizer, build model)
    print("\nInitializing pipeline...")
    pipeline.preprocess(data)

    # Get processed data for profiling
    processed_data = pipeline._preprocessor.transform(data)

    vocab_size = pipeline._tokenizer.vocab.size
    print(f"Vocabulary size: {vocab_size}")

    # Adjust iterations for quick mode
    num_batches = 20 if args.quick else 50
    num_steps = 30 if args.quick else args.num_steps
    num_iterations = 10 if args.quick else 20

    # Collect results
    results = {
        "timestamp": datetime.now().isoformat(),
        "system": sys_info.to_dict(),
        "config": {
            "d_model": args.d_model,
            "n_layers": args.n_layers,
            "n_heads": args.n_heads,
            "batch_size": args.batch_size,
            "vocab_size": vocab_size,
            "complexity": args.complexity,
        },
    }

    # Run profiling
    results["grammar"] = profile_grammar_comparison(
        pipeline, processed_data, batch_size=args.batch_size, num_iterations=num_iterations
    )

    results["data_loading"] = profile_data_loading(
        pipeline, processed_data, batch_size=args.batch_size, num_batches=num_batches
    )

    results["training_step"] = profile_training_step(
        pipeline, processed_data, batch_size=args.batch_size, num_steps=num_steps, num_workers=0
    )

    results["forward_breakdown"] = profile_forward_breakdown(
        pipeline, processed_data, batch_size=args.batch_size, num_iterations=num_iterations
    )

    if args.memory or args.full:
        results["memory"] = profile_memory_usage(pipeline, processed_data)

    if args.compare_workers:
        results["workers_comparison"] = profile_compare_workers(
            pipeline, processed_data, batch_size=args.batch_size, num_steps=30
        )

    if args.full:
        run_torch_profiler(pipeline, processed_data, batch_size=args.batch_size, output_dir=args.tb_dir)

    # Save results
    if args.output:
        # Convert TimingResult objects to dicts
        def convert_results(obj):
            if isinstance(obj, TimingResult):
                return obj.to_dict()
            elif isinstance(obj, dict):
                return {k: convert_results(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_results(v) for v in obj]
            return obj

        output_path = Path(args.output)
        with open(output_path, "w") as f:
            json.dump(convert_results(results), f, indent=2)
        print(f"\nResults saved to {output_path}")

    # Summary
    print("\n" + "=" * 80)
    print("PROFILING COMPLETE".center(80))
    print("=" * 80)

    print("\nKey findings:")

    # Grammar overhead
    if "grammar" in results and results["grammar"]:
        if "numba" in results["grammar"] and "pytorch" in results["grammar"]:
            speedup = results["grammar"]["pytorch"].mean_ms / results["grammar"]["numba"].mean_ms
            print(f"  • Grammar: Numba is {speedup:.1f}x faster than PyTorch")

    # Data loading overhead
    if "data_loading" in results and "grammar_overhead_pct" in results["data_loading"]:
        pct = results["data_loading"]["grammar_overhead_pct"]
        print(f"  • Grammar adds {pct:.0f}% overhead to data loading")

    # Training throughput
    if "training_step" in results and results["training_step"].get("samples_per_sec"):
        print(f"  • Training throughput: {results['training_step']['samples_per_sec']:.0f} samples/sec")

    print("\nRecommendations:")
    print("  1. Enable dataloader_num_workers > 0 to parallelize grammar computation")
    print("  2. Use --compare-workers to find optimal worker count")
    print("  3. Use --full for detailed torch.profiler traces")
    print("  4. On NVIDIA GPUs: enable torch.backends.cudnn.benchmark = True")


if __name__ == "__main__":
    main()
