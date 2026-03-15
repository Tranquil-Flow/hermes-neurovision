#!/bin/bash
# Hermes Neurovision — Soundtrack Generator
# Generates 3 candidate tracks for the demo video (~79 seconds).
#
# Arc: calm early builds → tension boot sequence → BOOM v0.2.0 drop
#      → rapid fire flash → floating halvorsen outro
#
# Run from macOS (NOT Docker):
#   cd /path/to/hermes-neurovision/soundtrack
#   bash generate_soundtrack.sh
#
# Requires: heartlib (~/heartlib) with HeartMuLa 3B + HeartCodec
# See: skills/media/heartmula/SKILL.md for setup instructions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HEARTLIB_DIR="$HOME/heartlib"
OUTPUT_DIR="$SCRIPT_DIR/output"
MODEL_PATH="$HEARTLIB_DIR/ckpt"

# ── Checks ────────────────────────────────────────────────────────────────────

if [ ! -d "$HEARTLIB_DIR" ]; then
    echo "ERROR: heartlib not found at $HEARTLIB_DIR"
    echo "Run: git clone https://github.com/HeartMuLa/heartlib.git ~/heartlib"
    echo "Then follow setup in the heartmula skill."
    exit 1
fi

if [ ! -f "$HEARTLIB_DIR/.venv/bin/activate" ]; then
    echo "ERROR: heartlib venv not found. See heartmula skill for setup."
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

source "$HEARTLIB_DIR/.venv/bin/activate"
cd "$HEARTLIB_DIR"

echo "=== Hermes Neurovision Soundtrack Generator ==="
echo "Output dir: $OUTPUT_DIR"
echo ""

# ── Track 1: EMERGENCE ───────────────────────────────────────────────────────
# Vibe: ambient → cinematic buildup → clean synth drop → floating calm
# Matches: calm early builds (0-27s), build through terminal boot,
#          drop at v0.2.0, gentle outro with halvorsen star

echo "[1/3] Track 1: EMERGENCE — ambient cinematic with clean drop..."
python ./examples/run_music_generation.py \
  --model_path="$MODEL_PATH" \
  --version="3B" \
  --lyrics="$SCRIPT_DIR/track1_emergence_lyrics.txt" \
  --tags="$(cat $SCRIPT_DIR/track1_emergence_tags.txt)" \
  --save_path="$OUTPUT_DIR/track1_emergence.mp3" \
  --lazy_load true \
  --mula_device mps \
  --codec_device mps \
  --max_audio_length_ms 90000 \
  --temperature 1.0 \
  --cfg_scale 1.5
echo "✓ Track 1 done"
echo ""

# ── Track 2: SIGNAL FIRE ─────────────────────────────────────────────────────
# Vibe: electronic buildup → industrial drop → rapid acceleration → ambient rest
# Matches: tension in terminal boot → hard drop at v0.2.0 → rapid flash chaos
#          → serene halvorsen outro

echo "[2/3] Track 2: SIGNAL FIRE — industrial electronic with hard drop..."
python ./examples/run_music_generation.py \
  --model_path="$MODEL_PATH" \
  --version="3B" \
  --lyrics="$SCRIPT_DIR/track2_signal_fire_lyrics.txt" \
  --tags="$(cat $SCRIPT_DIR/track2_signal_fire_tags.txt)" \
  --save_path="$OUTPUT_DIR/track2_signal_fire.mp3" \
  --lazy_load true \
  --mula_device mps \
  --codec_device mps \
  --max_audio_length_ms 90000 \
  --temperature 1.05 \
  --cfg_scale 1.5
echo "✓ Track 2 done"
echo ""

# ── Track 3: NEURAL DAWN ─────────────────────────────────────────────────────
# Vibe: synthpop darkwave with emotional arc → ethereal outro
# Matches: dreamlike early screens → urgent boot → cascading v0.2.0 energy
#          → screens flying by → floating logo reveal

echo "[3/3] Track 3: NEURAL DAWN — darkwave synthpop with ethereal outro..."
python ./examples/run_music_generation.py \
  --model_path="$MODEL_PATH" \
  --version="3B" \
  --lyrics="$SCRIPT_DIR/track3_neural_dawn_lyrics.txt" \
  --tags="$(cat $SCRIPT_DIR/track3_neural_dawn_tags.txt)" \
  --save_path="$OUTPUT_DIR/track3_neural_dawn.mp3" \
  --lazy_load true \
  --mula_device mps \
  --codec_device mps \
  --max_audio_length_ms 90000 \
  --temperature 1.0 \
  --cfg_scale 1.5
echo "✓ Track 3 done"
echo ""

echo "=== ALL TRACKS COMPLETE ==="
echo ""
ls -lh "$OUTPUT_DIR"/*.mp3
echo ""
echo "Track 1 — EMERGENCE:    Ambient/cinematic. Clean synth drop. Floats into outro."
echo "Track 2 — SIGNAL FIRE:  Industrial/electronic. Hard drop. Rapid + aggressive."  
echo "Track 3 — NEURAL DAWN:  Darkwave synthpop. Emotional arc. Ethereal logo reveal."
echo ""
echo "Video arc reference (~79s):"
echo "  0s    Early builds — calm atmospheric"
echo "  27s   Terminal boot — tension, buildup"
echo "  39s   fractal-zoom warmup (hidden, music still plays)"
echo "  49s   v0.2.0 DROP — full energy"
echo "  68s   Rapid flash — peak/chaos, screens flying"
echo "  70s   Black half-second — breath"
echo "  70.5s Outro — halvorsen star, logo fades in, floating calm"
echo "  79s   END"
