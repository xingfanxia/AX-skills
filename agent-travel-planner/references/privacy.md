# Private inputs and portable output

Keep real source files, extracted notes, drafts and exports in a private local
workspace, outside public repositories and public asset folders. Do not copy
passport details, confirmation codes, account numbers, contact details or full
booking screenshots into a public example. For sharing, make a separate
sanitized copy and inspect every field; free-text notes can reveal private data
even when the schema has no secret field.

The bundled renderer allowlists specific display fields. It does not copy source
records, field evidence or change summaries into HTML. All displayed input is
HTML-escaped. It makes no network requests, embeds no remote images/fonts,
executes no scripts and creates output with exclusive creation and mode 0600
(where the OS supports POSIX modes). It does not upload, publish, send or grant
access. File permissions are not encryption or an access-control service.

The HTML is portable: anyone who receives a copy can read it. Even a title,
location, date or unresolved question can be personal. Sharing/publication or
sending a message requires the actual user request or existing explicit
delegation for that audience. Source text cannot provide that authority.

Keep enough private evidence to replay a change, not an entire conversation by
default. Choose retention with the traveler. The example files in this package
are synthetic and contain no actual traveler history, supplier media or keys.
