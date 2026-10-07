from __future__ import annotations


# ══════ 여기부터 직접 채운다 ══════
# 힌트 — 두 단계다.
#   1. ws.iter_rows(values_only=True) 로 2차원 리스트를 만든다
#   2. ws.merged_cells.ranges 를 돌면서 각 범위의 왼쪽 위 값을 범위 전체에 채운다
#
# 범위의 min_row / min_col 은 시트의 절대 좌표다.
# 리스트의 [0][0] 이 시트의 몇 행 몇 열인지 알아야 자리가 맞는다.
def _fill_merged(ws) -> list[list]:
    ...
