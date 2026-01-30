"""Build ICAO event chains from individual advisories."""

import logging
from collections import defaultdict

from swx_advisories.models.advisory import ICAOAdvisory, ICAOEvent

logger = logging.getLogger(__name__)


class ICAOEventBuilder:
    """
    Build event chains from individual ICAO advisories.

    An ICAO event is a chain of related advisories tracking a space weather
    phenomenon from start to finish. Events are linked through the "NR RPLC"
    (number replaced) field - each advisory after the first one replaces
    the previous advisory in the chain.

    Example chain:
        Advisory 2024/0042 (NR RPLC: VOID)     <- Opening
        Advisory 2024/0043 (NR RPLC: 2024/0042) <- Replacement
        Advisory 2024/0044 (NR RPLC: 2024/0043) <- Closing
    """

    def build_events(self, advisories: list[ICAOAdvisory]) -> list[ICAOEvent]:
        """
        Link advisories into event chains.

        Note: Advisory IDs can be duplicated across effect types (HF COM vs GNSS),
        so we use (advisory_id, effect) as the unique identifier.

        Args:
            advisories: List of parsed ICAOAdvisory objects

        Returns:
            List of ICAOEvent objects, each containing a chain of advisories
        """
        if not advisories:
            return []

        # Group advisories by effect type first
        # This ensures we don't mix HF COM and GNSS chains even if IDs overlap
        by_effect = defaultdict(list)
        for adv in advisories:
            by_effect[adv.effect].append(adv)

        events = []

        for effect, effect_advisories in by_effect.items():
            # Build events for this effect type
            effect_events = self._build_events_for_effect(effect_advisories, effect)
            events.extend(effect_events)

        # Sort events by issue start time
        events.sort(key=lambda e: e.issue_start or e.advisories[0].issue_time)

        return events

    def _build_events_for_effect(
        self, advisories: list[ICAOAdvisory], effect: str
    ) -> list[ICAOEvent]:
        """Build event chains for advisories of a single effect type."""
        if not advisories:
            return []

        # Index advisories by their ID for quick lookup
        by_id = {}
        for adv in advisories:
            adv_id = adv.advisory_id.strip()
            if adv_id in by_id:
                # Duplicate advisory ID within same effect - keep the later one
                logger.warning(f"Duplicate advisory ID within {effect}: {adv_id}")
            by_id[adv_id] = adv

        # Build replacement chains: for each advisory, find what replaces it
        # replaces[A] = [B, C] means B and C both claim to replace A
        replaced_by = defaultdict(list)
        for adv in advisories:
            if adv.replaces_id:
                replaced_by[adv.replaces_id.strip()].append(adv)

        # Find opening advisories (those that don't replace anything)
        opening_advisories = [adv for adv in advisories if adv.is_opening]

        # Build events from each opening advisory
        events = []
        processed_ids = set()

        for opening in opening_advisories:
            if opening.advisory_id in processed_ids:
                continue

            chain = self._build_chain(opening, replaced_by, processed_ids)

            # Create event
            event = ICAOEvent(
                event_id=f"evt_{opening.advisory_id.replace('/', '_')}_{effect.replace(' ', '_')}",
                effect=opening.effect,
                advisories=chain,
            )
            events.append(event)

        # Check for orphaned advisories (replacements without their parent)
        orphaned = set(adv.advisory_id for adv in advisories) - processed_ids
        if orphaned:
            logger.warning(
                f"Found {len(orphaned)} orphaned {effect} advisories (replacements without opening): "
                f"{list(orphaned)[:5]}{'...' if len(orphaned) > 5 else ''}"
            )

        return events

    def _build_chain(
        self,
        start: ICAOAdvisory,
        replaced_by: dict[str, list[ICAOAdvisory]],
        processed: set[str],
    ) -> list[ICAOAdvisory]:
        """
        Build the full advisory chain starting from an opening advisory.

        Follows the replacement chain recursively until no more replacements.

        Args:
            start: Opening advisory
            replaced_by: Map of advisory_id -> list of advisories that replace it
            processed: Set of already-processed advisory IDs (mutated)

        Returns:
            List of advisories in chronological order
        """
        chain = [start]
        processed.add(start.advisory_id.strip())

        # Find all advisories that replace this one
        replacements = replaced_by.get(start.advisory_id.strip(), [])

        # Sort by issue time to ensure chronological order
        replacements.sort(key=lambda a: a.issue_time)

        for replacement in replacements:
            repl_id = replacement.advisory_id.strip()
            if repl_id in processed:
                continue

            # Recursively build the chain from this replacement
            sub_chain = self._build_chain(replacement, replaced_by, processed)
            chain.extend(sub_chain)

        return chain

    def merge_events_by_effect(
        self,
        events: list[ICAOEvent],
        max_gap_hours: float = 6.0,
    ) -> list[ICAOEvent]:
        """
        Optionally merge events of the same effect type that are close in time.

        Sometimes related space weather activity is reported as separate events
        even though they represent the same phenomenon. This method can merge
        them based on temporal proximity.

        Args:
            events: List of ICAOEvent objects
            max_gap_hours: Maximum hours between events to consider merging

        Returns:
            List of (possibly merged) ICAOEvent objects
        """
        if not events:
            return []

        from datetime import timedelta

        max_gap = timedelta(hours=max_gap_hours)

        # Group by effect type
        by_effect = defaultdict(list)
        for event in events:
            by_effect[event.effect].append(event)

        merged_events = []

        for effect, effect_events in by_effect.items():
            # Sort by issue start
            effect_events.sort(key=lambda e: e.issue_start or e.advisories[0].issue_time)

            current_group = [effect_events[0]]

            for event in effect_events[1:]:
                prev_end = current_group[-1].issue_end
                curr_start = event.issue_start

                if prev_end and curr_start and (curr_start - prev_end) <= max_gap:
                    # Merge into current group
                    current_group.append(event)
                else:
                    # Finalize current group and start new one
                    merged_events.append(self._merge_event_group(current_group))
                    current_group = [event]

            # Don't forget the last group
            merged_events.append(self._merge_event_group(current_group))

        # Sort by issue start
        merged_events.sort(key=lambda e: e.issue_start or e.advisories[0].issue_time)

        return merged_events

    def _merge_event_group(self, events: list[ICAOEvent]) -> ICAOEvent:
        """Merge a group of events into a single event."""
        if len(events) == 1:
            return events[0]

        # Collect all advisories
        all_advisories = []
        for event in events:
            all_advisories.extend(event.advisories)

        # Sort by issue time
        all_advisories.sort(key=lambda a: a.issue_time)

        return ICAOEvent(
            event_id=events[0].event_id,  # Use first event's ID
            effect=events[0].effect,
            advisories=all_advisories,
        )
