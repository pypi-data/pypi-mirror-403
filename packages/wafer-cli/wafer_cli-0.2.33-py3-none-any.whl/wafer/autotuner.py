"""Autotuner CLI - Run hyperparameter sweep experiments.

This module provides the implementation for the `wafer autotuner` commands.
"""

import asyncio
import json
from datetime import UTC
from pathlib import Path
from typing import Any


def run_sweep_command(
    config_file: Path | None = None,
    parallel: int = 4,
    resume_sweep_id: str | None = None,
) -> str:
    """Run an autotuner sweep from a JSON config file or resume existing sweep.

    Args:
        config_file: Path to JSON config file (required if not resuming)
        parallel: Number of trials to run concurrently
        resume_sweep_id: Sweep ID to resume (optional)

    Returns:
        JSON string with sweep results

    Raises:
        ValueError: If config file is invalid or sweep not found
        FileNotFoundError: If config file doesn't exist
    """
    if config_file and not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    # Import autotuner core
    from datetime import datetime
    from uuid import uuid4

    import trio
    from wafer_core.tools.autotuner import AutotunerConfig, run_sweep
    from wafer_core.tools.autotuner.dtypes import Sweep, Trial
    from wafer_core.tools.autotuner.search import generate_grid_trials
    from wafer_core.tools.autotuner.storage import add_trial, create_sweep, get_sweep, get_trials

    # Load or reconstruct config
    if resume_sweep_id:
        # Resume existing sweep - load from database
        try:
            existing_sweep = asyncio.run(get_sweep(resume_sweep_id))
            existing_trials = asyncio.run(get_trials(resume_sweep_id))
        except Exception as e:
            raise ValueError(f"Failed to load sweep {resume_sweep_id}: {e}") from e

        # Reconstruct config from stored sweep config
        config_dict = existing_sweep.config
        config = AutotunerConfig(
            name=config_dict["name"],
            description=config_dict.get("description"),
            search_space=config_dict["search_space"],
            command=config_dict["command"],
            metrics=config_dict["metrics"],
            max_trials=config_dict.get("max_trials", 0),
            parallel=parallel,  # Use new parallel value
            timeout=config_dict.get("timeout", 300),
            trials_per_config=config_dict.get("trials_per_config", 1),
        )

        # Reconstruct objectives if present
        if "objectives" in config_dict:
            from wafer_core.tools.autotuner.dtypes import Objective
            config.objectives = [
                Objective(
                    metric=obj["metric"],
                    direction=obj["direction"],
                    weight=obj.get("weight", 1.0),
                )
                for obj in config_dict["objectives"]
            ]

        # Reconstruct constraints if present
        if "constraints" in config_dict:
            from wafer_core.tools.autotuner.dtypes import Constraint
            config.constraints = [
                Constraint(
                    metric=c["metric"],
                    min=c.get("min"),
                    max=c.get("max"),
                    equals=c.get("equals"),
                )
                for c in config_dict["constraints"]
            ]

        actual_sweep_id = resume_sweep_id
        is_resume = True
        # Use current working directory for resume (user should run from same place)
        working_dir = Path.cwd()
    else:
        # New sweep
        if not config_file:
            raise ValueError("config_file is required when not resuming")

        # Load config
        try:
            config = AutotunerConfig.from_json(config_file)
        except Exception as e:
            raise ValueError(f"Failed to parse config: {e}") from e

        # Override parallel from CLI flag
        config.parallel = parallel
        is_resume = False
        working_dir = config_file.parent
        actual_sweep_id = None  # Will be set after creating sweep

    # Run sweep synchronously
    try:
        async def _run_sweep() -> str:
            nonlocal actual_sweep_id

            # Calculate total trials
            search_space = config.get_search_space()
            trial_configs = generate_grid_trials(search_space, config.max_trials)
            total_trials = len(trial_configs) * config.trials_per_config

            if is_resume:
                # Resume mode
                # Print resume status
                num_configs = len(trial_configs)
                print(f"\n🔄 Resuming sweep: {config.name}")
                print(f"Sweep ID: {actual_sweep_id}")
                if config.trials_per_config > 1:
                    print(f"Configurations: {num_configs}")
                    print(f"Trials per config: {config.trials_per_config}")
                    print(f"Total trials: {total_trials}")
                else:
                    print(f"Total trials: {total_trials}")
                print(f"Already completed: {len(existing_trials)}")
                print(f"Parallelism: {config.parallel}")
                print()

                # Track progress (starting from existing)
                completed_count = len(existing_trials)
                success_count = sum(1 for t in existing_trials if t.status.value == "success")
                failed_count = len(existing_trials) - success_count

            else:
                # New sweep mode
                # Generate sweep ID
                sweep_id = str(uuid4())

                # Serialize config to dict for storage
                config_dict: dict[str, Any] = {
                    "name": config.name,
                    "description": config.description,
                    "search_space": config.search_space,
                    "command": config.command,
                    "metrics": config.metrics,
                    "max_trials": config.max_trials,
                    "parallel": config.parallel,
                    "timeout": config.timeout,
                    "trials_per_config": config.trials_per_config,
                }

                if config.objectives:
                    config_dict["objectives"] = [
                        {
                            "metric": obj.metric,
                            "direction": obj.direction,
                            "weight": obj.weight,
                        }
                        for obj in config.objectives
                    ]

                if config.constraints:
                    config_dict["constraints"] = [
                        {
                            "metric": c.metric,
                            "min": c.min,
                            "max": c.max,
                            "equals": c.equals,
                        }
                        for c in config.constraints
                    ]

                # Create sweep in database
                sweep = Sweep(
                    id=sweep_id,
                    user_id="",  # Will be filled by API from auth
                    name=config.name,
                    description=config.description,
                    config=config_dict,
                    status="running",
                    total_trials=total_trials,
                    completed_trials=0,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )

                # Create sweep and get the actual ID from the API
                actual_sweep_id = await create_sweep(sweep)

                # Print initial status
                num_configs = len(trial_configs)
                print(f"\n🚀 Starting sweep: {config.name}")
                print(f"Sweep ID: {actual_sweep_id}")
                if config.trials_per_config > 1:
                    print(f"Configurations: {num_configs}")
                    print(f"Trials per config: {config.trials_per_config}")
                    print(f"Total trials: {total_trials}")
                else:
                    print(f"Total trials: {total_trials}")
                print(f"Parallelism: {config.parallel}")
                print()

                # Track progress
                completed_count = 0
                success_count = 0
                failed_count = 0

            # Define callback to upload and print progress
            async def on_trial_complete(trial: Trial) -> None:
                nonlocal completed_count, success_count, failed_count

                # Upload trial to database immediately
                await add_trial(trial)

                # Update counters
                completed_count += 1
                if trial.status.value == "success":
                    success_count += 1
                else:
                    failed_count += 1

                # Print progress
                status_icon = "✓" if trial.status.value == "success" else "✗"
                constraint_str = " (passed)" if trial.passed_constraints else " (constraint violation)" if trial.status.value == "success" else ""

                # Calculate config number and run number
                config_idx = trial.trial_number // config.trials_per_config
                run_idx = (trial.trial_number % config.trials_per_config) + 1

                # Show config and run info
                if config.trials_per_config > 1:
                    print(f"[{completed_count}/{total_trials}] {status_icon} Config #{config_idx + 1}, Run {run_idx}/{config.trials_per_config}{constraint_str}")
                else:
                    print(f"[{completed_count}/{total_trials}] {status_icon} Config #{config_idx + 1}{constraint_str}")

            # Helper to update sweep status
            async def update_sweep_status(status: str) -> None:
                import httpx
                from wafer_core.tools.autotuner.storage import _get_auth_headers, get_api_url

                api_url = get_api_url()
                headers = _get_auth_headers()

                async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                    await client.patch(
                        f"{api_url}/v1/autotuner/sweeps/{actual_sweep_id}/status",
                        json={"status": status},
                    )

            # Run trials with the actual sweep ID and callback
            # Note: working_dir already set based on is_resume flag

            try:
                await run_sweep(
                    config=config,
                    sweep_id=actual_sweep_id,
                    working_dir=working_dir,
                    on_trial_complete=on_trial_complete,
                    existing_trials=existing_trials if is_resume else None,
                )

                # Mark as completed
                await update_sweep_status("completed")

                # Print final summary
                print()
                print("✅ Sweep completed!")
                print(f"   Total: {total_trials} trials")
                print(f"   Success: {success_count}")
                print(f"   Failed: {failed_count}")
                print(f"   Constraint violations: {completed_count - success_count - failed_count}")
                print()

                # Return result
                return json.dumps(
                    {
                        "success": True,
                        "sweep_id": actual_sweep_id,
                        "name": config.name,
                        "total_trials": total_trials,
                        "completed_trials": completed_count,
                        "success_trials": success_count,
                        "failed_trials": failed_count,
                    },
                    indent=2,
                )

            except KeyboardInterrupt:
                # User pressed Ctrl+C
                print()
                print("❌ Sweep interrupted by user (Ctrl+C)")
                print(f"   Completed: {completed_count}/{total_trials} trials")
                await update_sweep_status("failed")
                raise

            except Exception as e:
                # Any other error
                import traceback
                print()
                print(f"❌ Sweep failed with error: {e}")
                print(f"   Completed: {completed_count}/{total_trials} trials")

                # For Trio nursery exceptions (MultiError/ExceptionGroup), show all sub-exceptions
                if hasattr(e, '__cause__') and e.__cause__ is not None:
                    print(f"\nCause: {e.__cause__}")
                if hasattr(e, 'exceptions'):
                    print(f"\nSub-exceptions ({len(e.exceptions)}):")
                    for i, exc in enumerate(e.exceptions, 1):
                        print(f"  {i}. {type(exc).__name__}: {exc}")
                        if hasattr(exc, '__traceback__'):
                            print(f"     {''.join(traceback.format_tb(exc.__traceback__, limit=3))}")

                await update_sweep_status("failed")
                raise

        return trio.run(_run_sweep)

    except Exception as e:
        raise ValueError(f"Failed to run sweep: {e}") from e


