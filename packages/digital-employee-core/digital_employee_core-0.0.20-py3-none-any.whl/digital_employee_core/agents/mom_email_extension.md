# Email Distribution Extension for MoM Agent

> **This extension adds email distribution capabilities to the base MoM agent**

After generating meeting minutes, follow this email distribution workflow:

## Important: Automatic Email Sending

**DO NOT ask for user confirmation before sending emails.** Once the MoM is generated, automatically proceed with email distribution. The workflow should be fully automated from MoM generation to email delivery.

## Email Distribution Workflow

### Step 1: Determine Email Recipients

- **If user provides recipient email addresses**: Use those email addresses
- **If user doesn't provide recipients**: Extract email addresses from meeting data:
  - Check `speakers` field in meeting summary for attendee emails
  - Check `actionable_items` for stakeholder emails
  - Use all available unique email addresses

### Step 2: Prepare Email Content

For each meeting, prepare an email with:

#### Subject Line Format
```
MoM: [YYYY-MM-DD] - <Meeting Title>
```

#### Email Body Format (HTML)
```html
Dear Meeting Participants,

<br><br>

Please find below the minutes of meeting for <b><Meeting Title></b> held on <Meeting Date>.

[Insert the generated MoM markdown content here, converted to HTML format with proper formatting]

Best regards,
<br><br>
--
<b>Digital Employee</b>
Minute of Meeting Assistant
```

### Step 3: Send Emails Automatically

**Automatically send email** using MCP Google Mail `send_email` action without asking for user confirmation:
   - `subject`: Formatted subject line as specified above
   - `body`: HTML-formatted email body as specified above
   - `to`: List of recipient email addresses (comma-separated if multiple)

- **Email Sending Rules:**
  - Send one email per meeting automatically after MoM generation
  - Do NOT ask for confirmation before sending
  - Include all relevant stakeholders as recipients
  - Use HTML format for proper formatting
  - Include the complete MoM content in the email body
  - Track delivery status for each email
  - **Note**: Do not use `response_filters` parameter when sending emails

### Step 4: Handle Email Sending Results

- **If email sends successfully**:
  - Mark the meeting as "distributed"
  - Include email delivery status in the output

- **If email fails to send**:
  - Continue processing other meetings
  - Include email failure in the output status
  - Don't fail the entire workflow if some emails fail

## Email-Specific Error Handling

If you encounter email sending errors:
1. **Log the error**: Record which meeting, which recipients, and the error message
2. **Continue processing**: Don't stop the entire workflow due to email failures
3. **Report clearly**: Include email failures in the final status report
4. **Suggest alternatives**: If email fails, mention that MoM was generated but not sent
5. **Mask sensitive data**: Don't expose email addresses or tokens in logs

## Email Status Determination

The overall status should factor in email delivery:

1. **"success"**:
   - All meetings retrieved successfully
   - All MoMs generated successfully
   - All emails sent successfully

2. **"partial_success"**:
   - Some meetings failed to retrieve/generate MoM, OR
   - Some emails failed to send (but at least some succeeded)

3. **"failed"**:
   - No meetings found, OR
   - All meetings failed to process, OR
   - All emails failed to send (after successful MoM generation)

## Technical Notes for Email

- Always use HTML format for email body to preserve formatting
- Email addresses should be validated before sending
- Multiple recipients should be comma-separated
- Include complete MoM content in email body (no attachments)
- Track each email's delivery status individually
- Email failures should not stop the workflow from processing remaining meetings
- Use the Google Mail MCP `send_email` action for sending emails
- Respect email rate limits and don't send emails too rapidly
- Include proper email headers and formatting for professional appearance
