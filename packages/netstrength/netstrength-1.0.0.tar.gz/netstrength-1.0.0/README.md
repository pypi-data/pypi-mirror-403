# netstrength

Beautiful network quality analyzer with real-world usage estimates.

```
╔══════════════════════════════════════════════════════════════╗
║           netstrength - Network Quality Analyzer            ║
╚══════════════════════════════════════════════════════════════╝
```

## Features

- **Zero dependencies** - Pure Python, works out of the box
- **Beautiful terminal output** - Colors, progress bars, clear formatting
- **Real-world estimates** - Tells you if you can stream 4K, game competitively, etc.
- **Cross-platform** - Works on macOS, Linux, and Windows
- **Simple grades** - A through F rating system anyone can understand

## Installation

### Via pip (recommended)
```bash
pip install netstrength
```

### Via Homebrew (macOS/Linux)
```bash
brew tap chibokocl/tools
brew install netstrength
```

### From source
```bash
git clone https://github.com/chibokocl/netstrength
cd netstrength
pip install .
```

## Usage

```bash
# Quick test with defaults
netstrength

# Test specific hosts
netstrength -t google.com -t cloudflare.com

# Quick 5-ping test
netstrength --quick

# More pings for accuracy
netstrength -n 30

# Run continuously
netstrength --continuous

# High-latency network? Increase timeout
netstrength --timeout 10
```

## Sample Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  🌍 Quad9 DNS (9.9.9.9)
     [A] Excellent
     ████░░░░░░░░░░░░░░░░   45.2 ms avg
     Latency: 32/45/78 ms (min/avg/max)
     Jitter:   8.3 ms   Loss:  0.0% (10/10)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  WHAT CAN YOU DO?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✓ 4K Streaming            Smooth playback
  ✓ Video Calls             HD quality
  ✓ Competitive Gaming      Pro-level
  ✓ 120Hz Gaming            Smooth
  ✓ Web Browsing            Snappy
  ✓ Downloads               Full speed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  OVERALL GRADE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ★★★★★  Grade A - Excellent
  Avg latency: 45ms | Jitter: 8ms | Loss: 0.0%

  ► Best target: Quad9 DNS (45ms avg)
```

## Options

| Option | Description |
|--------|-------------|
| `-t, --target HOST` | Target host(s) to test |
| `-n, --count N` | Number of pings (default: 10) |
| `-i, --interval SEC` | Seconds between pings (default: 1.0) |
| `--timeout SEC` | Ping timeout (default: 5) |
| `--quick` | Quick 5-ping test |
| `--continuous` | Run until Ctrl+C |
| `--no-color` | Disable colors |
| `-v, --version` | Show version |

## License

MIT
