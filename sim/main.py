"""CLI 엔트리 포인트 — 시뮬레이션 실행 및 시각화."""

from __future__ import annotations

import argparse
import sys
import time

from . import config
from .engine import SimulationEngine
from .visualizer import TerminalVisualizer


def run_headless(engine: SimulationEngine, max_ticks: int,
                 summary_interval: int = 100) -> None:
    """헤드리스 모드: 주기적으로 요약만 출력."""
    engine.running = True

    for tick in range(1, max_ticks + 1):
        if not engine.running:
            break
        engine._step()

        if tick % summary_interval == 0:
            snap = engine.metrics.latest()
            if snap:
                print(engine.metrics.summary_text(snap))
                print()

        alive = [e for e in engine.world.entities.values() if e.alive]
        if not alive:
            print("[멸종] 모든 개체가 죽었습니다.")
            break

    engine.running = False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="자가발전 문명 시뮬레이션 — Phase 0"
    )
    parser.add_argument(
        "--ticks", type=int, default=500,
        help=f"실행할 최대 틱 수 (기본: 500)"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="난수 시드 (재현성)"
    )
    parser.add_argument(
        "--visual", action="store_true", default=True,
        help="실시간 터미널 시각화 (기본: 켜짐)"
    )
    parser.add_argument(
        "--no-visual", action="store_true",
        help="시각화 없이 실행 (헤드리스)"
    )
    parser.add_argument(
        "--speed", type=float, default=1.0,
        help="시각화 속도 (1.0=기본, 0.5=절반속도, 0=최대속도)"
    )
    parser.add_argument(
        "--interval", type=int, default=config.VISUALIZER_REFRESH_TICKS,
        help="화면 갱신 간격 (틱, 기본: 5)"
    )

    args = parser.parse_args()
    headless = args.no_visual

    print("\033[1;36m")
    print("  +----------------------------------------+")
    print("  |     문명 시뮬레이션 -- Phase 0         |")
    print("  |     자가발전하는 생태계                |")
    print("  +----------------------------------------+")
    print("\033[0m")
    print(f"  월드: {config.WORLD_WIDTH}×{config.WORLD_HEIGHT}")
    print(f"  초기 개체: {config.INITIAL_ENTITY_COUNT}")
    print(f"  최대 틱: {args.ticks}")
    print(f"  시드: {args.seed or config.SEED}")
    print()

    engine = SimulationEngine(seed=args.seed)

    if headless:
        print("헤드리스 모드로 실행 중...")
        run_headless(engine, args.ticks)
        visualizer = TerminalVisualizer(engine)
        visualizer.render_final_summary(engine.metrics)
    else:
        visualizer = TerminalVisualizer(engine)
        engine.running = True

        try:
            for tick in range(1, args.ticks + 1):
                if not engine.running:
                    break

                engine._step()

                # 주기적으로 화면 갱신
                if tick % args.interval == 0 or tick == 1:
                    visualizer.render()

                # 속도 제어
                if args.speed > 0:
                    delay = config.TICK_INTERVAL_MS / 1000.0 / args.speed
                    time.sleep(delay)

                # 멸종 검사
                alive = [e for e in engine.world.entities.values() if e.alive]
                if not alive:
                    print("\n\033[1;31m☠ 모든 개체가 멸종했습니다.\033[0m")
                    break

        except KeyboardInterrupt:
            print("\n\n사용자 중단.")
        finally:
            engine.running = False

        # 최종 통계
        visualizer.render_final_summary(engine.metrics)


if __name__ == "__main__":
    main()
