---
name: prediction-market-analytics
description: |
  Analyze prediction markets (Jupiter Prediction, Polymarket, sports/esports betting lines), extract live prices and odds, produce strictly balanced two-sided analytical breakdowns, and export standardized prediction tickets.
  Trigger when:
  - User provides prediction market links (e.g., jup.ag/prediction, polymarket.com).
  - User asks to analyze esports, sports, or crypto prediction markets.
  - User asks to generate prediction tickets, picks, or betting analyses.
  - User asks to format picks using the ticket standard [ticket#{number}][sector][matchup][pick].
---

# Prediction Market Analytics & Ticket Generation Skill

A specialized protocol for analyzing prediction markets, extracting odds from on-chain/clob orderbooks, writing strictly unbiased, two-sided match evaluations, and exporting standardized ticket files.

---

## 1. Core Principles

1. **Strict Analytical Neutrality**:
   Never bias analysis toward the user's selected outcome. High-probability favorites (e.g., 83¢) carry extreme downside asymmetry. The analysis must rigorously present the opposing team's win condition and the failure modes of the pick.
2. **Zero AI Slop**:
   Cut throat-clearing intros (no "Your boy monmon is back", no "Let's dive in"). Never use LLM clichés (*delve, tapestry, testament, underscore, pivotal, crucial, seamless, game-changer, cutting-edge*).
3. **Data-Grounded Specificity**:
   Reference concrete metrics: market prices/points (e.g., `83 pts`), lane gold/CS differentials, objective timers (herald, first drake, baron), and champion match-up dynamics.
4. **Standard File Export Protocol**:
   Every pick must be saved to `~/vibe/` with the exact naming structure:
   `[ticket#{number}][sector][matchup][pick].md`

---

## 2. Market Ingestion Protocol

When given a Jupiter Prediction (`jup.ag/prediction/POLY-...`) or Polymarket URL:

### Method A: Open Graph Image Inspection (Fastest & Most Reliable)
Jupiter generates live OG images containing the market title, event time, and current bid prices in cents (`¢`).
1. Derive the OG image URL:
   `https://jup.ag/api/prediction/<EVENT_ID>/og.png`
2. Download or view the image:
   ```bash
   curl -s "https://jup.ag/api/prediction/<EVENT_ID>/og.png" -o "/tmp/<EVENT_ID>.png"
   ```
3. Read the exact prices for both teams using the `view_file` tool on the image.

### Method B: Dehydrated Router State Extraction
For detailed market rules and clob token IDs:
1. Fetch the raw HTML via `read_url_content` or `curl`.
2. Inspect the TanStack router state embedded in the page script:
   Look for `sportsMarketType:"moneyline"`, `outcomes`, and `clobTokenIds`.
3. Extract the market ID and event timing.

---

## 3. The Unbiased Analytical Framework

Structure every matchup breakdown with these five components:

1. **BLUF (Bottom Line Up Front)**:
   2–3 direct sentences summarizing the expected series trajectory, teamfight/macro dynamics, and the price value/risk trade-off.
2. **Strengths & Win Condition (Pick Team)**:
   Concrete mechanisms: lane priority, champion pool flexibility, objective setup speed, scaling spikes.
3. **Counter-Threat & Win Condition (Opponent Team)**:
   How the opponent can win: early jungle invades, punish weak vision control, draft hard engage, exploit side-lane overextensions.
4. **Pick Risk**:
   The exact conditions under which the pick fails. Assess whether the market price (pts) leaves adequate margin for error.
5. **Key Player Matchups**:
   Evaluate 2 critical lane/role matchups with bilateral analysis (how Player A wins vs how Player B punishes).

---

## 4. Standard Ticket Output Schema

Always format the user-facing text as:

```text
<Prediction Market URL>
pick <Outcome> to win @ <Price> pts

analysis:
<Tournament/League> | <Stage> | <Format> (<Time>)

BLUF: <Summary and risk assessment>
Two-Sided Breakdown:
<Team A> Strengths & Win Condition: <Specific win conditions>
<Team B> Counter-Threat & Win Condition: <Opposing exploit vectors>
Pick Risk: <Explicit failure conditions>
Key Player Matchups:
<Role 1> (<Player 1 vs Player 2>): <Direct interaction>
<Role 2> (<Player 3 vs Player 4>): <Direct interaction>
#nfa #dyor
```

---

## 5. Export Automation Workflow

Whenever generating tickets:

1. Determine the sequential ticket number (e.g. `01`, `02`, `03`).
2. Identify the sector (e.g. `esports`, `sports`, `crypto`, `macro`).
3. Construct the clean file name:
   `[ticket#{number}][{sector}][{TeamA}-vs-{TeamB}][{Pick}].md`
4. Write the file directly into `~/vibe/`.
5. Provide clickable markdown links in the chat response.
