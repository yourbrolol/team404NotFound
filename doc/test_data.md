# ContestKeeper Test Data Specification

This document outlines the structured test data for the **ContestKeeper** project. The timeline covers approximately one month of activity, starting from early April 2026 to the current date of May 5, 2026.

## 1. Timeline Overview
- **Start of Data History:** 2026-04-01
- **Current Date:** 2026-05-05

---

## 2. User Roles & Profiles

### 2.1 Admin & Staff
| Username | Role | Special Status | Bio |
| :--- | :--- | :--- | :--- |
| `root_admin` | ORGANIZER | Superuser / Staff | Lead platform architect and global moderator. |

### 2.2 Organizers
| Username | Role | Special Status | Bio |
| :--- | :--- | :--- | :--- |
| `event_nexus` | ORGANIZER | Staff | Professional hackathon organizer with 10+ years experience. |
| `spark_labs` | ORGANIZER | | Innovation hub focusing on student-led initiatives. |

### 2.3 Jurors
| Username | Role | Expertise |
| :--- | :--- | :--- |
| `silent_evaluator` | JURY | Backend Architecture & Scalability |
| `pixel_perfect` | JURY | UI/UX Design and Frontend Excellence |
| `bug_hunter` | JURY | Cybersecurity and Quality Assurance |
| `logic_wizard` | JURY | Algorithms and Data Structures |
| `cloud_surfer` | JURY | DevOps and Cloud Infrastructure |
| `data_druid` | JURY | Machine Learning and Analytics |
| `vision_vanguard` | JURY | Product Vision and Market Fit |

### 2.4 Participants (Nickname Pattern: `dict + [-_] + dict`)
| Username | Role |
| :--- | :--- |
| `bold-eagle` | PARTICIPANT |
| `fast_tiger` | PARTICIPANT |
| `silent-fox` | PARTICIPANT |
| `clever_owl` | PARTICIPANT |
| `brave-wolf` | PARTICIPANT |
| `lazy_bear` | PARTICIPANT |
| `mighty-lion` | PARTICIPANT |
| `quick_hawk` | PARTICIPANT |
| `fierce-shark` | PARTICIPANT |
| `gentle_deer` | PARTICIPANT |
| `bright-lynx` | PARTICIPANT |
| `shadow_panther` | PARTICIPANT |
| `silver-cobra` | PARTICIPANT |
| `golden_falcon` | PARTICIPANT |
| `iron-whale` | PARTICIPANT |

---

## 3. Contests & State

### 3.1 Finished Contests (History)
#### **Contest A: "Retro Web Revival"**
- **Organizer:** `spark_labs`
- **Timeline:** 2026-04-05 to 2026-04-12
- **Status:** FINISHED
- **Jurors:** `pixel_perfect`, `silent_evaluator`
- **Results:** 5 Teams participated. All submissions rated.

#### **Contest B: "Python Efficiency Sprint"**
- **Organizer:** `event_nexus`
- **Timeline:** 2026-04-15 to 2026-04-20
- **Status:** FINISHED
- **Jurors:** `logic_wizard`, `bug_hunter`
- **Results:** 3 Teams participated.

### 3.2 Running Contests (Active)
#### **Contest C: "The AI Edge"**
- **Organizer:** `root_admin`
- **Timeline:** 2026-05-01 to 2026-05-10
- **Status:** RUNNING
- **Jurors:** `data_druid`, `cloud_surfer`, `vision_vanguard`
- **Current State:** Round 1 active. Submissions starting to flow in.

#### **Contest D: "Decentralized Future"**
- **Organizer:** `spark_labs`
- **Timeline:** 2026-05-03 to 2026-05-15
- **Status:** RUNNING
- **Jurors:** `silent_evaluator`, `security_pro`
- **Current State:** Registration closed, Round 1 just started.

### 3.3 Registration Phase
#### **Contest E: "Global Green Tech"**
- **Organizer:** `event_nexus`
- **Registration:** 2026-05-01 to 2026-05-08
- **Start Date:** 2026-05-10
- **Status:** REGISTRATION
- **Jurors:** TBD

### 3.4 Draft Phase
#### **Contest F: "Cyber Security Dash"**
- **Organizer:** `spark_labs`
- **Status:** DRAFT
- **Note:** Initial setup, no jurors assigned yet.

---

## 4. Teams & Submissions