def results_command(
    sweep_id: str,
    sort_by: str | None = None,
    direction: str = "maximize",
    pareto: str | None = None,
    show_all: bool = False,
    limit: int | None = None,
) -> str:
    """Show results from a sweep with optional sorting.

    Args:
        sweep_id: Sweep ID to retrieve
        sort_by: Metric name to sort by (optional)
        direction: Sort direction - "maximize" or "minimize"
        pareto: Comma-separated list of metrics for Pareto frontier
        show_all: Include failed and constraint-violated trials
        limit: Maximum number of results to show (default: all)

    Returns:
        Formatted string with results
    """
    from wafer_core.tools.autotuner import compute_pareto_frontier
    from wafer_core.tools.autotuner.aggregation import aggregate_trials_by_config
    from wafer_core.tools.autotuner.storage import get_sweep, get_trials

    try:
        # Get sweep and trials
        sweep = asyncio.run(get_sweep(sweep_id))
        trials = asyncio.run(get_trials(sweep_id))

        # Check if we should aggregate by config
        trials_per_config = sweep.config.get("trials_per_config", 1) if sweep.config else 1
        use_aggregation = trials_per_config > 1

        # Filter trials based on show_all flag
        if show_all:
            # Show all trials, but separate them by status
            valid_trials = [t for t in trials if t.status.value in ("success", "completed") and t.passed_constraints]
            failed_trials = [t for t in trials if t.status.value in ("failed", "timeout")]
            constraint_violated_trials = [t for t in trials if t.status.value == "constraint_violation" or not t.passed_constraints]
            completed_trials = valid_trials  # For ranking/sorting
        else:
            # Default: only show successful trials
            completed_trials = [t for t in trials if t.status.value in ("success", "completed")]
            valid_trials = completed_trials
            failed_trials = []
            constraint_violated_trials = []

        if not valid_trials and not show_all:
            return f"No completed trials found for sweep {sweep_id}"

        # Aggregate trials if trials_per_config > 1
        aggregated_configs = None
        if use_aggregation:
            aggregated_configs = aggregate_trials_by_config(completed_trials, trials_per_config)
            if not aggregated_configs:
                return f"No valid configurations found for sweep {sweep_id}"

        # Build result string
        lines = [
            f"Sweep: {sweep.name}",
            f"Status: {sweep.status}",
        ]

        if show_all:
            lines.append(f"Trials: {len(valid_trials)} valid, {len(constraint_violated_trials)} constraint violations, {len(failed_trials)} failed / {sweep.total_trials} total")
        else:
            lines.append(f"Trials: {len(completed_trials)} completed / {sweep.total_trials} total")

        lines.append("")

        # Handle Pareto frontier
        if pareto:
            from wafer_core.tools.autotuner.dtypes import Objective

            metrics = [m.strip() for m in pareto.split(",")]
            # Create objectives (default to maximize for all)
            objectives = [Objective(metric=m, direction="maximize") for m in metrics]

            if use_aggregation:
                from wafer_core.tools.autotuner.scoring import compute_pareto_frontier_configs
                pareto_configs = compute_pareto_frontier_configs(aggregated_configs, objectives)

                lines.append(f"Pareto Frontier ({len(pareto_configs)} configs):")
                lines.append("No single config dominates on all metrics.")
                lines.append("")

                for i, config in enumerate(pareto_configs, 1):
                    lines.append(f"Config {i}: {json.dumps(config.config)}")
                    for metric in metrics:
                        if metric in config.metrics:
                            stats = config.metrics[metric]
                            lines.append(f"  {metric}: {stats.mean:.2f} ± {stats.std:.2f}")
                        else:
                            lines.append(f"  {metric}: N/A")
                    lines.append(f"  runs: {len(config.trials)}")
                    lines.append("")
            else:
                pareto_trials = compute_pareto_frontier(completed_trials, objectives)

                lines.append(f"Pareto Frontier ({len(pareto_trials)} configs):")
                lines.append("No single config dominates on all metrics.")
                lines.append("")

                for i, trial in enumerate(pareto_trials, 1):
                    lines.append(f"Config {i}: {json.dumps(trial.config)}")
                    for metric in metrics:
                        value = trial.metrics.get(metric, "N/A")
                        lines.append(f"  {metric}: {value}")
                    lines.append("")

        # Handle single metric sorting
        elif sort_by:
            from wafer_core.tools.autotuner.dtypes import Objective

            objective = Objective(metric=sort_by, direction=direction)

            if use_aggregation:
                from wafer_core.tools.autotuner.scoring import rank_configs_single_objective
                best_configs = rank_configs_single_objective(aggregated_configs, objective)

                lines.append(f"Results (sorted by {sort_by}, {direction}):")
                lines.append("")

                # Apply limit if specified
                configs_to_show = best_configs[:limit] if limit else best_configs

                for i, config in enumerate(configs_to_show, 1):
                    marker = " ⭐" if i == 1 else ""
                    lines.append(f"Rank {i}{marker}: {json.dumps(config.config)}")
                    for metric_name, stats in config.metrics.items():
                        lines.append(f"  {metric_name}: {stats.mean:.2f} ± {stats.std:.2f}")
                    lines.append(f"  runs: {len(config.trials)}")
                    lines.append("")

                # Show count if limited
                if limit and len(best_configs) > limit:
                    lines.append(f"... and {len(best_configs) - limit} more results")
                    lines.append("")
            else:
                from wafer_core.tools.autotuner.scoring import rank_trials_single_objective
                best_trials = rank_trials_single_objective(completed_trials, objective)

                lines.append(f"Results (sorted by {sort_by}, {direction}):")
                lines.append("")

                # Apply limit if specified
                trials_to_show = best_trials[:limit] if limit else best_trials

                for i, trial in enumerate(trials_to_show, 1):
                    marker = " ⭐" if i == 1 else ""
                    lines.append(f"Rank {i}{marker}: {json.dumps(trial.config)}")
                    for metric_name, metric_value in trial.metrics.items():
                        lines.append(f"  {metric_name}: {metric_value}")
                    lines.append(f"  duration: {trial.duration_ms}ms")
                    lines.append("")

                # Show count if limited
                if limit and len(best_trials) > limit:
                    lines.append(f"... and {len(best_trials) - limit} more results")
                    lines.append("")

        # Default: use objectives from config
        else:
            if sweep.config and "objectives" in sweep.config:
                from wafer_core.tools.autotuner.dtypes import Objective

                objectives_data = sweep.config["objectives"]

                if use_aggregation:
                    # Use aggregated config scoring
                    if len(objectives_data) > 1:
                        # Multi-objective: compute Pareto
                        from wafer_core.tools.autotuner.scoring import (
                            compute_pareto_frontier_configs,
                            rank_pareto_configs,
                        )
                        objectives = [
                            Objective(
                                metric=obj["metric"],
                                direction=obj["direction"],
                                weight=obj.get("weight", 1.0)
                            )
                            for obj in objectives_data
                        ]
                        pareto_configs = compute_pareto_frontier_configs(aggregated_configs, objectives)
                        ranked_configs = rank_pareto_configs(pareto_configs, objectives)

                        lines.append("Pareto Frontier (using config objectives):")
                        lines.append(f"Found {len(ranked_configs)} non-dominated configurations.")
                        lines.append("")

                        for i, config in enumerate(ranked_configs, 1):
                            lines.append(f"Config {i}: {json.dumps(config.config)}")
                            # Show all metrics, not just objectives
                            for metric_name, stats in sorted(config.metrics.items()):
                                lines.append(f"  {metric_name}: {stats.mean:.2f} ± {stats.std:.2f}")
                            lines.append(f"  runs: {len(config.trials)}")
                            lines.append("")
                    else:
                        # Single objective
                        from wafer_core.tools.autotuner.scoring import rank_configs_single_objective

                        obj = objectives_data[0]
                        objective = Objective(metric=obj["metric"], direction=obj["direction"])
                        best_configs = rank_configs_single_objective(aggregated_configs, objective)

                        lines.append(f"Results (sorted by {obj['metric']}, {obj['direction']}):")
                        lines.append("")

                        # Apply limit if specified
                        configs_to_show = best_configs[:limit] if limit else best_configs

                        for i, config in enumerate(configs_to_show, 1):
                            lines.append(f"Rank {i}: {json.dumps(config.config)}")
                            for metric_name, stats in config.metrics.items():
                                lines.append(f"  {metric_name}: {stats.mean:.2f} ± {stats.std:.2f}")
                            lines.append(f"  runs: {len(config.trials)}")
                            lines.append("")

                        # Show count if limited
                        if limit and len(best_configs) > limit:
                            lines.append(f"... and {len(best_configs) - limit} more results")
                            lines.append("")
                else:
                    # Use individual trial scoring
                    if len(objectives_data) > 1:
                        # Multi-objective: compute Pareto
                        objectives = [
                            Objective(
                                metric=obj["metric"],
                                direction=obj["direction"],
                                weight=obj.get("weight", 1.0)
                            )
                            for obj in objectives_data
                        ]
                        pareto_trials = compute_pareto_frontier(completed_trials, objectives)

                        lines.append("Pareto Frontier (using config objectives):")
                        lines.append(f"Found {len(pareto_trials)} non-dominated configurations.")
                        lines.append("")

                        for i, trial in enumerate(pareto_trials, 1):
                            lines.append(f"Config {i}: {json.dumps(trial.config)}")
                            lines.append(f"  Trial: {trial.trial_number + 1}")
                            # Show all metrics, not just objectives
                            for metric_name, metric_value in sorted(trial.metrics.items()):
                                lines.append(f"  {metric_name}: {metric_value}")
                            lines.append(f"  duration: {trial.duration_ms}ms")
                            lines.append("")
                    else:
                        # Single objective
                        from wafer_core.tools.autotuner.scoring import rank_trials_single_objective

                        obj = objectives_data[0]
                        objective = Objective(metric=obj["metric"], direction=obj["direction"])
                        best_trials = rank_trials_single_objective(completed_trials, objective)

                        lines.append(f"Results (sorted by {obj['metric']}, {obj['direction']}):")

                        # Apply limit if specified
                        trials_to_show = best_trials[:limit] if limit else best_trials

                        for i, trial in enumerate(trials_to_show, 1):
                            lines.append(f"Rank {i}: {json.dumps(trial.config)}")
                            for metric_name, metric_value in trial.metrics.items():
                                lines.append(f"  {metric_name}: {metric_value}")
                            lines.append("")

                        # Show count if limited
                        if limit and len(best_trials) > limit:
                            lines.append(f"... and {len(best_trials) - limit} more results")
                            lines.append("")
            else:
                # No objectives defined - just list trials or configs
                if use_aggregation:
                    lines.append("Results (no objectives defined):")

                    # Apply limit if specified
                    configs_to_show = aggregated_configs[:limit] if limit else aggregated_configs

                    for i, config in enumerate(configs_to_show, 1):
                        lines.append(f"Config {i}: {json.dumps(config.config)}")
                        for metric_name, stats in config.metrics.items():
                            lines.append(f"  {metric_name}: {stats.mean:.2f} ± {stats.std:.2f}")
                        lines.append(f"  runs: {len(config.trials)}")
                        lines.append("")

                    # Show count if limited
                    if limit and len(aggregated_configs) > limit:
                        lines.append(f"... and {len(aggregated_configs) - limit} more results")
                        lines.append("")
                else:
                    lines.append("Results (no objectives defined):")

                    # Apply limit if specified
                    trials_to_show = completed_trials[:limit] if limit else completed_trials

                    for i, trial in enumerate(trials_to_show, 1):
                        lines.append(f"Trial {i}: {json.dumps(trial.config)}")
                        for metric_name, metric_value in trial.metrics.items():
                            lines.append(f"  {metric_name}: {metric_value}")
                        lines.append("")

                    # Show count if limited
                    if limit and len(completed_trials) > limit:
                        lines.append(f"... and {len(completed_trials) - limit} more results")
                        lines.append("")

        # If show_all is enabled, append failed and constraint-violated trials
        if show_all and (constraint_violated_trials or failed_trials):
            lines.append("")
            lines.append("=" * 60)
            lines.append("Failed and Constraint-Violated Trials")
            lines.append("=" * 60)
            lines.append("")

            if constraint_violated_trials:
                lines.append(f"Constraint Violations ({len(constraint_violated_trials)} trials):")
                lines.append("These configs failed correctness checks or other constraints")
                lines.append("")

                for i, trial in enumerate(constraint_violated_trials[:20], 1):  # Show up to 20
                    lines.append(f"Trial {trial.trial_number}: {json.dumps(trial.config)}")
                    lines.append(f"  status: {trial.status.value}")
                    if trial.metrics:
                        for metric_name, metric_value in list(trial.metrics.items())[:5]:  # First 5 metrics
                            lines.append(f"  {metric_name}: {metric_value}")
                    if trial.stderr and len(trial.stderr) < 200:
                        lines.append(f"  error: {trial.stderr.strip()}")
                    lines.append("")

                if len(constraint_violated_trials) > 20:
                    lines.append(f"... and {len(constraint_violated_trials) - 20} more constraint violations")
                    lines.append("")

            if failed_trials:
                lines.append(f"Failed Trials ({len(failed_trials)} trials):")
                lines.append("These configs crashed, timed out, or had execution errors")
                lines.append("")

                for i, trial in enumerate(failed_trials[:20], 1):  # Show up to 20
                    lines.append(f"Trial {trial.trial_number}: {json.dumps(trial.config)}")
                    lines.append(f"  status: {trial.status.value}")
                    lines.append(f"  exit_code: {trial.exit_code}")
                    if trial.stderr and len(trial.stderr) < 200:
                        lines.append(f"  error: {trial.stderr.strip()}")
                    elif trial.stderr:
                        lines.append(f"  error: {trial.stderr[:200].strip()}...")
                    lines.append("")

                if len(failed_trials) > 20:
                    lines.append(f"... and {len(failed_trials) - 20} more failed trials")
                    lines.append("")

        return "\n".join(lines)

    except Exception as e:
        raise ValueError(f"Failed to get results: {e}") from e


