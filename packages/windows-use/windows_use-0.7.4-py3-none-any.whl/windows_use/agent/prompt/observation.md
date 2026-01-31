```xml
<input>
    <agent_state>
        Steps: {steps}/{max_steps}

        Observation: {observation}
    <agent_state>
    
    <desktop_state>
        [Begin of Desktop]
        Active Desktop: {active_desktop}
        Cursor Location: {cursor_location}
        [Begin of Window Info]
        Foreground Window: {active_window}

        Background Windows:
        {windows}
        [End of Window Info]
        
        [Begin of Screen]
        List of Interactive Elements:
        {interactive_elements}

        List of Scrollable Elements:
        {scrollable_elements}
        [End of Screen]

        [Begin of Virtual Desktops]
        Virtual Desktops:
        {desktops}
        [End of Virtual Desktops]
        [End of Desktop]
    <desktop_state>

    <user_query>
        {query}
    </user_query>
</input>
```

Based on the new Desktop State, give the next action to be taken by you in JSON format.