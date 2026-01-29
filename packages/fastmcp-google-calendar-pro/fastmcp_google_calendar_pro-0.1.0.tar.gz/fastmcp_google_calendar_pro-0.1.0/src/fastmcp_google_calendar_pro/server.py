"""
FastMCP Google Calendar Pro

Manage Google Calendar events with tools for creating, listing, searching, and checking availability
"""

from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("FastMCP Google Calendar Pro")

@mcp.tool()
def create_event(title: str, start_time: str, end_time: str, description: str, location: str, attendees: list) -> str:
    """Create a new event in Google Calendar

    Args:
        title: The title/summary of the event
        start_time: Start time in ISO format (e.g., '2024-01-15T10:00:00')
        end_time: End time in ISO format (e.g., '2024-01-15T11:00:00')
        description: Event description or notes
        location: Event location
        attendees: List of attendee email addresses

    Returns:
        Event ID and confirmation details
    """
    import os
    import json
    from datetime import datetime
    
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        creds_info = {
            'token': os.getenv('GOOGLE_TOKEN'),
            'refresh_token': os.getenv('GOOGLE_REFRESH_TOKEN'),
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET')
        }
        
        if not all(creds_info.values()):
            return "Error: Missing Google Calendar API credentials. Please set GOOGLE_TOKEN, GOOGLE_REFRESH_TOKEN, GOOGLE_CLIENT_ID, and GOOGLE_CLIENT_SECRET environment variables."
        
        creds = Credentials.from_authorized_user_info(creds_info)
        service = build('calendar', 'v3', credentials=creds)
        
        event_body = {
            'summary': title,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'}
        }
        
        if description:
            event_body['description'] = description
        if location:
            event_body['location'] = location
        if attendees:
            event_body['attendees'] = [{'email': email} for email in attendees]
        
        event = service.events().insert(calendarId='primary', body=event_body).execute()
        return f"Event '{title}' created successfully!\nID: {event['id']}\nStart: {start_time}\nEnd: {end_time}\nLink: {event.get('htmlLink', 'N/A')}"
        
    except ImportError:
        return "Error: Google Calendar API library not installed. Please install: pip install google-auth google-auth-oauthlib google-api-python-client"
    except Exception as e:
        return f"Error creating event: {str(e)}"

@mcp.tool()
def list_upcoming_events(max_results: int, days_ahead: int) -> str:
    """List upcoming events from Google Calendar

    Args:
        max_results: Maximum number of events to return (default: 10)
        days_ahead: Number of days ahead to look (default: 7)

    Returns:
        List of upcoming events with details
    """
    import os
    from datetime import datetime, timedelta
    
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        creds_info = {
            'token': os.getenv('GOOGLE_TOKEN'),
            'refresh_token': os.getenv('GOOGLE_REFRESH_TOKEN'),
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET')
        }
        
        if not all(creds_info.values()):
            return "Error: Missing Google Calendar API credentials. Please set required environment variables."
        
        creds = Credentials.from_authorized_user_info(creds_info)
        service = build('calendar', 'v3', credentials=creds)
        
        max_results = max_results or 10
        days_ahead = days_ahead or 7
        
        now = datetime.utcnow()
        time_max = now + timedelta(days=days_ahead)
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now.isoformat() + 'Z',
            timeMax=time_max.isoformat() + 'Z',
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f'No upcoming events found in the next {days_ahead} days.'
        
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            location_text = f" at {event.get('location', '')}" if event.get('location') else ''
            event_list.append(f"• {event.get('summary', 'No Title')} - {start[:19].replace('T', ' ')}{location_text}")
        
        return f"Found {len(event_list)} upcoming events:\n" + "\n".join(event_list)
        
    except ImportError:
        return "Error: Google Calendar API library not installed. Please install: pip install google-auth google-auth-oauthlib google-api-python-client"
    except Exception as e:
        return f"Error listing events: {str(e)}"

@mcp.tool()
def check_availability(start_time: str, end_time: str) -> str:
    """Check if a time slot is available in the calendar

    Args:
        start_time: Start time to check in ISO format
        end_time: End time to check in ISO format

    Returns:
        Availability status and any conflicts
    """
    import os
    from datetime import datetime
    
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        creds_info = {
            'token': os.getenv('GOOGLE_TOKEN'),
            'refresh_token': os.getenv('GOOGLE_REFRESH_TOKEN'),
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET')
        }
        
        if not all(creds_info.values()):
            return "Error: Missing Google Calendar API credentials. Please set required environment variables."
        
        creds = Credentials.from_authorized_user_info(creds_info)
        service = build('calendar', 'v3', credentials=creds)
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"✅ Time slot {start_time[:19].replace('T', ' ')} to {end_time[:19].replace('T', ' ')} is AVAILABLE"
        
        conflicts = []
        for event in events:
            event_start = event['start'].get('dateTime', event['start'].get('date'))
            event_end = event['end'].get('dateTime', event['end'].get('date'))
            conflicts.append(f"• {event.get('summary', 'Untitled')} ({event_start[:19].replace('T', ' ')} - {event_end[:19].replace('T', ' ')})")
        
        return f"❌ Time slot {start_time[:19].replace('T', ' ')} to {end_time[:19].replace('T', ' ')} has {len(conflicts)} CONFLICT(S):\n" + "\n".join(conflicts)
        
    except ImportError:
        return "Error: Google Calendar API library not installed. Please install: pip install google-auth google-auth-oauthlib google-api-python-client"
    except Exception as e:
        return f"Error checking availability: {str(e)}"

