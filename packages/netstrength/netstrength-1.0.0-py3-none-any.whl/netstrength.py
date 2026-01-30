#!/usr/bin/env python3
"""
netstrength - Beautiful network quality analyzer

A simple CLI tool to analyze your network strength with meaningful,
human-readable output and real-world usage estimates.

Usage:
    netstrength              # Run with default targets
    netstrength -t 8.8.8.8   # Test specific target
    netstrength --quick      # Quick 5-ping test
"""

import subprocess
import re
import time
import sys
import argparse
import platform
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from collections import deque


__version__ = "1.0.0"


# ══════════════════════════════════════════════════════════════════════════════
# ANSI COLORS (no dependencies needed)
# ══════════════════════════════════════════════════════════════════════════════

class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls):
        """Disable colors for non-TTY output."""
        cls.RED = cls.GREEN = cls.YELLOW = cls.CYAN = ""
        cls.MAGENTA = cls.WHITE = cls.BOLD = cls.DIM = cls.RESET = ""


# Auto-disable colors if not a terminal
if not sys.stdout.isatty():
    Colors.disable()


# ══════════════════════════════════════════════════════════════════════════════
# DEFAULT TARGETS
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_TARGETS = [
    {"host": "9.9.9.9", "name": "Quad9 DNS", "type": "international"},
    {"host": "8.8.8.8", "name": "Google DNS", "type": "international"},
    {"host": "1.1.1.1", "name": "Cloudflare", "type": "international"},
]


# ══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TargetStats:
    host: str
    name: str
    target_type: str
    rtts: deque = field(default_factory=lambda: deque(maxlen=100))
    total_sent: int = 0
    total_success: int = 0

    @property
    def loss_percent(self) -> float:
        return (self.total_sent - self.total_success) / self.total_sent * 100 if self.total_sent else 0.0

    @property
    def avg_rtt(self) -> float:
        return sum(self.rtts) / len(self.rtts) if self.rtts else 0.0

    @property
    def min_rtt(self) -> float:
        return min(self.rtts) if self.rtts else 0.0

    @property
    def max_rtt(self) -> float:
        return max(self.rtts) if self.rtts else 0.0

    @property
    def jitter(self) -> float:
        if len(self.rtts) < 2:
            return 0.0
        rtts = list(self.rtts)
        return sum(abs(rtts[i] - rtts[i-1]) for i in range(1, len(rtts))) / (len(rtts) - 1)


# ══════════════════════════════════════════════════════════════════════════════
# PING FUNCTION (cross-platform)
# ══════════════════════════════════════════════════════════════════════════════

def ping_host(host: str, timeout_sec: int = 5) -> Optional[float]:
    """
    Ping a host and return RTT in ms, or None if failed.
    Works on macOS, Linux, and Windows.
    """
    system = platform.system().lower()

    try:
        if system == "darwin":  # macOS
            # macOS: -W is in milliseconds, -t is TTL (not timeout!)
            # Use a longer subprocess timeout instead
            cmd = ["ping", "-c", "1", "-W", str(timeout_sec * 1000), host]
        elif system == "windows":
            cmd = ["ping", "-n", "1", "-w", str(timeout_sec * 1000), host]
        else:  # Linux
            cmd = ["ping", "-c", "1", "-W", str(timeout_sec), host]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec + 2
        )

        # Parse RTT from output
        output = result.stdout
        match = re.search(r'time[=<]([\d.]+)\s*ms', output)
        if match:
            return float(match.group(1))

    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass

    return None


# ══════════════════════════════════════════════════════════════════════════════
# DISPLAY HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def color_for_latency(rtt: float) -> str:
    if rtt < 50:
        return Colors.GREEN
    elif rtt < 150:
        return Colors.YELLOW
    elif rtt < 300:
        return Colors.RED
    return Colors.MAGENTA


