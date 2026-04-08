"""
Pipeline Repository

Handles data access for pipeline runs.
Replaces the in-memory kdd_state with persistent database storage.
"""
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.db_models import PipelineRun, Project, User
from schemas.pipeline import PipelineStatus, StageStatus


class PipelineRepository:
    """
    Repository for PipelineRun model.

    Provides CRUD operations and query methods for pipeline runs.
    """

    @staticmethod
    async def create(
        session: AsyncSession,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        num_topics: int = 5,
        total_urls: int = 0
    ) -> PipelineRun:
        """
        Create a new pipeline run.

        Args:
            session: Database session
            project_id: Associated project ID
            user_id: User who initiated the pipeline
            num_topics: Number of topics for LDA
            total_urls: Total URLs to process

        Returns:
            Created PipelineRun instance
        """
        pipeline_run = PipelineRun(
            project_id=project_id,
            user_id=user_id,
            status=PipelineStatus.pending,
            crawling_status=StageStatus.pending,
            preprocessing_status=StageStatus.pending,
            transforming_status=StageStatus.pending,
            datamining_status=StageStatus.pending,
            num_topics=num_topics,
            total_urls=total_urls
        )

        session.add(pipeline_run)
        await session.flush()
        await session.refresh(pipeline_run)

        return pipeline_run

    @staticmethod
    async def get_by_id(session: AsyncSession, run_id: int) -> Optional[PipelineRun]:
        """Get a pipeline run by ID."""
        result = await session.execute(
            select(PipelineRun).where(PipelineRun.id == run_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_run(
        session: AsyncSession,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Optional[PipelineRun]:
        """
        Get the currently active (running or pending) pipeline run.

        Args:
            session: Database session
            project_id: Filter by project
            user_id: Filter by user

        Returns:
            Active PipelineRun or None
        """
        query = select(PipelineRun).where(
            or_(
                PipelineRun.status == PipelineStatus.pending,
                PipelineRun.status == PipelineStatus.running
            )
        )

        if project_id:
            query = query.where(PipelineRun.project_id == project_id)
        if user_id:
            query = query.where(PipelineRun.user_id == user_id)

        query = query.order_by(PipelineRun.started_at.desc())

        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_runs(
        session: AsyncSession,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: Optional[PipelineStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[PipelineRun]:
        """
        List pipeline runs with optional filters.

        Args:
            session: Database session
            project_id: Filter by project
            user_id: Filter by user
            status: Filter by status
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of PipelineRun instances
        """
        query = select(PipelineRun)

        if project_id:
            query = query.where(PipelineRun.project_id == project_id)
        if user_id:
            query = query.where(PipelineRun.user_id == user_id)
        if status:
            query = query.where(PipelineRun.status == status)

        query = query.order_by(PipelineRun.started_at.desc())
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_status(
        session: AsyncSession,
        run_id: int,
        status: PipelineStatus
    ) -> Optional[PipelineRun]:
        """Update the overall status of a pipeline run."""
        pipeline_run = await PipelineRepository.get_by_id(session, run_id)
        if pipeline_run:
            pipeline_run.status = status

            if status == PipelineStatus.completed:
                pipeline_run.completed_at = datetime.utcnow()

            # Update all stage statuses if error
            if status == PipelineStatus.error:
                pipeline_run.crawling_status = StageStatus.error
                pipeline_run.preprocessing_status = StageStatus.error
                pipeline_run.transforming_status = StageStatus.error
                pipeline_run.datamining_status = StageStatus.error

            await session.flush()
            await session.refresh(pipeline_run)

        return pipeline_run

    @staticmethod
    async def update_stage_status(
        session: AsyncSession,
        run_id: int,
        stage: str,
        status: StageStatus
    ) -> Optional[PipelineRun]:
        """
        Update the status of a specific pipeline stage.

        Args:
            session: Database session
            run_id: Pipeline run ID
            stage: Stage name (crawling, preprocessing, transforming, datamining)
            status: New stage status

        Returns:
            Updated PipelineRun or None
        """
        pipeline_run = await PipelineRepository.get_by_id(session, run_id)
        if pipeline_run:
            stage_field = f"{stage}_status"
            if hasattr(pipeline_run, stage_field):
                setattr(pipeline_run, stage_field, status)

                # Update overall status if starting a stage
                if status == StageStatus.running and pipeline_run.status == PipelineStatus.pending:
                    pipeline_run.status = PipelineStatus.running

                # Check if all stages are complete
                await PipelineRepository._check_completion(pipeline_run)

                await session.flush()
                await session.refresh(pipeline_run)

        return pipeline_run

    @staticmethod
    async def _check_completion(pipeline_run: PipelineRun):
        """Check if all pipeline stages are completed and update overall status."""
        stages = [
            pipeline_run.crawling_status,
            pipeline_run.preprocessing_status,
            pipeline_run.transforming_status,
            pipeline_run.datamining_status
        ]

        if all(s == StageStatus.completed for s in stages):
            pipeline_run.status = PipelineStatus.completed
            pipeline_run.completed_at = datetime.utcnow()
        elif any(s == StageStatus.error for s in stages):
            pipeline_run.status = PipelineStatus.error
            pipeline_run.completed_at = datetime.utcnow()

    @staticmethod
    async def set_error(
        session: AsyncSession,
        run_id: int,
        stage: str,
        error_message: str
    ) -> Optional[PipelineRun]:
        """
        Mark a pipeline run as failed with error details.

        Args:
            session: Database session
            run_id: Pipeline run ID
            stage: Stage where error occurred
            error_message: Error message

        Returns:
            Updated PipelineRun or None
        """
        pipeline_run = await PipelineRepository.get_by_id(session, run_id)
        if pipeline_run:
            pipeline_run.status = PipelineStatus.error
            pipeline_run.error_stage = stage
            pipeline_run.error_message = error_message
            pipeline_run.completed_at = datetime.utcnow()

            # Set the specific stage to error
            stage_field = f"{stage}_status"
            if hasattr(pipeline_run, stage_field):
                setattr(pipeline_run, stage_field, StageStatus.error)

            await session.flush()
            await session.refresh(pipeline_run)

        return pipeline_run

    @staticmethod
    async def update_crawl_results(
        session: AsyncSession,
        run_id: int,
        total_urls: int,
        success_count: int,
        failed_count: int
    ) -> Optional[PipelineRun]:
        """Update crawling results for a pipeline run."""
        pipeline_run = await PipelineRepository.get_by_id(session, run_id)
        if pipeline_run:
            pipeline_run.total_urls = total_urls
            pipeline_run.success_count = success_count
            pipeline_run.failed_count = failed_count

            await session.flush()
            await session.refresh(pipeline_run)

        return pipeline_run

    @staticmethod
    async def get_latest_completed(
        session: AsyncSession,
        project_id: Optional[int] = None
    ) -> Optional[PipelineRun]:
        """Get the most recent completed pipeline run."""
        query = select(PipelineRun).where(
            PipelineRun.status == PipelineStatus.completed
        )

        if project_id:
            query = query.where(PipelineRun.project_id == project_id)

        query = query.order_by(PipelineRun.completed_at.desc())

        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_old_runs(
        session: AsyncSession,
        days_old: int = 30,
        keep_completed: int = 10
    ) -> int:
        """
        Delete old pipeline runs.

        Args:
            session: Database session
            days_old: Delete runs older than this many days
            keep_completed: Keep this many recent completed runs

        Returns:
            Number of deleted runs
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        # Get IDs of completed runs to keep
        keep_result = await session.execute(
            select(PipelineRun.id)
            .where(PipelineRun.status == PipelineStatus.completed)
            .order_by(PipelineRun.completed_at.desc())
            .limit(keep_completed)
        )
        keep_ids = [row[0] for row in keep_result.all()]

        # Delete old runs
        delete_query = delete(PipelineRun).where(
            and_(
                PipelineRun.started_at < cutoff_date,
                PipelineRun.id.not_in(keep_ids) if keep_ids else True
            )
        )

        result = await session.execute(delete_query)
        return result.rowcount

    @staticmethod
    async def count_by_status(
        session: AsyncSession,
        project_id: Optional[int] = None
    ) -> dict:
        """Count pipeline runs by status."""
        query = select(PipelineRun.status, func.count(PipelineRun.id))

        if project_id:
            query = query.where(PipelineRun.project_id == project_id)

        query = query.group_by(PipelineRun.status)

        result = await session.execute(query)
        return {status.value: count for status, count in result.all()}
