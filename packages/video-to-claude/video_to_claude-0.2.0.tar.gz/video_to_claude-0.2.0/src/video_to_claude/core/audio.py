"""Audio extraction and analysis."""

from __future__ import annotations

import subprocess
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
from scipy.io import wavfile


def extract_audio(video_path: Path | str, output_path: Path | str) -> Path:
    """
    Extract audio from video as WAV file.

    Args:
        video_path: Path to the input video
        output_path: Path for output WAV file

    Returns:
        Path to the extracted audio file
    """
    video_path = Path(video_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",  # No video
        "-acodec", "pcm_s16le",
        "-ar", "44100",  # Sample rate
        "-ac", "1",  # Mono
        str(output_path),
        "-y"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extraction failed: {result.stderr}")

    return output_path


def generate_spectrogram(audio_path: Path | str, output_path: Path | str) -> Path:
    """
    Generate a spectrogram image from audio.

    Args:
        audio_path: Path to WAV file
        output_path: Path for output PNG

    Returns:
        Path to the spectrogram image
    """
    audio_path = Path(audio_path)
    output_path = Path(output_path)

    sample_rate, audio_data = wavfile.read(audio_path)

    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)

    # Normalize
    audio_data = audio_data.astype(float) / np.max(np.abs(audio_data) + 1e-10)

    # Generate spectrogram
    fig, ax = plt.subplots(figsize=(16, 6))

    frequencies, times, spectrogram_data = signal.spectrogram(
        audio_data,
        sample_rate,
        nperseg=2048,
        noverlap=1024
    )

    # Plot with log scale for better visualization
    im = ax.pcolormesh(
        times,
        frequencies,
        10 * np.log10(spectrogram_data + 1e-10),
        shading='gouraud',
        cmap='magma'
    )

    ax.set_ylabel('Frequency (Hz)')
    ax.set_xlabel('Time (s)')
    ax.set_title('Spectrogram')
    ax.set_ylim(0, 8000)  # Focus on audible range

    plt.colorbar(im, ax=ax, label='Power (dB)')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return output_path


