from typing import Optional, Dict, Any, Tuple, List


def extract_integration_from_path(filepath: str, patterns: Optional[List[str]] = None) -> Optional[str]:
    if patterns is None:
        patterns = ["integrations/", "services/", "connectors/", "adapters/"]
    for pattern in patterns:
        if pattern in filepath:
            parts = filepath.split(pattern)
            if len(parts) > 1:
                integration = parts[1].split("/")[0]
                return integration
    return None


def filepath_to_component_label(filepath: str) -> str:
    for prefix in ["/app/src/", "/app/", "/src/", "/"]:
        if filepath.startswith(prefix):
            filepath = filepath[len(prefix):]
            break
    if filepath.endswith(".py"):
        filepath = filepath[:-3]
    return filepath.replace("/", ".")


def format_github_issue(
    service_name: str,
    environment: str,
    error_type: str,
    error_message: str,
    location: str,
    function_name: str,
    full_traceback: str,
    context: Dict[str, Any],
    first_seen: str,
    occurrences: int
) -> Tuple[str, str]:
    title_message = error_message[:80] + "..." if len(error_message) > 80 else error_message
    title = f"🚨 {error_type}: {title_message}"

    if context:
        context_rows = "\n".join([f"| {k} | `{v}` |" for k, v in context.items()])
        context_table = f"""| Key | Value |
|-----|-------|
{context_rows}"""
    else:
        context_table = "No context available"

    component = context.get("component", "")
    component_label = filepath_to_component_label(component) if component else "unknown"

    integration = extract_integration_from_path(component) if component else None

    labels_list = [
        f"`service:{service_name}`",
        f"`error:{error_type}`",
        f"`env:{environment}`",
        f"`component:{component_label}`",
    ]
    if integration:
        labels_list.append(f"`integration:{integration}`")
    labels_display = ", ".join(labels_list)

    body = f"""## 🚨 {error_type}: {error_message}

**Service:** {service_name}
**Environment:** {environment}
**Location:** `{location}` in `{function_name}()`
**First Seen:** {first_seen}
**Occurrences:** {occurrences}

---

### Context

{context_table}

---

### Full Stack Trace

```python
{full_traceback}
```

---

### Labels

{labels_display}

---

*This issue was automatically created by fika_logger*
"""

    return title, body
