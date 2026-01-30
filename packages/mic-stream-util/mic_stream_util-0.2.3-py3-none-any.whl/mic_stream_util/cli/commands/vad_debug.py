"""VAD debug command with extensive memory and performance logging."""

from __future__ import annotations

import gc
import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Optional

import click
import numpy as np
import psutil

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)8s] [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Monitor memory usage and log statistics."""

    def __init__(self, interval: float = 5.0):
        self.interval = interval
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024
        self.last_memory = self.initial_memory
        self.running = False
        self.thread: threading.Thread | None = None
        self.samples: list[tuple[float, float]] = []

        # Track object counts
        self.initial_obj_count = len(gc.get_objects())

    def start(self) -> None:
        """Start monitoring thread."""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=False)
        self.thread.start()
        logger.info("Memory monitor started")

    def stop(self) -> None:
        """Stop monitoring thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("Memory monitor stopped")
        self._print_summary()

    def _monitor_loop(self) -> None:
        """Monitoring loop."""
        while self.running:
            try:
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                memory_delta = memory_mb - self.initial_memory
                memory_change = memory_mb - self.last_memory
                thread_count = threading.active_count()
                process_threads = self.process.num_threads()

                # Get object count
                obj_count = len(gc.get_objects())
                obj_delta = obj_count - self.initial_obj_count

                # Get shared memory usage
                shm_count, shm_size = self._get_shared_memory()

                logger.info(
                    f"MEMORY: {memory_mb:.1f} MB (Δ{memory_delta:+.1f} MB, change: {memory_change:+.1f} MB) | "
                    f"Threads: {thread_count} py/{process_threads} proc | "
                    f"Objects: {obj_count} (Δ{obj_delta:+d}) | "
                    f"SharedMem: {shm_count} ({shm_size / 1024 / 1024:.1f} MB)"
                )

                self.samples.append((time.time(), memory_mb))
                self.last_memory = memory_mb

                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in memory monitor: {e}")

    def _get_shared_memory(self) -> tuple[int, int]:
        """Get shared memory buffer count and total size."""
        try:
            shm_path = "/dev/shm"
            count = 0
            total_size = 0
            for filename in os.listdir(shm_path):
                if "mic_buffer" in filename:
                    filepath = os.path.join(shm_path, filename)
                    total_size += os.path.getsize(filepath)
                    count += 1
            return count, total_size
        except Exception:
            return 0, 0

    def _print_summary(self) -> None:
        """Print monitoring summary."""
        if len(self.samples) < 2:
            return

        final_memory = self.samples[-1][1]
        total_change = final_memory - self.initial_memory
        duration = self.samples[-1][0] - self.samples[0][0]

        logger.info("=" * 80)
        logger.info("MEMORY MONITORING SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration:.1f}s")
        logger.info(f"Initial memory: {self.initial_memory:.1f} MB")
        logger.info(f"Final memory: {final_memory:.1f} MB")
        logger.info(f"Total change: {total_change:+.1f} MB")
        if duration > 0:
            logger.info(f"Rate: {total_change / (duration / 60):.2f} MB/min")

        # Check for shared memory leaks
        shm_count, shm_size = self._get_shared_memory()
        if shm_count > 0:
            logger.warning(f"Shared memory still allocated: {shm_count} buffers, {shm_size / 1024 / 1024:.1f} MB")


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option("--device", "-d", help="Device name or index (default: default device)")
@click.option("--sample-rate", "-r", type=int, default=16000, help="Sample rate (default: 16000)")
@click.option("--threshold", "-t", type=float, default=0.5, help="VAD threshold (0.0-1.0, default: 0.5)")
@click.option("--padding-before", type=int, default=300, help="Padding before speech in ms (default: 300)")
@click.option("--padding-after", type=int, default=300, help="Padding after speech in ms (default: 300)")
@click.option("--max-silence", type=int, default=1000, help="Max silence duration in ms (default: 1000)")
@click.option("--output-dir", "-o", type=click.Path(file_okay=False), help="Directory to save speech segments")
@click.option("--monitor-interval", type=float, default=5.0, help="Memory monitoring interval in seconds (default: 5)")
@click.option("--duration", type=int, default=0, help="Test duration in seconds (0 = infinite)")
@click.option("--force-gc", is_flag=True, help="Force garbage collection every monitor interval")
@click.option("--no-vad", is_flag=True, help="Skip VAD processing, only stream microphone (isolate audio capture leak)")
def vad_debug(
    device: Optional[str],
    sample_rate: int,
    threshold: float,
    padding_before: int,
    padding_after: int,
    max_silence: int,
    output_dir: Optional[str],
    monitor_interval: float,
    duration: int,
    force_gc: bool,
    no_vad: bool,
):
    """Run Voice Activity Detection with extensive debugging and memory monitoring.

    This command provides detailed logging of:
    - Memory usage over time
    - Thread counts
    - Buffer sizes
    - Queue states
    - Object counts
    - Shared memory usage

    Use this to identify memory leaks and performance issues.
    """
    # Import audio config (always needed)
    from mic_stream_util.core.audio_config import AudioConfig
    from mic_stream_util.core.microphone_manager import MicrophoneStream

    # Check if VAD functionality is available (only if not --no-vad)
    if not no_vad:
        try:
            from mic_stream_util import VAD_AVAILABLE

            if not VAD_AVAILABLE:
                raise ImportError("VAD functionality not available")
        except ImportError:
            click.echo("❌ VAD functionality requires additional dependencies.")
            click.echo("Install with: uv add 'mic-stream-util[vad]'")
            return

        # Dynamic imports for VAD
        try:
            from mic_stream_util.speech import SpeechManager, VADConfig
        except ImportError as e:
            click.echo(f"❌ Failed to import VAD dependencies: {e}")
            return

    try:
        # Create configurations
        audio_config = AudioConfig(
            sample_rate=sample_rate,
            device_name=device,
            dtype="float32",
            num_samples=512,
        )

        if not no_vad:
            vad_config = VADConfig(
                threshold=threshold,
                padding_before_ms=padding_before,
                padding_after_ms=padding_after,
                max_silence_ms=max_silence,
            )
        else:
            vad_config = None

        # Create output directory if specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 80)
        if no_vad:
            logger.info("MICROPHONE STREAM - DEBUG MODE (NO VAD)")
        else:
            logger.info("VOICE ACTIVITY DETECTION - DEBUG MODE")
        logger.info("=" * 80)
        logger.info(f"Device: {device or 'default'}")
        logger.info(f"Sample Rate: {sample_rate} Hz")
        if not no_vad:
            logger.info(f"VAD Threshold: {threshold}")
            logger.info(f"Padding: {padding_before}ms before, {padding_after}ms after")
            logger.info(f"Max Silence: {max_silence}ms")
        logger.info(f"Monitor Interval: {monitor_interval}s")
        logger.info(f"Force GC: {force_gc}")
        if duration > 0:
            logger.info(f"Duration: {duration}s")
        logger.info("=" * 80)
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 80)

        speech_count = 0
        audio_chunk_count = 0
        vad_change_count = 0
        last_stats_time = time.time()
        last_gc_time = time.time()

        # Start memory monitor
        memory_monitor = MemoryMonitor(interval=monitor_interval)
        memory_monitor.start()

        def on_speech_start(timestamp: float):
            nonlocal speech_count
            speech_count += 1
            logger.info(f"🎙️  SPEECH START #{speech_count} at {timestamp:.2f}s")

        def on_speech_chunk(speech_chunk, vad_score: float):
            logger.debug(f"   Speech chunk: {len(speech_chunk.audio_chunk)} samples, VAD: {vad_score:.3f}")

        def on_speech_ended(speech_chunk):
            logger.info(f"🛑 SPEECH END #{speech_count} - Duration: {speech_chunk.duration:.2f}s, Samples: {len(speech_chunk.audio_chunk)}")

            # Save audio if output directory specified
            if output_dir and len(speech_chunk.audio_chunk) > 0:
                import soundfile as sf

                output_file = Path(output_dir) / f"speech_{speech_count:03d}.wav"
                sf.write(str(output_file), speech_chunk.audio_chunk, sample_rate)
                logger.info(f"   Saved to: {output_file}")

        def on_audio_chunk(audio_chunk, timestamp: float):
            nonlocal audio_chunk_count, last_stats_time
            audio_chunk_count += 1

            # Log stats every 10 seconds
            if time.time() - last_stats_time >= 10.0:
                logger.debug(f"Audio chunks processed: {audio_chunk_count}")
                last_stats_time = time.time()

        def on_vad_changed(vad_score: float):
            nonlocal vad_change_count
            vad_change_count += 1
            if vad_change_count % 100 == 0:  # Log every 100 VAD changes
                logger.debug(f"VAD changes: {vad_change_count}, Current: {vad_score:.3f}")

        start_time = time.time()

        if no_vad:
            # MODE 1: No VAD - Just stream microphone (test base audio capture)
            logger.info("Creating MicrophoneStream (NO VAD)...")
            mic_stream = MicrophoneStream(audio_config)

            # Simple callback that just counts chunks
            def on_raw_audio_chunk(audio_chunk: np.ndarray):
                nonlocal audio_chunk_count, last_stats_time
                audio_chunk_count += 1

                # Log stats periodically
                if time.time() - last_stats_time >= 10.0:
                    logger.debug(f"Audio chunks processed: {audio_chunk_count}")
                    last_stats_time = time.time()

            mic_stream.set_callback(on_raw_audio_chunk)
            logger.info("Starting audio stream (no VAD)...")

            try:
                with mic_stream.stream():
                    logger.info("Audio stream active (no VAD processing)")

                    while True:
                        time.sleep(1.0)

                        # Force garbage collection if requested
                        if force_gc and time.time() - last_gc_time >= monitor_interval:
                            collected = gc.collect()
                            logger.debug(f"🗑️  Forced GC collected {collected} objects")
                            last_gc_time = time.time()

                        # Check duration
                        if duration > 0 and (time.time() - start_time) >= duration:
                            logger.info(f"Duration {duration}s reached, stopping...")
                            break

            except KeyboardInterrupt:
                logger.info("Stream stopped by user")
            finally:
                logger.info("Stopping audio stream...")
                logger.info("=" * 80)
                logger.info("FINAL STATISTICS (NO VAD)")
                logger.info("=" * 80)
                logger.info(f"Audio chunks processed: {audio_chunk_count}")
                logger.info("=" * 80)

                mic_stream.stop_stream()
                logger.info("Stream stopped")

                # Give some time for cleanup
                time.sleep(0.5)

                # Delete microphone stream
                logger.info("Deleting MicrophoneStream...")
                del mic_stream

                # Force garbage collection
                logger.info("Running garbage collection...")
                collected = gc.collect()
                logger.info(f"Collected {collected} objects")

                # Stop memory monitor
                memory_monitor.stop()

                # Check for remaining shared memory
                shm_count, shm_size = memory_monitor._get_shared_memory()
                if shm_count > 0:
                    logger.warning(f"⚠️  {shm_count} shared memory buffers still exist ({shm_size / 1024 / 1024:.1f} MB)")
                    logger.warning("You may need to manually clean /dev/shm")

        else:
            # MODE 2: With VAD - Full speech detection
            logger.info("Creating SpeechManager...")
            speech_manager = SpeechManager(audio_config=audio_config, vad_config=vad_config)

            # Set callbacks
            speech_manager.set_callbacks(
                on_speech_start=on_speech_start,
                on_speech_chunk=on_speech_chunk,
                on_speech_ended=on_speech_ended,
                on_audio_chunk=on_audio_chunk,
                on_vad_changed=on_vad_changed,
            )

            logger.info("Starting audio stream...")

            try:
                with speech_manager.stream_context():
                    logger.info("Audio stream active")

                    # Run for specified duration or until interrupted
                    while True:
                        time.sleep(1.0)

                        # Log buffer stats every monitor interval
                        if time.time() - last_stats_time >= monitor_interval:
                            stats = speech_manager.get_buffer_stats()
                            logger.info(
                                f"📊 BUFFER STATS - "
                                f"Queue: {stats['callback_queue_size']}/{stats['callback_queue_max']}, "
                                f"PreSpeech: {stats['pre_speech_buffer_chunks']} chunks, "
                                f"Speech: {stats['speech_buffer_chunks']} chunks ({stats['speech_buffer_duration_s']:.2f}s), "
                                f"Processed: {stats['total_chunks_processed']}, "
                                f"Dropped: {stats['dropped_events']}"
                            )
                            last_stats_time = time.time()

                        # Force garbage collection if requested
                        if force_gc and time.time() - last_gc_time >= monitor_interval:
                            collected = gc.collect()
                            logger.debug(f"🗑️  Forced GC collected {collected} objects")
                            last_gc_time = time.time()

                        # Check duration
                        if duration > 0 and (time.time() - start_time) >= duration:
                            logger.info(f"Duration {duration}s reached, stopping...")
                            break

            except KeyboardInterrupt:
                logger.info("VAD stopped by user")
            finally:
                logger.info("Stopping audio stream...")

                # Get final stats
                stats = speech_manager.get_buffer_stats()
                logger.info("=" * 80)
                logger.info("FINAL STATISTICS")
                logger.info("=" * 80)
                logger.info(f"Speech segments: {speech_count}")
                logger.info(f"Audio chunks processed: {audio_chunk_count}")
                logger.info(f"VAD changes: {vad_change_count}")
                logger.info(f"Callback events processed: {stats['processed_events']}")
                logger.info(f"Callback events dropped: {stats['dropped_events']}")
                logger.info(f"Final queue size: {stats['callback_queue_size']}")
                logger.info(f"Final pre-speech buffer: {stats['pre_speech_buffer_chunks']} chunks")
                logger.info(f"Final speech buffer: {stats['speech_buffer_chunks']} chunks")
                logger.info("=" * 80)

                speech_manager.stop_stream()
                logger.info("Stream stopped")

                # Give some time for cleanup
                time.sleep(0.5)

                # Delete speech manager
                logger.info("Deleting SpeechManager...")
                del speech_manager

                # Force garbage collection
                logger.info("Running garbage collection...")
                collected = gc.collect()
                logger.info(f"Collected {collected} objects")

                # Stop memory monitor
                memory_monitor.stop()

                # Check for remaining shared memory
                shm_count, shm_size = memory_monitor._get_shared_memory()
                if shm_count > 0:
                    logger.warning(f"⚠️  {shm_count} shared memory buffers still exist ({shm_size / 1024 / 1024:.1f} MB)")
                    logger.warning("You may need to manually clean /dev/shm")

    except Exception as e:
        logger.exception(f"❌ Error: {e}")
        return


if __name__ == "__main__":
    vad_debug()
