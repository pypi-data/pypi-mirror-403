"""greenlet/gevent 환경 지원 유틸리티"""
import sys
import threading


def get_current_frame(ctx=None):
    """현재 실행 frame 가져오기"""
    return sys._getframe()


def set_greenlet_info(ctx):
    """greenlet 환경이면 context에 greenlet 정보 저장"""
    greenlet_module = sys.modules.get('greenlet')
    if greenlet_module:
        current_greenlet = greenlet_module.getcurrent()
        if current_greenlet is not None:
            ctx.greenlet = current_greenlet
            ctx.greenlet_id = id(current_greenlet)
            return True
    return False
