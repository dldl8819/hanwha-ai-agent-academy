from app.core.config import get_settings

def test_설정_불러오기():
    assert get_settings().app_mode == "mock"

'''
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