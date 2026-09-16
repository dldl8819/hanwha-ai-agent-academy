# app 패키지를 import 하는 테스트
# - 예전에는 ModuleNotFoundError 로 실패했다 (아래 로그)
# - pyproject.toml 의 pythonpath = ["backend"] 를 넣고 나서 통과한다
from app.core.config import get_settings

def test_설정_불러오기():
    assert get_settings().app_mode == "mock"

# 아래는 당시 실패 로그를 기록용으로 붙여둔 것이다.
# - r'''...''' 로 감싼 이유 : 로그 안에 C:\Users 같은 윈도우 경로가 있는데,
#   일반 문자열이면 \U 를 유니코드 이스케이프로 해석해서 SyntaxError 가 난다.
r'''
================================================================== ERRORS ===================================================================
____________________________________________ ERROR collecting sandbox/pytest/test_import_fail.py ____________________________________________
ImportError while importing test module 'C:\workspace\hanwha-agent\sandbox\pytest\test_import_fail.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Users\user\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sandbox\pytest\test_import_fail.py:1: in <module>
    from app.core.config import get_settings
E   ModuleNotFoundError: No module named 'app'
========================================================== short test summary info ==========================================================
ERROR sandbox/pytest/test_import_fail.py
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
=============================================
'''