# Project Log

Generated: {{ generation_date }}  
Repository: {{ repo_path }}  
Branch: {{ current_branch }}

**Total Items:** {{ total_items }} ({{ total_commits }} commits, {{ total_tests }} tests, {{ total_entries }} entries)

---

{% for item in items %}
![[{{ item.path }}]]
{% endfor %}
