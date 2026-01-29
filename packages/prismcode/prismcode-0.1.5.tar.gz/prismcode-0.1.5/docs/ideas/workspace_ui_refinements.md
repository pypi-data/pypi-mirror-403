# Workspace UI Refinements

## Overview
Align the new workspace UI styling with the original Mobius UI for visual consistency.

## Requirements

### 1. Remove All Emojis
Replace emoji icons with simple text/symbol equivalents or CSS-based indicators:
- `📌` focus icon → `●` (accent colored dot)
- `📁` explorer icon → text or CSS icon
- `💬` sessions icon → text or CSS icon
- `⚙` settings icon → text or CSS icon
- `⌨` terminal icon → text or CSS icon

### 2. Match Original Styling
Copy the smooth, rounded styles from the original UI:
- Border radius values (`--radius: 6px`)
- Button padding and sizing
- Input field styling
- Color scheme consistency
- Font sizes and weights
- Subtle borders and backgrounds

### 3. Send Button Sizing
- Match the send button height to the textarea input height
- Proper vertical alignment with input field
- Consistent padding with original UI buttons

### 4. Visual Elements to Match
From original `style.css`:
- `.btn` styling (padding, border-radius, transitions)
- `.message-input` styling
- `.input-group` layout
- Color variables usage
- Tool pill styling (`.message-tool`)
- Smooth animations and transitions

### 5. Component Consistency
Ensure these workspace components match original aesthetic:
- Chat input area
- Message bubbles
- Tool indicators
- Activity indicators
- Focus bar
- Tab styling
- Sidebar items

## Reference Files
- Original: `static/css/style.css`, `static/js/app.js`, `templates/index.html`
- Workspace: `static/workspace/css/components/chat.css`, `static/workspace/css/base.css`
