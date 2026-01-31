# SECURITY

- pywheelhouse prints the full pip command before execution. Avoid putting
  secrets directly in command-line args if logs are retained.
- Prefer environment variables or pip configuration files for credentials.
- If you pass `--index-url` or `--extra-index-url` with tokens, treat logs as
  sensitive.
- Use `--no-index` and a prebuilt wheelhouse to avoid unintended network access.