def best_command(
    sweep_id: str,
    metric: str,
) -> str:
    """Show the single best config from a sweep by a specific metric.

    Args:
        sweep_id: Sweep ID to retrieve
        metric: Metric to optimize (REQUIRED)

    Returns:
        Formatted string with best config
    """
    from wafer_core.tools.autotuner.aggregation import aggregate_trials_by_config
    from wafer_core.tools.autotuner.storage import get_sweep, get_trials

    try:
        # Get sweep and trials
        sweep = asyncio.run(get_sweep(sweep_id))
        trials = asyncio.run(get_trials(sweep_id))

        # Filter to completed trials only
        completed_trials = [t for t in trials if t.status.value in ("success", "completed")]

        if not completed_trials:
            return f"No completed trials found for sweep {sweep_id}"

        # Check if we should aggregate
        trials_per_config = sweep.config.get("trials_per_config", 1) if sweep.config else 1
        use_aggregation = trials_per_config > 1

        # Determine direction from config objectives if available
        from wafer_core.tools.autotuner.dtypes import Objective

        direction = "maximize"  # Default
        if sweep.config and "objectives" in sweep.config:
            for obj in sweep.config["objectives"]:
                if obj["metric"] == metric:
                    direction = obj["direction"]
                    break

        objective = Objective(metric=metric, direction=direction)

        if use_aggregation:
            # Use aggregated configs
            from wafer_core.tools.autotuner.scoring import rank_configs_single_objective

            aggregated_configs = aggregate_trials_by_config(completed_trials, trials_per_config)
            if not aggregated_configs:
                return f"No valid configurations found for sweep {sweep_id}"

            best_configs = rank_configs_single_objective(aggregated_configs, objective)
            if not best_configs:
                return f"No configs found with metric '{metric}'"

            best_config = best_configs[0]

            # Format output with aggregated stats
            lines = [
                f"=== Best Config (by {metric}, {direction}) ===",
                "",
                f"Config: {best_config.config_number + 1}",
                f"Runs: {len(best_config.trials)} (all successful)",
                f"All Passed Constraints: {best_config.all_passed_constraints}",
                "",
                "Configuration:",
                json.dumps(best_config.config, indent=2),
                "",
                "Metrics (mean ± std):",
            ]

            for metric_name, stats in best_config.metrics.items():
                lines.append(f"  {metric_name}: {stats.mean:.4f} ± {stats.std:.4f} (min: {stats.min:.4f}, max: {stats.max:.4f})")

            # Show one representative trial's stdout/stderr
            representative_trial = best_config.trials[0]
            lines.append("")
            lines.append("=" * 60)
            lines.append("STDOUT (from first run):")
            lines.append("=" * 60)
            if representative_trial.stdout.strip():
                lines.append(representative_trial.stdout)
            else:
                lines.append("(empty)")

            lines.append("")
            lines.append("=" * 60)
            lines.append("STDERR (from first run):")
            lines.append("=" * 60)
            if representative_trial.stderr.strip():
                lines.append(representative_trial.stderr)
            else:
                lines.append("(empty)")

            return "\n".join(lines)

        else:
            # Use individual trials
            from wafer_core.tools.autotuner.scoring import rank_trials_single_objective

            best_trials = rank_trials_single_objective(completed_trials, objective)
            if not best_trials:
                return f"No trials found with metric '{metric}'"
            best = best_trials[0]

            # Format output with full details (similar to trial command)
            lines = [
                f"=== Best Config (by {metric}, {direction}) ===",
                "",
                f"Trial: {best.trial_number}",
                f"Status: {best.status.value}",
                f"Duration: {best.duration_ms}ms",
                f"Exit Code: {best.exit_code}",
                f"Passed Constraints: {best.passed_constraints}",
                f"Started: {best.started_at.isoformat()}",
                f"Completed: {best.completed_at.isoformat()}",
                "",
                "Configuration:",
                json.dumps(best.config, indent=2),
                "",
                "Metrics:",
            ]

            for metric_name, metric_value in best.metrics.items():
                lines.append(f"  {metric_name}: {metric_value}")

            lines.append("")
            lines.append("=" * 60)
            lines.append("STDOUT:")
            lines.append("=" * 60)
            if best.stdout.strip():
                lines.append(best.stdout)
            else:
                lines.append("(empty)")

            lines.append("")
            lines.append("=" * 60)
            lines.append("STDERR:")
            lines.append("=" * 60)
            if best.stderr.strip():
                lines.append(best.stderr)
            else:
                lines.append("(empty)")

            return "\n".join(lines)

    except Exception as e:
        raise ValueError(f"Failed to get best config: {e}") from e


