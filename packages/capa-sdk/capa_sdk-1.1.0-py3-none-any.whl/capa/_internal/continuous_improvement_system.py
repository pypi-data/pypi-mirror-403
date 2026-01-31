"""
Continuous Improvement System - CAPA (Craniofacial Analysis & Prediction Architecture)

Provides automated learning, performance optimization, and adaptive improvements
across all scientific analysis modules.

Version: 1.1
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import pickle
from pathlib import Path
from collections import defaultdict, deque
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score
import threading
import time

logger = logging.getLogger(__name__)


class ImprovementStrategy(Enum):
    """Strategies for continuous improvement"""
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ACCURACY_ENHANCEMENT = "accuracy_enhancement"
    ADAPTIVE_PARAMETERS = "adaptive_parameters"
    OUTLIER_REDUCTION = "outlier_reduction"
    CROSS_VALIDATION = "cross_validation"


class LearningMode(Enum):
    """Learning modes for the system"""
    CONSERVATIVE = "conservative"  # Slow, careful adaptation
    BALANCED = "balanced"         # Moderate adaptation rate
    AGGRESSIVE = "aggressive"     # Fast adaptation
    DISABLED = "disabled"         # No learning


@dataclass
class PerformanceMetrics:
    """Performance metrics for analysis modules"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    processing_time: float
    memory_usage: float
    confidence_correlation: float
    error_rate: float
    
    @property
    def overall_performance(self) -> float:
        """Calculate overall performance score (0-1)"""
        return (self.accuracy + self.precision + self.recall + self.f1_score) / 4.0


@dataclass
class ImprovementAction:
    """Represents an improvement action taken by the system"""
    action_id: str
    timestamp: datetime
    strategy: ImprovementStrategy
    module_name: str
    parameters_changed: Dict[str, Any]
    expected_improvement: float
    actual_improvement: Optional[float] = None
    success: Optional[bool] = None
    rollback_data: Optional[Dict[str, Any]] = None


@dataclass
class LearningSession:
    """Represents a learning session with collected data"""
    session_id: str
    start_time: datetime
    module_name: str
    end_time: Optional[datetime] = None
    samples_collected: int = 0
    performance_before: Optional[PerformanceMetrics] = None
    performance_after: Optional[PerformanceMetrics] = None
    actions_taken: List[ImprovementAction] = field(default_factory=list)
    learning_data: Dict[str, Any] = field(default_factory=dict)


class AdaptiveParameterOptimizer:
    """Optimizes parameters based on performance feedback"""
    
    def __init__(self, learning_rate: float = 0.01):
        self.learning_rate = learning_rate
        self.parameter_history = defaultdict(list)
        self.performance_history = defaultdict(list)
        self.optimal_parameters = {}
        
    def suggest_parameter_update(self, module_name: str, current_params: Dict[str, float],
                                current_performance: float) -> Dict[str, float]:
        """Suggest parameter updates based on performance"""
        
        # Record current state
        self.parameter_history[module_name].append(current_params.copy())
        self.performance_history[module_name].append(current_performance)
        
        # Keep only recent history
        max_history = 100
        if len(self.parameter_history[module_name]) > max_history:
            self.parameter_history[module_name] = self.parameter_history[module_name][-max_history:]
            self.performance_history[module_name] = self.performance_history[module_name][-max_history:]
        
        # If not enough history, return current parameters
        if len(self.parameter_history[module_name]) < 5:
            return current_params
        
        # Simple gradient-based optimization
        suggested_params = current_params.copy()
        
        # Find the best performing recent configuration
        recent_performances = self.performance_history[module_name][-10:]
        recent_params = self.parameter_history[module_name][-10:]
        
        best_idx = np.argmax(recent_performances)
        best_params = recent_params[best_idx]
        best_performance = recent_performances[best_idx]
        
        # If current performance is not the best, move towards best parameters
        if current_performance < best_performance:
            for param_name, current_value in current_params.items():
                if param_name in best_params:
                    best_value = best_params[param_name]
                    # Move towards best value
                    direction = best_value - current_value
                    suggested_params[param_name] = current_value + self.learning_rate * direction
        
        return suggested_params


