# LLM Leaderboard Game System — Design Document
**Purpose:** To design a robust, scalable, and cost-effective system for benchmarking and ranking LLMs (proprietary and open source) through creative, deterministic, multi-player games.

---

## Table of Contents

1. [System Goals](#system-goals)
2. [Core Requirements](#core-requirements)
3. [Game Design Overview](#game-design-overview)
4. [Scoring & Ranking System](#scoring--ranking-system)
5. [Game Types](#game-types)
6. [Challenge Creation & Solving Game (Deep Dive)](#challenge-creation--solving-game-deep-dive)
7. [System Architecture](#system-architecture)
8. [Cost Optimization & Scheduling](#cost-optimization--scheduling)
9. [Fairness, Reproducibility, and Edge Cases](#fairness-reproducibility-and-edge-cases)
10. [Next Steps & Open Questions](#next-steps--open-questions)
11. [Front-End Technical Specifications](#front-end-technical-specifications)

---

## 1. System Goals

- **Objective, scalable LLM benchmarking** via multiplayer, deterministic games.
- **Leaderboard** reflects *relative* LLM performance, not just participation count.
- **Support for both proprietary (token-based) and open source (GPU-based) LLMs** with different cost and availability models.
- **Automated, auditable, and reproducible** evaluation pipeline.

---

## 2. Core Requirements

- **Multi-player games**: 2–10 LLMs per game, with variable participants per game.
- **Deterministic scoring**: Objective win/loss or ranking for each game, minimal human judgment.
- **Flexible, robust rating system**: Frequency-agnostic, able to handle missing data and variable matchups (TrueSkill recommended).
- **Cost-effective scheduling**: Minimize both token and GPU-hour costs while maximizing leaderboard coverage and rating confidence.
- **Automation-ready**: Minimal manual intervention, support for batch processing, logging, and analytics.

---

## 3. Game Design Overview

- **Game = a round of competition between N LLMs** (N variable per game).
- **Game output**: An objective, full ranking of participants (with ties allowed).
- **Each game type defines its own input, rules, and scoring mechanism.**
- **Games can be replayed with different combinations of LLMs** for more robust ratings.

---

## 4. Scoring & Ranking System

### **A. TrueSkill Rating**

- Each LLM has a skill distribution: (μ, σ)
- After each game, all participants’ ratings are updated based on the full ranking.
- Handles variable numbers of players and missing data.
- Leaderboard is sorted by “conservative skill” (μ – k·σ), optionally displaying both μ and σ.
- Open-source libraries (e.g., `trueskill` in Python) are available.

### **B. Ranking from Game Results**

- For each game, produce a ranked list of participants (ties allowed).
- If a single LLM plays multiple slots, aggregate their outcomes for leaderboard updates.

---

## 5. Game Types

### **A. Deterministic, Automatable Games**

1. **Code Golf**: Shortest correct code wins.
2. **Bug Hunt**: Find/fix bugs in code; rank by bugs fixed.
3. **Trivia/Quiz**: Most correct answers.
4. **Fact-Checking**: Highest accuracy in classifying statements.
5. **Math/Logic Puzzles**: Solve for a unique answer.
6. **Data Transformation**: Output must exactly match expected result.
7. **Compression Challenge**: Shortest valid summary.
8. **Resource Allocation**: Closest to optimal split.
9. **Simulated Market/Game Theory**: Deterministic payoff from auctions, negotiations, voting, etc.
10. **Automated Output Evaluation**: Use objective metrics (BLEU, ROUGE, F1).

### **B. Social/Reasoning Games (Advanced)**

- **Werewolves/Mafia**: Can be run if scoring is based on survival/team outcome (see [Section 9](#fairness-reproducibility-and-edge-cases)).

---

## 6. Challenge Creation & Solving Game (Deep Dive)

### **A. Game Protocol**

1. **Challenge Creation**
    - Each LLM generates creative coding challenges.
    - Challenge must produce a single integer output (“password”).
    - Must provide: description, reference answer, and (optionally) test cases or a reference solution.

2. **Challenge Pool**
    - All challenges are pooled and reused across rounds.
    - Metadata (author, answer) is hidden from solvers.

3. **Solving Phase**
    - Each LLM is assigned a set of challenges (randomized, can include their own).
    - For each challenge, the LLM submits an integer answer or “pass”.

4. **Scoring**
    - **+1** for correct answer
    - **–1** for incorrect answer
    - **0** for pass/skip
    - **–1 extra penalty** if failing own challenge (wrong or pass)

5. **Leaderboard Integration**
    - Total points per round = input to TrueSkill or used as a direct leaderboard score.

### **B. Implementation Schema (Sample)**

**Challenge:**
```json
{
  "challenge_id": "abc123",
  "author_llm": "LLM_X",
  "description": "Find the sum of all even numbers between 1 and 1000, inclusive.",
  "reference_answer": 250500
}
```
**Attempt:**
```json
{
  "llm_id": "LLM_Y",
  "challenge_id": "abc123",
  "submitted_answer": 250500,
  "result": "correct",  // or "incorrect", "pass"
  "own_challenge": false,
  "points": 1
}
```

---

## 7. System Architecture

### **A. Components**

| Component          | Responsibility                                              |
|--------------------|------------------------------------------------------------|
| Game Engine        | Runs games, collects and validates results                 |
| Challenge Pool     | Stores challenges, metadata, and usage history             |
| Job Scheduler      | Orchestrates LLM availability, game assembly, and batching |
| Auto-Grader        | Checks submitted answers, applies scoring rules            |
| Result Store       | Logs all attempts, scores, and game metadata               |
| Rating Engine      | Updates LLM skill ratings (TrueSkill)                      |
| Leaderboard API/UI | Displays rankings, stats, and analytics                    |
| Cost Tracker       | Logs token and GPU-hour spend per LLM/game                 |

### **B. Data Flow**

1. LLMs create challenges → Challenge Pool
2. Scheduler assembles games/challenges → Assigns to LLMs
3. LLMs submit answers → Auto-Grader
4. Grader checks answers, assigns points → Result Store
5. Results update ratings → Leaderboard
6. Cost Tracker logs usage → Analytics

---

## 8. Cost Optimization & Scheduling

### **A. Proprietary LLMs**
- **Per-token cost**
- **Always available**: Schedule on-demand, fill in gaps, anchor leaderboard

### **B. Open Source LLMs**
- **Per-GPU-hour cost**
- **Batch jobs**: When server is up, assign as many games as possible
- **Preload**: Prepare all data before spin-up
- **Auto-shutdown**: Stop server after batch is complete

### **C. Scheduling Strategies**
- **Dynamic game assembly**: Match available LLMs, ensure sufficient leaderboard coverage
- **Priority scheduling**: Focus on under-benchmarked LLMs or “high-value” matchups
- **Job queue system**: Automate assignment, maximize throughput per server session

### **D. Cost Tracking**
- Log spend per LLM/game
- Analyze “games per dollar” or “information per dollar” for ongoing optimization

---

## 9. Fairness, Reproducibility, and Edge Cases

- **Variable game size**: TrueSkill natively supports this.
- **LLM as multiple players**: Attribute all agent slots to the LLM; aggregate outcomes for leaderboard updates.
- **Challenge assignment**: Randomized, avoid information leakage, anonymize author.
- **Challenge pool growth**: Reuse challenges, track difficulty, flag ambiguous/unsolvable challenges.
- **Werewolves/Mafia**: For deterministic ranking, use team outcome + survival order as ranking (see [previous explanation](#)).
- **Reproducibility**: Seed all randomness, log all assignments and results.

---

## 10. Next Steps & Open Questions

### **Immediate Prototyping**
- Implement the challenge creation/solving pipeline (challenge pool, auto-grader, scoring, logging).
- Set up TrueSkill rating engine and leaderboard update flow.
- Build job queue/scheduler for batching open source LLMs.
- Create cost tracker for analytics.

### **Open Questions**
- What additional deterministic game types might be valuable?
- Should scoring be adjusted for challenge "difficulty"?
- How to automate challenge quality review (LLM-based or manual)?
- How often to re-anchor proprietary/open source matchups for leaderboard accuracy?

---

## 11. Front-End Technical Specifications

### **A. Hosting & Data Architecture**

- **GitHub Pages**: Static site hosting for the leaderboard front-end
- **Git-Based Data Storage**: 
  - Game results stored as JSON files in the repository
  - Each game result added via commits to the repository
  - Git history provides versioning, audit trail, and rollback capabilities
  - Authentication handled through Git's mechanisms (SSH keys, personal access tokens)

### **B. Tech Stack**

#### **Core Technologies**
- Python 3.12 for data processing and static site generation
- Flask for development server
- Frozen-Flask for converting Flask app to static files
- Jinja2 templates for HTML generation

#### **UI Components**
- Bootstrap or Tailwind CSS for styling (via CDN, no build step needed)
- Chart.js (loaded via CDN) for data visualizations
- Minimal JavaScript for interactivity

#### **Data Processing**
- `trueskill` Python package for rating calculations
- `pandas` for data manipulation (if needed)

#### **Build Tools & Deployment**
- GitHub Actions for CI/CD pipeline
- Automated site rebuilds when data changes

#### **Testing & Quality**
- pytest for Python testing
- flake8 and black for code quality

#### **Additional Utilities**
- PyYAML for configuration
- Markdown for content formatting
- Flask-Assets for asset management (if needed)

### **C. Project Structure**

```
valyrian-games-leaderboard/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── models.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── trueskill_calculator.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── leaderboard.html
│   │   └── game_history.html
│   └── static/
│       ├── css/
│       ├── js/
│       └── images/
├── data/
│   ├── leaderboard.json
│   └── games/
│       ├── game_001.json
│       └── ...
├── scripts/
│   ├── update_leaderboard.py  # Script for adding new game results
│   └── freeze.py              # Script to generate static site
├── venv/                      # Python virtual environment
├── requirements.txt
├── config.py
├── run.py                     # Development server entry point
└── README.md
```

### **D. Data Flow**

1. **Game Results Generation**:
   - External system runs LLM games and produces result data
   - Python script processes results and updates JSON data files

2. **Data Update Process**:
   ```
   # After a new game is completed
   1. Script reads current leaderboard.json and game_history.json
   2. Adds new game results to game_history.json
   3. Updates LLM ratings in leaderboard.json using TrueSkill algorithm
   4. Commits changes to Git repository
   5. GitHub Actions workflow is triggered, which:
      - Sets up Python environment
      - Runs the freeze.py script to generate static site
      - Deploys the static files to GitHub Pages
   ```

3. **Static Site Generation**:
   - Flask app defines routes and templates
   - Frozen-Flask crawls the Flask app and generates static HTML
   - Static files are deployed to GitHub Pages

---

## Appendices

### **A. Sample Python Snippet: TrueSkill Update**

```python
import trueskill

env = trueskill.TrueSkill(draw_probability=0)
llms = {name: env.create_rating() for name in ['A', 'B', 'C', 'D']}

# After a game, e.g., A wins, then B, C, D
ranks = [0, 1, 2, 3]
players = [llms['A'], llms['B'], llms['C'], llms['D']]
new_ratings = env.rate(zip([p] for p in players), ranks=ranks)
for idx, name in enumerate(['A', 'B', 'C', 'D']):
    llms[name] = new_ratings[idx][0]
```

### **B. Challenge Assignment Pseudocode**

```python
for llm in all_llms:
    challenges = random.sample(challenge_pool, N)
    for ch in challenges:
        answer = llm.solve(ch['description'])
        points = grade_submission(answer, ch['reference_answer'], own=(ch['author_llm'] == llm.id))
        log_attempt(llm.id, ch['challenge_id'], answer, points)
```
