"""
Worker pool for distributed processing.

Uses Ray for parallel task execution.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


@dataclass
class TaskResult:
    """Result of a worker task."""

    task_id: str
    success: bool
    result: Any | None = None
    error: str | None = None
    duration: float = 0.0


class WorkerPool:
    """
    Worker pool for parallel task execution.
    
    Uses Ray for distributed processing when available,
    falls back to asyncio for local execution.
    """

    def __init__(
        self,
        num_workers: int = 4,
        use_ray: bool = True,
        ray_address: str | None = None,
    ) -> None:
        """
        Initialize worker pool.

        Args:
            num_workers: Number of worker processes
            use_ray: Whether to use Ray
            ray_address: Ray cluster address
        """
        self.num_workers = num_workers
        self.use_ray = use_ray
        self.ray_address = ray_address

        self._ray_initialized = False
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the worker pool."""
        if self._initialized:
            return

        if self.use_ray:
            await self._init_ray()
        
        self._initialized = True
        logger.info(
            "Worker pool initialized",
            workers=self.num_workers,
            ray=self._ray_initialized,
        )

    async def _init_ray(self) -> None:
        """Initialize Ray runtime."""
        try:
            import ray

            if not ray.is_initialized():
                init_kwargs: dict[str, Any] = {
                    "num_cpus": self.num_workers,
                    "ignore_reinit_error": True,
                }
                
                if self.ray_address:
                    init_kwargs["address"] = self.ray_address

                ray.init(**init_kwargs)
                self._ray_initialized = True
                logger.info("Ray initialized", address=self.ray_address)

        except ImportError:
            logger.warning("Ray not available, using asyncio fallback")
            self.use_ray = False
        except Exception as e:
            logger.warning("Ray initialization failed, using asyncio", error=str(e))
            self.use_ray = False

    async def map(
        self,
        func: Callable[[T], Any],
        items: list[T],
        task_name: str = "task",
    ) -> list[TaskResult]:
        """
        Map function over items in parallel.

        Args:
            func: Function to apply
            items: Items to process
            task_name: Name for logging

        Returns:
            List of task results
        """
        if not self._initialized:
            await self.initialize()

        if self._ray_initialized:
            return await self._map_ray(func, items, task_name)
        else:
            return await self._map_asyncio(func, items, task_name)

    async def _map_ray(
        self,
        func: Callable[[T], Any],
        items: list[T],
        task_name: str,
    ) -> list[TaskResult]:
        """Map using Ray."""
        import ray
        import time

        @ray.remote
        def ray_task(item: T, task_id: str) -> TaskResult:
            start = time.time()
            try:
                result = func(item)
                return TaskResult(
                    task_id=task_id,
                    success=True,
                    result=result,
                    duration=time.time() - start,
                )
            except Exception as e:
                return TaskResult(
                    task_id=task_id,
                    success=False,
                    error=str(e),
                    duration=time.time() - start,
                )

        # Submit tasks
        futures = [
            ray_task.remote(item, f"{task_name}_{i}")
            for i, item in enumerate(items)
        ]

        # Gather results
        results = await asyncio.to_thread(ray.get, futures)
        return results

    async def _map_asyncio(
        self,
        func: Callable[[T], Any],
        items: list[T],
        task_name: str,
    ) -> list[TaskResult]:
        """Map using asyncio."""
        import time

        semaphore = asyncio.Semaphore(self.num_workers)

        async def run_task(item: T, task_id: str) -> TaskResult:
            async with semaphore:
                start = time.time()
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(item)
                    else:
                        result = await asyncio.to_thread(func, item)
                    
                    return TaskResult(
                        task_id=task_id,
                        success=True,
                        result=result,
                        duration=time.time() - start,
                    )
                except Exception as e:
                    return TaskResult(
                        task_id=task_id,
                        success=False,
                        error=str(e),
                        duration=time.time() - start,
                    )

        tasks = [
            run_task(item, f"{task_name}_{i}")
            for i, item in enumerate(items)
        ]

        return await asyncio.gather(*tasks)

    async def submit(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> TaskResult:
        """
        Submit single task.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Task result
        """
        if not self._initialized:
            await self.initialize()

        import time
        start = time.time()
        task_id = f"task_{id(func)}"

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = await asyncio.to_thread(func, *args, **kwargs)

            return TaskResult(
                task_id=task_id,
                success=True,
                result=result,
                duration=time.time() - start,
            )
        except Exception as e:
            return TaskResult(
                task_id=task_id,
                success=False,
                error=str(e),
                duration=time.time() - start,
            )

    async def batch_process(
        self,
        items: list[T],
        process_func: Callable[[T], Any],
        batch_size: int = 10,
        task_name: str = "batch",
    ) -> list[TaskResult]:
        """
        Process items in batches.

        Args:
            items: Items to process
            process_func: Processing function
            batch_size: Batch size
            task_name: Name for logging

        Returns:
            All results
        """
        all_results: list[TaskResult] = []

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            batch_results = await self.map(
                process_func,
                batch,
                f"{task_name}_batch_{i // batch_size}",
            )
            all_results.extend(batch_results)

            logger.debug(
                "Batch processed",
                batch=i // batch_size,
                total=len(items) // batch_size + 1,
            )

        return all_results

    def get_status(self) -> dict[str, Any]:
        """Get pool status."""
        status = {
            "initialized": self._initialized,
            "num_workers": self.num_workers,
            "use_ray": self.use_ray,
            "ray_initialized": self._ray_initialized,
        }

        if self._ray_initialized:
            import ray
            try:
                status["ray_nodes"] = len(ray.nodes())
                status["ray_resources"] = ray.available_resources()
            except Exception:
                pass

        return status

    async def shutdown(self) -> None:
        """Shutdown the worker pool."""
        if self._ray_initialized:
            import ray
            try:
                ray.shutdown()
            except Exception as e:
                logger.warning("Ray shutdown error", error=str(e))
        
        self._initialized = False
        self._ray_initialized = False
        logger.info("Worker pool shutdown")


class PageProcessor:
    """
    Specialized worker for page processing.
    """

    def __init__(
        self,
        worker_pool: WorkerPool,
    ) -> None:
        """
        Initialize page processor.

        Args:
            worker_pool: Worker pool to use
        """
        self.worker_pool = worker_pool

    async def process_pages(
        self,
        pages: list[Any],
        process_func: Callable[[Any], Any],
        batch_size: int = 10,
    ) -> list[Any]:
        """
        Process pages in parallel.

        Args:
            pages: Pages to process
            process_func: Processing function
            batch_size: Batch size

        Returns:
            Processed results
        """
        results = await self.worker_pool.batch_process(
            pages,
            process_func,
            batch_size=batch_size,
            task_name="page_process",
        )

        # Extract successful results in order
        processed = []
        for result in results:
            if result.success:
                processed.append(result.result)
            else:
                logger.warning("Page processing failed", error=result.error)
                processed.append(None)

        return processed


class ChapterProcessor:
    """
    Specialized worker for chapter generation.
    """

    def __init__(
        self,
        worker_pool: WorkerPool,
    ) -> None:
        """
        Initialize chapter processor.

        Args:
            worker_pool: Worker pool to use
        """
        self.worker_pool = worker_pool

    async def generate_chapters(
        self,
        chapters: list[Any],
        generate_func: Callable[[Any], Any],
    ) -> list[Any]:
        """
        Generate chapters in parallel.

        Args:
            chapters: Chapters to generate
            generate_func: Generation function

        Returns:
            Generated chapters
        """
        # Process chapters sequentially for now to maintain context
        # Can be parallelized if chapters are independent
        results: list[Any] = []
        
        for chapter in chapters:
            result = await self.worker_pool.submit(generate_func, chapter)
            if result.success:
                results.append(result.result)
            else:
                logger.error("Chapter generation failed", error=result.error)
                results.append(None)

        return results