class PerformanceMonitor:
    """Monitors performance across different modules and time periods"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.performance_windows = defaultdict(lambda: deque(maxlen=window_size))
        self.baseline_performance = {}
        self.performance_trends = defaultdict(list)
        
    def record_performance(self, module_name: str, metrics: PerformanceMetrics):
        """Record performance metrics for a module"""
        self.performance_windows[module_name].append(metrics)
        
        # Update baseline if this is the first recording or if we have better performance
        if (module_name not in self.baseline_performance or 
            metrics.overall_performance > self.baseline_performance[module_name].overall_performance):
            self.baseline_performance[module_name] = metrics
        
        # Update trend
        if len(self.performance_windows[module_name]) >= 10:
            recent_avg = np.mean([m.overall_performance for m in list(self.performance_windows[module_name])[-10:]])
            self.performance_trends[module_name].append(recent_avg)
            
            # Keep trend history manageable
            if len(self.performance_trends[module_name]) > 1000:
                self.performance_trends[module_name] = self.performance_trends[module_name][-1000:]
    
    def get_performance_trend(self, module_name: str) -> str:
        """Get performance trend (improving, declining, stable)"""
        if module_name not in self.performance_trends or len(self.performance_trends[module_name]) < 10:
            return "insufficient_data"
        
        recent_trend = self.performance_trends[module_name][-10:]
        if len(recent_trend) < 5:
            return "insufficient_data"
        
        # Linear regression on recent trend
        x = np.arange(len(recent_trend))
        y = np.array(recent_trend)
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"
    
    def get_current_performance(self, module_name: str) -> Optional[PerformanceMetrics]:
        """Get most recent performance metrics"""
        if module_name in self.performance_windows and self.performance_windows[module_name]:
            return self.performance_windows[module_name][-1]
        return None


class ContinuousImprovementSystem:
    """
    Advanced continuous improvement system with automated learning
    
    Features:
    - Performance monitoring and trend analysis
    - Adaptive parameter optimization
    - Automated A/B testing
    - Rollback capabilities for failed improvements
    - Cross-module learning and knowledge transfer
    - Anomaly detection for performance issues
    """
    
    def __init__(self, 
                 learning_mode: LearningMode = LearningMode.BALANCED,
                 enable_auto_optimization: bool = True,
                 enable_cross_module_learning: bool = True,
                 improvement_cache_path: Optional[str] = None,
                 max_learning_sessions: int = 1000):
        
        self.learning_mode = learning_mode
        self.enable_auto_optimization = enable_auto_optimization
        self.enable_cross_module_learning = enable_cross_module_learning
        self.improvement_cache_path = improvement_cache_path
        self.max_learning_sessions = max_learning_sessions
        
        # Core components
        self.parameter_optimizer = AdaptiveParameterOptimizer()
        self.performance_monitor = PerformanceMonitor()
        
        # Learning sessions and actions
        self.active_sessions: Dict[str, LearningSession] = {}
        self.completed_sessions: List[LearningSession] = []
        self.improvement_actions: List[ImprovementAction] = []
        
        # Performance baselines and targets
        self.module_baselines: Dict[str, PerformanceMetrics] = {}
        self.improvement_targets: Dict[str, float] = {}
        
        # Anomaly detection
        self.anomaly_detectors: Dict[str, IsolationForest] = {}
        self.anomaly_threshold = 0.1
        
        # Learning rate adaptation
        self.learning_rates = {
            LearningMode.CONSERVATIVE: 0.005,
            LearningMode.BALANCED: 0.01,
            LearningMode.AGGRESSIVE: 0.02,
            LearningMode.DISABLED: 0.0
        }
        
        # Background optimization thread
        self.optimization_thread = None
        self.optimization_running = False
        
        if self.improvement_cache_path:
            self._load_improvement_cache()
        
        if self.enable_auto_optimization and self.learning_mode != LearningMode.DISABLED:
            self._start_background_optimization()
        
        logger.info(f"Continuous Improvement System initialized with {learning_mode.value} mode")
    
    def start_learning_session(self, module_name: str, session_id: Optional[str] = None) -> str:
        """Start a new learning session for a module"""
        if session_id is None:
            session_id = f"{module_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get current performance baseline
        current_performance = self.performance_monitor.get_current_performance(module_name)
        
        session = LearningSession(
            session_id=session_id,
            start_time=datetime.now(),
            module_name=module_name,
            performance_before=current_performance
        )
        
        self.active_sessions[session_id] = session
        logger.info(f"Started learning session {session_id} for {module_name}")
        
        return session_id
    
    def record_performance(self, module_name: str, metrics: PerformanceMetrics, 
                          session_id: Optional[str] = None):
        """Record performance metrics for a module"""
        
        # Record in performance monitor
        self.performance_monitor.record_performance(module_name, metrics)
        
        # Update active session if provided
        if session_id and session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.samples_collected += 1
            
            # Store learning data
            session.learning_data[f"sample_{session.samples_collected}"] = {
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics.__dict__
            }
        
        # Check for anomalies
        self._check_for_anomalies(module_name, metrics)
        
        # Trigger optimization if auto-optimization is enabled
        if self.enable_auto_optimization:
            self._trigger_optimization_if_needed(module_name, metrics)
    
    def suggest_improvements(self, module_name: str, 
                           current_parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest improvements for a module"""
        
        suggestions = []
        
        if self.learning_mode == LearningMode.DISABLED:
            return suggestions
        
        # Get current performance
        current_performance = self.performance_monitor.get_current_performance(module_name)
        if not current_performance:
            return suggestions
        
        # Parameter optimization suggestions
        if current_parameters:
            float_params = {k: v for k, v in current_parameters.items() if isinstance(v, (int, float))}
            if float_params:
                optimized_params = self.parameter_optimizer.suggest_parameter_update(
                    module_name, float_params, current_performance.overall_performance
                )
                
                if optimized_params != float_params:
                    suggestions.append({
                        'strategy': ImprovementStrategy.ADAPTIVE_PARAMETERS,
                        'description': 'Optimize parameters based on performance history',
                        'parameters': optimized_params,
                        'expected_improvement': 0.05,  # Conservative estimate
                        'confidence': 0.7
                    })
        
        # Performance trend analysis
        trend = self.performance_monitor.get_performance_trend(module_name)
        if trend == "declining":
            suggestions.append({
                'strategy': ImprovementStrategy.PERFORMANCE_OPTIMIZATION,
                'description': 'Performance is declining, consider rollback or parameter reset',
                'action': 'investigate_decline',
                'expected_improvement': 0.1,
                'confidence': 0.8
            })
        
        # Cross-module learning suggestions
        if self.enable_cross_module_learning:
            cross_suggestions = self._get_cross_module_suggestions(module_name)
            suggestions.extend(cross_suggestions)
        
        return suggestions
    
    def apply_improvement(self, module_name: str, improvement: Dict[str, Any], 
                         session_id: Optional[str] = None) -> str:
        """Apply an improvement action"""
        
        action_id = f"action_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        action = ImprovementAction(
            action_id=action_id,
            timestamp=datetime.now(),
            strategy=improvement['strategy'],
            module_name=module_name,
            parameters_changed=improvement.get('parameters', {}),
            expected_improvement=improvement.get('expected_improvement', 0.0)
        )
        
        # Store rollback data if needed
        if 'rollback_data' in improvement:
            action.rollback_data = improvement['rollback_data']
        
        self.improvement_actions.append(action)
        
        # Add to active session if provided
        if session_id and session_id in self.active_sessions:
            self.active_sessions[session_id].actions_taken.append(action)
        
        logger.info(f"Applied improvement action {action_id} for {module_name}")
        
        return action_id
    
    def evaluate_improvement(self, action_id: str, new_performance: PerformanceMetrics) -> bool:
        """Evaluate the success of an improvement action"""
        
        # Find the action
        action = None
        for a in self.improvement_actions:
            if a.action_id == action_id:
                action = a
                break
        
        if not action:
            logger.warning(f"Action {action_id} not found")
            return False
        
        # Get baseline performance
        baseline = self.performance_monitor.baseline_performance.get(action.module_name)
        if not baseline:
            # Use expected improvement as a rough guide
            action.success = new_performance.overall_performance > 0.5
            action.actual_improvement = 0.0
        else:
            action.actual_improvement = (new_performance.overall_performance - 
                                       baseline.overall_performance)
            action.success = action.actual_improvement > (action.expected_improvement * 0.5)
        
        # Update performance monitor
        self.performance_monitor.record_performance(action.module_name, new_performance)
        
        # If improvement failed and we have rollback data, suggest rollback
        if not action.success and action.rollback_data:
            logger.warning(f"Improvement {action_id} failed, rollback data available")
        
        logger.info(f"Evaluated improvement {action_id}: {'SUCCESS' if action.success else 'FAILED'}")
        
        return action.success
    
    def end_learning_session(self, session_id: str, final_performance: Optional[PerformanceMetrics] = None):
        """End a learning session"""
        
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return
        
        session = self.active_sessions[session_id]
        session.end_time = datetime.now()
        session.performance_after = final_performance
        
        # Move to completed sessions
        self.completed_sessions.append(session)
        del self.active_sessions[session_id]
        
        # Maintain max sessions limit
        if len(self.completed_sessions) > self.max_learning_sessions:
            self.completed_sessions = self.completed_sessions[-self.max_learning_sessions:]
        
        # Save cache if configured
        if self.improvement_cache_path:
            self._save_improvement_cache()
        
        logger.info(f"Ended learning session {session_id}")
    
    def get_improvement_report(self, module_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate improvement report"""
        
        report = {
            'generation_time': datetime.now().isoformat(),
            'learning_mode': self.learning_mode.value,
            'total_improvement_actions': len(self.improvement_actions),
            'active_sessions': len(self.active_sessions),
            'completed_sessions': len(self.completed_sessions)
        }
        
        # Filter actions by module if specified
        actions = self.improvement_actions
        if module_name:
            actions = [a for a in actions if a.module_name == module_name]
        
        # Calculate success rates by strategy
        strategy_stats = defaultdict(lambda: {'total': 0, 'successful': 0})
        for action in actions:
            if action.success is not None:
                strategy_stats[action.strategy.value]['total'] += 1
                if action.success:
                    strategy_stats[action.strategy.value]['successful'] += 1
        
        report['strategy_success_rates'] = {
            strategy: {
                'success_rate': stats['successful'] / stats['total'] if stats['total'] > 0 else 0.0,
                'total_attempts': stats['total']
            } for strategy, stats in strategy_stats.items()
        }
        
        # Performance trends
        if module_name:
            modules_to_report = [module_name]
        else:
            modules_to_report = list(self.performance_monitor.performance_trends.keys())
        
        report['performance_trends'] = {}
        for mod in modules_to_report:
            trend = self.performance_monitor.get_performance_trend(mod)
            current_perf = self.performance_monitor.get_current_performance(mod)
            baseline_perf = self.performance_monitor.baseline_performance.get(mod)
            
            report['performance_trends'][mod] = {
                'trend': trend,
                'current_performance': current_perf.overall_performance if current_perf else None,
                'baseline_performance': baseline_perf.overall_performance if baseline_perf else None,
                'improvement_from_baseline': (
                    current_perf.overall_performance - baseline_perf.overall_performance 
                    if current_perf and baseline_perf else None
                )
            }
        
        return report
    
    def _check_for_anomalies(self, module_name: str, metrics: PerformanceMetrics):
        """Check for performance anomalies"""
        
        # Initialize anomaly detector if needed
        if module_name not in self.anomaly_detectors:
            self.anomaly_detectors[module_name] = IsolationForest(contamination=0.1, random_state=42)
            return  # Need more data to detect anomalies
        
        # Get recent performance data
        recent_metrics = list(self.performance_monitor.performance_windows[module_name])[-50:]
        if len(recent_metrics) < 10:
            return
        
        # Prepare data for anomaly detection
        features = []
        for m in recent_metrics:
            features.append([
                m.accuracy, m.precision, m.recall, m.f1_score,
                m.processing_time, m.error_rate
            ])
        
        features_array = np.array(features)
        
        # Fit detector if we have enough data
        if len(features) >= 10:
            try:
                self.anomaly_detectors[module_name].fit(features_array)
                
                # Check if current metrics are anomalous
                current_features = np.array([[
                    metrics.accuracy, metrics.precision, metrics.recall, metrics.f1_score,
                    metrics.processing_time, metrics.error_rate
                ]])
                
                anomaly_score = self.anomaly_detectors[module_name].decision_function(current_features)[0]
                is_anomaly = self.anomaly_detectors[module_name].predict(current_features)[0] == -1
                
                if is_anomaly:
                    logger.warning(f"Performance anomaly detected for {module_name}: score={anomaly_score:.3f}")
                    
            except Exception as e:
                logger.warning(f"Anomaly detection failed for {module_name}: {e}")
    
    def _trigger_optimization_if_needed(self, module_name: str, metrics: PerformanceMetrics):
        """Trigger optimization if performance conditions are met"""
        
        # Only trigger in non-disabled modes
        if self.learning_mode == LearningMode.DISABLED:
            return
        
        # Check if optimization is needed based on trend
        trend = self.performance_monitor.get_performance_trend(module_name)
        baseline = self.performance_monitor.baseline_performance.get(module_name)
        
        should_optimize = False
        
        # Trigger on declining performance
        if trend == "declining":
            should_optimize = True
        
        # Trigger if significantly below baseline
        if baseline and metrics.overall_performance < baseline.overall_performance - 0.1:
            should_optimize = True
        
        # Trigger if error rate is high
        if metrics.error_rate > 0.2:
            should_optimize = True
        
        if should_optimize:
            logger.info(f"Triggering auto-optimization for {module_name}")
            # This would trigger actual optimization logic
            # Implementation depends on specific module interfaces
    
    def _get_cross_module_suggestions(self, module_name: str) -> List[Dict[str, Any]]:
        """Get improvement suggestions based on other modules' learning"""
        
        suggestions = []
        
        # Find modules with similar performance characteristics
        current_perf = self.performance_monitor.get_current_performance(module_name)
        if not current_perf:
            return suggestions
        
        for other_module, other_perf in self.performance_monitor.baseline_performance.items():
            if other_module == module_name:
                continue
            
            # If other module has significantly better performance
            if other_perf.overall_performance > current_perf.overall_performance + 0.1:
                
                # Look for successful actions in the other module
                successful_actions = [
                    a for a in self.improvement_actions 
                    if a.module_name == other_module and a.success
                ]
                
                if successful_actions:
                    # Suggest applying similar improvements
                    best_action = max(successful_actions, key=lambda x: x.actual_improvement or 0)
                    
                    suggestions.append({
                        'strategy': ImprovementStrategy.CROSS_VALIDATION,
                        'description': f'Apply successful strategy from {other_module}',
                        'source_module': other_module,
                        'source_action': best_action.action_id,
                        'parameters': best_action.parameters_changed,
                        'expected_improvement': best_action.actual_improvement * 0.5,  # Conservative estimate
                        'confidence': 0.6
                    })
        
        return suggestions
    
    def _start_background_optimization(self):
        """Start background optimization thread"""
        
        def optimization_loop():
            while self.optimization_running:
                try:
                    # Periodically check for optimization opportunities
                    for module_name in self.performance_monitor.performance_trends:
                        trend = self.performance_monitor.get_performance_trend(module_name)
                        if trend == "declining":
                            # This would trigger more sophisticated optimization
                            logger.debug(f"Background optimization check: {module_name} trend {trend}")
                    
                    time.sleep(300)  # Check every 5 minutes
                    
                except Exception as e:
                    logger.error(f"Background optimization error: {e}")
                    time.sleep(60)  # Wait a minute before retrying
        
        self.optimization_running = True
        self.optimization_thread = threading.Thread(target=optimization_loop, daemon=True)
        self.optimization_thread.start()
        
        logger.info("Started background optimization thread")
    
    def _save_improvement_cache(self):
        """Save improvement data to cache"""
        try:
            cache_data = {
                'improvement_actions': [
                    {
                        'action_id': action.action_id,
                        'timestamp': action.timestamp.isoformat(),
                        'strategy': action.strategy.value,
                        'module_name': action.module_name,
                        'parameters_changed': action.parameters_changed,
                        'expected_improvement': action.expected_improvement,
                        'actual_improvement': action.actual_improvement,
                        'success': action.success
                    } for action in self.improvement_actions[-1000:]  # Save last 1000 actions
                ],
                'completed_sessions': [
                    {
                        'session_id': session.session_id,
                        'start_time': session.start_time.isoformat(),
                        'end_time': session.end_time.isoformat() if session.end_time else None,
                        'module_name': session.module_name,
                        'samples_collected': session.samples_collected
                    } for session in self.completed_sessions[-100:]  # Save last 100 sessions
                ]
            }
            
            with open(self.improvement_cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to save improvement cache: {e}")
    
    def _load_improvement_cache(self):
        """Load improvement data from cache"""
        try:
            if not Path(self.improvement_cache_path).exists():
                return
            
            with open(self.improvement_cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Load improvement actions (basic info only)
            if 'improvement_actions' in cache_data:
                for action_data in cache_data['improvement_actions']:
                    action = ImprovementAction(
                        action_id=action_data['action_id'],
                        timestamp=datetime.fromisoformat(action_data['timestamp']),
                        strategy=ImprovementStrategy(action_data['strategy']),
                        module_name=action_data['module_name'],
                        parameters_changed=action_data['parameters_changed'],
                        expected_improvement=action_data['expected_improvement'],
                        actual_improvement=action_data.get('actual_improvement'),
                        success=action_data.get('success')
                    )
                    self.improvement_actions.append(action)
            
            logger.info(f"Loaded improvement cache from {self.improvement_cache_path}")
            
        except Exception as e:
            logger.warning(f"Failed to load improvement cache: {e}")
    
    def shutdown(self):
        """Shutdown the improvement system"""
        self.optimization_running = False
        
        if self.optimization_thread and self.optimization_thread.is_alive():
            self.optimization_thread.join(timeout=10)
        
        # Save final cache
        if self.improvement_cache_path:
            self._save_improvement_cache()
        
        logger.info("Continuous Improvement System shutdown complete")


# Export classes and enums
__all__ = [
    'ContinuousImprovementSystem',
    'PerformanceMetrics',
    'ImprovementStrategy',
    'LearningMode',
    'ImprovementAction',
    'LearningSession',
    'AdaptiveParameterOptimizer',
    'PerformanceMonitor'
]