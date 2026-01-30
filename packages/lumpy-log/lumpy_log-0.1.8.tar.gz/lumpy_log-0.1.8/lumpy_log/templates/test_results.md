
# Test Results
Date: {{ generation_date }}
<!-- **Format:** {{ format }} -->

{% if format == 'tap' %}
- **Tests Run:** {{ tests_run }}
- **Passed:** {{ tests_passed }} ✅
- **Failed:** {{ tests_failed }} {% if tests_failed > 0 %}❌{% endif %}
- **Skipped:** {{ tests_skipped }} {% if tests_skipped > 0 %}⏭️{% endif %}

{% if tests_failed > 0 %}
### Failed Tests

{% for failed in failed_tests %}
- **Test {{ failed.number }}:** {{ failed.description }}
  ```
  {{ failed.line }}
  ```
{% endfor %}
{% endif %}
{% else %}
**Raw output captured** ({{ summary }})
{% endif %}

{% if raw_output %}
## Raw Output

```console
{{ raw_output }}
```

{% endif %}
