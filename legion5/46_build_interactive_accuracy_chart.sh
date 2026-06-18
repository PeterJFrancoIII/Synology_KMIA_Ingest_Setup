# Build chart suite: golden-master PNG + unified HTML dashboard.
# Usage: 46_build_interactive_accuracy_chart.sh STUDY_NAME YEAR
exec "$(dirname "$0")/47_build_kmia_chart_suite.sh" "$@"
