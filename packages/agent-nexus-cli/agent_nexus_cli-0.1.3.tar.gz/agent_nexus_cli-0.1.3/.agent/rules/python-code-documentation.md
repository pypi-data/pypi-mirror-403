---
trigger: always_on
---

# Python Code Documentation Standards

## Class Documentation
- **Title**: Single line class name
- **Description**: Single line explaining purpose, ends with full stop
- **Gap**: One blank line between title and description
- **Inherits**: Parent classes
- **Attrs**: All attributes with types and descriptions ending with full stop
- **Methods**: All methods with full documentation

## Method/Function Documentation
- **Description**: Single line explaining what it does, ends with full stop
- **Gap**: One blank line after closing docstring quotes
- **Args**: Parameter name, type, brief explanation ending with full stop
- **Returns**: Return type and what is returned, ends with full stop
- **Raises**: Exception types, ends with full stop (use None if no exceptions)

## Type Annotations
- Use built-in types: `str`, `int`, `float`, `bool`
- Use lowercase generics: `list[str]`, `dict[str, any]`, `tuple[int, str]`
- Use pipe for unions: `str | int | None`
- Use `ClassVar` for class variables: `ClassVar[dict[str, int]]`
- Never use: `typing.Optional`, `typing.Union`, `typing.List`, `typing.Dict`

## Code Style
- Follow Ruff linting rules
- No English jargon in docstrings
- Keywords and technical terms only
- Clean, minimal documentation
- Always use `None` for Raises if no exceptions
- No comments above imports
- No comments above `__all__` exports
- All descriptions end with full stop
- One blank line after docstring before code

## Example

```python
import logging
from typing import ClassVar

from celery import Task

logger: logging.Logger = logging.getLogger(__name__)


class BaseTask(Task):
    """Base Task Class.
    
    Provides base implementation for Celery tasks.
    
    Inherits:
        celery.Task
    
    Attrs:
        autoretry_for: tuple[type[Exception], ...] - Exception types to retry on.
        retry_kwargs: ClassVar[dict[str, int]] - Retry configuration.
        retry_backoff: bool - Enable exponential backoff.
        retry_backoff_max: int - Maximum backoff time.
    
    Methods:
        on_failure(exc, task_id, args, kwargs, einfo): Handle task failure.
        on_success(retval, task_id, args, kwargs): Handle task success.
    """

    autoretry_for: tuple[type[Exception], ...] = (Exception,)
    retry_kwargs: ClassVar[dict[str, int]] = {"max_retries": 3}
    retry_backoff: bool = True
    retry_backoff_max: int = 600

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple,
        kwargs: dict,
        einfo: any,
    ) -> None:
        """Handle task failure by logging error details.
        
        Args:
            exc: Exception - Exception that caused failure.
            task_id: str - Unique task identifier.
            args: tuple - Task positional arguments.
            kwargs: dict - Task keyword arguments.
            einfo: any - Exception information.
        
        Returns:
            None
        
        Raises:
            None
        """

        msg: str = f"Task {self.name}[{task_id}] failed"
        logger.error(msg, extra={"task_id": task_id, "exception": str(exc)})
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(
        self,
        retval: any,
        task_id: str,
        args: tuple,
        kwargs: dict,
    ) -> None:
        """Handle task success by logging completion details.
        
        Args:
            retval: any - Return value of task.
            task_id: str - Unique task identifier.
            args: tuple - Task positional arguments.
            kwargs: dict - Task keyword arguments.
        
        Returns:
            None
        
        Raises:
            None
        """

        msg: str = f"Task {self.name}[{task_id}] succeeded"
        logger.info(msg, extra={"task_id": task_id})
        super().on_success(retval, task_id, args, kwargs)


class CriticalTask(BaseTask):
    """Critical Task Class.
    
    Task class for critical operations with higher retry limits.
    
    Inherits:
        BaseTask
    
    Attrs:
        retry_kwargs: ClassVar[dict[str, int]] - Retry configuration with higher max retries.
        retry_backoff_max: int - Maximum backoff time.
    """

    retry_kwargs: ClassVar[dict[str, int]] = {"max_retries": 5}
    retry_backoff_max: int = 1200


__all__: list[str] = ["BaseTask", "CriticalTask"]
```
