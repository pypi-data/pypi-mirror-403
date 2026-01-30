"""Inotify-based event consumer for RuneLite events."""

import glob
import os
import threading
import time
from collections import defaultdict

import msgpack
from inotify_simple import INotify
from inotify_simple import flags as inotify_flags

from escape._internal.logger import logger

from .channels import (
    DOORBELL_PATH,
    LATEST_STATE_CHANNELS,
    RING_BUFFER_CHANNELS,
    SHM_DIR,
)


class EventConsumer:
    """Consumes events from /dev/shm using inotify doorbell pattern."""

    def __init__(self, cache, warn_on_gaps: bool = True):
        """Initialize event consumer."""
        self.cache = cache
        self.warn_on_gaps = warn_on_gaps

        # Tracking state
        self.last_seq = defaultdict(int)  # Last processed sequence per channel
        self.last_state_mtime = defaultdict(float)  # Last mtime per state channel

        # Thread control
        self.running = False
        self.thread: threading.Thread | None = None

        # Warmup tracking
        self._warmup_complete = threading.Event()
        self._warmup_event_count = 0

        # Inotify setup
        self.inotify: INotify | None = None
        self._setup_inotify()

    def _setup_inotify(self) -> None:
        """Set up inotify watch on doorbell file."""
        self.inotify = INotify()

        # Check if doorbell exists
        if not os.path.exists(DOORBELL_PATH):
            logger.warning(f"Doorbell not found at {DOORBELL_PATH}")
            logger.info("Waiting for Java plugin to create it")
            # Wait up to 5 seconds for doorbell to appear
            for _ in range(50):
                if os.path.exists(DOORBELL_PATH):
                    break
                time.sleep(0.1)

        if not os.path.exists(DOORBELL_PATH):
            raise FileNotFoundError(
                f"Doorbell not found at {DOORBELL_PATH}. "
                f"Make sure RuneLite is running with Escape plugin."
            )

        # Watch for modifications and close-write events
        self.inotify.add_watch(DOORBELL_PATH, inotify_flags.MODIFY | inotify_flags.CLOSE_WRITE)
        logger.success(f"Watching doorbell: {DOORBELL_PATH}")

    def start(self, wait_for_warmup: bool = True, warmup_timeout: float = 5.0) -> bool:
        """Start background event consumer thread."""
        if self.running:
            logger.warning("Event consumer already running")
            return False

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True, name="EventConsumer")
        self.thread.start()

        logger.success("Event consumer started (inotify mode)")

        # Process initial backlog of events before continuing
        if wait_for_warmup:
            return self.wait_for_warmup(timeout=warmup_timeout)

        return True

    def wait_for_warmup(self, timeout: float = 5.0) -> bool:
        """Wait for initial warmup phase to complete."""
        if self._warmup_complete.wait(timeout=timeout):
            return True
        else:
            logger.warning(
                f"Warmup timeout after {timeout}s (processed {self._warmup_event_count} events)"
            )
            return False

    def stop(self) -> None:
        """Stop event consumer thread."""
        if not self.running:
            return

        logger.info("Stopping event consumer")
        self.running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        if self.inotify:
            self.inotify.close()

        logger.success("Event consumer stopped")

    def _run(self) -> None:
        """Run main event loop in background thread."""
        logger.info("Event consumer loop started")
        logger.info(f"Ring buffer channels: {', '.join(RING_BUFFER_CHANNELS)}")
        logger.info(f"Latest-state channels: {', '.join(LATEST_STATE_CHANNELS)}")
        print()

        # Perform initial warmup - process all existing events before entering main loop
        self._perform_warmup()

        while self.running:
            try:
                # Block here until doorbell rings (zero CPU usage!)
                inotify = self.inotify
                if inotify is None:
                    break
                events = inotify.read(timeout=1000)  # 1s timeout for clean shutdown

                if events:
                    # Doorbell was rung! Process all channels
                    self._process_all_channels()

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in event loop: {e}")
                import traceback

                traceback.print_exc()
                time.sleep(1)

    def _perform_warmup(self) -> None:
        """Process all existing events during startup."""
        logger.info("Warming up event cache")
        start_time = time.time()
        total_events = 0

        # Process all ring buffer channels
        for channel in RING_BUFFER_CHANNELS:
            count = self._process_ring_buffer(channel)
            total_events += count

        # Process all latest-state channels
        for channel in LATEST_STATE_CHANNELS:
            self._process_latest_state(channel)

        # Calculate stats
        elapsed_ms = (time.time() - start_time) * 1000
        per_event_us = (elapsed_ms * 1000) / total_events if total_events > 0 else 0

        # Store count for timeout reporting
        self._warmup_event_count = total_events

        if total_events > 0:
            logger.success(
                f"Warmup complete: processed {total_events} events in {elapsed_ms:.1f}ms ({per_event_us:.0f}μs/event)"
            )
        else:
            logger.success("Warmup complete: no backlog events found")

        # Signal that warmup is complete
        self._warmup_complete.set()

    def _process_all_channels(self) -> None:
        """Process all ring buffer and latest-state channels."""
        start_time = time.time()
        total_events = 0

        # Process ring buffer channels (guaranteed delivery)
        for channel in RING_BUFFER_CHANNELS:
            count = self._process_ring_buffer(channel)
            total_events += count

        # Process latest-state channels (current state only)
        for channel in LATEST_STATE_CHANNELS:
            self._process_latest_state(channel)

        # Log if we processed more than 10 events
        if total_events > 10:
            elapsed_ms = (time.time() - start_time) * 1000
            per_event_us = (elapsed_ms * 1000) / total_events if total_events > 0 else 0
            logger.success(
                f"Cleared {total_events} events in {elapsed_ms:.1f}ms ({per_event_us:.0f}μs/event)"
            )

    def _process_ring_buffer(self, channel: str) -> int:
        """Process ring buffer events for a channel."""
        pattern = f"{SHM_DIR}/{channel}.*"
        files = sorted(
            glob.glob(pattern),
            key=lambda x: int(x.split(".")[-1]) if x.split(".")[-1].isdigit() else 0,
        )

        events_processed = 0

        for filepath in files:
            try:
                # Extract sequence number
                filename = os.path.basename(filepath)
                parts = filename.split(".")
                if len(parts) < 2 or not parts[-1].isdigit():
                    continue

                seq = int(parts[-1])

                # Skip if already processed
                if seq <= self.last_seq[channel]:
                    os.remove(filepath)
                    continue

                # Read and deserialize event
                with open(filepath, "rb") as f:
                    event = msgpack.unpackb(f.read(), raw=False, strict_map_key=False)

                # Verify sequence continuity
                expected_seq = self.last_seq[channel] + 1
                if seq != expected_seq and self.last_seq[channel] > 0 and self.warn_on_gaps:
                    gap_size = seq - expected_seq
                    logger.warning(
                        f"[{channel}] Gap detected! Expected {expected_seq}, got {seq} (missed {gap_size})"
                    )

                # Store event in cache
                # print(f"🔔 [{channel}] Processing event seq={seq} with event {event}")
                self.cache.add_event(channel, event)

                # Update sequence tracker
                self.last_seq[channel] = seq
                events_processed += 1

                # Delete processed event
                os.remove(filepath)

            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")

        return events_processed

    def _process_latest_state(self, channel: str) -> bool:
        """Process latest-state event for a channel."""
        filepath = f"{SHM_DIR}/{channel}"

        try:
            if not os.path.exists(filepath):
                return False

            # Check if file was modified since last read
            stat = os.stat(filepath)
            current_mtime = stat.st_mtime

            # Skip if file hasn't changed
            if current_mtime <= self.last_state_mtime[channel]:
                return False

            # Update modification time tracker
            self.last_state_mtime[channel] = current_mtime

            # Read and deserialize state
            with open(filepath, "rb") as f:
                state = msgpack.unpackb(f.read(), raw=False, strict_map_key=False)

            # Update cache - all latest-state events use same method now
            self.cache.add_event(channel, state)

            return True

        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
            return False
