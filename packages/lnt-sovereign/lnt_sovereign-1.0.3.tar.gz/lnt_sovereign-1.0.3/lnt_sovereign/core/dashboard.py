from typing import Dict, Any
import os
from datetime import datetime

class SovereignDashboardGenerator:
    """
    Generates high-impact visual decision reports for LNT.
    Transforms raw analytics into actionable insights.
    """
    def __init__(self, output_dir: str = "docs/metrics") -> None:
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_html_report(self, summary: Dict[str, Any], heatmap: Dict[str, int]) -> str:
        """Creates a standalone HTML dashboard for the Sovereign Portal."""
        
        # Simple CSS-heavy dashboard template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LNT Sovereign Health Report</title>
            <style>
                body {{ font-family: 'Inter', sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; }}
                .container {{ max-width: 1000px; margin: 0 auto; }}
                .header {{ border-bottom: 2px solid #b45309; padding-bottom: 20px; margin-bottom: 40px; }}
                .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
                .card {{ background: #1e293b; padding: 25px; border-radius: 12px; border: 1px solid #334155; }}
                .metric {{ font-size: 2.5em; font-weight: bold; color: #fbbf24; }}
                .label {{ text-transform: uppercase; letter-spacing: 1px; font-size: 0.8em; color: #94a3b8; }}
                .heatmap {{ margin-top: 40px; }}
                .bar {{ height: 20px; background: #b45309; margin: 10px 0; border-radius: 4px; }}
                .status-certified {{ color: #4ade80; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Sovereign Grade Intelligence Report</h1>
                    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    <p class="status-certified">Status: {summary['overall_status']}</p>
                </div>
                
                <div class="grid">
                    <div class="card">
                        <div class="label">Hallucination Rate</div>
                        <div class="metric">{summary['hallucination_rate']}</div>
                    </div>
                    <div class="card">
                        <div class="label">Avg Latency</div>
                        <div class="metric">{summary['performance']['avg_latency_ms']}ms</div>
                    </div>
                    <div class="card">
                        <div class="label">Total Rules Triggered</div>
                        <div class="metric">{sum(heatmap.values())}</div>
                    </div>
                </div>

                <div class="heatmap">
                    <h2>Rule Violation Heatmap</h2>
                    {self._generate_bars(heatmap)}
                </div>
            </div>
        </body>
        </html>
        """
        
        output_path = os.path.join(self.output_dir, "sovereign_health.html")
        with open(output_path, "w") as f:
            f.write(html)
        
        return output_path

    def _generate_bars(self, heatmap: Dict[str, int]) -> str:
        bars = ""
        max_val = max(heatmap.values()) if heatmap else 1
        for rule_id, count in sorted(heatmap.items(), key=lambda x: x[1], reverse=True)[:10]:
            width = (count / max_val) * 100
            bars += f"""
            <div>
                <span class="label">{rule_id} ({count} triggers)</span>
                <div class="bar" style="width: {width}%"></div>
            </div>
            """
        return bars
