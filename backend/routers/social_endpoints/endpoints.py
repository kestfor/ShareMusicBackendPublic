from typing import Annotated

from fastapi import APIRouter, Depends, Response

from backend.routers.dependencies import *
from backend.routers.social_endpoints.utils import *

router = APIRouter()


@router.get("/view_relation/{ids}", tags=["user_actions"])
async def view_relation(ids: str, controller: Annotated[RelationsController, Depends(get_relations_controller)]):
    """
    ids - string with 2 user ids separated by ','
    """
    parsed_ids = ids.split(',')
    if len(parsed_ids) != 2 or parsed_ids[0] == parsed_ids[1]:
        return Response(content='invalid format', status_code=403)
    first_user, second_user = int(parsed_ids[0]), int(parsed_ids[1])
    swapped = False
    if first_user > second_user:
        first_user, second_user = second_user, first_user
        swapped = True
    relation: str = await controller.get_relation(first_user, second_user)
    if swapped:
        if relation == "first_user_follow":
            relation = "second_user_follow"
        elif relation == "second_user_follow":
            relation = "first_user_follow"
    print(relation)
    return JSONResponse(
        content={"type": relation if relation is not None else 'no_relation', "status": "success"},
        media_type="application/json;charset=utf-8")


@router.get("/users/{user_id}", tags=['user_actions'])
async def get_user_info_endpoint(user_id: str, controller: Annotated[UsersController, Depends(get_users_controller)]):
    user_info = await controller.get_user_info(int(user_id))
    return JSONResponse(
        content={"data": user_info, 'status': 'success' if user_info is not None else 'failure'},
        media_type="application/json;charset=utf-8")


@router.post("/users/follow", tags=['user_actions'])
async def follow_endpoint(info: RelationUpdateInfo,
                          controller: Annotated[RelationsController, Depends(get_relations_controller)]):
    return await handle_update_relation(info, controller)


@router.post("/users/unfollow", tags=['user_actions'])
async def unfollow_endpoint(info: RelationUpdateInfo,
                            controller: Annotated[RelationsController, Depends(get_relations_controller)]):
    return await handle_update_relation(info, controller)


@router.get("/users/search/{query}", tags=['user_actions'])
async def search_user(query: str, controller: Annotated[RelationsController, Depends(get_relations_controller)]):
    result = (await controller.search_for_username(query)).all()
    users = []
    for row in result[:20]:
        users.append(
            {"user_id": row[0], "username": row[1], "photo_url": row[2], "first_name": row[3], "last_name": row[4]})
    return JSONResponse(content={"data": users, "status": "success" if users is not [] else 'failure'},
                        media_type="application/json;charset=utf-8")
