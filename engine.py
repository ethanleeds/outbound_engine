"""Outbound engine: research a business, write the email, split-test the subject, score the replies.

    python engine.py build leads.csv > drafts.csv     # research + write + assign a version
    python engine.py score sent.csv                   # reply rate by version and by segment

Stdlib only. Set ANTHROPIC_API_KEY and ANTHROPIC_MODEL for `build`.
"""
import csv, hashlib, html, json, math, os, re, sys, urllib.request

SUBJECTS = {  # one entry per version; the body is identical so the subject is the only variable
    "A": "{sender}, UF student | An experiment for {business}",
    "C": "{sender}, UF student | An idea for {business}",
}
SENDER = os.environ.get("SENDER_NAME", "Ethan Leeds")
MIN_SENDS, MIN_GAP = 20, 3  # below this there is no winner, only noise

PROMPT = """You write cold emails from a college student who builds AI tools for small businesses.
Below is text from {business}'s website.

1. Pick ONE specific, checkable fact about this business from the text (founding year, who runs it,
   what they're known for, where they serve). Copy the sentence it came from.
   If there is no specific fact, return an empty fact. Never guess.
2. Write the email body using that fact, in this shape and voice, under 130 words:
   - who I am (junior at UF), and that I'd love to run a small experiment with them
   - the fact, then one honest question it makes me curious about, and what still eats up their day
   - my proof: {proof}
   - ask for a quick 15-minute call this week
   - sign off "Thanks either way,\\n{sender}"
   Plain words, no hype, no dashes, no exclamation marks.

Return only JSON: {{"fact": "...", "source_sentence": "...", "body": "..."}}

Website text:
{text}"""


def site_text(url, limit=6000):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
    raw = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).strip()[:limit]


def claude(prompt):
    body = json.dumps({"model": os.environ["ANTHROPIC_MODEL"], "max_tokens": 800,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", body, {
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
        "content-type": "application/json"})
    text = json.load(urllib.request.urlopen(req, timeout=60))["content"][0]["text"]
    return json.loads(text[text.find("{"): text.rfind("}") + 1])


def version_for(email):
    # stable split: the same lead always lands in the same version, even on a rerun
    keys = sorted(SUBJECTS)
    return keys[int(hashlib.sha1(email.lower().encode()).hexdigest(), 16) % len(keys)]


def build(path, proof):
    out = csv.writer(sys.stdout)
    out.writerow(["business", "email", "segment", "version", "subject", "fact", "source_sentence", "body", "status"])
    for lead in csv.DictReader(open(path, newline="")):
        try:
            d = claude(PROMPT.format(business=lead["business"], text=site_text(lead["website"]), proof=proof, sender=SENDER))
        except Exception as e:  # one dead site must not kill the batch
            print(f"skip {lead['business']}: {e}", file=sys.stderr)
            continue
        v = version_for(lead["email"])
        status = "ready" if d.get("fact") else "needs research"  # no fact found = a human looks, never a guess
        out.writerow([lead["business"], lead["email"], lead.get("segment", ""), v,
                      SUBJECTS[v].format(sender=SENDER, business=lead["business"]),
                      d.get("fact", ""), d.get("source_sentence", ""), d.get("body", ""), status])


def p_value(r1, n1, r2, n2):
    # two-proportion z-test, two-sided
    p = (r1 + r2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) if 0 < p < 1 else 0
    return 1.0 if se == 0 else math.erfc(abs(r1 / n1 - r2 / n2) / se / math.sqrt(2))


def tally(rows, key):
    t = {}
    for r in rows:
        s = t.setdefault(r[key] or "(none)", [0, 0])
        s[0] += 1
        s[1] += r["replied"].strip().lower() in ("1", "yes", "true", "y")
    return t


def verdict(t):
    (a, (na, ra)), (b, (nb, rb)) = sorted(t.items(), key=lambda kv: -kv[1][1] / kv[1][0])[:2]
    if min(na, nb) < MIN_SENDS:
        return f"too early: need {MIN_SENDS}+ sends per version"
    if ra - rb < MIN_GAP:
        return f"no winner yet: {a} leads {b} by {ra - rb} replies, need {MIN_GAP}"
    p = p_value(ra, na, rb, nb)
    if p >= 0.05:  # the gap rule is a working call; say plainly when it could still be luck
        return f"{a} leads {b} by {ra - rb} replies, but p = {p:.2f}: could be luck, keep sending"
    return f"{a} wins over {b} (p = {p:.2f})"


def score(path):
    rows = list(csv.DictReader(open(path, newline="")))
    for key in ("version", "segment"):
        t = tally(rows, key)
        print(f"\nby {key}")
        for k, (n, r) in sorted(t.items(), key=lambda kv: -kv[1][1] / kv[1][0]):
            print(f"  {k:<24} {r:>3}/{n:<4} {r / n:6.1%}")
        if key == "version" and len(t) > 1:
            print("  " + verdict(t))


if __name__ == "__main__":
    cmd, path = sys.argv[1], sys.argv[2]
    if cmd == "build":
        build(path, os.environ.get("PROOF", "I'm an AI GTM Engineer at a startup, where I built AI tools that save the team 50+ hours a week"))
    else:
        score(path)
