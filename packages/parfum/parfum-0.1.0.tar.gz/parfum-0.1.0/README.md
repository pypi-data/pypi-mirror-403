# Parfum

Strip the sensitive stuff from your chat data before you train on it.

I built Parfum because I got tired of manually cleaning up PII from datasets before fine-tuning. The name's a play on how perfume covers up smells—this library covers up personal info while keeping your data useful.

## What's this for?

You've got chat logs, customer support transcripts, or conversational data you want to train a model on. Problem is, it's full of emails, phone numbers, credit cards, and who knows what else. You need that gone, but you still want the conversations to make sense.

That's what Parfum does. It finds the sensitive bits and replaces them however you want—placeholders, masked versions, fake data, or just nukes them entirely.

## Getting started

```bash
pip install parfum
```

Want to catch people's names and locations too? You'll need spaCy:

```bash
pip install parfum[ner]
python -m spacy download en_core_web_sm
```

The NER stuff is optional. Without it you still get emails, phones, credit cards, SSNs, IPs, URLs, and dates. Just not names.

## Basic usage

```python
from parfum import Anonymizer

anon = Anonymizer()

text = "Hey, I'm John. Reach me at john@gmail.com or 555-123-4567"
result = anon.anonymize(text)

print(result.text)
# Hey, I'm [PERSON]. Reach me at [EMAIL] or [PHONE]
```

The `result` object gives you more than just the cleaned text:

```python
result.text           # the anonymized version
result.original_text  # what you passed in
result.pii_found      # True if anything was detected
result.pii_count      # how many entities were found
result.matches        # list of PIIMatch objects with positions
result.replacements   # dict mapping original values to replacements
```

## The five strategies

You can process PII in different ways depending on what you need:

**replace** (default) — Swaps PII with type labels
```python
anon = Anonymizer(strategy="replace")
anon.anonymize("john@example.com").text
# → [EMAIL]
```

**mask** — Keeps structure but hides most characters
```python
anon = Anonymizer(strategy="mask")
anon.anonymize("john@example.com").text
# → j***@e******.com
```

**hash** — Deterministic SHA-256 (first 16 chars)
```python
anon = Anonymizer(strategy="hash")
anon.anonymize("john@example.com").text
# → a1b2c3d4e5f67890
```

**fake** — Generates realistic-looking replacements
```python
anon = Anonymizer(strategy="fake", seed=42)  # seed for reproducibility
anon.anonymize("john@example.com").text
# → michael.smith@company.org
```

**redact** — Just removes it entirely
```python
anon = Anonymizer(strategy="redact")
anon.anonymize("Email: john@example.com today").text
# → Email:  today
```

## What it detects

Out of the box, the regex patterns catch:

- **Email addresses** — standard RFC-ish patterns
- **Phone numbers** — US/Canada formats, with or without country codes
- **Credit cards** — Visa, Mastercard, Amex, plus generic 16-digit patterns
- **SSNs** — US Social Security numbers in various formats
- **IP addresses** — both IPv4 and IPv6
- **URLs** — with or without protocol prefix
- **Dates** — ISO format, US format, written out like "January 15, 2024"
- **IBANs** — international bank account numbers

If you install the NER extra, you also get:

- **Person names** — via spaCy's named entity recognition
- **Organizations** — company names and such
- **Locations** — cities, countries, addresses

## Working with chat data

The library is built for conversations. Use `anonymize_chat()` to process message arrays while keeping the structure intact:

```python
from parfum import Anonymizer

anon = Anonymizer(strategy="fake")

chat = [
    {"role": "user", "content": "I'm Sarah, call me at 555-0123"},
    {"role": "assistant", "content": "Got it Sarah! I'll call that number."}
]

clean = anon.anonymize_chat(chat)
```

The fake strategy keeps replacements consistent—if "Sarah" becomes "Emily" in the first message, it stays "Emily" throughout.

## Processing files

Got a bunch of data files? There's support for that:

```python
from parfum import Anonymizer, process_file, process_directory

anon = Anonymizer(strategy="fake")

# single file
process_file("input.jsonl", "output.jsonl", anon)

# whole directory
process_directory(
    "raw_data/",
    "clean_data/",
    anon,
    pattern="*.jsonl",
    recursive=True
)
```

Supported formats:
- **JSONL** (.jsonl) — one JSON object per line, looks for "content" or "messages" keys
- **JSON** (.json) — arrays of objects or single conversation objects
- **CSV** (.csv) — you can specify which columns to process
- **Plain text** (.txt or anything else) — line by line

