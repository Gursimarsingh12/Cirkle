import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import psutil
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import AsyncSessionLocal, check_database_health
from caching.cache_service import cache_service
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class PerformanceMetrics:
    timestamp: datetime
    active_connections: int
    idle_connections: int
    total_connections: int
    avg_query_time: float
    slow_queries: int
    cache_hit_rate: float
    cache_memory_usage: str
    cache_ops_per_sec: int
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    feed_generation_time: float
    concurrent_users: int
    error_rate: float


class PerformanceMonitor:
    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.alert_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "db_connections": 80,
            "cache_hit_rate": 70.0,
            "avg_query_time": 2.0,
            "feed_generation_time": 5.0,
            "error_rate": 5.0,
        }
        self.is_monitoring = False

    @asynccontextmanager
    async def measure_time(self, operation_name: str):
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            if duration > 1.0:
                logger.warning(f"⚠️  Slow operation {operation_name}: {duration:.2f}s")

    async def collect_database_metrics(self) -> Dict:
        try:
            db_health = await check_database_health()
            async with AsyncSessionLocal() as session:
                queries = {
                    "active_connections": """
                        SELECT COUNT(*) FROM information_schema.processlist 
                        WHERE state IS NOT NULL AND state != 'Sleep'
                    """,
                    "idle_connections": """
                        SELECT COUNT(*) FROM information_schema.processlist 
                        WHERE state = 'Sleep'
                    """,
                    "total_connections": """
                        SELECT COUNT(*) FROM information_schema.processlist
                    """,
                    "slow_queries": """
                        SELECT COUNT(*) FROM information_schema.processlist 
                        WHERE state IS NOT NULL AND state != 'Sleep'
                        AND time > 5
                    """,
                    "avg_query_time": """
                        SELECT COALESCE(AVG(time), 0) as avg_time_sec
                        FROM information_schema.processlist 
                        WHERE state IS NOT NULL AND state != 'Sleep'
                        AND time > 0
                        LIMIT 100
                    """,
                    "table_sizes": """
                        SELECT 
                            table_schema as schemaname,
                            table_name as tablename,
                            CONCAT(ROUND((data_length + index_length) / 1024 / 1024, 2), 'MB') as size
                        FROM information_schema.tables 
                        WHERE table_schema = DATABASE()
                        AND table_name IN ('tweets', 'users', 'user_profiles', 'followers', 'tweet_likes')
                        ORDER BY (data_length + index_length) DESC
                    """,
                }
                metrics = {}
                for metric_name, query in queries.items():
                    try:
                        if metric_name == "table_sizes":
                            result = await session.execute(text(query))
                            metrics[metric_name] = [
                                dict(row._mapping) for row in result.fetchall()
                            ]
                        else:
                            result = await session.execute(text(query))
                            value = result.scalar() or 0
                            metrics[metric_name] = float(value)
                    except Exception as e:
                        logger.warning(f"Failed to collect {metric_name}: {e}")
                        metrics[metric_name] = 0
                metrics.update(db_health)
                return metrics
        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
            return {
                "active_connections": 0,
                "idle_connections": 0,
                "total_connections": 0,
                "slow_queries": 0,
                "avg_query_time": 0.0,
                "table_sizes": [],
            }

    async def collect_cache_metrics(self) -> Dict:
        try:
            cache_stats = await cache_service.get_cache_stats()
            return cache_stats
        except Exception as e:
            logger.error(f"Failed to collect cache metrics: {e}")
            return {
                "hit_rate": 0.0,
                "used_memory": "0B",
                "instantaneous_ops_per_sec": 0,
            }

    def collect_system_metrics(self) -> Dict:
        try:
            return {
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
                "load_average": (
                    psutil.getloadavg()[0] if hasattr(psutil, "getloadavg") else 0
                ),
                "network_connections": len(psutil.net_connections()),
            }
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "disk_usage": 0.0,
                "load_average": 0.0,
                "network_connections": 0,
            }

    async def test_feed_performance(self) -> Dict:
        try:
            from tweets.cruds.TweetCruds import TweetCruds

            test_user_id = "AB12345"
            tweet_cruds = TweetCruds()
            start_time = time.time()
            async with AsyncSessionLocal() as session:
                feed_result = await tweet_cruds.get_merged_feed(
                    session, test_user_id, page=1, include_recommendations=True
                )
            generation_time = time.time() - start_time
            return {
                "generation_time": generation_time,
                "tweets_count": len(feed_result.tweets),
                "success": True,
                "cache_used": generation_time < 0.5,
            }
        except Exception as e:
            logger.error(f"Failed to test feed performance: {e}")
            return {
                "generation_time": 999.0,
                "tweets_count": 0,
                "success": False,
                "cache_used": False,
            }

    async def collect_all_metrics(self) -> PerformanceMetrics:
        logger.info("📊 Collecting performance metrics...")
        db_metrics_task = self.collect_database_metrics()
        cache_metrics_task = self.collect_cache_metrics()
        feed_test_task = self.test_feed_performance()
        system_metrics = self.collect_system_metrics()
        db_metrics, cache_metrics, feed_metrics = await asyncio.gather(
            db_metrics_task, cache_metrics_task, feed_test_task, return_exceptions=True
        )
        if isinstance(db_metrics, Exception):
            logger.error(f"Database metrics error: {db_metrics}")
            db_metrics = {}
        if isinstance(cache_metrics, Exception):
            logger.error(f"Cache metrics error: {cache_metrics}")
            cache_metrics = {}
        if isinstance(feed_metrics, Exception):
            logger.error(f"Feed metrics error: {feed_metrics}")
            feed_metrics = {}
        error_rate = 0.0
        if not feed_metrics.get("success", False):
            error_rate = 100.0
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            active_connections=int(db_metrics.get("active_connections", 0)),
            idle_connections=int(db_metrics.get("idle_connections", 0)),
            total_connections=int(db_metrics.get("total_connections", 0)),
            avg_query_time=float(db_metrics.get("avg_query_time", 0)),
            slow_queries=int(db_metrics.get("slow_queries", 0)),
            cache_hit_rate=float(cache_metrics.get("hit_rate", 0)),
            cache_memory_usage=str(cache_metrics.get("used_memory", "0B")),
            cache_ops_per_sec=int(cache_metrics.get("instantaneous_ops_per_sec", 0)),
            cpu_usage=float(system_metrics.get("cpu_usage", 0)),
            memory_usage=float(system_metrics.get("memory_usage", 0)),
            disk_usage=float(system_metrics.get("disk_usage", 0)),
            feed_generation_time=float(feed_metrics.get("generation_time", 0)),
            concurrent_users=int(db_metrics.get("active_connections", 0)),
            error_rate=error_rate,
        )
        return metrics

    def check_alerts(self, metrics: PerformanceMetrics) -> List[str]:
        alerts = []
        if metrics.cpu_usage > self.alert_thresholds["cpu_usage"]:
            alerts.append(f"🚨 HIGH CPU USAGE: {metrics.cpu_usage:.1f}%")
        if metrics.memory_usage > self.alert_thresholds["memory_usage"]:
            alerts.append(f"🚨 HIGH MEMORY USAGE: {metrics.memory_usage:.1f}%")
        max_connections = 150
        connection_pct = (metrics.total_connections / max_connections) * 100
        if connection_pct > self.alert_thresholds["db_connections"]:
            alerts.append(
                f"🚨 HIGH DB CONNECTIONS: {metrics.total_connections}/{max_connections} ({connection_pct:.1f}%)"
            )
        if metrics.cache_hit_rate < self.alert_thresholds["cache_hit_rate"]:
            alerts.append(f"🚨 LOW CACHE HIT RATE: {metrics.cache_hit_rate:.1f}%")
        if metrics.avg_query_time > self.alert_thresholds["avg_query_time"]:
            alerts.append(f"🚨 SLOW QUERIES: {metrics.avg_query_time:.2f}s average")
        if metrics.feed_generation_time > self.alert_thresholds["feed_generation_time"]:
            alerts.append(
                f"🚨 SLOW FEED GENERATION: {metrics.feed_generation_time:.2f}s"
            )
        if metrics.error_rate > self.alert_thresholds["error_rate"]:
            alerts.append(f"🚨 HIGH ERROR RATE: {metrics.error_rate:.1f}%")
        if metrics.slow_queries > 5:
            alerts.append(
                f"🚨 MULTIPLE SLOW QUERIES: {metrics.slow_queries} queries > 5s"
            )
        return alerts

    def log_metrics(self, metrics: PerformanceMetrics, alerts: List[str]) -> None:
        logger.info(
            f"📊 Performance: CPU: {metrics.cpu_usage:.1f}% | Memory: {metrics.memory_usage:.1f}% | DB Conn: {metrics.total_connections} | Cache Hit: {metrics.cache_hit_rate:.1f}% | Feed Time: {metrics.feed_generation_time:.2f}s"
        )
        for alert in alerts:
            logger.warning(alert)
        if settings.DEBUG:
            logger.debug(f"Detailed metrics: {asdict(metrics)}")

    async def save_metrics_to_cache(self, metrics: PerformanceMetrics) -> None:
        try:
            timestamp_key = metrics.timestamp.strftime("%Y%m%d_%H%M")
            metrics_key = f"performance_metrics:{timestamp_key}"
            metrics_dict = asdict(metrics)
            metrics_dict["timestamp"] = metrics.timestamp.isoformat()
            await cache_service.set(metrics_key, metrics_dict, ttl=86400)
            recent_metrics_key = "performance_metrics:recent"
            recent_metrics = await cache_service.get(recent_metrics_key) or []
            recent_metrics.append(metrics_dict)
            recent_metrics = recent_metrics[-100:]
            await cache_service.set(recent_metrics_key, recent_metrics, ttl=86400)
        except Exception as e:
            logger.error(f"Failed to save metrics to cache: {e}")

    async def monitor_once(self) -> PerformanceMetrics:
        try:
            metrics = await self.collect_all_metrics()
            alerts = self.check_alerts(metrics)
            self.log_metrics(metrics, alerts)
            await self.save_metrics_to_cache(metrics)
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            return metrics
        except Exception as e:
            logger.error(f"❌ Monitoring cycle failed: {e}")
            return PerformanceMetrics(
                timestamp=datetime.now(),
                active_connections=0,
                idle_connections=0,
                total_connections=0,
                avg_query_time=0,
                slow_queries=0,
                cache_hit_rate=0,
                cache_memory_usage="0B",
                cache_ops_per_sec=0,
                cpu_usage=0,
                memory_usage=0,
                disk_usage=0,
                feed_generation_time=0,
                concurrent_users=0,
                error_rate=100.0,
            )

    async def start_monitoring(self, interval: int = 60) -> None:
        logger.info(f"🔍 Starting performance monitoring (interval: {interval}s)")
        self.is_monitoring = True
        try:
            while self.is_monitoring:
                await self.monitor_once()
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("🛑 Performance monitoring stopped")
        except Exception as e:
            logger.error(f"❌ Performance monitoring error: {e}")
        finally:
            self.is_monitoring = False

    def stop_monitoring(self) -> None:
        self.is_monitoring = False

    async def get_metrics_summary(self, hours: int = 24) -> Dict:
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = [
                m for m in self.metrics_history if m.timestamp >= cutoff_time
            ]
            if not recent_metrics:
                return {"error": "No metrics available"}
            avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage for m in recent_metrics) / len(
                recent_metrics
            )
            avg_feed_time = sum(m.feed_generation_time for m in recent_metrics) / len(
                recent_metrics
            )
            avg_cache_hit = sum(m.cache_hit_rate for m in recent_metrics) / len(
                recent_metrics
            )
            max_cpu = max(m.cpu_usage for m in recent_metrics)
            max_memory = max(m.memory_usage for m in recent_metrics)
            max_feed_time = max(m.feed_generation_time for m in recent_metrics)
            max_connections = max(m.total_connections for m in recent_metrics)
            return {
                "period_hours": hours,
                "total_samples": len(recent_metrics),
                "averages": {
                    "cpu_usage": round(avg_cpu, 1),
                    "memory_usage": round(avg_memory, 1),
                    "feed_generation_time": round(avg_feed_time, 2),
                    "cache_hit_rate": round(avg_cache_hit, 1),
                },
                "peaks": {
                    "max_cpu": round(max_cpu, 1),
                    "max_memory": round(max_memory, 1),
                    "max_feed_time": round(max_feed_time, 2),
                    "max_connections": max_connections,
                },
                "last_updated": recent_metrics[-1].timestamp.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {"error": str(e)}


performance_monitor = PerformanceMonitor()


async def start_performance_monitoring(interval: int = 60):
    await performance_monitor.start_monitoring(interval)


def stop_performance_monitoring():
    performance_monitor.stop_monitoring()


async def get_current_performance() -> Dict:
    metrics = await performance_monitor.monitor_once()
    return asdict(metrics)


async def get_performance_summary(hours: int = 24) -> Dict:
    return await performance_monitor.get_metrics_summary(hours)


if __name__ == "__main__":

    async def test_monitoring():
        await cache_service.connect()
        try:
            metrics = await performance_monitor.monitor_once()
            print(
                f"Performance test completed: {metrics.feed_generation_time:.2f}s feed generation"
            )
        finally:
            await cache_service.disconnect()

    asyncio.run(test_monitoring())
