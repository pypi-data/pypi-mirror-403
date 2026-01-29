"""Performance monitoring and benchmarking for AI integration."""

import time
import asyncio
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
from pathlib import Path
import logging

from .provider import AIResponse


logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for AI operations."""
    operation: str
    provider: str
    model: str
    start_time: float
    end_time: float
    duration: float
    tokens_used: int
    cost: float
    success: bool
    error_type: Optional[str] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    cache_hit: bool = False
    request_size: Optional[int] = None
    response_size: Optional[int] = None


@dataclass
class BenchmarkResult:
    """Benchmark result summary."""
    operation: str
    provider: str
    model: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_duration: float
    min_duration: float
    max_duration: float
    p95_duration: float
    p99_duration: float
    total_tokens: int
    total_cost: float
    requests_per_second: float
    tokens_per_second: float
    cost_per_request: float
    error_rate: float
    cache_hit_rate: float


class PerformanceMonitor:
    """Real-time performance monitoring for AI operations."""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.operation_stats: Dict[str, List[PerformanceMetrics]] = defaultdict(list)
        self.active_requests: Dict[str, float] = {}
        self.monitoring_enabled = True
        self._lock = threading.Lock()
    
    def start_monitoring(self, request_id: str, operation: str, provider: str, model: str) -> str:
        """Start monitoring a request."""
        if not self.monitoring_enabled:
            return request_id
        
        start_time = time.time()
        self.active_requests[request_id] = start_time
        
        # Monitor system resources
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        logger.debug(f"Started monitoring {operation} with {provider}/{model}")
        return request_id
    
    def end_monitoring(
        self, 
        request_id: str, 
        response: Optional[AIResponse] = None, 
        error: Optional[Exception] = None
    ) -> PerformanceMetrics:
        """End monitoring and record metrics."""
        if not self.monitoring_enabled or request_id not in self.active_requests:
            return None
        
        start_time = self.active_requests.pop(request_id)
        end_time = time.time()
        duration = end_time - start_time
        
        # Get system metrics
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        # Create metrics
        metrics = PerformanceMetrics(
            operation="unknown",  # Will be set by caller
            provider="unknown",    # Will be set by caller
            model="unknown",      # Will be set by caller
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            tokens_used=response.tokens_used if response else 0,
            cost=response.cost if response else 0.0,
            success=response is not None,
            error_type=type(error).__name__ if error else None,
            memory_usage_mb=memory_mb,
            cpu_usage_percent=cpu_percent,
            cache_hit=response.cached if response else False
        )
        
        with self._lock:
            self.metrics_history.append(metrics)
            self.operation_stats[metrics.operation].append(metrics)
        
        logger.debug(f"Recorded metrics for {metrics.operation}: {duration:.3f}s")
        return metrics
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time performance statistics."""
        with self._lock:
            if not self.metrics_history:
                return {}
            
            recent_metrics = list(self.metrics_history)[-100:]  # Last 100 requests
            
            stats = {
                "active_requests": len(self.active_requests),
                "total_requests": len(self.metrics_history),
                "recent_requests": len(recent_metrics),
                "average_duration": sum(m.duration for m in recent_metrics) / len(recent_metrics),
                "requests_per_second": len(recent_metrics) / (time.time() - recent_metrics[0].start_time) if len(recent_metrics) > 1 else 0,
                "success_rate": sum(1 for m in recent_metrics if m.success) / len(recent_metrics),
                "cache_hit_rate": sum(1 for m in recent_metrics if m.cache_hit) / len(recent_metrics),
                "average_memory_mb": sum(m.memory_usage_mb or 0 for m in recent_metrics) / len(recent_metrics),
                "average_cpu_percent": sum(m.cpu_usage_percent or 0 for m in recent_metrics) / len(recent_metrics)
            }
            
            return stats
    
    def get_operation_summary(self, operation: str) -> Dict[str, Any]:
        """Get summary statistics for specific operation."""
        with self._lock:
            metrics = self.operation_stats.get(operation, [])
            if not metrics:
                return {}
            
            durations = [m.duration for m in metrics]
            tokens = [m.tokens_used for m in metrics]
            costs = [m.cost for m in metrics]
            successful = [m for m in metrics if m.success]
            
            # Calculate percentiles
            sorted_durations = sorted(durations)
            p95_index = int(len(sorted_durations) * 0.95)
            p99_index = int(len(sorted_durations) * 0.99)
            
            return {
                "operation": operation,
                "total_requests": len(metrics),
                "successful_requests": len(successful),
                "failed_requests": len(metrics) - len(successful),
                "success_rate": len(successful) / len(metrics),
                "average_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "p95_duration": sorted_durations[p95_index] if p95_index < len(sorted_durations) else max(durations),
                "p99_duration": sorted_durations[p99_index] if p99_index < len(sorted_durations) else max(durations),
                "total_tokens": sum(tokens),
                "total_cost": sum(costs),
                "average_tokens_per_request": sum(tokens) / len(metrics),
                "average_cost_per_request": sum(costs) / len(metrics),
                "tokens_per_second": sum(tokens) / sum(durations) if sum(durations) > 0 else 0,
                "requests_per_second": len(metrics) / (time.time() - metrics[0].start_time) if len(metrics) > 1 else 0
            }
    
    def export_metrics(self, file_path: Path) -> None:
        """Export metrics to file."""
        with self._lock:
            metrics_data = {
                "export_timestamp": time.time(),
                "total_metrics": len(self.metrics_history),
                "metrics": [asdict(m) for m in self.metrics_history],
                "operation_summaries": {
                    op: self.get_operation_summary(op) 
                    for op in self.operation_stats.keys()
                }
            }
            
            file_path.write_text(json.dumps(metrics_data, indent=2))
            logger.info(f"Exported {len(self.metrics_history)} metrics to {file_path}")


