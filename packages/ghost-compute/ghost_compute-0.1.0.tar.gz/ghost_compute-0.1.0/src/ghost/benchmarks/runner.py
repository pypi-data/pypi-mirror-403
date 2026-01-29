"""
Benchmark runner for comparing optimization solutions.

Orchestrates simulations and generates comparison reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import statistics
import json

from ghost.benchmarks.competitors import (
    CompetitorModel,
    SimulationResult,
    get_all_competitors,
)
from ghost.benchmarks.simulator import (
    WorkloadSimulator,
    WorkloadProfile,
    ClusterSimulation,
    BenchmarkResult,
)


@dataclass
class ComparisonReport:
    """Complete comparison report across all solutions."""

    # Metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    simulation_months: int = 12
    num_workloads: int = 0
    total_baseline_cost: float = 0.0

    # Results by solution
    results: dict[str, BenchmarkResult] = field(default_factory=dict)

    # Rankings
    ranking_by_savings: list[str] = field(default_factory=list)
    ranking_by_net_savings: list[str] = field(default_factory=list)
    ranking_by_cold_start_prevention: list[str] = field(default_factory=list)

    # Ghost vs competitors
    ghost_vs_competitors: dict[str, dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        return {
            "metadata": {
                "generated_at": self.generated_at.isoformat(),
                "simulation_months": self.simulation_months,
                "num_workloads": self.num_workloads,
                "total_baseline_cost_usd": self.total_baseline_cost,
            },
            "results": {
                name: {
                    "avg_savings_percent": result.avg_savings_percent,
                    "avg_savings_usd": result.avg_savings_usd,
                    "avg_tool_cost": result.avg_tool_cost,
                    "avg_net_savings": result.avg_net_savings,
                    "cold_start_prevention_rate": result.cold_start_prevention_rate,
                    "idle_reduction_percent": result.idle_reduction_percent,
                    "spot_handling_rate": result.spot_handling_rate,
                }
                for name, result in self.results.items()
            },
            "rankings": {
                "by_gross_savings": self.ranking_by_savings,
                "by_net_savings": self.ranking_by_net_savings,
                "by_cold_start_prevention": self.ranking_by_cold_start_prevention,
            },
            "ghost_advantage": self.ghost_vs_competitors,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class BenchmarkRunner:
    """
    Runs benchmarks comparing optimization solutions.

    Example:
        runner = BenchmarkRunner()
        report = runner.run_full_comparison(num_months=12)
        print(report.to_json())
    """

    def __init__(
        self,
        competitors: Optional[list[CompetitorModel]] = None,
        simulator: Optional[WorkloadSimulator] = None,
        seed: Optional[int] = 42,  # Default seed for reproducibility
    ) -> None:
        """
        Initialize benchmark runner.

        Args:
            competitors: List of competitor models to compare
            simulator: Workload simulator instance
            seed: Random seed for reproducibility
        """
        self.competitors = competitors or get_all_competitors()
        self.simulator = simulator or WorkloadSimulator(seed=seed)

    def benchmark_single_workload(
        self,
        profile: WorkloadProfile,
        num_months: int = 12,
    ) -> dict[str, BenchmarkResult]:
        """
        Benchmark all solutions against a single workload profile.

        Args:
            profile: Workload profile to benchmark
            num_months: Number of months to simulate

        Returns:
            Dict mapping solution name to benchmark results
        """
        # Generate simulations
        simulations = self.simulator.simulate_workload(profile, num_months)

        results: dict[str, BenchmarkResult] = {}

        for competitor in self.competitors:
            result = BenchmarkResult(
                solution_name=competitor.name,
                num_simulations=len(simulations),
            )

            all_savings: list[float] = []
            total_baseline = 0.0
            total_optimized = 0.0
            total_tool_cost = 0.0
            total_cold_starts = 0
            total_cold_starts_prevented = 0
            total_idle = 0.0
            total_spot_interruptions = 0
            total_spot_handled = 0

            for sim in simulations:
                # Run through competitor model
                sim_result = competitor.simulate_workload(
                    baseline_cost=sim.baseline_total_cost,
                    runtime_hours=sim.actual_runtime_hours,
                    idle_hours=sim.actual_idle_hours,
                    cold_starts=sim.actual_cold_starts,
                    cold_start_time_seconds=profile.cold_start_time_seconds,
                    spot_eligible_percent=profile.spot_eligible_percent,
                    instance_hourly_cost=profile.instance_hourly_cost,
                    dbu_hourly_cost=profile.dbu_rate,
                )

                # Accumulate results
                total_baseline += sim.baseline_total_cost
                total_optimized += sim_result.total_cost_usd
                total_tool_cost += sim_result.tool_cost_usd
                total_cold_starts += sim.actual_cold_starts
                total_cold_starts_prevented += sim_result.cold_starts_prevented
                total_idle += sim_result.idle_time_hours
                total_spot_interruptions += sim_result.spot_interruptions
                total_spot_handled += sim_result.spot_interruptions_handled

                all_savings.append(sim_result.savings_vs_baseline_percent)

            # Calculate averages
            n = len(simulations)
            result.avg_baseline_cost = total_baseline / n
            result.avg_optimized_cost = total_optimized / n
            result.avg_savings_usd = (total_baseline - total_optimized) / n
            result.avg_savings_percent = statistics.mean(all_savings) if all_savings else 0
            result.avg_tool_cost = total_tool_cost / n
            result.avg_net_savings = result.avg_savings_usd - result.avg_tool_cost

            result.avg_cold_starts = total_cold_starts / n
            result.avg_cold_starts_prevented = total_cold_starts_prevented / n
            result.cold_start_prevention_rate = (
                (total_cold_starts_prevented / total_cold_starts * 100)
                if total_cold_starts > 0 else 0
            )

            result.avg_idle_hours = total_idle / n
            baseline_idle = sum(s.actual_idle_hours for s in simulations) / n
            result.idle_reduction_percent = (
                ((baseline_idle - result.avg_idle_hours) / baseline_idle * 100)
                if baseline_idle > 0 else 0
            )

            result.avg_spot_interruptions = total_spot_interruptions / n
            result.spot_handling_rate = (
                (total_spot_handled / total_spot_interruptions * 100)
                if total_spot_interruptions > 0 else 100
            )

            # Variability metrics
            result.all_savings_percents = all_savings
            if len(all_savings) > 1:
                result.savings_std_dev = statistics.stdev(all_savings)
            result.savings_min = min(all_savings) if all_savings else 0
            result.savings_max = max(all_savings) if all_savings else 0

            results[competitor.name] = result

        return results

    def run_full_comparison(
        self,
        num_months: int = 12,
        include_profiles: Optional[list[str]] = None,
        scale_factor: float = 1.0,
    ) -> ComparisonReport:
        """
        Run complete benchmark comparison across enterprise portfolio.

        Args:
            num_months: Number of months to simulate
            include_profiles: Specific profiles to include (None = all)
            scale_factor: Scale factor for enterprise portfolio

        Returns:
            Complete comparison report
        """
        report = ComparisonReport(simulation_months=num_months)

        # Get workload profiles
        if include_profiles:
            profiles = {
                name: self.simulator.get_profile(name)
                for name in include_profiles
            }
        else:
            profiles = self.simulator.STANDARD_PROFILES

        # Aggregate results across all workloads
        aggregated: dict[str, BenchmarkResult] = {
            competitor.name: BenchmarkResult(
                solution_name=competitor.name,
                num_simulations=0,
            )
            for competitor in self.competitors
        }

        total_baseline_cost = 0.0
        total_simulations = 0

        for profile_name, profile in profiles.items():
            # Run benchmark for this workload
            workload_results = self.benchmark_single_workload(profile, num_months)

            # Aggregate into totals
            for solution_name, result in workload_results.items():
                agg = aggregated[solution_name]

                # Weight by number of simulations
                weight = result.num_simulations
                total_weight = agg.num_simulations + weight

                if total_weight > 0:
                    # Weighted average update
                    agg.avg_baseline_cost = (
                        (agg.avg_baseline_cost * agg.num_simulations +
                         result.avg_baseline_cost * weight) / total_weight
                    )
                    agg.avg_optimized_cost = (
                        (agg.avg_optimized_cost * agg.num_simulations +
                         result.avg_optimized_cost * weight) / total_weight
                    )
                    agg.avg_savings_percent = (
                        (agg.avg_savings_percent * agg.num_simulations +
                         result.avg_savings_percent * weight) / total_weight
                    )
                    agg.avg_tool_cost = (
                        (agg.avg_tool_cost * agg.num_simulations +
                         result.avg_tool_cost * weight) / total_weight
                    )
                    agg.cold_start_prevention_rate = (
                        (agg.cold_start_prevention_rate * agg.num_simulations +
                         result.cold_start_prevention_rate * weight) / total_weight
                    )
                    agg.idle_reduction_percent = (
                        (agg.idle_reduction_percent * agg.num_simulations +
                         result.idle_reduction_percent * weight) / total_weight
                    )
                    agg.spot_handling_rate = (
                        (agg.spot_handling_rate * agg.num_simulations +
                         result.spot_handling_rate * weight) / total_weight
                    )

                agg.num_simulations = total_weight
                agg.all_savings_percents.extend(result.all_savings_percents)

            # Track baseline for first solution (they're all the same)
            first_result = next(iter(workload_results.values()))
            total_baseline_cost += first_result.avg_baseline_cost * num_months
            total_simulations += first_result.num_simulations

        # Finalize aggregated results
        for solution_name, agg in aggregated.items():
            agg.avg_savings_usd = agg.avg_baseline_cost - agg.avg_optimized_cost
            agg.avg_net_savings = agg.avg_savings_usd - agg.avg_tool_cost

            if agg.all_savings_percents:
                if len(agg.all_savings_percents) > 1:
                    agg.savings_std_dev = statistics.stdev(agg.all_savings_percents)
                agg.savings_min = min(agg.all_savings_percents)
                agg.savings_max = max(agg.all_savings_percents)

        report.results = aggregated
        report.num_workloads = len(profiles)
        report.total_baseline_cost = total_baseline_cost

        # Generate rankings
        report.ranking_by_savings = sorted(
            aggregated.keys(),
            key=lambda x: aggregated[x].avg_savings_percent,
            reverse=True,
        )
        report.ranking_by_net_savings = sorted(
            aggregated.keys(),
            key=lambda x: aggregated[x].avg_net_savings,
            reverse=True,
        )
        report.ranking_by_cold_start_prevention = sorted(
            aggregated.keys(),
            key=lambda x: aggregated[x].cold_start_prevention_rate,
            reverse=True,
        )

        # Calculate Ghost advantage vs each competitor
        ghost_result = aggregated.get("Ghost Compute")
        if ghost_result:
            for solution_name, result in aggregated.items():
                if solution_name != "Ghost Compute":
                    report.ghost_vs_competitors[solution_name] = {
                        "savings_advantage_percent": (
                            ghost_result.avg_savings_percent - result.avg_savings_percent
                        ),
                        "net_savings_advantage_percent": (
                            ((ghost_result.avg_net_savings - result.avg_net_savings) /
                             result.avg_baseline_cost * 100)
                            if result.avg_baseline_cost > 0 else 0
                        ),
                        "cold_start_advantage_percent": (
                            ghost_result.cold_start_prevention_rate -
                            result.cold_start_prevention_rate
                        ),
                        "idle_reduction_advantage_percent": (
                            ghost_result.idle_reduction_percent -
                            result.idle_reduction_percent
                        ),
                    }

        return report


def run_full_benchmark(
    num_months: int = 12,
    seed: int = 42,
    verbose: bool = True,
) -> ComparisonReport:
    """
    Convenience function to run a complete benchmark.

    Args:
        num_months: Number of months to simulate
        seed: Random seed for reproducibility
        verbose: Print progress

    Returns:
        Complete comparison report
    """
    if verbose:
        print("=" * 70)
        print("GHOST COMPUTE BENCHMARK - COMPETITOR COMPARISON")
        print("=" * 70)
        print(f"\nSimulating {num_months} months of enterprise workloads...")
        print("Comparing: No Optimization, Native Autoscaling, Pepperdata,")
        print("           Sync Computing, Unravel Data, Ghost Compute\n")

    runner = BenchmarkRunner(seed=seed)
    report = runner.run_full_comparison(num_months=num_months)

    if verbose:
        print_report(report)

    return report


def print_report(report: ComparisonReport) -> None:
    """Print a formatted benchmark report."""
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)

    print(f"\nTotal Baseline Monthly Cost: ${report.total_baseline_cost / report.simulation_months:,.2f}")
    print(f"Workload Profiles Tested: {report.num_workloads}")
    print(f"Simulation Period: {report.simulation_months} months")

    print("\n" + "-" * 70)
    print("SAVINGS COMPARISON (Gross Savings %)")
    print("-" * 70)
    print(f"{'Solution':<30} {'Savings %':>12} {'Net Savings %':>14} {'Tool Cost %':>12}")
    print("-" * 70)

    for solution_name in report.ranking_by_savings:
        result = report.results[solution_name]
        net_savings_pct = (
            (result.avg_net_savings / result.avg_baseline_cost * 100)
            if result.avg_baseline_cost > 0 else 0
        )
        tool_cost_pct = (
            (result.avg_tool_cost / result.avg_baseline_cost * 100)
            if result.avg_baseline_cost > 0 else 0
        )

        marker = " <-- BEST" if solution_name == report.ranking_by_savings[0] else ""
        print(f"{solution_name:<30} {result.avg_savings_percent:>11.1f}% {net_savings_pct:>13.1f}% {tool_cost_pct:>11.1f}%{marker}")

    print("\n" + "-" * 70)
    print("COLD START PREVENTION")
    print("-" * 70)
    print(f"{'Solution':<30} {'Prevention Rate':>16} {'Idle Reduction':>16}")
    print("-" * 70)

    for solution_name in report.ranking_by_cold_start_prevention:
        result = report.results[solution_name]
        print(f"{solution_name:<30} {result.cold_start_prevention_rate:>15.1f}% {result.idle_reduction_percent:>15.1f}%")

    # Ghost advantage summary
    if report.ghost_vs_competitors:
        print("\n" + "-" * 70)
        print("GHOST COMPUTE ADVANTAGE VS COMPETITORS")
        print("-" * 70)

        for competitor, advantages in report.ghost_vs_competitors.items():
            if competitor == "No Optimization (Baseline)":
                continue
            print(f"\nvs {competitor}:")
            print(f"  • {advantages['savings_advantage_percent']:+.1f}% better gross savings")
            print(f"  • {advantages['net_savings_advantage_percent']:+.1f}% better net savings")
            print(f"  • {advantages['cold_start_advantage_percent']:+.1f}% better cold start prevention")
            print(f"  • {advantages['idle_reduction_advantage_percent']:+.1f}% better idle reduction")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    ghost_result = report.results.get("Ghost Compute")
    if ghost_result:
        print(f"\nGhost Compute delivers:")
        print(f"  • {ghost_result.avg_savings_percent:.1f}% gross cost savings")
        net_pct = (ghost_result.avg_net_savings / ghost_result.avg_baseline_cost * 100) if ghost_result.avg_baseline_cost > 0 else 0
        print(f"  • {net_pct:.1f}% net cost savings (after Ghost fee)")
        print(f"  • {ghost_result.cold_start_prevention_rate:.1f}% cold starts eliminated")
        print(f"  • {ghost_result.idle_reduction_percent:.1f}% reduction in idle time")
        print(f"  • {ghost_result.spot_handling_rate:.1f}% spot interruptions handled gracefully")

    # Show ranking
    print(f"\nOverall Ranking by Net Savings:")
    for i, solution in enumerate(report.ranking_by_net_savings[:3], 1):
        result = report.results[solution]
        net_pct = (result.avg_net_savings / result.avg_baseline_cost * 100) if result.avg_baseline_cost > 0 else 0
        print(f"  {i}. {solution}: {net_pct:.1f}% net savings")
