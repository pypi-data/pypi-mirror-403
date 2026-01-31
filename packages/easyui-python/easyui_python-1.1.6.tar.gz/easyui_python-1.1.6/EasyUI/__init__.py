# EasyUI/__init__.py
from .library import Create, create as _internal_create

# 여기서 직접 정의된 것처럼 보여주면 파이참이 거부할 수 없습니다.
create: Create = _internal_create