class AIBenchmark:
    """Comprehensive AI benchmarking suite."""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.benchmark_results: List[BenchmarkResult] = []
    
    async def benchmark_provider(
        self, 
        provider: str, 
        model: str, 
        operation: Callable,
        num_requests: int = 10,
        concurrency: int = 1
    ) -> BenchmarkResult:
        """Benchmark a specific provider and model."""
        print(f"🚀 Benchmarking {provider}/{model} with {num_requests} requests...")
        
        start_time = time.time()
        metrics = []
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrency)
        
        async def single_request(request_id: int):
            async with semaphore:
                request_start = time.time()
                try:
                    result = await operation()
                    request_end = time.time()
                    
                    metric = PerformanceMetrics(
                        operation=operation.__name__,
                        provider=provider,
                        model=model,
                        start_time=request_start,
                        end_time=request_end,
                        duration=request_end - request_start,
                        tokens_used=getattr(result, 'tokens_used', 0),
                        cost=getattr(result, 'cost', 0.0),
                        success=True,
                        cache_hit=getattr(result, 'cached', False)
                    )
                    metrics.append(metric)
                    
                except Exception as e:
                    request_end = time.time()
                    metric = PerformanceMetrics(
                        operation=operation.__name__,
                        provider=provider,
                        model=model,
                        start_time=request_start,
                        end_time=request_end,
                        duration=request_end - request_start,
                        tokens_used=0,
                        cost=0.0,
                        success=False,
                        error_type=type(e).__name__
                    )
                    metrics.append(metric)
        
        # Run requests concurrently
        tasks = [single_request(i) for i in range(num_requests)]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calculate benchmark statistics
        successful_metrics = [m for m in metrics if m.success]
        durations = [m.duration for m in successful_metrics]
        tokens = [m.tokens_used for m in successful_metrics]
        costs = [m.cost for m in successful_metrics]
        
        if durations:
            sorted_durations = sorted(durations)
            p95_index = int(len(sorted_durations) * 0.95)
            p99_index = int(len(sorted_durations) * 0.99)
        else:
            sorted_durations = []
            p95_index = p99_index = 0
        
        result = BenchmarkResult(
            operation=operation.__name__,
            provider=provider,
            model=model,
            total_requests=num_requests,
            successful_requests=len(successful_metrics),
            failed_requests=num_requests - len(successful_metrics),
            average_duration=sum(durations) / len(durations) if durations else 0,
            min_duration=min(durations) if durations else 0,
            max_duration=max(durations) if durations else 0,
            p95_duration=sorted_durations[p95_index] if p95_index < len(sorted_durations) else 0,
            p99_duration=sorted_durations[p99_index] if p99_index < len(sorted_durations) else 0,
            total_tokens=sum(tokens),
            total_cost=sum(costs),
            requests_per_second=num_requests / total_duration,
            tokens_per_second=sum(tokens) / total_duration if total_duration > 0 else 0,
            cost_per_request=sum(costs) / len(successful_metrics) if successful_metrics else 0,
            error_rate=(num_requests - len(successful_metrics)) / num_requests,
            cache_hit_rate=sum(1 for m in successful_metrics if m.cache_hit) / len(successful_metrics) if successful_metrics else 0
        )
        
        self.benchmark_results.append(result)
        self._print_benchmark_result(result)
        
        return result
    
    def _print_benchmark_result(self, result: BenchmarkResult):
        """Print benchmark result in a formatted way."""
        print(f"\n📊 Benchmark Results for {result.provider}/{result.model}")
        print("=" * 60)
        print(f"Operation: {result.operation}")
        print(f"Requests: {result.successful_requests}/{result.total_requests} successful")
        print(f"Error Rate: {result.error_rate:.2%}")
        print(f"Cache Hit Rate: {result.cache_hit_rate:.2%}")
        print(f"Requests/sec: {result.requests_per_second:.2f}")
        print(f"Tokens/sec: {result.tokens_per_second:.0f}")
        print(f"Cost/Request: ${result.cost_per_request:.6f}")
        print(f"Average Duration: {result.average_duration:.3f}s")
        print(f"P95 Duration: {result.p95_duration:.3f}s")
        print(f"P99 Duration: {result.p99_duration:.3f}s")
        print(f"Total Cost: ${result.total_cost:.6f}")
        print()
    
    async def compare_providers(
        self, 
        providers: List[str], 
        models: List[str], 
        operation: Callable
    ) -> Dict[str, BenchmarkResult]:
        """Compare multiple providers and models."""
        results = {}
        
        for provider in providers:
            for model in models:
                try:
                    result = await self.benchmark_provider(provider, model, operation)
                    results[f"{provider}/{model}"] = result
                except Exception as e:
                    print(f"❌ Failed to benchmark {provider}/{model}: {e}")
        
        self._print_comparison_table(results)
        return results
    
    def _print_comparison_table(self, results: Dict[str, BenchmarkResult]):
        """Print comparison table of all results."""
        if not results:
            return
        
        print("\n🏆 Provider Comparison")
        print("=" * 80)
        print(f"{'Provider/Model':<25} {'Avg Duration':<12} {'Requests/sec':<12} {'Cost/Request':<12} {'Success Rate':<12}")
        print("-" * 80)
        
        # Sort by average duration
        sorted_results = sorted(results.items(), key=lambda x: x[1].average_duration)
        
        for key, result in sorted_results:
            print(f"{key:<25} {result.average_duration:<12.3f} {result.requests_per_second:<12.2f} ${result.cost_per_request:<11.6f} {(1-result.error_rate):<12.2%}")
        
        print()
    
    def export_benchmark_results(self, file_path: Path) -> None:
        """Export benchmark results to file."""
        results_data = {
            "benchmark_timestamp": time.time(),
            "results": [asdict(result) for result in self.benchmark_results]
        }
        
        file_path.write_text(json.dumps(results_data, indent=2))
        logger.info(f"Exported benchmark results to {file_path}")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_ai_operation(operation: str, provider: str, model: str):
    """Decorator to monitor AI operations."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request_id = f"{operation}_{int(time.time() * 1000)}"
            performance_monitor.start_monitoring(request_id, operation, provider, model)
            
            try:
                result = await func(*args, **kwargs)
                performance_monitor.end_monitoring(request_id, result)
                return result
            except Exception as e:
                performance_monitor.end_monitoring(request_id, error=e)
                raise
        
        return wrapper
    return decorator


def get_performance_dashboard() -> Dict[str, Any]:
    """Get performance dashboard data."""
    real_time_stats = performance_monitor.get_real_time_stats()
    
    # Get operation summaries
    operation_summaries = {}
    for operation in performance_monitor.operation_stats.keys():
        operation_summaries[operation] = performance_monitor.get_operation_summary(operation)
    
    return {
        "real_time": real_time_stats,
        "operations": operation_summaries,
        "timestamp": time.time()
    }