def trial_command(
    sweep_id: str,
    trial_number: int,
) -> str:
    """Show detailed information about a specific trial.

    Args:
        sweep_id: Sweep ID
        trial_number: Trial number to inspect (1-indexed, as displayed to user)

    Returns:
        Formatted string with trial details including stdout, stderr, config, and metrics
    """
    from wafer_core.tools.autotuner.storage import get_trials

    try:
        # Convert from 1-indexed (user input) to 0-indexed (internal storage)
        trial_number_internal = trial_number - 1

        # Get all trials for this sweep
        trials = asyncio.run(get_trials(sweep_id))

        # Find the specific trial
        trial = None
        for t in trials:
            if t.trial_number == trial_number_internal:
                trial = t
                break

        if not trial:
            return f"Config #{trial_number} not found in sweep {sweep_id}"

        # Format output with full details (display as 1-indexed)
        lines = [
            f"=== Config #{trial.trial_number + 1} (Sweep: {sweep_id[:8]}...) ===",
            "",
            f"Status: {trial.status.value}",
            f"Duration: {trial.duration_ms}ms",
            f"Exit Code: {trial.exit_code}",
            f"Passed Constraints: {trial.passed_constraints}",
            f"Started: {trial.started_at.isoformat()}",
            f"Completed: {trial.completed_at.isoformat()}",
            "",
            "Configuration:",
            json.dumps(trial.config, indent=2),
            "",
            "Metrics:",
        ]

        if trial.metrics:
            for metric_name, metric_value in trial.metrics.items():
                lines.append(f"  {metric_name}: {metric_value}")
        else:
            lines.append("  (none)")

        lines.append("")
        lines.append("=" * 60)
        lines.append("STDOUT:")
        lines.append("=" * 60)
        if trial.stdout.strip():
            lines.append(trial.stdout)
        else:
            lines.append("(empty)")

        lines.append("")
        lines.append("=" * 60)
        lines.append("STDERR:")
        lines.append("=" * 60)
        if trial.stderr.strip():
            lines.append(trial.stderr)
        else:
            lines.append("(empty)")

        return "\n".join(lines)

    except Exception as e:
        raise ValueError(f"Failed to get trial details: {e}") from e