def generate_waveform(audio_path: Path | str, output_path: Path | str) -> Path:
    """
    Generate a waveform image from audio.

    Args:
        audio_path: Path to WAV file
        output_path: Path for output PNG

    Returns:
        Path to the waveform image
    """
    audio_path = Path(audio_path)
    output_path = Path(output_path)

    sample_rate, audio_data = wavfile.read(audio_path)

    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)

    # Normalize
    audio_data = audio_data.astype(float) / np.max(np.abs(audio_data) + 1e-10)

    # Downsample for visualization
    duration = len(audio_data) / sample_rate
    times = np.linspace(0, duration, len(audio_data))

    # Plot
    fig, ax = plt.subplots(figsize=(16, 3))

    # Downsample for plotting (every Nth sample)
    step = max(1, len(audio_data) // 10000)
    ax.plot(times[::step], audio_data[::step], color='#3498db', linewidth=0.5)
    ax.fill_between(times[::step], audio_data[::step], alpha=0.3, color='#3498db')

    ax.set_ylabel('Amplitude')
    ax.set_xlabel('Time (s)')
    ax.set_title('Waveform')
    ax.set_xlim(0, duration)
    ax.set_ylim(-1, 1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return output_path


def analyze_audio(audio_path: Path | str) -> dict:
    """
    Perform detailed analysis of audio file.

    Args:
        audio_path: Path to WAV file

    Returns:
        Dictionary containing audio analysis with:
        - metadata: sample_rate, duration, total_samples
        - overall_characteristics: RMS energy, peak amplitude, dynamic range, zero crossing rate
        - frequency_analysis: band energy distribution, spectral centroid
        - temporal_analysis: per-second energy analysis
        - notable_events: detected energy changes
        - text_description: human-readable summary
    """
    audio_path = Path(audio_path)
    sample_rate, audio_data = wavfile.read(audio_path)

    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)

    # Normalize
    audio_data = audio_data.astype(float) / np.max(np.abs(audio_data) + 1e-10)

    duration = len(audio_data) / sample_rate

    analysis = {
        "metadata": {
            "sample_rate": sample_rate,
            "duration_seconds": round(duration, 2),
            "total_samples": len(audio_data)
        },
        "overall_characteristics": {},
        "frequency_analysis": {},
        "temporal_analysis": [],
        "notable_events": []
    }

    # Overall characteristics
    rms = float(np.sqrt(np.mean(audio_data**2)))
    peak = float(np.max(np.abs(audio_data)))

    analysis["overall_characteristics"] = {
        "rms_energy": round(rms, 4),
        "peak_amplitude": round(peak, 4),
        "dynamic_range_db": round(float(20 * np.log10(peak / (np.mean(np.abs(audio_data)) + 1e-10))), 2),
        "zero_crossing_rate": round(float(np.sum(np.abs(np.diff(np.sign(audio_data)))) / (2 * len(audio_data))), 6)
    }

    # Frequency analysis using FFT
    n = len(audio_data)
    yf = np.abs(fft(audio_data))[:n//2]
    xf = fftfreq(n, 1/sample_rate)[:n//2]

    # Frequency band energy distribution
    bands = {
        "sub_bass_20_60hz": (20, 60),
        "bass_60_250hz": (60, 250),
        "low_mid_250_500hz": (250, 500),
        "mid_500_2000hz": (500, 2000),
        "high_mid_2000_4000hz": (2000, 4000),
        "presence_4000_6000hz": (4000, 6000),
        "brilliance_6000_20000hz": (6000, 20000)
    }

    band_energy = {}
    total_energy = np.sum(yf**2) + 1e-10
    for band_name, (low, high) in bands.items():
        mask = (xf >= low) & (xf < high)
        energy = np.sum(yf[mask]**2) / total_energy * 100
        band_energy[band_name] = round(float(energy), 2)

    # Spectral centroid (brightness indicator)
    spectral_centroid = float(np.sum(xf * yf) / (np.sum(yf) + 1e-10))

    analysis["frequency_analysis"] = {
        "frequency_band_energy_percent": band_energy,
        "spectral_centroid_hz": round(spectral_centroid, 1),
    }

    # Temporal analysis - analyze in 1-second chunks
    chunk_size = sample_rate
    for i in range(0, len(audio_data) - chunk_size, chunk_size):
        chunk = audio_data[i:i+chunk_size]
        chunk_time = i / sample_rate

        chunk_rms = float(np.sqrt(np.mean(chunk**2)))

        # Determine energy level
        if chunk_rms > 0.15:
            energy_level = "high"
        elif chunk_rms > 0.05:
            energy_level = "medium"
        else:
            energy_level = "low"

        analysis["temporal_analysis"].append({
            "time_seconds": round(chunk_time, 1),
            "rms_energy": round(chunk_rms, 4),
            "energy_level": energy_level
        })

    # Detect notable events (sudden changes in energy)
    if len(analysis["temporal_analysis"]) > 1:
        chunk_energies = [c["rms_energy"] for c in analysis["temporal_analysis"]]
        energy_diff = np.diff(chunk_energies)

        for i, diff in enumerate(energy_diff):
            if abs(diff) > 0.05:
                event_type = "energy_increase" if diff > 0 else "energy_decrease"
                analysis["notable_events"].append({
                    "time_seconds": analysis["temporal_analysis"][i+1]["time_seconds"],
                    "event_type": event_type,
                    "magnitude": round(float(abs(diff)), 4)
                })

    # Generate text description
    analysis["text_description"] = _generate_description(analysis)

    return analysis


def _generate_description(analysis: dict) -> str:
    """Generate a human-readable description of the audio."""
    desc = []

    meta = analysis["metadata"]
    desc.append(f"Audio duration: {meta['duration_seconds']} seconds.")

    overall = analysis["overall_characteristics"]
    if overall["rms_energy"] < 0.05:
        energy_desc = "quiet"
    elif overall["rms_energy"] < 0.15:
        energy_desc = "moderate"
    else:
        energy_desc = "loud"
    desc.append(f"Overall energy: {energy_desc}.")

    freq = analysis["frequency_analysis"]
    bands = freq["frequency_band_energy_percent"]
    dominant_band = max(bands.items(), key=lambda x: x[1])
    band_name = dominant_band[0].replace("_", " ").replace("hz", "Hz")
    desc.append(f"Dominant frequency band: {band_name} ({dominant_band[1]}% of energy).")

    events = analysis["notable_events"]
    if events:
        desc.append(f"Notable events: {len(events)} significant energy changes detected.")

    return " ".join(desc)