def color_for_loss(loss: float) -> str:
    if loss < 1:
        return Colors.GREEN
    elif loss < 5:
        return Colors.YELLOW
    elif loss < 20:
        return Colors.RED
    return Colors.MAGENTA


def color_for_jitter(jitter: float) -> str:
    if jitter < 20:
        return Colors.GREEN
    elif jitter < 50:
        return Colors.YELLOW
    elif jitter < 100:
        return Colors.RED
    return Colors.MAGENTA


def get_quality_grade(avg_rtt: float, jitter: float, loss: float) -> tuple[str, str, str]:
    """Returns (grade, color, description)."""
    score = 100
    score -= min(30, avg_rtt / 10)
    score -= min(20, jitter)
    score -= loss * 5
    score = max(0, score)

    if score >= 85:
        return "A", Colors.GREEN, "Excellent"
    elif score >= 70:
        return "B", Colors.CYAN, "Good"
    elif score >= 50:
        return "C", Colors.YELLOW, "Fair"
    elif score >= 30:
        return "D", Colors.RED, "Poor"
    return "F", Colors.MAGENTA, "Critical"


def create_bar(value: float, max_val: float, width: int = 20) -> str:
    """Create a visual bar."""
    if max_val == 0:
        return "░" * width
    filled = min(int((value / max_val) * width), width)
    return "█" * filled + "░" * (width - filled)


# ══════════════════════════════════════════════════════════════════════════════
# REAL-WORLD ESTIMATES
# ══════════════════════════════════════════════════════════════════════════════

def get_usage_estimates(avg_rtt: float, jitter: float, loss: float) -> list[tuple[str, str, str, str]]:
    """Return list of (activity, status, color, note)."""
    estimates = []

    # Video Streaming
    if loss < 2 and jitter < 50:
        estimates.append(("4K Streaming", "✓", Colors.GREEN, "Smooth playback"))
    elif loss < 5:
        estimates.append(("4K Streaming", "~", Colors.YELLOW, "May buffer"))
    else:
        estimates.append(("4K Streaming", "✗", Colors.RED, "Frequent buffering"))

    # Video Calls
    if avg_rtt < 150 and jitter < 30 and loss < 2:
        estimates.append(("Video Calls", "✓", Colors.GREEN, "HD quality"))
    elif avg_rtt < 300 and loss < 5:
        estimates.append(("Video Calls", "~", Colors.YELLOW, "Some glitches"))
    else:
        estimates.append(("Video Calls", "✗", Colors.RED, "Poor quality"))

    # Competitive Gaming
    if avg_rtt < 50 and jitter < 15 and loss < 1:
        estimates.append(("Competitive Gaming", "✓", Colors.GREEN, "Pro-level"))
    elif avg_rtt < 100 and jitter < 30 and loss < 3:
        estimates.append(("Competitive Gaming", "~", Colors.YELLOW, "Playable"))
    else:
        estimates.append(("Competitive Gaming", "✗", Colors.RED, "Lag issues"))

    # 120Hz Gaming
    if avg_rtt < 30 and jitter < 10:
        estimates.append(("120Hz Gaming", "✓", Colors.GREEN, "Smooth"))
    elif avg_rtt < 80 and jitter < 25:
        estimates.append(("120Hz Gaming", "~", Colors.YELLOW, "60Hz better"))
    else:
        estimates.append(("120Hz Gaming", "✗", Colors.RED, "Not recommended"))

    # Web Browsing
    if avg_rtt < 100 and loss < 2:
        estimates.append(("Web Browsing", "✓", Colors.GREEN, "Snappy"))
    elif avg_rtt < 300:
        estimates.append(("Web Browsing", "~", Colors.YELLOW, "Noticeable delay"))
    else:
        estimates.append(("Web Browsing", "✗", Colors.RED, "Slow"))

    # Downloads
    if loss < 1:
        estimates.append(("Downloads", "✓", Colors.GREEN, "Full speed"))
    elif loss < 5:
        estimates.append(("Downloads", "~", Colors.YELLOW, "~10% slower"))
    else:
        estimates.append(("Downloads", "✗", Colors.RED, f"~{int(loss*3)}% slower"))

    return estimates


