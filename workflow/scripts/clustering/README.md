
Which Normalization to use in Clustering Demand-Supply profiles to get a representative profile?
---

| Use Case Aspect             | Min-Max Normalization                              | Euclidean Normalization                              |
|----------------------------|---------------------------------------------------|-----------------------------------------------------|
| **Purpose**                | Scale all profile values between 0 and 1 globally | Normalize each day's 24-hour vector to unit length  |
| **Normalization Scope**    | Across entire dataset (all days and hours)        | Per day (each 24-hour profile independently)        |
| **Effect on Data**         | Preserves relative magnitude differences           | Preserves shape (profile pattern), removes magnitude scale differences |
| **When to use**            | When absolute value ranges matter                   | When profile shape similarity matters more than magnitude |
| **Impact on Clustering**   | Groups days by absolute value similarity           | Groups days by shape/pattern similarity regardless of scale |
| **Interpretation of Results** | Representative days show typical absolute demand levels | Representative days show typical demand shapes normalized to unit magnitude |
| **Visualization**          | Values range [0, 1]                                | Values scaled per day, range varies but norm = 1    |
| **Example Application**    | Comparing demand profiles across different magnitudes or locations | Extracting shape-based demand patterns ignoring scale differences |


Examples:
---
| Scenario                                                                                                                      | Recommended Normalization & Why                                                                                                                                        |
| ----------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| You care about **absolute demand levels** (e.g., total energy use)                                                            | **Min-Max normalization across whole year** — preserves magnitude differences, so clusters reflect days with similar absolute demand patterns and levels.              |
| You care about **daily demand shape/patterns**, ignoring scale differences (e.g., shape of load curve matters more than size) | **Euclidean normalization (normalize each day vector to unit length)** — clusters focus on shape similarity regardless of magnitude, capturing typical daily profiles. |
| You want a **balanced approach** to detect both magnitude and shape differences                                               | Consider **using both** and comparing results or even combining features.                                                                                              |
