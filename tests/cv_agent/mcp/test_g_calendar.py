import asyncio
from datetime import datetime, timedelta

from dotenv import load_dotenv

from cv_agent.mcp.g_calendar import schedule_interview

load_dotenv()


async def main():
    """Test the schedule_interview method."""

    # Configure your test parameters
    user_email = "recruiter@gmail.com"  # Replace with your actual email

    print("=" * 80)
    print("Testing Schedule Interview")
    print("=" * 80)

    try:
        # Schedule interview for tomorrow at 2 PM
        interview_start = datetime.now() + timedelta(days=1)
        interview_start = interview_start.replace(
            hour=14, minute=0, second=0, microsecond=0
        )
        interview_end = interview_start + timedelta(hours=1)

        print(f"\nScheduling interview...")
        print(f"Organizer: {user_email}")
        print(f"Candidate: John Doe (john.doe@example.com)")
        print(f"Position: Senior Software Engineer")
        print(
            f"Date & Time: {interview_start.strftime('%Y-%m-%d %H:%M')} - {interview_end.strftime('%H:%M')}"
        )
        print(f"Duration: 1 hour")
        print("-" * 80)

        interview_response = await schedule_interview(
            user_email=user_email,
            candidate_name="John Doe",
            candidate_email="candidate@gmail.com",
            position="Senior Software Engineer",
            start_time=interview_start,
            end_time=interview_end,
            timezone="Europe/Kyiv",
            interviewer_emails=None,
            add_google_meet=True,
            description="Technical interview focusing on system design and coding skills.",
        )

        if interview_response.success:
            print(f"\n✅ Successfully scheduled interview!")
            print(f"\nEvent Details:")
            print(f"  Event ID: {interview_response.event_id}")
            print(f"  Title: {interview_response.summary}")
            print(f"  Start: {interview_response.start_time}")
            print(f"  End: {interview_response.end_time}")
            print(f"  Attendees: {', '.join(interview_response.attendees)}")
            print(f"  Google Meet: {interview_response.google_meet_link or 'N/A'}")
            print(f"  Calendar Link: {interview_response.event_link}")
            if interview_response.message:
                print(f"  Message: {interview_response.message}")
        else:
            print(f"\n❌ Failed to schedule interview")
            print(f"  Message: {interview_response.message}")

    except Exception as e:
        print(f"\n❌ Error scheduling interview: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
