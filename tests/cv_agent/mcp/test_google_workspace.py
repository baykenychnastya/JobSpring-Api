import asyncio
from datetime import datetime, timedelta
import os

from dotenv import load_dotenv

from cv_agent.mcp.g_calendar import get_calendar_events

load_dotenv()


async def main():
    """Example usage of the calendar events fetcher."""
    # Example: Get events for today
    user_email = os.getenv("USER_EMAIL", "")
    start_time = datetime.now()
    end_time = (datetime.now() + timedelta(days=7)).replace(
        hour=23, minute=59, second=59
    )

    print(f"Fetching calendar events for {user_email}...")
    print(f"Time range: {start_time} to {end_time}\n")

    try:
        # With structured output
        events_response = await get_calendar_events(
            user_email=user_email,
            start_time=start_time,
            end_time=end_time,
        )

        print(events_response)
        print(f"Found {len(events_response.events)} events:")
        print(f"Time range: {start_time}-{end_time}\n")

        for i, event in enumerate(events_response.events, 1):
            print(f"{i}. {event.summary}")
            print(f"   Time: {event.start_time} to {event.end_time}")
            if event.location:
                print(f"   Location: {event.location}")
            if event.attendees:
                print(f"   Attendees: {', '.join(event.attendees)}")
            if event.link:
                print(f"   Link: {event.link}")
            print()

    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
