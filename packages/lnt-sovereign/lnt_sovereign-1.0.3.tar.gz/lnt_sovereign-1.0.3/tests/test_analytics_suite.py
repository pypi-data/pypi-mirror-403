import asyncio
from lnt_sovereign.core.monitor import SovereignMonitor
from lnt_sovereign.core.analytics import SovereignAnalyticsEngine
from lnt_sovereign.core.dashboard import SovereignDashboardGenerator

async def verify_analytics():
    print("--- Sovereign Analytics Verification ---")
    monitor = SovereignMonitor()
    analytics = SovereignAnalyticsEngine(monitor)
    dashboard = SovereignDashboardGenerator(output_dir="docs/metrics")

    # Simulate 10 transactions
    for i in range(10):
        is_safe = i % 3 != 0
        violations = [{"id": "RULE_X", "severity": "HIGH"}] if not is_safe else []
        monitor.log_transaction(
            domain="TEST_DOMAIN",
            is_safe=is_safe,
            score=85.0 - (i * 2),
            violations=violations,
            latency_ms=2.5 + (i * 0.1)
        )
    
    summary = analytics.generate_health_summary()
    heatmap = analytics.get_violation_heatmap()
    trends = analytics.get_score_trends()

    print(f"Summary: {summary}")
    print(f"Heatmap: {heatmap}")
    print(f"Trends: {len(trends)} entries recorded.")

    # Generate Dashbaord
    path = dashboard.generate_html_report(summary, heatmap)
    print(f"Visual Report Generated: {path}")

    assert summary['critical_rules_triggered'] == 1
    assert len(trends) == 10
    print("VERIFICATION SUCCESSFUL")

if __name__ == "__main__":
    asyncio.run(verify_analytics())