@mcp.tool()
def search_events(query: str, max_results: int) -> str:
    """Search for events in Google Calendar

    Args:
        query: Search query (title, description, location, etc.)
        max_results: Maximum number of results to return (default: 10)

    Returns:
        List of matching events
    """
    import os
    from datetime import datetime
    
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        creds_info = {
            'token': os.getenv('GOOGLE_TOKEN'),
            'refresh_token': os.getenv('GOOGLE_REFRESH_TOKEN'),
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET')
        }
        
        if not all(creds_info.values()):
            return "Error: Missing Google Calendar API credentials. Please set required environment variables."
        
        creds = Credentials.from_authorized_user_info(creds_info)
        service = build('calendar', 'v3', credentials=creds)
        
        max_results = max_results or 10
        
        events_result = service.events().list(
            calendarId='primary',
            q=query,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"No events found matching '{query}'"
        
        result_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            location_text = f" at {event.get('location', '')}" if event.get('location') else ''
            event_id = event['id'][:8] + '...'
            result_list.append(f"• {event.get('summary', 'No Title')} - {start[:19].replace('T', ' ')}{location_text} (ID: {event_id})")
        
        return f"Found {len(result_list)} events matching '{query}':\n" + "\n".join(result_list)
        
    except ImportError:
        return "Error: Google Calendar API library not installed. Please install: pip install google-auth google-auth-oauthlib google-api-python-client"
    except Exception as e:
        return f"Error searching events: {str(e)}"

@mcp.resource("calendar://settings")
def calendar_settings() -> str:
    """Get current calendar settings and configuration"""
    import os
    config = {
        'calendar_id': 'primary',
        'timezone': 'UTC',
        'default_duration': '1 hour',
        'reminder_minutes': 15,
        'has_credentials': bool(os.getenv('GOOGLE_TOKEN'))
    }
    return f"Calendar Configuration:\n" + "\n".join([f"• {k}: {v}" for k, v in config.items()])

@mcp.resource("calendar://auth")
def auth_status() -> str:
    """Check Google Calendar API authentication status"""
    import os
    required_vars = ['GOOGLE_TOKEN', 'GOOGLE_REFRESH_TOKEN', 'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']
    status = {}
    for var in required_vars:
        status[var] = 'Set' if os.getenv(var) else 'Missing'
    
    missing = [k for k, v in status.items() if v == 'Missing']
    if missing:
        return f"❌ Authentication incomplete. Missing: {', '.join(missing)}\n\nTo set up Google Calendar API access:\n1. Go to Google Cloud Console\n2. Create a project and enable Calendar API\n3. Create OAuth2 credentials\n4. Set the environment variables"
    else:
        return "✅ All required authentication credentials are configured."

@mcp.prompt()
def meeting_scheduler(meeting_type: str, duration: str) -> str:
    """Generate a prompt for scheduling meetings with specific requirements

    Args:
        meeting_type: Type of meeting (e.g., 'team standup', 'client call', 'interview')
        duration: Meeting duration (e.g., '30 minutes', '1 hour')
    """
    return f"""I need to schedule a {meeting_type} that will last {duration}. Please help me:

1. Find an available time slot in my calendar
2. Create the calendar event with appropriate details
3. Consider the best time based on my existing schedule

What information do you need from me to schedule this meeting effectively?"""

@mcp.prompt()
def calendar_review(time_period: str) -> str:
    """Generate a prompt for reviewing and analyzing calendar events

    Args:
        time_period: Time period to review (e.g., 'this week', 'next month', 'last quarter')
    """
    return f"""Please review my calendar for {time_period} and provide:

1. A summary of all scheduled events
2. Analysis of time allocation (meetings vs. free time)
3. Identification of any scheduling conflicts
4. Suggestions for better time management

Focus on helping me optimize my schedule and identify patterns in my calendar usage."""

@mcp.prompt()
def event_planner(event_name: str, attendee_count: str) -> str:
    """Generate a prompt for planning complex events with multiple considerations

    Args:
        event_name: Name or type of event to plan
        attendee_count: Expected number of attendees
    """
    return f"""I'm planning '{event_name}'{attendee_count and f' with approximately {attendee_count} attendees' or ''}. Help me create a comprehensive calendar event by:

1. Suggesting optimal timing based on my current schedule
2. Recommending event duration and structure
3. Planning any preparation time needed before the event
4. Setting up appropriate reminders and notifications
5. Creating a detailed description and agenda

What additional details do you need to make this event successful?"""

def main():
    """Entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
