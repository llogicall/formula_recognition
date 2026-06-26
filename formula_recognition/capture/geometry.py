from typing import Iterable, Optional, Tuple

RectTuple = Tuple[int, int, int, int]


def normalize_drag(start: Tuple[int, int], end: Tuple[int, int]) -> Optional[RectTuple]:
    x1, y1 = start
    x2, y2 = end
    left = min(x1, x2)
    top = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    if width == 0 or height == 0:
        return None
    return left, top, width, height


def union_rects(rects: Iterable[RectTuple]) -> Optional[RectTuple]:
    rects = list(rects)
    if not rects:
        return None

    left = min(rect[0] for rect in rects)
    top = min(rect[1] for rect in rects)
    right = max(rect[0] + rect[2] for rect in rects)
    bottom = max(rect[1] + rect[3] for rect in rects)
    return left, top, right - left, bottom - top


def translate_rect_to_origin(rect: RectTuple, origin_rect: RectTuple) -> RectTuple:
    return rect[0] - origin_rect[0], rect[1] - origin_rect[1], rect[2], rect[3]
