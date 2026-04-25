# System Architecture: VibeFinder Agent

```mermaid
flowchart TD
    A([User Input]) --> B{Guardrail Check}

    B -- "empty / too short / not music-related" --> C([Early Exit: error message\nresults=[], iterations=0])

    B -- passes --> D[PLAN\ncall claude-haiku-4-5-20251001\nparse JSON profile + scoring_mode]

    D --> E[ACT\ncall recommend_songs\nfrom recommender.py\nreturn top 5 results]

    E --> F[EVALUATE\ndiversity_score = unique genres / 5\navg_score = mean of top-5 scores\nquality_pass = avg >= 1.2 AND diversity >= 0.4]

    F -- "quality_pass = True\nOR iterations = 3" --> G([Final Output\nresults + full agent_log\niterations count\nfinal_profile\nquality dict])

    F -- "quality_pass = False\nAND iterations < 3" --> H[REVISE\nbuild revised prompt with\nfailure reason appended]

    H -- "increment iteration counter" --> D

    style A fill:#4a90d9,color:#fff
    style C fill:#e05252,color:#fff
    style D fill:#7b68ee,color:#fff
    style E fill:#5ba85b,color:#fff
    style F fill:#e0a030,color:#fff
    style H fill:#c47a20,color:#fff
    style G fill:#4a90d9,color:#fff
```
