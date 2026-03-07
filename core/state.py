"""
KDD Pipeline State Manager with async support
"""
import asyncio
from typing import Optional, Dict, Any, List
from enum import Enum


class PipelineStatus(str, Enum):
    """Pipeline status enum"""
    pending = "pending"
    running = "running"
    completed = "completed"
    error = "error"


class KDDStateManager:
    """
    Thread-safe state manager for KDD pipeline progress tracking
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._state = {
            'project_name': None,
            'raw_data': None,
            'selected_data': None,
            'preprocessed_data': None,
            'transformed_data': None,
            'lda_results': None,
            'crawl_results': None,
            'status': {
                'crawling': PipelineStatus.pending,
                'selection': PipelineStatus.pending,
                'preprocessing': PipelineStatus.pending,
                'transforming': PipelineStatus.pending,
                'datamining': PipelineStatus.pending
            }
        }

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value from state"""
        async with self._lock:
            return self._state.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        """Set a value in state"""
        async with self._lock:
            self._state[key] = value

    async def update_status(self, stage: str, status: PipelineStatus) -> None:
        """Update the status of a pipeline stage"""
        async with self._lock:
            self._state['status'][stage] = status

    async def get_status(self, stage: Optional[str] = None) -> PipelineStatus | Dict[str, PipelineStatus]:
        """Get status of a specific stage or all stages"""
        async with self._lock:
            if stage:
                return self._state['status'].get(stage)
            return self._state['status'].copy()

    async def get_all(self) -> Dict[str, Any]:
        """Get a copy of the entire state"""
        async with self._lock:
            return self._state.copy()

    async def get_raw_data_count(self) -> int:
        """Get count of raw data items"""
        async with self._lock:
            return len(self._state['raw_data']) if self._state['raw_data'] else 0

    async def get_selected_data_count(self) -> int:
        """Get count of selected data items"""
        async with self._lock:
            return len(self._state['selected_data']) if self._state['selected_data'] else 0

    async def get_preprocessed_data_count(self) -> int:
        """Get count of preprocessed data items"""
        async with self._lock:
            return len(self._state['preprocessed_data']) if self._state['preprocessed_data'] else 0

    async def get_crawl_results(self) -> Optional[Dict[str, Any]]:
        """Get crawl results"""
        async with self._lock:
            return self._state['crawl_results']

    async def reset(self) -> None:
        """Reset the state to initial values"""
        async with self._lock:
            self._state = {
                'project_name': None,
                'raw_data': None,
                'selected_data': None,
                'preprocessed_data': None,
                'transformed_data': None,
                'lda_results': None,
                'crawl_results': None,
                'status': {
                    'crawling': PipelineStatus.pending,
                    'selection': PipelineStatus.pending,
                    'preprocessing': PipelineStatus.pending,
                    'transforming': PipelineStatus.pending,
                    'datamining': PipelineStatus.pending
                }
            }

    async def get_data_counts(self) -> Dict[str, int]:
        """Get counts for all data stages"""
        async with self._lock:
            return {
                'raw': len(self._state['raw_data']) if self._state['raw_data'] else 0,
                'selected': len(self._state['selected_data']) if self._state['selected_data'] else 0,
                'preprocessed': len(self._state['preprocessed_data']) if self._state['preprocessed_data'] else 0
            }


# Global state manager instance
kdd_state_manager = KDDStateManager()
