from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import logging
from typing import Dict, List, Optional

from cv_agent.mcp.g_calendar import get_calendar_events
from cv_agent.mcp.schemas import CalendarEvent

logger = logging.getLogger(__name__)


@dataclass
class AvailabilityConstraints:
    """Constraints for recruiter availability."""

    # Working hours
    earliest_meeting_time: time = time(10, 0)  # 10:00 AM
    latest_meeting_end: time = time(18, 0)  # 6:00 PM

    # Lunch break
    lunch_break_start: time = time(13, 0)  # 1:00 PM
    lunch_break_end: time = time(14, 0)  # 2:00 PM

    # Meeting constraints
    meeting_duration_minutes: int = 45
    min_break_between_meetings: int = 5
    max_meetings_per_day: int = 4

    # Buffer time
    setup_time_minutes: int = 5  # Time before meeting to prepare


@dataclass
class TimeSlot:
    """Represents a time slot."""

    start: datetime
    end: datetime

    def __str__(self):
        return f"{self.start.strftime('%I:%M %p')} - {self.end.strftime('%I:%M %p')}"

    def overlaps_with(self, other: "TimeSlot") -> bool:
        """Check if this slot overlaps with another."""
        return not (self.end <= other.start or self.start >= other.end)

    def contains_time(self, check_time: time) -> bool:
        """Check if a specific time falls within this slot."""
        slot_start = self.start.time()
        slot_end = self.end.time()
        return slot_start <= check_time < slot_end


