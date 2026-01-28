"""
Export Service - Handles CSV and PDF export of compliance results
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
from models.schemas import ComplianceResult
from config import Config


class ExportService:
    def __init__(self):
        self.upload_folder = Config.UPLOAD_FOLDER
        os.makedirs(self.upload_folder, exist_ok=True)

    def export_to_csv(
            self,
            results: List[ComplianceResult],
            include_details: bool = True
    ) -> dict:
        """
        Export compliance results to CSV

        Args:
            results: List of compliance results
            include_details: Include detailed check results

        Returns:
            Dictionary with file information
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_report_{timestamp}.csv"
        filepath = os.path.join(self.upload_folder, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            if include_details:
                # Detailed export with all check results
                fieldnames = [
                    'Page Path', 'Page Title', 'Overall Score', 'Grade',
                    'Total Issues', 'High Priority', 'Medium Priority', 'Low Priority',
                    'Category', 'Category Score', 'Check Name', 'Check Status',
                    'Check Score', 'Issues', 'Recommendations', 'Severity',
                    'Checked At'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for result in results:
                    for category in result.categories:
                        for check in category.checks:
                            writer.writerow({
                                'Page Path': result.page_path,
                                'Page Title': result.page_title,
                                'Overall Score': result.overall_score,
                                'Grade': result.grade,
                                'Total Issues': result.total_issues,
                                'High Priority': result.high_priority_issues,
                                'Medium Priority': result.medium_priority_issues,
                                'Low Priority': result.low_priority_issues,
                                'Category': category.name,
                                'Category Score': category.score,
                                'Check Name': check.name,
                                'Check Status': 'PASS' if check.passed else 'FAIL',
                                'Check Score': check.score,
                                'Issues': '; '.join(check.issues),
                                'Recommendations': '; '.join(check.recommendations),
                                'Severity': check.severity.upper(),
                                'Checked At': result.checked_at.strftime("%Y-%m-%d %H:%M:%S")
                            })
            else:
                # Summary export
                fieldnames = [
                    'Page Path', 'Page Title', 'Overall Score', 'Grade',
                    'Total Issues', 'High Priority', 'Medium Priority',
                    'Low Priority', 'Checked At'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for result in results:
                    writer.writerow({
                        'Page Path': result.page_path,
                        'Page Title': result.page_title,
                        'Overall Score': result.overall_score,
                        'Grade': result.grade,
                        'Total Issues': result.total_issues,
                        'High Priority': result.high_priority_issues,
                        'Medium Priority': result.medium_priority_issues,
                        'Low Priority': result.low_priority_issues,
                        'Checked At': result.checked_at.strftime("%Y-%m-%d %H:%M:%S")
                    })

        file_size = os.path.getsize(filepath)

        return {
            'success': True,
            'file_path': filepath,
            'file_name': filename,
            'format': 'csv',
            'size_bytes': file_size
        }

    def export_to_pdf(
            self,
            results: List[ComplianceResult],
            include_details: bool = True
    ) -> dict:
        """
        Export compliance results to PDF

        Args:
            results: List of compliance results
            include_details: Include detailed check results

        Returns:
            Dictionary with file information
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_report_{timestamp}.pdf"
        filepath = os.path.join(self.upload_folder, filename)

        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        # Container for PDF elements
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
        avg_score = sum(r.overall_score for r in results) / total_pages if total_pages > 0 else 0
        total_issues = sum(r.total_issues for r in results)

        summary_data = [
            ['Total Pages Analyzed', str(total_pages)],
            ['Average Score', f"{avg_score:.2f}"],
            ['Total Issues Found', str(total_issues)],
            ['High Priority Issues', str(sum(r.high_priority_issues for r in results))],
            ['Medium Priority Issues', str(sum(r.medium_priority_issues for r in results))],
            ['Low Priority Issues', str(sum(r.low_priority_issues for r in results))]
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
            page_title = Paragraph(
                f"<b>Page {idx + 1}:</b> {result.page_title}",
                heading_style
            )
            elements.append(page_title)

            # Page details
            page_info = [
                ['Path', result.page_path],
                ['Overall Score', f"{result.overall_score:.2f}"],
                ['Grade', result.grade],
                ['Total Issues', str(result.total_issues)]
            ]

            page_table = Table(page_info, colWidths=[1.5 * inch, 4 * inch])
            page_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('PADDING', (0, 0), (-1, -1), 6)
            ]))
            elements.append(page_table)
            elements.append(Spacer(1, 0.2 * inch))

            if include_details:
                # Category results
                for category in result.categories:
                    cat_header = Paragraph(
                        f"<b>{category.name}</b> - Score: {category.score:.2f}%",
                        styles['Heading3']
                    )
                    elements.append(cat_header)

                    # Check results table
                    check_data = [['Check', 'Status', 'Severity', 'Issues']]

                    for check in category.checks:
                        status = '✓ PASS' if check.passed else '✗ FAIL'
                        issues_text = check.issues[0][:50] + '...' if check.issues and len(check.issues[0]) > 50 else (
                            check.issues[0] if check.issues else 'None')

                        check_data.append([
                            check.name,
                            status,
                            check.severity.upper(),
                            issues_text
                        ])

                    check_table = Table(
                        check_data,
                        colWidths=[2 * inch, 0.8 * inch, 0.8 * inch, 2 * inch]
                    )
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

    def export_results(
            self,
            results: List[ComplianceResult],
            format: str = 'csv',
            include_details: bool = True
    ) -> dict:
        """
        Export results in specified format

        Args:
            results: Compliance results
            format: Export format ('csv' or 'pdf')
            include_details: Include detailed results

        Returns:
            Export information
        """
        if format.lower() == 'csv':
            return self.export_to_csv(results, include_details)
        elif format.lower() == 'pdf':
            return self.export_to_pdf(results, include_details)
        else:
            return {
                'success': False,
                'error': f'Unsupported format: {format}'
            }