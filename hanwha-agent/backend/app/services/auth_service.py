from __future__ import annotations

from app.core.exceptions import AuthFailed
from app.core.security import verify_password
from app.db.session import session_scope
from app.models.org import User
from app.repositories import user_repo

# 변환 함수
# - User 정보를 UserOut이 받을 수 있는 정보로 돌려주는 함수
# schemas\auth.py의 UserOut 에게 전달
def _to_out(user: User) -> dict:
    return {
        "id": user.id,
        "emp_no": user.emp_no,
        "name": user.name,
        "dept": user.dept.name,
        "role": user.role,
        "clearance": user.clearance,
    }

# 인증 처리 로직
# - 사번과 비밀번호를 확인해서 사용자 정보 리턴
def authenticate(emp_no: str, password: str) -> dict:
    with session_scope() as s:
        # DB에서 emp_no로 사원 정보 조회
        user = user_repo.get_by_emp_no(s, emp_no)
        # 사번이 없거나 비밀번호가 일치하지 않으면
        if user is None or not verify_password(password, user.password_hash): # 입력 비밀번호와 DB에 암호화된 비밀번호 비교 
            raise AuthFailed() # 사용자 정의 인증 예외 발생
        return _to_out(user) # UserOut 형태로 데이터 변형해서 리턴

# 사번으로 로그인한 사용자 정보를 돌려주는 함수
# - 비밀번호를 확인하지 않는다
# - 임시 검증 로직
#   - 추후 JWT 토큰으로 변경 예정 
def get_me(emp_no: str) -> dict:
    with session_scope() as s:
        # DB에서 emp_no로 사번 조회
        user = user_repo.get_by_emp_no(s, emp_no)
        # 사용자 정보가 없으면 예외 발생
        if user is None:
            raise AuthFailed()
        return _to_out(user)
