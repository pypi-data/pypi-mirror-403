import os
from pathlib import Path
from datetime import datetime
from typing import List
import base64
from ..actions import ActionResult


class HTMLReporter:
    """Generates HTML test reports with embedded screenshots"""
    
    def __init__(self, output_dir: str = "./test-results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(
        self, 
        test_description: str,
        results: List[ActionResult],
        start_time: datetime,
        end_time: datetime,
        output_dir: str = None
    ) -> str:
        """
        Generate HTML report with test results.
        
        Args:
            output_dir: Optional directory to save report (overrides instance output_dir)
        
        Returns:
            Path to the generated HTML report
        """
        # Use provided output_dir or fall back to instance output_dir
        report_dir = Path(output_dir) if output_dir else self.output_dir
        report_dir.mkdir(parents=True, exist_ok=True)
        
        duration = (end_time - start_time).total_seconds()
        passed = sum(1 for r in results if r.success)
        failed = len(results) - passed
        
        html = self._generate_html(
            test_description=test_description,
            results=results,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            passed=passed,
            failed=failed
        )
        
        # Save report with simpler name since it's in a timestamped directory
        report_path = report_dir / "report.html"
        report_path.write_text(html, encoding='utf-8')
        
        return str(report_path)
    
    def _generate_html(
        self, 
        test_description: str,
        results: List[ActionResult],
        start_time: datetime,
        end_time: datetime,
        duration: float,
        passed: int,
        failed: int
    ) -> str:
        """Generate the HTML content"""
        
        status_color = "#00c851" if failed == 0 else "#ff4444"
        status_text = "PASS" if failed == 0 else "FAIL"
        
        # Generate results rows
        results_html = []
        for i, result in enumerate(results, 1):
            results_html.append(self._generate_result_row(i, result))
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - Agentic Test Framework</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}
        
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        .header p {{
            opacity: 0.9;
            font-size: 14px;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .summary-card .label {{
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        
        .summary-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        
        .summary-card.status {{
            background: {status_color};
            color: white;
        }}
        
        .summary-card.status .label,
        .summary-card.status .value {{
            color: white;
        }}
        
        .test-description {{
            padding: 30px;
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            margin: 20px 30px;
            border-radius: 4px;
        }}
        
        .test-description h3 {{
            margin-bottom: 10px;
            color: #856404;
        }}
        
        .test-description p {{
            color: #856404;
            white-space: pre-wrap;
        }}
        
        .results {{
            padding: 30px;
        }}
        
        .results h2 {{
            margin-bottom: 20px;
            color: #333;
        }}
        
        .result-item {{
            border: 1px solid #dee2e6;
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
            transition: box-shadow 0.3s;
        }}
        
        .result-item:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .result-header {{
            padding: 15px 20px;
            background: #f8f9fa;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 15px;
            user-select: none;
        }}
        
        .result-header:hover {{
            background: #e9ecef;
        }}
        
        .step-number {{
            background: #667eea;
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
        }}
        
        .status-badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .status-badge.pass {{
            background: #d4edda;
            color: #155724;
        }}
        
        .status-badge.fail {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .result-title {{
            flex: 1;
            font-weight: 500;
        }}
        
        .action-type {{
            background: #e7f3ff;
            color: #004085;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        
        .expand-icon {{
            width: 20px;
            height: 20px;
            transition: transform 0.3s;
        }}
        
        .result-item.expanded .expand-icon {{
            transform: rotate(180deg);
        }}
        
        .result-details {{
            padding: 20px;
            background: white;
            border-top: 1px solid #dee2e6;
            display: none;
        }}
        
        .result-item.expanded .result-details {{
            display: block;
        }}
        
        .detail-row {{
            margin-bottom: 15px;
        }}
        
        .detail-label {{
            font-weight: 600;
            color: #495057;
            margin-bottom: 5px;
        }}
        
        .detail-value {{
            color: #6c757d;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }}
        
        .screenshot {{
            margin-top: 15px;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #dee2e6;
        }}
        
        .screenshot img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        
        .error-message {{
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #f5c6cb;
            margin-top: 10px;
        }}
        
        .extracted-data {{
            background: #d1ecf1;
            color: #0c5460;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #bee5eb;
            margin-top: 10px;
            font-weight: 600;
        }}
        
        .comparison-table {{
            margin-top: 15px;
            width: 100%;
            border-collapse: collapse;
            background: #fff;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .comparison-table th {{
            background: #f8d7da;
            color: #721c24;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #f5c6cb;
        }}
        
        .comparison-table td {{
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
            vertical-align: top;
            word-break: break-word;
        }}
        
        .comparison-table tr:last-child td {{
            border-bottom: none;
        }}
        
        .comparison-label {{
            font-weight: 600;
            color: #495057;
            min-width: 100px;
        }}
        
        .comparison-value {{
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #333;
            background: #f8f9fa;
            padding: 8px;
            border-radius: 4px;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
            border-top: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Agentic Test Framework</h1>
            <p>AI-Powered Browser Testing Report</p>
        </div>
        
        <div class="summary">
            <div class="summary-card status">
                <div class="label">Status</div>
                <div class="value">{status_text}</div>
            </div>
            <div class="summary-card">
                <div class="label">Total Steps</div>
                <div class="value">{len(results)}</div>
            </div>
            <div class="summary-card">
                <div class="label">Passed</div>
                <div class="value" style="color: #00c851;">{passed}</div>
            </div>
            <div class="summary-card">
                <div class="label">Failed</div>
                <div class="value" style="color: #ff4444;">{failed}</div>
            </div>
            <div class="summary-card">
                <div class="label">Duration</div>
                <div class="value">{duration:.2f}s</div>
            </div>
            <div class="summary-card">
                <div class="label">Start Time</div>
                <div class="value" style="font-size: 14px;">{start_time.strftime("%H:%M:%S")}</div>
            </div>
        </div>
        
        <div class="test-description">
            <h3>📝 Test Description</h3>
            <p>{test_description}</p>
        </div>
        
        <div class="results">
            <h2>Test Execution Steps</h2>
            {''.join(results_html)}
        </div>
        
        <div class="footer">
            <p>Generated by Agentic Test Framework | {end_time.strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
    
    <script>
        document.querySelectorAll('.result-header').forEach(header => {{
            header.addEventListener('click', () => {{
                header.parentElement.classList.toggle('expanded');
            }});
        }});
        
        // Expand failed tests by default
        document.querySelectorAll('.result-item').forEach(item => {{
            if (item.querySelector('.status-badge.fail')) {{
                item.classList.add('expanded');
            }}
        }});
    </script>
</body>
</html>"""
        
        return html
    
    def _generate_result_row(self, step_number: int, result: ActionResult) -> str:
        """Generate HTML for a single result row"""
        status_class = "pass" if result.success else "fail"
        status_text = "✓ PASS" if result.success else "✗ FAIL"
        
        # Build details section
        details_html = f"""
            <div class="detail-row">
                <div class="detail-label">Message</div>
                <div class="detail-value">{result.message}</div>
            </div>
        """
        
        if result.extracted_data:
            details_html += f"""
            <div class="extracted-data">
                <strong>📊 Extracted Data:</strong> {result.extracted_data}
            </div>
            """
        
        if result.error:
            details_html += f"""
            <div class="error-message">
                <strong>❌ Error:</strong> {result.error}
            </div>
            """
            
            # Show expected vs actual comparison for failed assertions
            if result.metadata.get('expected') and result.metadata.get('actual'):
                expected = result.metadata['expected']
                actual = result.metadata['actual']
                details_html += f"""
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th colspan="2">📋 Comparison Details</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="comparison-label">Expected:</td>
                        <td class="comparison-value">{expected}</td>
                    </tr>
                    <tr>
                        <td class="comparison-label">Actual:</td>
                        <td class="comparison-value">{actual}</td>
                    </tr>
                </tbody>
            </table>
            """
        
        if result.screenshot_path and Path(result.screenshot_path).exists():
            # Embed screenshot as base64
            with open(result.screenshot_path, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')
            details_html += f"""
            <div class="screenshot">
                <img src="data:image/png;base64,{img_data}" alt="Screenshot">
            </div>
            """
        
        return f"""
        <div class="result-item">
            <div class="result-header">
                <div class="step-number">{step_number}</div>
                <span class="status-badge {status_class}">{status_text}</span>
                <span class="action-type">{result.action.type}</span>
                <span class="result-title">{result.action.description}</span>
                <svg class="expand-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
            </div>
            <div class="result-details">
                {details_html}
            </div>
        </div>
        """
