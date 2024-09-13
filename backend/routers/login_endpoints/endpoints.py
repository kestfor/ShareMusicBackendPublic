from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, Response
from backend.routers.dependencies import *
from fastapi.responses import JSONResponse
from backend.routers.login_endpoints.utils import *


router = APIRouter()


@router.get('/login/', response_class=HTMLResponse, tags=['login'])
def index(response: Response):
    print(dict(response.headers))
    return '''
    <head>
        <style>
        html, body {
            height: 100%;
        }
    
        html {
            display: table;
            margin: auto;
        }
        
        body {
            display: table-cell;
            vertical-align: middle;
        }
    
        @media screen and (min-width: 768px) {
            .neighbourhood-img img {display:none;}  
        }
    
        @media screen and (max-width: 767px) {
    
            .neighbourhood-img img {display:block;}
    
        }
        </style> 
    </head>
        <center>
        <body>''' + f'''<script async
                src="https://telegram.org/js/telegram-widget.js?22"
                data-telegram-login="{BOT_LOGIN}"
                data-size="large"
                data-auth-url="{BOT_DOMAIN}/login/result/"
                data-request-access="write">
            </script>
        </body>
        </center>
        '''


@router.get('/login/result/', tags=['login'])
async def login_telegram(controller: Annotated[UsersController, Depends(get_users_controller)], id: str = None, first_name: str = None,
                         last_name: str = None,
                         username: str = None, photo_url: str = None, auth_date: str = None, hash: str = None, ):
    data = {
        'id': id,
        'first_name': first_name,
        'last_name': last_name,
        'username': username,
        'photo_url': photo_url,
        'auth_date': auth_date,
        'hash': hash
    }
    if verify_auth_data(data):
        data_og = data.copy()
        await controller.update_user(data)
        return JSONResponse(content=data_og, media_type='application/json;charset=utf-8')
    else:
        return Response(content="Auth fail", media_type='application/json;charset=utf-8', status_code=403)