### 4.1 Finished Contest: Retro Web Revival
| Team Name | Members | Submission Status | Score |
| :--- | :--- | :--- | :--- |
| **OldSchool** | `bold-eagle`, `fast_tiger` | Posted & Rated | 85/100 |
| **PixelPioneers** | `silent-fox`, `clever_owl` | Posted & Rated | 92/100 |
| **VGA_Warriors** | `brave-wolf`, `lazy_bear` | Posted & Rated | 78/100 |
| **C64_Legends** | `mighty-lion`, `quick_hawk` | Posted & Rated | 81/100 |
| **Terminal_Turtles** | `fierce-shark`, `gentle_deer` | Posted & Rated | 74/100 |

### 4.2 Running Contest: The AI Edge
| Team Name | Members | Submission Status |
| :--- | :--- | :--- |
| **NeuralKnights** | `brave-wolf`, `mighty-lion` | **Rated** (High quality ML model) |
| **DataDragons** | `quick_hawk`, `fierce-shark` | **Submitted** (Pending Jury Review) |
| **CodeCommandos** | `gentle_deer`, `bright-lynx` | **Draft** (Not yet posted) |

### 4.3 Running Contest: Decentralized Future
| Team Name | Members | Submission Status |
| :--- | :--- | :--- |
| **BlockBuilders** | `shadow_panther`, `silver-cobra` | **Submitted** (Fresh) |
| **ChainChasers** | `golden_falcon`, `iron-whale` | **No Submission** (Waiting for last minute) |

---

## 5. System Configuration & Engagement

### 5.1 Scoring Criteria (Examples)
| Contest | Criteria | Max Score | Weight |
| :--- | :--- | :--- | :--- |
| Retro Web Revival | Visual Aesthetics, Code Cleanliness, Historical Accuracy | 100 | 1.0 |
| The AI Edge | Innovation, Model Accuracy, Technical Complexity | 100 | 1.0 |
| Decentralized Future | Security, Smart Contract Logic, UI/UX | 100 | 1.0 |

### 5.2 Announcements (By Contest)
- **Retro Web Revival:**
    - "Winners Announced!" - Final leaderboard update.
    - "Final Review in Progress" - Status update during judging.
- **Python Efficiency Sprint:**
    - "Leaderboard Finalized" - Final scores posted.
    - "Check your feedback" - Instructions for viewing jury notes.
- **The AI Edge:**
    - "Halfway Point Reached!" - Pinned motivation.
    - "New Dataset Released" - Technical update.
    - "Server Maintenance" - Operational notification.
- **Decentralized Future:**
    - "Security First!" - Best practices reminder.
    - "Round 1 Checklist" - Requirement validation.
- **Global Green Tech:**
    - "Registration Open!" - Call for participants.
    - "Mentorship Program" - Special initiative announcement.

### 5.3 Detailed Contest Schedules
| Contest | Event | Type | Timing (Offset) |
| :--- | :--- | :--- | :--- |
| **Retro Web Revival** | Opening Ceremony | OTHER | Start + 0h |
| | Code Jam Phase | ROUND | Start + 2h |
| | Submission Deadline | DEADLINE | Start + 160h |
| | Award Ceremony | OTHER | Start + 180h |
| **Python Efficiency** | Kickoff Webinar | WORKSHOP | Start + 0h |
| | Coding Phase | ROUND | Start + 1h |
| | Final Push (24h) | DEADLINE | Start + 96h |
| **The AI Edge** | ML Workshop | WORKSHOP | Start + 24h |
| | Data Science Q&A | OTHER | Start + 48h |
| **Decentralized Future**| Smart Contract Audit | WORKSHOP | Start + 12h |
| | Web3 Networking | OTHER | Start + 36h |
| **Global Green Tech** | Launch Event | OTHER | Start + 0h |
| | Sustainability Webinar| WORKSHOP | Start + 48h |

### 5.4 Administrative Applications
- **Role Applications:** 
    - `new_judge_alex` (JURY): **PENDING**. Reason: "I have judge 5 hackathons before."
    - `bad_actor` (ORGANIZER): **REJECTED**. Reason: "I want to mess things up."
- **Contest Applications:**
    - `lazy_bear` applying for "Global Green Tech": **PENDING**.

---

## 6. Realistic Interaction Scenarios

1.  **Cross-Contest Participation:** 
    - `bold-eagle` finished "Retro Web Revival" in mid-April and is now waiting for "Global Green Tech" registration to end.
    - `fast_tiger` is currently active in "The AI Edge" after finishing the "Retro Web Revival".
2.  **Jury Workload:** 
    - `silent_evaluator` has finished judging "Retro Web Revival" and is now assigned to "Decentralized Future".
3.  **Submission States:**
    - **Team CodeCommandos** has a draft submission for "The AI Edge". They have uploaded descriptions but haven't hit "Submit" because they are debugging their Live Demo URL.
    - **Team DataDragons** submitted their work 2 hours ago. `data_druid` is currently viewing their GitHub repository.
