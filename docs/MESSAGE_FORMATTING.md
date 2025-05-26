# Message Formatting

Telert provides formatting options for messages, with different levels of support across providers.

## Telegram Formatting

Telegram fully supports rich formatting with both HTML and Markdown options:

```bash
# Send a message with HTML formatting (auto-detected)
telert send "Project build <b>completed</b> with <i>zero</i> errors"

# Or explicitly specify HTML parsing mode
telert send --parse-mode HTML "Project build <b>completed</b> with <i>zero</i> errors"

# Send with Markdown formatting (auto-detected)
telert send "Project build **completed** with *zero* errors"

# Or explicitly specify Markdown parsing mode
telert send --parse-mode MarkdownV2 "Project build **completed** with *zero* errors"
```

### Supported HTML tags in Telegram

- `<b>`, `<strong>` - Bold text
- `<i>`, `<em>` - Italic text
- `<u>` - Underlined text
- `<s>`, `<strike>`, `<del>` - Strikethrough text
- `<code>` - Monospace text
- `<pre>` - Pre-formatted text
- `<a href="...">` - Links


### Supported Markdown formatting in Telegram

- `**text**` or `__text__` - Bold text
- `*text*` or `_text_` - Italic text
- `` `text` `` - Monospace text
- ```text``` - Pre-formatted text
- `~~text~~` - Strikethrough text
- `[link text](https://example.com)` - Links


## Cross-Platform Formatting

For providers that don't natively support HTML or Markdown formatting (Slack, Teams, Discord, Pushover, etc.), Telert automatically strips the formatting tags while preserving the content. This ensures that your messages remain readable across all providers.

### HTML Tag Stripping
When a message with HTML tags is sent to non-Telegram providers, Telert extracts the text content while removing the tags.

### Markdown Conversion
When a message with Markdown formatting is sent to non-Telegram providers, Telert removes the formatting characters while keeping the text content.

## Examples

```bash
# When sending to Telegram, this shows bold and italic text
# When sending to other providers, formatting is stripped but text is preserved
telert send --provider "telegram,slack,discord" "Project <b>completed</b> with <i>zero</i> errors"

# Same with Markdown formatting
telert send --provider "telegram,pushover,teams" "Project **completed** with *zero* errors" 

# Send to multiple providers at once with automatic formatting handling
telert send --all-providers "Build <b>successful</b>: version 1.0.0 released!"
```

Note: Telert intelligently handles the formatting based on each provider's capabilities. You only need to format your message once, and Telert will ensure it displays properly across all providers. This makes it easy to send the same notification to multiple services without worrying about formatting compatibility.
