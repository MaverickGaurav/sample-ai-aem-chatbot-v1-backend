"""
Compliance Service - Handles AEM page compliance checking
"""
from typing import List, Dict, Optional
from datetime import datetime
from models.compliance_rules import ComplianceRules
from services.aem_service import AEMService
from services.ollama_service import OllamaService
from models.schemas import ComplianceResult, CategoryResult, CheckResult
import asyncio
from concurrent.futures import ThreadPoolExecutor
from config import Config


class ComplianceService:
    def __init__(self):
        self.aem_service = AEMService()
        self.ollama_service = OllamaService()
        self.rules = ComplianceRules()
        self.max_concurrent = Config.MAX_CONCURRENT_CHECKS

    def check_page_compliance(
            self,
            page_path: str,
            categories: Optional[List[str]] = None,
            model: str = "gemma:2b"
    ) -> ComplianceResult:
        """
        Run compliance check on a single AEM page

        Args:
            page_path: Path to the AEM page
            categories: Specific categories to check (None = all)
            model: Ollama model to use

        Returns:
            ComplianceResult object
        """
        # Get page content
        content_result = self.aem_service.get_page_content(page_path)

        if not content_result.get('success'):
            return self._create_error_result(
                page_path,
                f"Failed to retrieve page: {content_result.get('error')}"
            )

        html_content = content_result.get('html', '')
        page_title = content_result.get('title', page_path)

        # Determine which categories to check
        all_rules = self.rules.get_all_rules()
        if categories:
            rules_to_check = {k: v for k, v in all_rules.items() if k in categories}
        else:
            rules_to_check = all_rules

        # Run checks for each category
        category_results = []

        for category_name, category_data in rules_to_check.items():
            category_result = self._check_category(
                category_name,
                category_data,
                html_content,
                model
            )
            category_results.append(category_result)

        # Calculate overall score and statistics
        category_scores = {
            cat.category: cat.score for cat in category_results
        }
        overall_score = self.rules.calculate_overall_score(category_scores)

        # Count issues by severity
        total_issues = 0
        high_priority = 0
        medium_priority = 0
        low_priority = 0

        for cat_result in category_results:
            for check in cat_result.checks:
                if not check.passed:
                    total_issues += 1
                    if check.severity == 'high':
                        high_priority += 1
                    elif check.severity == 'medium':
                        medium_priority += 1
                    else:
                        low_priority += 1

        # Determine grade
        grade = self._calculate_grade(overall_score)

        return ComplianceResult(
            page_path=page_path,
            page_title=page_title,
            overall_score=overall_score,
            grade=grade,
            categories=category_results,
            total_issues=total_issues,
            high_priority_issues=high_priority,
            medium_priority_issues=medium_priority,
            low_priority_issues=low_priority,
            checked_at=datetime.now()
        )

    def check_multiple_pages(
            self,
            page_paths: List[str],
            categories: Optional[List[str]] = None,
            model: str = "gemma:2b"
    ) -> List[ComplianceResult]:
        """
        Run compliance checks on multiple pages (with concurrency)

        Args:
            page_paths: List of page paths
            categories: Categories to check
            model: Model to use

        Returns:
            List of compliance results
        """
        results = []

        # Use ThreadPoolExecutor for concurrent checks
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = {
                executor.submit(
                    self.check_page_compliance,
                    path,
                    categories,
                    model
                ): path for path in page_paths
            }

            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    path = futures[future]
                    error_result = self._create_error_result(
                        path,
                        f"Check failed: {str(e)}"
                    )
                    results.append(error_result)

        return results

    def _check_category(
            self,
            category_name: str,
            category_data: Dict,
            html_content: str,
            model: str
    ) -> CategoryResult:
        """
        Check all rules in a category

        Args:
            category_name: Category identifier
            category_data: Category rule data
            html_content: Page HTML
            model: Model to use

        Returns:
            CategoryResult object
        """
        checks = category_data.get('checks', [])
        check_results = []

        for check in checks:
            check_result = self._run_single_check(
                check,
                html_content,
                model
            )
            check_results.append(check_result)

        # Calculate category score
        passed_checks = sum(1 for c in check_results if c.passed)
        total_checks = len(check_results)

        # Weighted score calculation
        total_weight = sum(check['weight'] for check in checks)
        weighted_score = sum(
            check['weight'] for i, check in enumerate(checks)
            if check_results[i].passed
        )
        category_score = (weighted_score / total_weight * 100) if total_weight > 0 else 0

        return CategoryResult(
            category=category_name,
            name=category_data.get('name', category_name),
            score=round(category_score, 2),
            checks=check_results,
            total_checks=total_checks,
            passed_checks=passed_checks
        )

    def _run_single_check(
            self,
            check: Dict,
            html_content: str,
            model: str
    ) -> CheckResult:
        """
        Run a single compliance check using Ollama

        Args:
            check: Check configuration
            html_content: HTML to analyze
            model: Model to use

        Returns:
            CheckResult object
        """
        check_prompt = check.get('prompt', '')

        # Analyze with Ollama
        analysis = self.ollama_service.analyze_html(
            html_content,
            check_prompt,
            model
        )

        passed = analysis.get('passed', False)
        issues = analysis.get('issues', [])
        recommendations = analysis.get('recommendations', [])

        # Calculate check score
        score = 100.0 if passed else 0.0

        return CheckResult(
            id=check.get('id', ''),
            name=check.get('name', ''),
            passed=passed,
            score=score,
            issues=issues,
            recommendations=recommendations,
            severity=check.get('severity', 'medium')
        )

    def _calculate_grade(self, score: float) -> str:
        """
        Calculate letter grade from score

        Args:
            score: Numeric score (0-100)

        Returns:
            Letter grade
        """
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def _create_error_result(self, page_path: str, error_msg: str) -> ComplianceResult:
        """
        Create an error result when compliance check fails

        Args:
            page_path: Page path
            error_msg: Error message

        Returns:
            ComplianceResult with error information
        """
        return ComplianceResult(
            page_path=page_path,
            page_title=f"Error: {page_path}",
            overall_score=0.0,
            grade='F',
            categories=[],
            total_issues=1,
            high_priority_issues=1,
            medium_priority_issues=0,
            low_priority_issues=0,
            checked_at=datetime.now()
        )

    def get_summary_statistics(self, results: List[ComplianceResult]) -> Dict:
        """
        Generate summary statistics from multiple compliance results

        Args:
            results: List of compliance results

        Returns:
            Summary statistics
        """
        if not results:
            return {
                'total_pages': 0,
                'average_score': 0,
                'grade_distribution': {},
                'total_issues': 0
            }

        total_pages = len(results)
        total_score = sum(r.overall_score for r in results)
        average_score = total_score / total_pages if total_pages > 0 else 0

        # Grade distribution
        grade_dist = {}
        for result in results:
            grade = result.grade
            grade_dist[grade] = grade_dist.get(grade, 0) + 1

        # Issue statistics
        total_issues = sum(r.total_issues for r in results)
        total_high = sum(r.high_priority_issues for r in results)
        total_medium = sum(r.medium_priority_issues for r in results)
        total_low = sum(r.low_priority_issues for r in results)

        return {
            'total_pages': total_pages,
            'average_score': round(average_score, 2),
            'grade_distribution': grade_dist,
            'total_issues': total_issues,
            'high_priority_issues': total_high,
            'medium_priority_issues': total_medium,
            'low_priority_issues': total_low,
            'pages_passed': sum(1 for r in results if r.overall_score >= 70),
            'pages_failed': sum(1 for r in results if r.overall_score < 70)
        }