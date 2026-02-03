"""
Export Service V2 - FIXED CSV and PDF export
Handles export of compliance results with proper encoding and formatting
"""
import csv
import os
from datetime import datetime
from typing import List
from io import BytesIO
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from config import Config


class ExportService:
    def __init__(self):
        self.upload_folder = Config.UPLOAD_FOLDER
        os.makedirs(self.upload_folder, exist_ok=True)

    def export_to_csv(self, results: List[dict], include_details: bool = True) -> dict:
        """
        Export compliance results to CSV - FIXED VERSION

        Args:
            results: List of compliance result dictionaries
            include_details: Include detailed check results

        Returns:
            Dictionary with file information
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_report_{timestamp}.csv"
        filepath = os.path.join(self.upload_folder, filename)

        try:
            if include_details:
                # Detailed export with all check results
                rows = []

                for result in results:
                    page_path = result.get('page_path', '')
                    page_title = result.get('page_title', '')
                    overall_score = result.get('overall_score', 0)
                    grade = result.get('grade', 'F')
                    total_issues = result.get('total_issues', 0)
                    high_priority = result.get('high_priority_issues', 0)
                    medium_priority = result.get('medium_priority_issues', 0)
                    low_priority = result.get('low_priority_issues', 0)
                    checked_at = result.get('checked_at', datetime.now().isoformat())

                    categories = result.get('categories', [])

                    for category in categories:
                        category_name = category.get('name', '')
                        category_score = category.get('score', 0)

                        checks = category.get('checks', [])
                        for check in checks:
                            rows.append({
                                'Page Path': page_path,
                                'Page Title': page_title,
                                'Overall Score': f"{overall_score:.2f}",
                                'Grade': grade,
                                'Total Issues': total_issues,
                                'High Priority': high_priority,
                                'Medium Priority': medium_priority,
                                'Low Priority': low_priority,
                                'Category': category_name,
                                'Category Score': f"{category_score:.2f}",
                                'Check Name': check.get('name', ''),
                                'Check Status': 'PASS' if check.get('passed', False) else 'FAIL',
                                'Check Score': f"{check.get('score', 0):.2f}",
                                'Issues': '; '.join(check.get('issues', [])),
                                'Recommendations': '; '.join(check.get('recommendations', [])),
                                'Severity': check.get('severity', 'medium').upper(),
                                'Checked At': checked_at
                            })

                # Write using pandas for better encoding handling
                df = pd.DataFrame(rows)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')

            else:
                # Summary export
                rows = []
                for result in results:
                    rows.append({
                        'Page Path': result.get('page_path', ''),
                        'Page Title': result.get('page_title', ''),
                        'Overall Score': f"{result.get('overall_score', 0):.2f}",
                        'Grade': result.get('grade', 'F'),
                        'Total Issues': result.get('total_issues', 0),
                        'High Priority': result.get('high_priority_issues', 0),
                        'Medium Priority': result.get('medium_priority_issues', 0),
                        'Low Priority': result.get('low_priority_issues', 0),
                        'Checked At': result.get('checked_at', datetime.now().isoformat())
                    })

                df = pd.DataFrame(rows)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')

            file_size = os.path.getsize(filepath)

            return {
                'success': True,
                'file_path': filepath,
                'file_name': filename,
                'format': 'csv',
                'size_bytes': file_size
            }

        except Exception as e:
            print(f"CSV Export Error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def export_to_pdf(self, results: List[dict], include_details: bool = True) -> dict:
        """
        Export compliance results to PDF - FIXED VERSION

        Args:
            results: List of compliance result dictionaries
            include_details: Include detailed check results

        Returns:
            Dictionary with file information
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_report_{timestamp}.pdf"
        filepath = os.path.join(self.upload_folder, filename)

        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )

            elements = []
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1e40af'),
                spaceAfter=30,
                alignment=TA_CENTER
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#1e40af'),
                spaceAfter=12,
                spaceBefore=12
            )

            # Title
            title = Paragraph("AEM Compliance Report", title_style)
            elements.append(title)

            # Report metadata
            report_date = Paragraph(
                f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles['Normal']
            )
            elements.append(report_date)
            elements.append(Spacer(1, 0.2 * inch))

            # Summary statistics
            total_pages = len(results)
            avg_score = sum(r.get('overall_score', 0) for r in results) / total_pages if total_pages > 0 else 0
            total_issues = sum(r.get('total_issues', 0) for r in results)

            summary_data = [
                ['Metric', 'Value'],
                ['Total Pages Analyzed', str(total_pages)],
                ['Average Score', f"{avg_score:.2f}%"],
                ['Total Issues Found', str(total_issues)],
                ['High Priority Issues', str(sum(r.get('high_priority_issues', 0) for r in results))],
                ['Medium Priority Issues', str(sum(r.get('medium_priority_issues', 0) for r in results))],
                ['Low Priority Issues', str(sum(r.get('low_priority_issues', 0) for r in results))]
            ]

            summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e7ff')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))

            elements.append(Paragraph("Executive Summary", heading_style))
            elements.append(summary_table)
            elements.append(Spacer(1, 0.3 * inch))

            # Individual page results
            for idx, result in enumerate(results):
                if idx > 0:
                    elements.append(PageBreak())

                # Page header
                page_title_text = result.get('page_title', 'Unknown Page')
                page_title = Paragraph(f"<b>Page {idx + 1}:</b> {page_title_text}", heading_style)
                elements.append(page_title)

                # Page details
                page_info = [
                    ['Field', 'Value'],
                    ['Path', result.get('page_path', '')],
                    ['Overall Score', f"{result.get('overall_score', 0):.2f}%"],
                    ['Grade', result.get('grade', 'F')],
                    ['Total Issues', str(result.get('total_issues', 0))]
                ]

                page_table = Table(page_info, colWidths=[1.5 * inch, 4 * inch])
                page_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('PADDING', (0, 0), (-1, -1), 6)
                ]))
                elements.append(page_table)
                elements.append(Spacer(1, 0.2 * inch))

                if include_details:
                    # Category results
                    categories = result.get('categories', [])
                    for category in categories:
                        cat_header = Paragraph(
                            f"<b>{category.get('name', 'Unknown Category')}</b> - Score: {category.get('score', 0):.2f}%",
                            styles['Heading3']
                        )
                        elements.append(cat_header)

                        # Check results table
                        check_data = [['Check', 'Status', 'Severity', 'Issues']]

                        checks = category.get('checks', [])
                        for check in checks:
                            status = '✓ PASS' if check.get('passed', False) else '✗ FAIL'
                            issues = check.get('issues', [])
                            issues_text = issues[0][:50] + '...' if issues and len(issues[0]) > 50 else (
                                issues[0] if issues else 'None')

                            check_data.append([
                                check.get('name', ''),
                                status,
                                check.get('severity', 'medium').upper(),
                                issues_text
                            ])

                        check_table = Table(check_data, colWidths=[2 * inch, 0.8 * inch, 0.8 * inch, 2 * inch])
                        check_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e7ff')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('PADDING', (0, 0), (-1, -1), 4),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP')
                        ]))
                        elements.append(check_table)
                        elements.append(Spacer(1, 0.15 * inch))

            # Build PDF
            doc.build(elements)

            file_size = os.path.getsize(filepath)

            return {
                'success': True,
                'file_path': filepath,
                'file_name': filename,
                'format': 'pdf',
                'size_bytes': file_size
            }

        except Exception as e:
            print(f"PDF Export Error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def export_results(self, results: List[dict], format: str = 'csv', include_details: bool = True) -> dict:
        """
        Export results in specified format

        Args:
            results: Compliance results (as dictionaries)
            format: Export format ('csv' or 'pdf')
            include_details: Include detailed results

        Returns:
            Export information
        """
        if not results:
            return {
                'success': False,
                'error': 'No results to export'
            }

        if format.lower() == 'csv':
            return self.export_to_csv(results, include_details)
        elif format.lower() == 'pdf':
            return self.export_to_pdf(results, include_details)
        else:
            return {
                'success': False,
                'error': f'Unsupported format: {format}'
            }