# Technical Documentation Style Guide

## Purpose

This skill provides a comprehensive ruleset for writing technical documentation with consistent quality, structure, and tone. Based on patterns from Next.js documentation, applicable to any programming language or framework.

## 1. Document Structure Principles

### 1.1 Table of Contents Hierarchy (3-Tier Information Architecture)

```
Level 1: Getting Started     → Minimize entry barrier, tutorial-focused
Level 2: Guides              → Use-case based, intermediate difficulty
Level 3: API Reference       → Complete technical specification, reference
```

**TOC Ordering Principles:**

| Priority | Criterion | Description |
|----------|-----------|-------------|
| 1st | Usage frequency | Most commonly used features first |
| 2nd | Dependencies | Topics requiring prior knowledge come later |
| 3rd | Complexity | Simple → Complex, progressive difficulty |

**Example:**
```
Installation → Project Structure → Basic Usage → Advanced Patterns → API Reference
```

### 1.2 Section Naming Conventions

```markdown
# Page Title (singular noun/gerund)
## What is [Feature]?              ← Concept definition
## How [Feature] Works             ← Mechanism explanation
## Creating/Using [Feature]        ← Hands-on guide
## [Feature] Options               ← API/options detail
## Troubleshooting                 ← Problem resolution (optional)
```

**Naming Rules:**
- **Use gerunds**: `Getting Started`, `Building Applications`, `Configuring`
- **Use nouns**: `Authentication`, `Routing`, `Data Models`
- **Avoid verb phrases**: ~~`How to Authenticate`~~ → `Authentication`

---

## 2. Tone and Voice Guide

### 2.1 Base Voice

```
✓ Second person direct: "You can create...", "Run the following command"
✓ Imperative (action-oriented): "Create a new file", "Install the package"
✓ Present tense: "The function returns...", "This method accepts..."
✗ Avoid: "We will...", "Let's...", "You should probably..."
```

### 2.2 Tone Spectrum by Document Type

| Document Type | Tone | Characteristics | Example |
|---------------|------|-----------------|---------|
| Getting Started | **Concise + Action-oriented** | Minimal words, immediate action | "Run the following command" |
| Guides | Practical + Direct | Step-by-step, use-case focused | "To enable this feature, add..." |
| API Reference | Technical + Neutral | Precise, specification-style | "Returns a value of type X when..." |
| Troubleshooting | Empathetic + Solution-focused | Problem → Cause → Solution | "If you encounter this error, check..." |

**Key distinction:**
- Getting Started: Focus on **doing**, not explaining
- Guides: Balance between **doing** and **understanding**
- API Reference: Focus on **completeness** and **accuracy**

### 2.3 Technical Term Handling

```markdown
<!-- First occurrence: bold + definition -->
A **middleware** is a function that intercepts requests before they reach your handler.

<!-- Subsequent uses: plain text -->
The middleware can modify the request object.

<!-- External concept reference: provide link -->
Learn more about [dependency injection](external-link).
```

---

## 3. Content Brevity Principles

### 3.1 Paragraph Writing Rules

```
✓ Maximum 3 sentences per paragraph
✓ 1 sentence = 1 concept
✓ Lead with the key point (inverted pyramid)
```

**Good:**
> The cache stores frequently accessed data in memory. It reduces database load and improves response times.

**Bad:**
> The caching mechanism that we have implemented in this library is designed to store data that is frequently accessed by the application in memory, which can help to reduce the load on your database server and also improve the overall response times that your users experience when using the application.

### 3.2 List Usage Guidelines

```markdown
<!-- 3+ items → use bullet list -->
The library supports:
- MySQL
- PostgreSQL
- SQLite

<!-- 2 or fewer → inline enumeration -->
The library supports MySQL and PostgreSQL.

<!-- Order matters → use numbered list -->
1. Install the package
2. Configure the connection
3. Run migrations
```

---

## 4. Code Example Rules

### 4.1 Basic Structure

````markdown
```<language> filename="<path/to/file>"
// code content
```
````

**Required Elements:**
- **Language specification**: Always specify for syntax highlighting
- **File path**: Use `filename` attribute to indicate location
- **Highlight**: Emphasize key lines (optional)

**Language-Specific Examples:**

```python filename="src/handlers/user.py"
def get_user(user_id: int) -> User:
    return db.query(User).filter_by(id=user_id).first()
```

```go filename="internal/handlers/user.go"
func GetUser(id int) (*User, error) {
    return db.FindUserByID(id)
}
```

### 4.2 Code Comment Principles