# ══════════════════════════════════════════════════════════════════════════════
# MAIN OUTPUT
# ══════════════════════════════════════════════════════════════════════════════

def print_header():
    C = Colors
    print()
    print(f"{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}║{C.WHITE}           netstrength - Network Quality Analyzer            {C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}╚══════════════════════════════════════════════════════════════╝{C.RESET}")
    print()


def print_live_ping(host: str, name: str, rtt: Optional[float], count: int):
    """Print single ping result inline."""
    C = Colors
    if rtt is not None:
        color = color_for_latency(rtt)
        print(f"\r  {C.DIM}[{count:3d}]{C.RESET} {name:20} {color}{rtt:7.1f} ms{C.RESET}   ", end="", flush=True)
    else:
        print(f"\r  {C.DIM}[{count:3d}]{C.RESET} {name:20} {C.RED}timeout{C.RESET}        ", end="", flush=True)


def print_results(all_stats: dict[str, TargetStats]):
    """Print final results."""
    C = Colors

    print(f"\n\n{C.CYAN}{C.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}")
    print(f"{C.WHITE}{C.BOLD}  RESULTS{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}\n")

    # Sort by average RTT (best first)
    sorted_stats = sorted(
        [s for s in all_stats.values() if s.total_success > 0],
        key=lambda s: s.avg_rtt
    )

    if not sorted_stats:
        print(f"  {C.RED}No successful pings. Check your network connection.{C.RESET}\n")
        return

    # Per-target results
    for i, stats in enumerate(sorted_stats, 1):
        icon = "🌍" if stats.target_type == "international" else "🏠"
        grade, grade_color, grade_desc = get_quality_grade(stats.avg_rtt, stats.jitter, stats.loss_percent)
        lat_color = color_for_latency(stats.avg_rtt)
        loss_color = color_for_loss(stats.loss_percent)
        jitter_color = color_for_jitter(stats.jitter)

        bar = create_bar(min(stats.avg_rtt, 500), 500)

        print(f"  {icon} {C.WHITE}{C.BOLD}{stats.name}{C.RESET} ({C.DIM}{stats.host}{C.RESET})")
        print(f"     {grade_color}[{grade}] {grade_desc}{C.RESET}")
        print(f"     {C.DIM}{bar}{C.RESET} {lat_color}{stats.avg_rtt:6.1f} ms{C.RESET} avg")
        print(f"     Latency: {C.GREEN}{stats.min_rtt:.0f}{C.RESET}/{lat_color}{stats.avg_rtt:.0f}{C.RESET}/{C.RED}{stats.max_rtt:.0f}{C.RESET} ms (min/avg/max)")
        print(f"     Jitter:  {jitter_color}{stats.jitter:5.1f} ms{C.RESET}   Loss: {loss_color}{stats.loss_percent:4.1f}%{C.RESET} ({stats.total_success}/{stats.total_sent})")
        print()

    # Overall averages
    overall_rtt = sum(s.avg_rtt for s in sorted_stats) / len(sorted_stats)
    overall_jitter = sum(s.jitter for s in sorted_stats) / len(sorted_stats)
    overall_loss = sum(s.loss_percent for s in sorted_stats) / len(sorted_stats)

    # Usage estimates
    print(f"{C.CYAN}{C.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}")
    print(f"{C.WHITE}{C.BOLD}  WHAT CAN YOU DO?{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}\n")

    estimates = get_usage_estimates(overall_rtt, overall_jitter, overall_loss)
    for activity, status, color, note in estimates:
        print(f"  {color}{status}{C.RESET} {activity:22} {C.DIM}{note}{C.RESET}")

    # Overall grade
    grade, grade_color, grade_desc = get_quality_grade(overall_rtt, overall_jitter, overall_loss)
    print(f"\n{C.CYAN}{C.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}")
    print(f"{C.WHITE}{C.BOLD}  OVERALL GRADE{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}\n")

    grade_stars = {"A": "★★★★★", "B": "★★★★☆", "C": "★★★☆☆", "D": "★★☆☆☆", "F": "★☆☆☆☆"}
    print(f"  {grade_color}{C.BOLD}{grade_stars[grade]}  Grade {grade} - {grade_desc}{C.RESET}")
    print(f"  {C.DIM}Avg latency: {overall_rtt:.0f}ms | Jitter: {overall_jitter:.0f}ms | Loss: {overall_loss:.1f}%{C.RESET}")

    # Recommendation
    if sorted_stats:
        best = sorted_stats[0]
        print(f"\n  {C.GREEN}► Best target: {best.name} ({best.avg_rtt:.0f}ms avg){C.RESET}")

    print()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def run_analysis(targets: list[dict], ping_count: int = 10, interval: float = 1.0, timeout: int = 5):
    """Run the network analysis."""
    C = Colors

    all_stats: dict[str, TargetStats] = {}
    for t in targets:
        all_stats[t["host"]] = TargetStats(
            host=t["host"],
            name=t["name"],
            target_type=t.get("type", "international")
        )

    print(f"  {C.DIM}Testing {len(targets)} target(s), {ping_count} pings each...{C.RESET}")
    print(f"  {C.DIM}Press Ctrl+C to stop early{C.RESET}\n")

    try:
        for cycle in range(1, ping_count + 1):
            for target in targets:
                stats = all_stats[target["host"]]
                stats.total_sent += 1

                rtt = ping_host(target["host"], timeout)
                if rtt is not None:
                    stats.total_success += 1
                    stats.rtts.append(rtt)

                print_live_ping(target["host"], target["name"], rtt, cycle)
                time.sleep(0.05)  # Brief pause between targets

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\n  {C.YELLOW}Stopped early by user{C.RESET}")

    print_results(all_stats)


