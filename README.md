# outbound-engine

The loop I run for my own outbound, pulled out of the private CRM I built so it can be shared without any lead data.

**Research a business, write the email from a real fact about it, split-test the subject line, then score replies by version and by segment.**

## Why it exists

Since Oct 1, 2026 I've sent 601 researched cold emails to local service businesses in Gainesville, FL. That's 10 replies and 1 paying client so far. Every email starts from something true about that business, and every reply gets logged against the version that earned it.

That logging is how I learned where to point volume: established trades and auto shops reply, gyms and studios mostly say no. So the next batch goes where the replies are, not where the list is longest.

## What it does

| Step | What happens |
|---|---|
| Research | Pulls the business's website text and has Claude pick **one** checkable fact, with the sentence it came from |
| Write | Turns that fact into a short email in my voice: who I am, the fact, one honest question, proof, a 15-minute ask |
| Guardrail | No fact found means `needs research`, never a guess. A made-up detail in a cold email kills trust instantly |
| Split | Each lead gets a stable version (hash of the email), so a rerun never reshuffles who got what |
| Score | Reply rate by version and by segment, with a plain verdict: too early, no winner yet, could be luck, or a real winner |

The verdict uses the same rules I use on my own sends: no call under 20 sends per version, a gap of 3+ replies before anything counts, and a two-proportion z-test so a lucky week doesn't get mistaken for a better subject line.

## Run it

```bash
python test_engine.py                        # self-check, no network
python engine.py score sent.example.csv      # made-up sent log, shows the output

export ANTHROPIC_API_KEY=...  ANTHROPIC_MODEL=...   # any current Claude model
python engine.py build leads.csv > drafts.csv
```

`leads.csv` needs `business, website, email, segment`. `sent.csv` needs `version, segment, replied`. Python standard library only.

```
by version
  C                          7/120    5.8%
  A                          3/120    2.5%
  C leads A by 4 replies, but p = 0.20: could be luck, keep sending

by segment
  auto                       8/71    11.3%
  trades                     2/58     3.4%
  health                     0/57     0.0%
  fitness                    0/54     0.0%
```

(`sent.example.csv` is generated, not real outreach.)

## Not in here

Sending. I send every email by hand from my own inbox, and the CRM, call logging and walk-in routes stay private because they hold real people's details.

Ethan Leeds · UF · [volvera.net](https://volvera.net)
