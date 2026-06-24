"""CLI entry point -- simulation runner with warm-comfort TUI."""

from __future__ import annotations

import argparse
import os
import sys
import time

from rich.live import Live

from . import config
from .engine import SimulationEngine
from .exporter import export_all
from .visualizer import TerminalVisualizer, console


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
        description="Self-growing civilization simulation - Phase 0"
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
    parser.add_argument(
        "--export", type=str, default=None,
        help="결과 내보내기 경로 (지정 시 CSV/JSON 파일 생성)"
    )
    parser.add_argument(
        "--export-format", type=str, default="csv", choices=["csv", "json"],
        help="내보내기 포맷 (csv/json, 기본: csv)"
    )
    parser.add_argument(
        "--experiment", type=str, default=None,
        help="실험 설정 JSON 파일 경로 (지정 시 다중 실행 비교)"
    )

    args = parser.parse_args()
    headless = args.no_visual

    if args.experiment:
        from .experiment import run_experiment_file
        report = run_experiment_file(args.experiment)
        print(report)
        return

    console.print()
    console.rule("[cp.magenta]\u26a1 자가발전 문명 [cp.cyan]Phase 0[/][/]")
    console.print()
    console.print(f"  [cp.dim]월드:[/]  {config.WORLD_WIDTH}\u00d7{config.WORLD_HEIGHT}")
    console.print(f"  [cp.dim]개체:[/] {config.INITIAL_ENTITY_COUNT}")
    console.print(f"  [cp.dim]최대 틱:[/] {args.ticks}")
    console.print(f"  [cp.dim]시드:[/]     {args.seed or config.SEED}")
    console.print()

    _start = time.time()
    engine = SimulationEngine(seed=args.seed)

    if headless:
        print("헤드리스 모드로 실행 중...")
        run_headless(engine, args.ticks)
        visualizer = TerminalVisualizer(engine)
        visualizer.render_final_summary(engine.metrics)
    else:
        visualizer = TerminalVisualizer(engine)
        engine.running = True
        extinction = False

        try:
            with Live(console=console, refresh_per_second=8, screen=True) as live:
                for tick in range(1, args.ticks + 1):
                    if not engine.running:
                        break

                    engine._step()

                    if tick % args.interval == 0 or tick == 1:
                        live.update(visualizer.render())

                    # 속도 제어
                    if args.speed > 0:
                        delay = config.TICK_INTERVAL_MS / 1000.0 / args.speed
                        time.sleep(delay)

                    alive = [e for e in engine.world.entities.values() if e.alive]
                    if not alive:
                        extinction = True
                        live.update(visualizer.render())
                        time.sleep(1.5)
                        break

        except KeyboardInterrupt:
            pass
        finally:
            engine.running = False

        if extinction:
            console.print("\n[cp.red]\u2620 모든 개체가 멸종했습니다.[/]\n")
        visualizer.render_final_summary(engine.metrics)

    _duration = time.time() - _start
    if args.export:
        export_all(engine, args.export, fmt=args.export_format)
        print(f"\n결과 내보내기 완료: {os.path.abspath(args.export)}/")


if __name__ == "__main__":
    main()
