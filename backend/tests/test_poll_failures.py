def test_poll_failures():
    # basic shape
    from live_engagement_coach.services import polls
    assert polls.PollService
