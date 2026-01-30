from typing import List, Union

from sqlalchemy import select

from caerp.models.project.project import Project
from caerp.models.project.types import BusinessType
from caerp.models.task.task import Task
from caerp.services.project.types import base_project_type_allowed


def get_active_business_type_ids(request) -> List[BusinessType]:
    return [
        btype
        for btype in request.dbsession.execute(
            select(BusinessType).where(BusinessType.active.is_(True))
        )
        .scalars()
        .all()
        if base_project_type_allowed(request, btype)
    ]


def get_business_types_from_request(request):
    """
    Collect available business types allowed for the current user/context

    :param obj request: The current Pyramid request
    """
    context: Union[Project, Task] = request.context
    project = None

    if isinstance(context, Project):
        project = context
    elif hasattr(context, "project"):
        project = context.project

    result = []

    if project:
        if project.project_type.default_business_type:
            result.append(project.project_type.default_business_type)

        for business_type in project.get_all_business_types(request):
            if business_type != project.project_type.default_business_type:
                if base_project_type_allowed(request, business_type):
                    result.append(business_type)
    else:
        result = [
            i
            for i in BusinessType.query_for_select()
            if base_project_type_allowed(request, i)
        ]

    return result