class RecruiterAvailabilityChecker:
    """
    Check recruiter availability considering all constraints.

    Uses Google Calendar MCP server to get existing events and find free slots.
    """

    def __init__(self, constraints: Optional[AvailabilityConstraints] = None):
        self.constraints = constraints or AvailabilityConstraints()

    async def get_available_slots_str(
        self,
        recruiter_email: str,
        num_slots_to_propose: int = 3,
        search_days_ahead: int = 14,
    ) -> str:
        """
        Adjust email template with available time slots.

        Args:
            recruiter_email: Recruiter's email address
            num_slots_to_propose: Number of time slots to propose (default: 3)
            search_days_ahead: How many days ahead to search

        Returns:
            Available time slots
        """

        logger.info(f"Adjusting email template with availability for {recruiter_email}")

        # Get available slots
        start_date = datetime.now() + timedelta(days=1)  # Start from tomorrow
        end_date = start_date + timedelta(days=search_days_ahead)

        available_slots = await self.get_available_slots(
            recruiter_email=recruiter_email,
            start_date=start_date,
            end_date=end_date,
        )

        # Flatten all slots
        all_slots = []
        for date_str, slots in available_slots.items():
            all_slots.extend(slots)

        if not all_slots:
            logger.warning("No available slots found")
            return "No available time slots found in recruiter's calendar"

        # Select diverse slots (morning, midday, afternoon on different days)
        selected_slots = self._select_diverse_slots(
            all_slots=all_slots,
            num_slots=num_slots_to_propose,
        )

        # Format time slots for email
        formatted_slots = self._format_slots_for_email(selected_slots)

        return formatted_slots

    def _select_diverse_slots(
        self,
        all_slots: List[TimeSlot],
        num_slots: int = 3,
    ) -> List[TimeSlot]:
        """
        Select diverse time slots across different days and times.

        Tries to select:
        - Different days (preferably)
        - Different times of day (morning, midday, afternoon)
        """

        if len(all_slots) <= num_slots:
            return all_slots

        # Classify slots by time of day
        morning_slots = []
        midday_slots = []
        afternoon_slots = []

        for slot in all_slots:
            time_classification = self._classify_time_of_day(slot.start)

            if time_classification == "morning":
                morning_slots.append(slot)
            elif time_classification == "midday":
                midday_slots.append(slot)
            elif time_classification == "afternoon":
                afternoon_slots.append(slot)

        # Try to select one from each category on different days
        selected_slots = []
        used_dates = set()

        # Priority: morning, midday, afternoon
        for slot_list in [morning_slots, midday_slots, afternoon_slots]:
            if len(selected_slots) >= num_slots:
                break

            # Find slot on a different day
            for slot in slot_list:
                slot_date = slot.start.date()

                if slot_date not in used_dates:
                    selected_slots.append(slot)
                    used_dates.add(slot_date)
                    break

        # If we still need more slots, add any remaining on different days
        if len(selected_slots) < num_slots:
            for slot in all_slots:
                if len(selected_slots) >= num_slots:
                    break

                slot_date = slot.start.date()

                if slot_date not in used_dates:
                    selected_slots.append(slot)
                    used_dates.add(slot_date)

        # If we still need more slots, just add the next available ones
        if len(selected_slots) < num_slots:
            for slot in all_slots:
                if len(selected_slots) >= num_slots:
                    break

                if slot not in selected_slots:
                    selected_slots.append(slot)

        # Sort by date and time
        selected_slots.sort(key=lambda s: s.start)

        return selected_slots[:num_slots]

    def _classify_time_of_day(self, dt: datetime) -> str:
        """
        Classify time of day.

        Morning: 10:00 - 12:00
        Midday: 12:00 - 16:00 (excluding lunch 13:00-14:00)
        Afternoon: 16:00 - 18:00
        """

        hour = dt.hour

        if 10 <= hour < 12:
            return "morning"
        elif 12 <= hour < 16:
            return "midday"
        elif 16 <= hour < 18:
            return "afternoon"
        else:
            return "other"

    def _format_slots_for_email(self, slots: List[TimeSlot]) -> str:
        """
        Format time slots for email display.

        Example output:
        - Monday, December 2nd at 10:00 AM - 10:45 AM
        - Wednesday, December 4th at 2:00 PM - 2:45 PM
        - Friday, December 6th at 4:30 PM - 5:15 PM
        """

        formatted_lines = []

        for slot in slots:
            # Format: "Monday, December 2nd at 10:00 AM - 10:45 AM"
            day_name = slot.start.strftime("%A")
            month_name = slot.start.strftime("%B")
            day_num = slot.start.day

            # Add ordinal suffix (1st, 2nd, 3rd, 4th, etc.)
            if 10 <= day_num % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(day_num % 10, "th")

            start_time = slot.start.strftime("%I:%M %p").lstrip("0")
            end_time = slot.end.strftime("%I:%M %p").lstrip("0")

            formatted_line = (
                f"- {day_name}, {month_name} {day_num}{suffix} "
                f"at {start_time} - {end_time}"
            )

            formatted_lines.append(formatted_line)

        return "\n".join(formatted_lines)

    async def get_available_slots(
        self,
        recruiter_email: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, List[TimeSlot]]:
        """
        Get all available time slots for recruiter within date range.

        Args:
            recruiter_email: Recruiter's email address
            start_date: Start of search range
            end_date: End of search range

        Returns:
            Dictionary mapping date strings to list of available slots
        """

        logger.info(
            f"Checking availability for {recruiter_email} "
            f"from {start_date} to {end_date}"
        )

        # Get recruiter's calendar events
        calendar_response = await get_calendar_events(
            user_email=recruiter_email,
            start_time=start_date,
            end_time=end_date,
        )

        # Parse existing events into TimeSlot objects
        busy_slots = self._parse_calendar_events(calendar_response.events)

        # Generate available slots for each day
        available_slots_by_date = {}
        current_date = start_date.date()
        end = end_date.date()

        while current_date <= end:
            # Get busy slots for this specific day
            day_busy_slots = [
                slot for slot in busy_slots if slot.start.date() == current_date
            ]

            # Find available slots for this day
            day_available_slots = self._find_available_slots_for_day(
                date=current_date,
                busy_slots=day_busy_slots,
            )

            if day_available_slots:
                date_str = current_date.strftime("%Y-%m-%d")
                available_slots_by_date[date_str] = day_available_slots

            current_date += timedelta(days=1)

        logger.info(
            f"Found {sum(len(slots) for slots in available_slots_by_date.values())} "
            f"available slots across {len(available_slots_by_date)} days"
        )

        return available_slots_by_date

    def _parse_calendar_events(self, events: List[CalendarEvent]) -> List[TimeSlot]:
        """Parse calendar events into TimeSlot objects."""

        busy_slots = []

        for event in events:
            try:
                # Parse ISO format datetime strings
                start = datetime.fromisoformat(event.start_time.replace("Z", "+00:00"))
                end = datetime.fromisoformat(event.end_time.replace("Z", "+00:00"))

                # Convert to local time if needed
                # For simplicity, assuming times are already in correct timezone
                start = start.replace(tzinfo=None)
                end = end.replace(tzinfo=None)

                busy_slots.append(TimeSlot(start=start, end=end))

            except Exception as e:
                logger.warning(f"Error parsing event time: {e}")
                continue

        return busy_slots

    def _find_available_slots_for_day(
        self,
        date: date,
        busy_slots: List[TimeSlot],
    ) -> List[TimeSlot]:
        """
        Find available time slots for a specific day.

        Considers:
        - Working hours (10:00 - 18:00)
        - Lunch break (13:00 - 14:00)
        - Minimum breaks between meetings (5 mins)
        - Maximum meetings per day (4)
        - Meeting duration (45 mins)
        """

        # Create datetime objects for the day's boundaries
        day_start = datetime.combine(date, self.constraints.earliest_meeting_time)
        day_end = datetime.combine(date, self.constraints.latest_meeting_end)

        # Create lunch break slot
        lunch_start = datetime.combine(date, self.constraints.lunch_break_start)
        lunch_end = datetime.combine(date, self.constraints.lunch_break_end)
        lunch_break = TimeSlot(start=lunch_start, end=lunch_end)

        # Add lunch break to busy slots
        all_busy_slots = busy_slots + [lunch_break]

        # Sort busy slots by start time
        all_busy_slots.sort(key=lambda slot: slot.start)

        # Find free time windows
        available_slots = []
        current_time = day_start

        for busy_slot in all_busy_slots:
            # If there's a gap before this busy slot
            if current_time < busy_slot.start:
                # Check if we can fit a meeting in this gap
                free_slots = self._generate_slots_in_window(
                    window_start=current_time,
                    window_end=busy_slot.start,
                )
                available_slots.extend(free_slots)

            # Move current time to end of busy slot + minimum break
            current_time = busy_slot.end + timedelta(
                minutes=self.constraints.min_break_between_meetings
            )

        # Check for slots after the last busy period
        if current_time < day_end:
            free_slots = self._generate_slots_in_window(
                window_start=current_time,
                window_end=day_end,
            )
            available_slots.extend(free_slots)

        # Limit to max meetings per day
        available_slots = available_slots[: self.constraints.max_meetings_per_day]

        return available_slots

    def _generate_slots_in_window(
        self,
        window_start: datetime,
        window_end: datetime,
    ) -> List[TimeSlot]:
        """
        Generate possible meeting slots within a time window.

        Args:
            window_start: Start of available window
            window_end: End of available window

        Returns:
            List of possible meeting slots
        """

        slots = []
        meeting_duration = timedelta(minutes=self.constraints.meeting_duration_minutes)

        # Start from the beginning of the window
        current_start = window_start

        while True:
            # Calculate when this meeting would end
            meeting_end = current_start + meeting_duration

            # Check if meeting would end after day ends
            if meeting_end.time() > self.constraints.latest_meeting_end:
                break

            # Check if meeting fits in the window
            if meeting_end > window_end:
                break

            # Check if meeting overlaps with lunch break
            slot = TimeSlot(start=current_start, end=meeting_end)
            lunch_start = self.constraints.lunch_break_start
            lunch_end = self.constraints.lunch_break_end

            # Skip if slot contains lunch break
            if not (slot.contains_time(lunch_start) or slot.contains_time(lunch_end)):
                slots.append(slot)

            # Move to next possible slot (with minimum break)
            current_start = meeting_end + timedelta(
                minutes=self.constraints.min_break_between_meetings
            )

        return slots

    async def check_slot_availability(
        self,
        recruiter_email: str,
        proposed_slot: TimeSlot,
    ) -> bool:
        """
        Check if a specific time slot is available.

        Args:
            recruiter_email: Recruiter's email
            proposed_slot: Proposed time slot

        Returns:
            True if slot is available, False otherwise
        """

        # Get calendar events for the day
        day_start = datetime.combine(proposed_slot.start.date(), time(0, 0))
        day_end = day_start + timedelta(days=1)

        calendar_response = await get_calendar_events(
            user_email=recruiter_email,
            start_time=day_start,
            end_time=day_end,
        )

        busy_slots = self._parse_calendar_events(calendar_response.events)

        # Check if proposed slot overlaps with any busy slot
        for busy_slot in busy_slots:
            if proposed_slot.overlaps_with(busy_slot):
                return False

        # Check constraints
        if not self._slot_meets_constraints(proposed_slot, busy_slots):
            return False

        return True

    def _slot_meets_constraints(
        self,
        slot: TimeSlot,
        existing_slots: List[TimeSlot],
    ) -> bool:
        """Check if a slot meets all constraints."""

        # Check working hours
        if slot.start.time() < self.constraints.earliest_meeting_time:
            return False

        if slot.end.time() > self.constraints.latest_meeting_end:
            return False

        # Check lunch break
        lunch_start = self.constraints.lunch_break_start
        lunch_end = self.constraints.lunch_break_end

        if slot.contains_time(lunch_start) or slot.contains_time(lunch_end):
            return False

        # Check meeting duration
        duration = (slot.end - slot.start).total_seconds() / 60
        if abs(duration - self.constraints.meeting_duration_minutes) > 1:
            return False

        # Check max meetings per day
        same_day_slots = [
            s for s in existing_slots if s.start.date() == slot.start.date()
        ]

        if len(same_day_slots) >= self.constraints.max_meetings_per_day:
            return False

        # Check minimum break between meetings
        for existing_slot in same_day_slots:
            if slot.start < existing_slot.end:
                time_gap = (slot.start - existing_slot.end).total_seconds() / 60
                if 0 < time_gap < self.constraints.min_break_between_meetings:
                    return False

            if slot.end > existing_slot.start:
                time_gap = (existing_slot.start - slot.end).total_seconds() / 60
                if 0 < time_gap < self.constraints.min_break_between_meetings:
                    return False

        return True

    async def get_next_available_slot(
        self,
        recruiter_email: str,
        from_date: Optional[datetime] = None,
        max_days_ahead: int = 14,
    ) -> Optional[TimeSlot]:
        """
        Get the next available time slot for recruiter.

        Args:
            recruiter_email: Recruiter's email
            from_date: Start searching from this date (default: tomorrow)
            max_days_ahead: Maximum days to search ahead

        Returns:
            Next available slot or None if no slots found
        """

        if from_date is None:
            from_date = datetime.now() + timedelta(days=1)
            from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)

        end_date = from_date + timedelta(days=max_days_ahead)

        available_slots = await self.get_available_slots(
            recruiter_email=recruiter_email,
            start_date=from_date,
            end_date=end_date,
        )

        # Get earliest slot
        for date_str in sorted(available_slots.keys()):
            slots = available_slots[date_str]
            if slots:
                return slots[0]

        return None

    async def get_available_slots_summary(
        self,
        recruiter_email: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict:
        """
        Get summary of available slots with statistics.

        Returns:
            Dictionary with summary information
        """

        available_slots = await self.get_available_slots(
            recruiter_email=recruiter_email,
            start_date=start_date,
            end_date=end_date,
        )

        total_slots = sum(len(slots) for slots in available_slots.values())

        return {
            "recruiter_email": recruiter_email,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_available_slots": total_slots,
            "days_with_availability": len(available_slots),
            "available_slots_by_date": {
                date: [str(slot) for slot in slots]
                for date, slots in available_slots.items()
            },
            "constraints": {
                "earliest_meeting": self.constraints.earliest_meeting_time.strftime(
                    "%H:%M"
                ),
                "latest_meeting_end": self.constraints.latest_meeting_end.strftime(
                    "%H:%M"
                ),
                "lunch_break": f"{self.constraints.lunch_break_start.strftime('%H:%M')} - {self.constraints.lunch_break_end.strftime('%H:%M')}",
                "meeting_duration_minutes": self.constraints.meeting_duration_minutes,
                "min_break_between_meetings": self.constraints.min_break_between_meetings,
                "max_meetings_per_day": self.constraints.max_meetings_per_day,
            },
        }
