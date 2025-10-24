# Text Selection Context Tool - Feature Specifications

## Feature: Text Selection Context Detection

**As a** user working with various documents and applications  
**I want** contextual information to appear when I select text  
**So that** I can quickly access related information and take relevant actions

---

## Scenario: First text selection with no existing data

```gherkin
Given I have no previous data in the context system
When I select the text "JT-346"
Then I should see a context popup
And the popup should show "No previous records found"
And I should see action buttons: [Save Snippet, Ask AI, Web Search, Add Context]
And the system should detect the format as "Jira ticket format"
And I should see suggested actions for project management tools
```

---

## Scenario: Text selection with existing related content

```gherkin
Given I have existing data:
  | Type    | Content                           | Tags                    |
  | snippet | "JT-344 login timeout issues"    | JT-344, auth, timeout   |
  | contact | "Sarah M - Auth Team Lead"        | auth, teammate          |
  | snippet | "JT-3xx series auth overhaul"    | auth, project-planning  |

When I select the text "JT-346"
Then I should see a context popup
And I should see "Related Found:" section with:
  | Item                              | Context                    |
  | JT-344: "login timeout issues"   | saved 3 days ago          |
  | Sarah M. (auth team lead)         | last messaged about JT-344|
  | "JT-3xx series auth overhaul"    | saved last week           |
And I should see "Smart Context:" showing:
  | Field   | Value                        |
  | Project | Authentication System Redesign |
  | Status  | In Progress                   |
And I should see action buttons: [Save Snippet, Open in Jira, Ask AI, Deep Search, Copy]
```

---

## Scenario: Saving a snippet with auto-tagging and linking

```gherkin
Given I have existing contacts: "Sarah Mitchell - Auth Team Lead"
And I have existing tickets: "JT-344 - login timeout issues"
When I use the save command "/save I tried to fix JT-344 with a new cert but it didn't fix the problem"
Then the system should save the snippet with auto-tags: [JT-344, troubleshooting, certificates, auth-issues]
And the system should create links to: [Sarah Mitchell, JT-344, Authentication System project]
And I should see confirmation: "Saved: snippet with auto-tags and links"
And the system should update the knowledge graph with new connections
```

---

## Scenario: Contact detection and auto-suggestions

```gherkin
Given I have existing contact: "Sarah Mitchell" with context "Auth Team Lead"
When I select the text "Sarah M"
Then I should see a context popup
And I should see "Contact Found:" with full details:
  | Field        | Value                              |
  | Name         | Sarah Mitchell                     |
  | Role         | Auth Team Lead                     |
  | Email        | sarah.m@company.com               |
  | Last Contact | 3 days ago via Slack about JT-344|
  | Next Event   | Meeting tomorrow 2pm              |
And I should see suggested actions: [Save Snippet, Message on Teams, Send Email, Schedule Meeting, Ask AI]
And the actions should be communication-focused due to contact type detection
```

---

## Scenario: Cross-context knowledge building

```gherkin
Given I have existing data:
  | Type    | Content                    | Links                |
  | contact | Sarah Mitchell             | JT-344, auth-team    |
  | ticket  | JT-344                     | Sarah, timeout-issue |
  | domain  | Authentication             | JT-344, certificates |

When I select the text "authentication"
Then I should see a context popup with "Related Found:" showing clustered information:
  | Category        | Items                           |
  | Active Project  | Authentication System Redesign  |
  | Team Contact    | Sarah Mitchell - Auth Team Lead |
  | Current Issues  | JT-344: Login timeout issues   |
  | Your Work       | Cert fix attempt (failed)      |
And I should see "Smart Insights:" with:
  | Insight | Description                                    |
  | Pattern | 3 auth-related tickets suggest systemic issue |
  | Blocker | Certificate fix didn't work                    |
  | Timing  | Tomorrow's meeting with Sarah = good timing    |
And I should see strategic actions: [View Full Auth Timeline, Prep Sarah Meeting Notes, Find Similar Past Issues]
```

---

## Scenario: New information with knowledge graph updates

```gherkin
Given I have no data about "Magnus Sjöstrand"
When I select the text "I met Magnus Sjöstrand today, he was talking about a europe trip"
Then I should see a context popup
And I should see "New Contact Detected: Magnus Sjöstrand"
And I should see "Topic: Europe trip"
And I should see suggested actions: [Save Snippet, Add Contact, Trip Details, Ask AI, Follow Up Reminder]
When I choose "Add Contact"
Then the system should save: "Magnus Sjöstrand - Met today, discussed Europe trip"
And the system should add Magnus to the knowledge graph
And the system should tag the interaction with: [travel, europe, new-contact]
```

---

## Scenario: Ambiguous text handling

```gherkin
Given I have multiple contexts for abbreviations
When I select the text "HUD"
Then I should see a context popup with "Ambiguity Detected"
And I should see "HUD could mean many things without surrounding text"
And I should see quick disambiguation options:
  | Option  | Description              |
  | UI/UX   | Heads-up display design  |
  | Gaming  | Game interface element   |
  | Auto    | Car dashboard display    |
  | Other   | Specify meaning          |
And I should see actions: [Save Snippet, Ask AI: "What's HUD in this context?", Add Context Note]
```

---

## Scenario: System learning and adaptation

```gherkin
Given I have been working frequently with "authentication" topics
And I have saved multiple auth-related snippets
And I have regular contact with Sarah Mitchell about auth issues
When I select any auth-related text
Then the system should prioritize auth-related contexts in results
And the system should show patterns like "You've been focusing on auth systems lately"
And the system should suggest proactive actions based on learned patterns
And response time should be optimized for frequent contexts
```

---

## Background: System Context State

```gherkin
Background:
  Given the context system is running
  And I have text selection monitoring enabled
  And the system has access to:
    | Data Type | Source           |
    | contacts  | local storage    |
    | snippets  | local storage    |
    | projects  | local storage    |
    | meetings  | calendar access  |
  And popup rendering is configured for non-intrusive display
  And all actions are available with proper permissions
```