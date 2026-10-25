# AI Discovery Engine - Flow

To generate a PNG of this flow, you can view this markdown file in an editor that supports Mermaid (like VS Code or GitHub) and export it, or paste it into [Mermaid Live Editor](https://mermaid.live).

```mermaid
graph TD
    classDef input fill:#2c3e50,stroke:#34495e,stroke-width:2px,color:#fff;
    classDef process fill:#2980b9,stroke:#2980b9,stroke-width:2px,color:#fff;
    classDef output fill:#27ae60,stroke:#2ecc71,stroke-width:2px,color:#fff;

    A[USER-GENERATED EVIDENCE<br/>Reviews, Reddit, Surveys]:::input --> B
    
    B[AI SIGNAL EXTRACTION<br/>Identify Intent & Friction]:::process --> C
    
    C[BEHAVIOURAL CLASSIFICATION<br/>Map to Abandonment Barriers]:::process --> D
    
    D[THEME CLUSTERING<br/>Group Recurring Patterns]:::process --> E
    
    E[OPPORTUNITY SCORING<br/>Rank by Frequency & Severity]:::process --> F
    
    F[GROWTH HYPOTHESES<br/>Data-Backed PM Insights]:::output
```
