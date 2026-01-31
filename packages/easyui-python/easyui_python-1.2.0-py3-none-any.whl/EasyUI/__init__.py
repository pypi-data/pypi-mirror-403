# EasyUI/__init__.py
from .library import Create, create, run_designer

# 파이참에게 create의 정체를 명확히 알려줍니다.
create: Create = create

# 외부에서 보일 목록을 명시합니다.
__all__ = ['create', 'run_designer']