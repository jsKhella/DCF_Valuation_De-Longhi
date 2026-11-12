"""Banned-phrase list for the three deliverables (plan Amendment 3, step 9; extends the step-8 list).

Purpose
    One definition of the banned phrases, shared by checks/check_step07.py, check_step08.py and check_step09.py.
    Matching is case-insensitive and word-bounded, except `US_RX` (lowercase "us" only).
Inputs
    none. Outputs: BANNED (regex fragments), BANNED_RX, US_RX, hits(text).
"""
import re

BANNED = [r"you", r"your", r"yourself", r"could be asked", r"portfolio", r"student", r"recruiter", r"for the human",
          r"the human", r"check yourself", r"open point", r"restyle", r"plain english", r"we", r"our",
          r"interview\w*", r"planner", r"plan(?:s|ned|ning|'s)?", r"executors?", r"verifiers?(?:'s)?", r"surpris\w*",
          r"fragile", r"smell", r"gate", r"curiosity", r"pre-registered", r"notes carried", r"final review"]
BANNED_RX = re.compile(r"(?<![\w])(?:" + "|".join(BANNED) + r")(?![\w])", re.I)
US_RX = re.compile(r"(?<![\w])us(?![\w])")


def hits(text):
    return sorted({m.group(0).lower() for m in BANNED_RX.finditer(text)} | {m.group(0) for m in US_RX.finditer(text)})