For JSON/JSONL, it automatically handles the OpenAI-style `messages` format.

## Command line

There's a CLI too:

```bash
# anonymize a file
parfum anonymize data.json -o clean.json --strategy fake

# process a directory
parfum anonymize ./chats/ -o ./output/ --recursive --pattern "*.jsonl"

# quick one-liner
parfum quick "Email me at john@test.com"
# → Email me at [EMAIL]

# just detect, don't change anything
parfum detect "My SSN is 123-45-6789"
# Found 1 PII entities:
#   [SSN] "123-45-6789" (pos 10-21)
```

Options:
- `-s, --strategy` — replace, mask, hash, fake, or redact
- `-o, --output` — where to write (required for anonymize)
- `--no-ner` — skip the NER model, regex only
- `-r, --recursive` — for directories
- `-p, --pattern` — glob pattern like "*.txt"
- `--content-key` — if your JSON uses something other than "content"
- `--locale` — for fake data generation (default: en_US)
- `--seed` — make fake data reproducible

## Custom patterns

Need to catch something specific to your data? Add your own regex:

```python
from parfum import Anonymizer, PIIType

anon = Anonymizer()

# catch employee IDs like "EMP-123456"
anon.add_pattern(
    name="employee_id",
    pattern=r"EMP-\d{6}",
    pii_type=PIIType.CUSTOM
)

result = anon.anonymize("Contact EMP-123456")
# → Contact [CUSTOM]
```

You can also assign custom patterns to existing types if you want them handled the same way:

```python
anon.add_pattern(
    name="company_email",
    pattern=r"\w+@mycompany\.com",
    pii_type=PIIType.EMAIL  # treated as email for masking, faking, etc.
)
```

## Different strategies per type

Maybe you want names faked but emails just masked:

```python
from parfum import Anonymizer, PIIType, Strategy

anon = Anonymizer(strategy="replace")  # default

anon.set_strategy(Strategy.FAKE, pii_type=PIIType.PERSON)
anon.set_strategy(Strategy.MASK, pii_type=PIIType.EMAIL)

text = "John at john@test.com"
result = anon.anonymize(text)
# → Michael at j***@t***.com
```

Or if you want total control:

```python
def my_email_handler(match):
    local, domain = match.text.split("@")
    return f"[HIDDEN]@{domain}"

anon.set_custom_anonymizer(PIIType.EMAIL, my_email_handler)
```

## Without spaCy (lightweight mode)

If you don't need name detection and want to keep dependencies minimal:

```python
from parfum import Anonymizer

anon = Anonymizer(use_ner=False)
```

You still get all the regex-based detection. Just no names, organizations, or locations.

## Batch processing

```python
texts = [
    "Email: a@b.com",
    "Phone: 555-1234",
    "Just some text with no PII"
]

results = anon.anonymize_many(texts)

for r in results:
    print(f"Found {r.pii_count} entities")
```

## Detection only

If you just want to find PII without changing anything:

```python
matches = anon.detect("Contact john@test.com or call 555-1234")

for m in matches:
    print(f"{m.pii_type.value}: {m.text} (position {m.start}-{m.end})")
```

## Reproducibility

For the fake strategy, you can set a seed to get consistent results:

```python
anon = Anonymizer(strategy="fake", seed=42)
```

Note that the caching is per-session. The same original value will get the same fake replacement within one `Anonymizer` instance. Call `anon.clear_cache()` if you want to reset that.

## Locales

The fake data generator supports different locales:

```python
anon = Anonymizer(strategy="fake", locale="de_DE")
```

Check [Faker's documentation](https://faker.readthedocs.io/) for available locales.

## How masking works

Different PII types get masked differently:

- **Emails**: `john.doe@example.com` → `j***.d**@e******.com`
- **Phones**: `555-123-4567` → `555-***-**67` (keeps first 3, last 2)
- **Credit cards**: `4111-1111-1111-1234` → `****-****-****-1234` (keeps last 4)
- **SSNs**: `123-45-6789` → `***-**-6789` (keeps last 4)
- **IPs**: `192.168.1.100` → `192.168.*.*` (keeps first 2 octets)
- **Everything else**: `secretdata` → `s********a` (first and last char)

## Installation notes

The base install is just:
- `regex` — for pattern matching
- `faker` — for generating fake data

The `[ner]` extra adds:
- `spacy` — for named entity recognition

If spaCy isn't installed or the model isn't downloaded, it'll just skip NER silently and use regex only.

## License

MIT. Do whatever you want with it.

## Bugs?

Open an issue. PRs welcome too.
