"""modules/echo_control.py
Simple post-processing echo reduction utility.

Usage:
  python modules/echo_control.py <input.wav> [--out <output.wav>]

Behavior:
- If `noisereduce` is available, uses its spectral gating (fast and effective).
- Else if `librosa` + `scipy` are available, applies a basic spectral subtraction / high-pass filter.
- Falls back to copying the file unchanged if no audio libraries are present.

This is a best-effort offline post-processor, not a real-time AEC.
"""

import sys
import os
import argparse

try:
    import soundfile as sf
except Exception:
    sf = None

try:
    import noisereduce as nr
except Exception:
    nr = None

try:
    import librosa
    import numpy as np
    from scipy import signal
except Exception:
    librosa = None
    np = None
    signal = None


def reduce_echo_with_noisereduce(in_path, out_path):
    data, sr = sf.read(in_path)
    if data.ndim > 1:
        # convert to mono for processing then restore
        mono = data.mean(axis=1)
    else:
        mono = data
    reduced = nr.reduce_noise(y=mono, sr=sr)
    if data.ndim > 1:
        # replicate channels
        for ch in range(data.shape[1]):
            data[:, ch] = reduced
        sf.write(out_path, data, sr)
    else:
        sf.write(out_path, reduced, sr)


def reduce_echo_with_librosa(in_path, out_path):
    y, sr = librosa.load(in_path, sr=None, mono=True)
    # simple high-pass to reduce low-frequency reverb
    sos = signal.butter(4, 120, 'hp', fs=sr, output='sos')
    filtered = signal.sosfiltfilt(sos, y)
    # mild spectral gating using median noise estimate
    # estimate noise from first 0.5s
    n0 = int(min(len(filtered), int(0.5 * sr)))
    noise_sample = filtered[:n0]
    if len(noise_sample) < 256:
        sf.write(out_path, filtered, sr)
        return
    # simple spectral subtraction via STFT magnitude thresholding
    import numpy as np
    D = librosa.stft(filtered)
    mag, phase = np.abs(D), np.angle(D)
    noise_mag = np.median(np.abs(librosa.stft(noise_sample)), axis=1, keepdims=True)
    # reduce magnitude where below some threshold times noise
    mag2 = np.maximum(mag - 1.0 * noise_mag, 0.0)
    D2 = mag2 * np.exp(1j * phase)
    y_out = librosa.istft(D2)
    sf.write(out_path, y_out, sr)


def simple_copy(in_path, out_path):
    import shutil
    shutil.copyfile(in_path, out_path)


def process_file(in_path, out_path=None):
    if out_path is None:
        base, ext = os.path.splitext(in_path)
        out_path = base + "_echo_reduced" + ext

    print(f"Processing {in_path} -> {out_path}")

    if sf is None:
        print("soundfile not available; cannot read/write audio. Copying file instead.")
        simple_copy(in_path, out_path)
        return out_path

    try:
        if nr is not None:
            reduce_echo_with_noisereduce(in_path, out_path)
            print("Used noisereduce for echo reduction.")
        elif librosa is not None and signal is not None:
            reduce_echo_with_librosa(in_path, out_path)
            print("Used librosa+scipy based processing for echo reduction.")
        else:
            print("No advanced audio libraries available; copying file.")
            simple_copy(in_path, out_path)
    except Exception as e:
        print(f"Post-processing failed: {e}")
        print("Copying original file as fallback.")
        simple_copy(in_path, out_path)

    return out_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Echo reduction post-processor')
    parser.add_argument('inputs', nargs='+', help='Input WAV files to process')
    parser.add_argument('--out', '-o', help='Optional single output file (only valid with one input)')
    args = parser.parse_args()

    if args.out and len(args.inputs) != 1:
        print('When using --out you must supply exactly one input file')
        sys.exit(2)

    for i, inp in enumerate(args.inputs):
        if not os.path.exists(inp):
            print(f"File not found: {inp}")
            continue
        out = args.out if args.out else None
        try:
            result = process_file(inp, out)
            print(f"Wrote: {result}")
        except Exception as e:
            print(f"Error processing {inp}: {e}")