def main():
    parser = argparse.ArgumentParser(
        prog="netstrength",
        description="Beautiful network quality analyzer with real-world usage estimates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  netstrength                     # Test default DNS servers
  netstrength -t google.com       # Test specific host
  netstrength -t 8.8.8.8 -n 20    # 20 pings to Google DNS
  netstrength --quick             # Quick 5-ping test
  netstrength --continuous        # Keep running (Ctrl+C to stop)
        """
    )

    parser.add_argument("-t", "--target", action="append", metavar="HOST",
                        help="Target host(s) to test (can use multiple times)")
    parser.add_argument("-n", "--count", type=int, default=10,
                        help="Number of pings per target (default: 10)")
    parser.add_argument("-i", "--interval", type=float, default=1.0,
                        help="Seconds between ping cycles (default: 1.0)")
    parser.add_argument("--timeout", type=int, default=5,
                        help="Ping timeout in seconds (default: 5)")
    parser.add_argument("--quick", action="store_true",
                        help="Quick test (5 pings, faster interval)")
    parser.add_argument("--continuous", action="store_true",
                        help="Run continuously until Ctrl+C")
    parser.add_argument("--no-color", action="store_true",
                        help="Disable colored output")
    parser.add_argument("-v", "--version", action="version",
                        version=f"netstrength {__version__}")

    args = parser.parse_args()

    if args.no_color:
        Colors.disable()

    # Build target list
    if args.target:
        targets = [{"host": h, "name": h, "type": "custom"} for h in args.target]
    else:
        targets = DEFAULT_TARGETS

    # Adjust for quick mode
    count = args.count
    interval = args.interval
    if args.quick:
        count = 5
        interval = 0.5

    if args.continuous:
        count = 999999  # Effectively infinite

    print_header()
    run_analysis(targets, count, interval, args.timeout)


if __name__ == "__main__":
    main()
