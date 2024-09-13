from fastapi.responses import JSONResponse
from backend.routers.social_endpoints.models import RelationUpdateInfo
from backend.sql.controllers.relations_controller import RelationsController


async def handle_update_relation(info: RelationUpdateInfo, controller: RelationsController):
    try:
        result = await controller.update_relation(info.first_user_id, info.second_user_id, info.action)
        return JSONResponse(
            content={"status": "success", "result": result},
            media_type='application/json;charset=utf-8')
    except Exception as error:
        return JSONResponse(
            content={"status": "failure", "result": error},
            media_type='application/json;charset=utf-8')