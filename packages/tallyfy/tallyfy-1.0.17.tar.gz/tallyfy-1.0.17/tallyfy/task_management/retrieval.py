"""
Task and process retrieval operations
"""

from typing import List, Optional
from .base import TaskManagerBase
from ..models import Task, Run, TasksList, RunsList, TallyfyError


class TaskRetrieval(TaskManagerBase):
    """Handles task and process retrieval operations"""

    def get_my_tasks(self, org_id: str, page: int = 1, per_page: int = 100) -> TasksList:
        """
        Get all tasks assigned to the current user in the organization.

        Args:
            org_id: Organization ID
            page: Page number (default: 1)
            per_page: Number of results per page (default: 100)

        Returns:
            TasksList object containing tasks and pagination metadata (total count, etc.)

        Raises:
            TallyfyError: If the request fails
        """
        self._validate_org_id(org_id)

        try:
            endpoint = f"organizations/{org_id}/me/tasks"
            params = self._build_query_params(page=page, per_page=per_page)
            response_data = self.sdk._make_request('GET', endpoint, params=params)

            # Return the structured response with pagination
            return TasksList.from_dict(response_data)

        except TallyfyError:
            raise
        except Exception as e:
            self._handle_api_error(e, "get my tasks", org_id=org_id)

    def get_user_tasks(self, org_id: str, user_id: int, page: int = 1, per_page: int = 100,
                        sort_by: str = 'newest', status: str = 'all') -> TasksList:
        """
        Get all tasks assigned to the given user in the organization.

        Args:
            org_id: Organization ID
            user_id: User ID
            page: Page number (default: 1)
            per_page: Number of results per page (default: 100)
            sort_by: Sort order (default: 'newest')
            status: Task status filter (default: 'all')

        Returns:
            TasksList object containing tasks and pagination metadata (total count, etc.)

        Raises:
            TallyfyError: If the request fails
        """
        self._validate_org_id(org_id)
        self._validate_user_id(user_id)

        try:
            endpoint = f"organizations/{org_id}/users/{user_id}/tasks"
            params = {
                'page': str(page),
                'per_page': str(per_page),
                'sort_by': sort_by,
                'status': status,
                'with': 'run,threads_count,step,tags,folders,member_watchers.watcher'
            }

            response_data = self.sdk._make_request('GET', endpoint, params=params)

            # Return the structured response with pagination
            return TasksList.from_dict(response_data)

        except TallyfyError:
            raise
        except Exception as e:
            self._handle_api_error(e, "get user tasks", org_id=org_id, user_id=user_id)

    def get_tasks_for_process(self, org_id: str, process_id: Optional[str] = None, process_name: Optional[str] = None,
                           status: Optional[str] = None, sort: Optional[str] = None, with_: Optional[str] = None,
                           owners: Optional[str] = None, groups: Optional[str] = None, guests: Optional[str] = None,
                           page: int = 1, per_page: int = 100, current_task: Optional[str] = None,
                           replace_page: Optional[int] = None, without_pagination: str = "false",
                           deadline_start_range: Optional[str] = None, deadline_end_range: Optional[str] = None,
                           unassigned: Optional[bool] = None) -> TasksList:
        """
        Get all tasks for a given process (run).

        Args:
            org_id: Organization ID
            process_id: Process (run) ID to get tasks for
            process_name: Process (run) name to get tasks for (alternative to process_id)
            status: Filter by task status (complete, hasproblem, overdue, due_soon, active, active_visible, incomplete, inprogress, not-started)
            sort: Sort by position or deadline (position, deadline, -position, -deadline)
            with_: Additional data to retrieve (activities, run, run.checklist, step, form_fields, threads, comments, assets, summary)
            owners: Search tasks assigned to specific members (comma-separated member IDs)
            groups: Filter by Group ID
            guests: Search tasks assigned to specific group (comma-separated group IDs)
            page: Results page to retrieve (default: 1)
            per_page: Tasks per page (default: 100)
            current_task: Task ID
            replace_page: Replace page
            without_pagination: Results without pagination (true/false, default: false)
            deadline_start_range: Deadline range starting date
            deadline_end_range: Deadline range ending date
            unassigned: Filter tasks with nobody assigned

        Returns:
            TasksList object containing tasks and pagination metadata (total count, etc.)

        Raises:
            TallyfyError: If the request fails
            ValueError: If neither process_id nor process_name is provided
        """
        self._validate_org_id(org_id)

        if not process_id and not process_name:
            raise ValueError("Either process_id or process_name must be provided")

        try:
            # If process_name is provided but not process_id, search for the process first
            if process_name and not process_id:
                # We need to import TaskSearch here to avoid circular imports
                from .search import TaskSearch
                search = TaskSearch(self.sdk)
                process_id = search.search_processes_by_name(org_id, process_name)

            self._validate_process_id(process_id)

            endpoint = f"organizations/{org_id}/runs/{process_id}/tasks"

            # Build parameters using base class helper
            params = self._build_query_params(
                status=status,
                sort=sort,
                owners=owners,
                groups=groups,
                guests=guests,
                page=page,
                per_page=per_page,
                currentTask=current_task,
                replace_page=replace_page,
                without_pagination=without_pagination,
                deadline_start_range=deadline_start_range,
                deadline_end_range=deadline_end_range,
                unassigned=unassigned
            )

            # Handle the 'with' parameter specially due to Python keyword conflict
            if with_:
                params['with'] = with_

            response_data = self.sdk._make_request('GET', endpoint, params=params)

            # Return the structured response with pagination
            return TasksList.from_dict(response_data)

        except TallyfyError:
            raise
        except Exception as e:
            self._handle_api_error(e, "get tasks for process", org_id=org_id, process_id=process_id, process_name=process_name)

    def get_organization_runs(self, org_id: str, per_page: int = 100, page: int = 1, with_data: Optional[str] = None,
                            form_fields_values: Optional[bool] = None,
                            owners: Optional[str] = None, task_status: Optional[str] = None,
                            groups: Optional[str] = None, status: Optional[str] = None,
                            folder: Optional[str] = None, checklist_id: Optional[str] = None,
                            starred: Optional[bool] = None, run_type: Optional[str] = None,
                            tag: Optional[str] = None, sort: Optional[str] = None) -> RunsList:
        """
        Get all processes (runs) in the organization.

        Args:
            org_id: Organization ID
            per_page: Results per page (default: 100)
            page: Results page to retrieve (default: 1)
            with_data: Comma-separated data to include (e.g., 'checklist,tasks,assets,tags')
            form_fields_values: Include form field values
            owners: Filter by specific member IDs
            task_status: Filter by task status ('all', 'in-progress', 'completed')
            groups: Filter by group IDs
            status: Filter by process status ('active', 'problem', 'delayed', 'complete', 'archived')
            folder: Filter by folder ID
            checklist_id: Filter by template ID
            starred: Filter by starred status
            run_type: Filter by type ('procedure', 'form', 'document')
            tag: Filter by tag ID
            sort: Sort by creation date ('created_at', '-created_at')

        Returns:
            RunsList object containing runs and pagination metadata (total count, etc.)

        Raises:
            TallyfyError: If the request fails
        """
        self._validate_org_id(org_id)

        try:
            endpoint = f"organizations/{org_id}/runs"

            # Build parameters using base class helper
            params = self._build_query_params(
                with_=with_data,  # Use with_ to avoid Python keyword conflict
                form_fields_values=form_fields_values,
                owners=owners,
                task_status=task_status,
                groups=groups,
                status=status,
                folder=folder,
                checklist_id=checklist_id,
                starred=starred,
                type=run_type,  # API expects 'type' parameter
                tag=tag,
                sort=sort,
                per_page=per_page,
                page=page
            )

            # Handle the 'with' parameter specially due to Python keyword conflict
            if with_data:
                params['with'] = with_data
                if 'with_' in params:
                    del params['with_']

            response_data = self.sdk._make_request('GET', endpoint, params=params)

            # Return the structured response with pagination
            return RunsList.from_dict(response_data)

        except TallyfyError:
            raise
        except Exception as e:
            self._handle_api_error(e, "get organization runs", org_id=org_id)

    def get_organization_processes(self, org_id: str, **kwargs) -> RunsList:
        """
        Alias for get_organization_runs for better naming consistency.

        Args:
            org_id: Organization ID
            **kwargs: Same parameters as get_organization_runs

        Returns:
            RunsList object containing runs and pagination metadata (total count, etc.)
        """
        return self.get_organization_runs(org_id, **kwargs)