def list_command(show_all: bool = False) -> str:
    """List sweeps for the current user.

    Args:
        show_all: If False (default), only show running and completed sweeps.
                  If True, show all sweeps including pending and failed.

    Returns:
        Formatted string with sweep list
    """
    from wafer_core.tools.autotuner.storage import list_sweeps

    try:
        # Get all sweeps
        all_sweeps = asyncio.run(list_sweeps())

        if not all_sweeps:
            return "No sweeps found."

        # Filter by status unless --all is specified
        if show_all:
            sweeps = all_sweeps
        else:
            sweeps = [s for s in all_sweeps if s.status in ("running", "completed")]

        if not sweeps:
            if show_all:
                return "No sweeps found."
            else:
                return "No running or completed sweeps found. Use --all to see pending/failed sweeps."

        # Sort by creation time (most recent first)
        sweeps.sort(key=lambda s: s.created_at, reverse=True)

        lines = [
            f"Found {len(sweeps)} sweep(s)" + (" (showing all)" if show_all else " (running/completed only)") + ":",
            "",
        ]

        for sweep in sweeps:
            # Format timestamps
            created = sweep.created_at.strftime("%Y-%m-%d %H:%M:%S")

            # Status emoji
            status_emoji = {
                "pending": "⏳",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌",
            }.get(sweep.status, "❓")

            lines.append(f"{status_emoji} {sweep.name}")
            lines.append(f"   ID: {sweep.id}")
            lines.append(f"   Status: {sweep.status}")
            lines.append(f"   Trials: {sweep.completed_trials}/{sweep.total_trials}")
            lines.append(f"   Created: {created}")
            if sweep.description:
                lines.append(f"   Description: {sweep.description}")
            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        raise ValueError(f"Failed to list sweeps: {e}") from e


