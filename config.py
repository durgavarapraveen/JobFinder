"""
Job Radar config — edit this file to tune your search.
No secrets here. Phone + CallMeBot key come from environment variables
(set as GitHub Actions secrets when deployed).
"""

# What to search for. Broad title filter used against every source.
KEYWORDS = "software engineer"
LOCATION = "India"

# How many top matches to send to WhatsApp each run.
TOP_N = 12

# Minimum score (0-100) a job must reach to be sent. Raise to get fewer, closer matches.
MIN_SCORE = 25

# LinkedIn public guest endpoint: how many pages (25 jobs each) to pull.
# Keep LOW (2-3). Higher = more requests = higher chance LinkedIn throttles your IP.
LINKEDIN_PAGES = 3

# ── Resume signal ─────────────────────────────────────────────────────────
# Weighted keywords pulled from your resume. Higher weight = matters more.
# A job's score = sum of weights of terms it mentions, normalized to 0-100.
RESUME_TERMS = {
    # core role
    "software engineer": 5, "backend": 4, "full stack": 4, "developer": 3,
    "rest api": 4, "api": 2, "microservices": 3, "distributed": 3,
    # languages (your real proficiency)
    "python": 5, "java": 4, "spring boot": 4, "javascript": 3, "typescript": 3,
    "c++": 2, "node": 3,
    # web
    "react": 4, "next.js": 3, "nextjs": 3, "fastapi": 4, "django": 3,
    # cloud / devops
    "aws": 4, "azure": 4, "docker": 3, "kubernetes": 2, "ci/cd": 3,
    "terraform": 2, "cloud": 3, "postgres": 2, "postgresql": 2, "mysql": 2,
    # AI / agents (your differentiator)
    "llm": 5, "ai agent": 5, "agentic": 5, "genai": 4, "generative ai": 4,
    "copilot": 3, "rag": 4, "machine learning": 2,
    # security (your background)
    "security": 4, "red team": 4, "penetration": 3, "pentest": 3,
    "threat model": 3, "owasp": 3, "vulnerability": 3, "application security": 4,
    "cloud security": 4, "devsecops": 3,
}

# Titles to drop outright (too senior / wrong track).
EXCLUDE_TITLE = [
    "principal", "director", "vice president", "vp ", "staff ",
    "manager", "intern", "internship", "lead ", "head of",
]

# Sources to enable.
SOURCES = {
    "microsoft": True,
    "linkedin": True,     # public guest endpoint, low volume
    "remotive": True,
    "arbeitnow": True,
}
