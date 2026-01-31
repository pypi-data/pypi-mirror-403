# EasyUI/__init__.py
from .library import _Create, create, run_designer

# 파이참에게 create가 'Create' 클래스의 인스턴스임을 확실히 알려줍니다.
create: _Create = create

# 외부에서 접근 가능한 목록을 정의하면 자동완성이 더 정확해집니다.
__all__ = ['create', 'run_designer', '_Create']