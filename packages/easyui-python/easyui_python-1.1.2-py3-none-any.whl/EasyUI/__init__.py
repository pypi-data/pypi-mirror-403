# EasyUI/__init__.py

# library.py에 있는 모든 클래스와 인스턴스(create)를 패키지 루트로 끌어올립니다.
from .library import *

# 이제 사용자는 EasyUI.library.create 대신 EasyUI.create로 쓸 수 있습니다.