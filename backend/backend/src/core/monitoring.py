"""
Cache performance monitoring and analytics module
"""

import time
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque


logger = logging.getLogger(__name__)


@dataclass
class CacheOperation:
    """Represents a single cache operation"""
    operation_type: str  # get, set, delete, etc.
    key_pattern: str    # pattern of the cache key
    success: bool
    duration_ms: float
    data_size: int
    timestamp: datetime
    hit: bool = False   # for get operations


class CacheAnalytics:
    """Advanced cache analytics and monitoring"""
    
    def __init__(self, max_operations: int = 10000):
        self.operations = deque(maxlen=max_operations)
        self.pattern_stats = defaultdict(lambda: {
            'hits': 0, 'misses': 0, 'sets': 0, 'deletes': 0,
            'total_size': 0, 'avg_duration': 0.0
        })
        self.hourly_stats = defaultdict(lambda: {
            'operations': 0, 'hits': 0, 'misses': 0, 'errors': 0
        })
        
    def record_operation(self, operation: CacheOperation):
        """Record a cache operation for analysis"""
        self.operations.append(operation)
        self._update_pattern_stats(operation)
        self._update_hourly_stats(operation)
        
    def _update_pattern_stats(self, op: CacheOperation):
        """Update pattern-based statistics"""
        pattern = self._extract_pattern(op.key_pattern)
        stats = self.pattern_stats[pattern]
        
        if op.operation_type == 'get':
            if op.hit:
                stats['hits'] += 1
            else:
                stats['misses'] += 1
        elif op.operation_type == 'set':
            stats['sets'] += 1
            stats['total_size'] += op.data_size
        elif op.operation_type == 'delete':
            stats['deletes'] += 1
            
        # Update average duration
        if stats['avg_duration'] == 0:
            stats['avg_duration'] = op.duration_ms
        else:
            # Simple moving average
            stats['avg_duration'] = (stats['avg_duration'] + op.duration_ms) / 2
            
    def _update_hourly_stats(self, op: CacheOperation):
        """Update hourly statistics"""
        hour = op.timestamp.replace(minute=0, second=0, microsecond=0)
        stats = self.hourly_stats[hour]
        
        stats['operations'] += 1
        if op.operation_type == 'get':
            if op.hit:
                stats['hits'] += 1
            else:
                stats['misses'] += 1
        if not op.success:
            stats['errors'] += 1
            
    def _extract_pattern(self, key: str) -> str:
        """Extract pattern from cache key"""
        # Remove user-specific IDs and dynamic parts
        patterns = [
            (r':\w{2}\d{5}:', ':USER_ID:'),  # User IDs
            (r':\d+:', ':ID:'),              # Generic IDs
            (r':p\d+:', ':PAGE:'),           # Page numbers
            (r':h\d+:', ':HOUR:'),           # Hour timestamps
            (r':[a-f0-9]{12}:', ':HASH:'),   # Hash values
        ]
        
        pattern = key
        for regex, replacement in patterns:
            import re
            pattern = re.sub(regex, replacement, pattern)
            
        return pattern
        
    def get_performance_insights(self) -> Dict:
        """Generate performance insights and recommendations"""
        if not self.operations:
            return {"status": "no_data", "insights": []}
            
        insights = []
        
        # Calculate overall hit ratio
        total_gets = sum(1 for op in self.operations if op.operation_type == 'get')
        total_hits = sum(1 for op in self.operations if op.operation_type == 'get' and op.hit)
        hit_ratio = (total_hits / total_gets) if total_gets > 0 else 0
        
        if hit_ratio < 0.7:
            insights.append({
                "type": "low_hit_ratio",
                "severity": "high",
                "message": f"Cache hit ratio is low ({hit_ratio:.2%}). Consider increasing TTL or optimizing cache keys.",
                "metric": hit_ratio
            })
            
        # Identify slow operations
        slow_ops = [op for op in self.operations if op.duration_ms > 100]
        if len(slow_ops) > total_gets * 0.1:  # More than 10% slow operations
            insights.append({
                "type": "slow_operations",
                "severity": "medium", 
                "message": f"{len(slow_ops)} operations took >100ms. Check Redis performance.",
                "metric": len(slow_ops)
            })
            
        # Check for cache stampede patterns
        recent_ops = [op for op in self.operations if 
                     op.timestamp > datetime.now() - timedelta(minutes=5)]
        
        key_frequency = defaultdict(int)
        for op in recent_ops:
            if op.operation_type == 'get':
                key_frequency[op.key_pattern] += 1
                
        high_frequency_keys = [k for k, v in key_frequency.items() if v > 50]
        if high_frequency_keys:
            insights.append({
                "type": "potential_stampede",
                "severity": "high",
                "message": f"High frequency access detected for {len(high_frequency_keys)} key patterns",
                "metric": len(high_frequency_keys),
                "keys": high_frequency_keys[:5]  # Show top 5
            })
            
        # Memory usage insights
        large_objects = [op for op in self.operations if 
                        op.operation_type == 'set' and op.data_size > 50000]  # >50KB
        if large_objects:
            insights.append({
                "type": "large_objects",
                "severity": "medium",
                "message": f"{len(large_objects)} large objects cached. Consider compression.",
                "metric": len(large_objects)
            })
            
        return {
            "status": "analyzed",
            "insights": insights,
            "summary": {
                "total_operations": len(self.operations),
                "hit_ratio": hit_ratio,
                "avg_duration_ms": sum(op.duration_ms for op in self.operations) / len(self.operations),
                "patterns_tracked": len(self.pattern_stats)
            }
        }
        
    def get_pattern_analysis(self) -> Dict:
        """Get detailed analysis by cache key patterns"""
        analysis = {}
        
        for pattern, stats in self.pattern_stats.items():
            total_requests = stats['hits'] + stats['misses']
            hit_ratio = (stats['hits'] / total_requests) if total_requests > 0 else 0
            
            analysis[pattern] = {
                "hit_ratio": hit_ratio,
                "total_requests": total_requests,
                "cache_efficiency": "good" if hit_ratio > 0.8 else "poor" if hit_ratio < 0.5 else "medium",
                "avg_duration_ms": stats['avg_duration'],
                "total_data_size": stats['total_size'],
                "recommendations": self._get_pattern_recommendations(pattern, stats, hit_ratio)
            }
            
        return analysis
        
    def _get_pattern_recommendations(self, pattern: str, stats: Dict, hit_ratio: float) -> List[str]:
        """Generate recommendations for a specific pattern"""
        recommendations = []
        
        if hit_ratio < 0.5:
            recommendations.append("Consider increasing TTL or reviewing cache strategy")
            
        if stats['avg_duration'] > 50:
            recommendations.append("Optimize cache key structure or Redis configuration")
            
        if "feed" in pattern.lower() and hit_ratio < 0.7:
            recommendations.append("Consider implementing cache warming for feeds")
            
        if stats['total_size'] > 1000000:  # >1MB total
            recommendations.append("Consider implementing compression for this pattern")
            
        return recommendations
        
    def export_metrics(self) -> str:
        """Export metrics in JSON format"""
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "performance_insights": self.get_performance_insights(),
            "pattern_analysis": self.get_pattern_analysis(),
            "hourly_stats": {
                str(hour): stats for hour, stats in self.hourly_stats.items()
            }
        }
        
        return json.dumps(export_data, indent=2)


# Global analytics instance
cache_analytics = CacheAnalytics()


def record_cache_operation(operation_type: str, key: str, success: bool, 
                          duration_ms: float, data_size: int = 0, hit: bool = False):
    """Record a cache operation for monitoring"""
    operation = CacheOperation(
        operation_type=operation_type,
        key_pattern=key,
        success=success,
        duration_ms=duration_ms,
        data_size=data_size,
        timestamp=datetime.now(),
        hit=hit
    )
    
    cache_analytics.record_operation(operation)


def get_cache_insights() -> Dict:
    """Get current cache performance insights"""
    return cache_analytics.get_performance_insights()


def get_cache_analytics() -> Dict:
    """Get detailed cache analytics"""
    return {
        "insights": cache_analytics.get_performance_insights(),
        "patterns": cache_analytics.get_pattern_analysis()
    } 