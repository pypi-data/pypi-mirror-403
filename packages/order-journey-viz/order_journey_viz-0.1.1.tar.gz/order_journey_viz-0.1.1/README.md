## Examples

Below are **self-contained example scripts** you can copy and run to try the
Order Journey Visualizer. Each example generates an interactive HTML file
that you can open in your browser.

---

### Minimal Example

The simplest possible usage. Good starting point.

```python
import pandas as pd
from order_journey import OrderJourneyVisualizer

df = pd.DataFrame({
    "order_id": ["A", "A"],
    "status": ["Start", "End"],
    "timestamp": ["2024-01-01", "2024-01-02"]
})

viz = OrderJourneyVisualizer(df)
viz.build_graph()
viz.generate_html("minimal_example.html")

print("Done! Open minimal_example.html in your browser")

import pandas as pd
from order_journey import OrderJourneyVisualizer

df = pd.DataFrame({
    "order_id": ["A", "A", "A", "A"],
    "status": ["New", "Processing", "Failed", "Processing"],
    "timestamp": [
        "2024-01-01 10:00",
        "2024-01-01 11:00",
        "2024-01-01 12:00",
        "2024-01-01 13:00",
    ],
})

viz = OrderJourneyVisualizer(df)
viz.build_graph()
viz.generate_html("retry_example.html")

print("Done! Open retry_example.html in your browser")
```

### Retry / Failure Pattern Example

```python
import pandas as pd
from order_journey import OrderJourneyVisualizer

df = pd.DataFrame({
    "order_id": ["A", "A", "A", "A"],
    "status": ["New", "Processing", "Failed", "Processing"],
    "timestamp": [
        "2024-01-01 10:00",
        "2024-01-01 11:00",
        "2024-01-01 12:00",
        "2024-01-01 13:00",
    ],
})

viz = OrderJourneyVisualizer(df)
viz.build_graph()
viz.generate_html("retry_example.html")

print("Done! Open retry_example.html in your browser")

```
