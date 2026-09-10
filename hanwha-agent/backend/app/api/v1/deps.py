# 의존성 정의하는 파일

from typing import Annotated
from fastapi import Depends

from app.core.config import Settings, get_settings

SettingsDep = Annotated[
    Settings,
    Depends(get_settings)
]