def delete_command(sweep_id: str) -> str:
    """Delete a sweep and all its trials.

    Args:
        sweep_id: Sweep ID to delete

    Returns:
        Success message
    """
    import httpx
    from wafer_core.tools.autotuner.storage import _get_auth_headers, get_api_url

    try:
        api_url = get_api_url()
        headers = _get_auth_headers()

        async def _delete() -> str:
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                response = await client.delete(f"{api_url}/v1/autotuner/sweeps/{sweep_id}")
                response.raise_for_status()
            return f"Successfully deleted sweep {sweep_id}"

        return asyncio.run(_delete())

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise ValueError(f"Sweep {sweep_id} not found")
        raise ValueError(f"Failed to delete sweep: {e}")
    except Exception as e:
        raise ValueError(f"Failed to delete sweep: {e}") from e


def delete_all_command(status_filter: str | None = None) -> str:
    """Delete all sweeps (optionally filtered by status).

    Args:
        status_filter: Optional status to filter by (pending, running, completed, failed)

    Returns:
        Summary of deletions
    """
    import httpx
    from wafer_core.tools.autotuner.storage import _get_auth_headers, get_api_url, list_sweeps

    try:
        # Get all sweeps
        all_sweeps = asyncio.run(list_sweeps())

        if not all_sweeps:
            return "No sweeps found."

        # Filter by status if specified
        if status_filter:
            sweeps_to_delete = [s for s in all_sweeps if s.status == status_filter]
            if not sweeps_to_delete:
                return f"No sweeps found with status '{status_filter}'."
        else:
            sweeps_to_delete = all_sweeps

        # Show what will be deleted
        count = len(sweeps_to_delete)
        status_msg = f" with status '{status_filter}'" if status_filter else ""

        print(f"Found {count} sweep(s){status_msg} to delete:")
        print()
        for sweep in sweeps_to_delete:
            print(f"  - {sweep.name} ({sweep.id})")
            print(f"    Status: {sweep.status}, Trials: {sweep.completed_trials}/{sweep.total_trials}")
        print()

        # Delete all
        api_url = get_api_url()
        headers = _get_auth_headers()

        async def _delete_all() -> int:
            deleted_count = 0
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                for sweep in sweeps_to_delete:
                    try:
                        response = await client.delete(f"{api_url}/v1/autotuner/sweeps/{sweep.id}")
                        response.raise_for_status()
                        deleted_count += 1
                        print(f"✓ Deleted {sweep.id}")
                    except Exception as e:
                        print(f"✗ Failed to delete {sweep.id}: {e}")
            return deleted_count

        deleted_count = asyncio.run(_delete_all())
        return f"\nSuccessfully deleted {deleted_count}/{count} sweeps"

    except Exception as e:
        raise ValueError(f"Failed to delete sweeps: {e}") from e