```python
# ✓ Explain WHY
# Retry 3 times to handle transient network failures
response = fetch_with_retry(url, max_retries=3)

# ✗ Explain WHAT only - avoid
# Call fetch_with_retry with max_retries set to 3
response = fetch_with_retry(url, max_retries=3)
```

### 4.3 Code Example Complexity Progression

```
Stage 1: Minimal working example
Stage 2: Common use case
Stage 3: Advanced configuration
```

---

## 5. Information Box Types

### 5.1 Good to know (General info/tips)

```markdown
> **Good to know**:
> - This feature requires version 2.0 or later
> - The default timeout is 30 seconds
```

### 5.2 Warning (Cautions)

```markdown
> **Warning**: This operation is irreversible. Back up your data before proceeding.
```

### 5.3 Note (References)

```markdown
> **Note**: On Windows, use backslashes for file paths.
```

### 5.4 Tip (Useful tips)

```markdown
> **Tip**: Use environment variables to avoid hardcoding credentials.
```

### 5.5 Version (Version info)

```markdown
> **Version**: This feature was introduced in v3.2.0
```

---

## 6. Visual Aid Usage

### 6.1 Diagram Selection Guide

| Situation | Diagram Type |
|-----------|--------------|
| File/folder structure | Tree diagram |
| Data/request flow | Flowchart |
| Time-sequenced process | Sequence diagram |
| Option/feature comparison | Table |
| Architecture composition | Block diagram |
| State transitions | State diagram |

### 6.2 Diagram + Text Combination Principle

```markdown
![Request Flow Diagram](/images/request-flow.png)

1. **Client sends request**: The request enters the system
2. **Middleware processes**: Authentication and validation occur
3. **Handler executes**: Business logic runs
4. **Response returns**: Result sent back to client
```

**Principle:** Never use diagrams alone; always accompany with text explanation

---

## 7. Linking and Reference Strategy

### 7.1 Internal Link Patterns

```markdown
<!-- Action-based (recommended) -->
Learn how to [configure authentication](/docs/auth)

<!-- Reference-based -->
See the [`connect()` function reference](/docs/api/connect)

<!-- Related concepts -->
Related: [Error Handling](/docs/errors), [Logging](/docs/logging)
```

### 7.2 Link Density Principles

```
✓ Maximum 2-3 links per paragraph
✓ Link only on first occurrence of a concept
✓ No repeated links to same target on same page
✗ Avoid inserting links in every sentence
```

---

## 8. API Reference Template

### 8.1 Format A: Table-based (Simple APIs with few options)

```markdown
# function_name

[One sentence describing the function's purpose]

## Signature

\`\`\`<language>
function_name(param1: Type, param2: Type, options?: Options) -> ReturnType
\`\`\`

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `param1` | `string` | Yes | - | Parameter description |
| `param2` | `int` | No | `10` | Parameter description |

## Returns

`ReturnType` - Description of return value

## Errors/Exceptions

| Error | Condition |
|-------|-----------|
| `ValueError` | When param1 is empty |
| `TimeoutError` | When request times out |

## Example

\`\`\`<language> filename="examples/usage.ext"
// Real usage example
result = function_name("value", 5)
\`\`\`
```

---

## 9. Quality Checklist

### Post-Writing Verification:

**Structure Verification:**
```
□ Does the first sentence contain the key point (conclusion)?
□ Are there no paragraphs with more than 3 sentences?
□ Does the TOC follow logical ordering (frequency/dependencies/complexity)?
□ Do section titles follow consistent naming conventions?
```

**Code Verification:**
```
□ Is a language specified for all code blocks?
□ Do code examples include filename attributes?
□ Is the code copy-paste executable?
□ Are language/tool variants provided as tabs? (where applicable)
```

**Terminology and Links Verification:**
```
□ Are technical terms defined on first occurrence?
□ Are internal links action-based?
□ Are there no more than 3 links per paragraph?
□ Are there no repeated links to the same target?
```

---

## 10. Anti-Patterns to Avoid

### Writing Anti-Patterns
- ❌ **Wall of text**: Paragraphs longer than 3 sentences
- ❌ **Jargon soup**: Technical terms without definition
- ❌ **Passive voice overuse**: "The file is created" → "Create the file"
- ❌ **Burying the lede**: Key info hidden in middle of paragraph

### Structure Anti-Patterns
- ❌ **Flat hierarchy**: No clear section organization
- ❌ **Missing prerequisites**: Advanced topics without links to basics
- ❌ **Orphan pages**: No navigation to related content

### Code Example Anti-Patterns
- ❌ **Incomplete snippets**: Code that can't run as-is
- ❌ **Missing context**: No filename or file path
- ❌ **Single tool assumption**: Only showing npm when pip/cargo also apply
