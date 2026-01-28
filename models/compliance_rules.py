"""
AEM Compliance Rules with scoring and weighting
"""


class ComplianceRules:
    """Defines all compliance rules for AEM pages"""

    RULES = {
        'accessibility': {
            'name': 'Accessibility Compliance',
            'weight': 0.25,
            'checks': [
                {
                    'id': 'alt_text',
                    'name': 'Image Alt Text',
                    'description': 'All images must have descriptive alt text',
                    'severity': 'high',
                    'weight': 0.3,
                    'prompt': 'Check if all images in this HTML have alt text attributes. List any images missing alt text.'
                },
                {
                    'id': 'heading_hierarchy',
                    'name': 'Heading Hierarchy',
                    'description': 'Headings must follow proper hierarchy (h1, h2, h3, etc.)',
                    'severity': 'high',
                    'weight': 0.25,
                    'prompt': 'Analyze the heading structure. Are headings in proper hierarchy? List any issues.'
                },
                {
                    'id': 'aria_labels',
                    'name': 'ARIA Labels',
                    'description': 'Interactive elements should have ARIA labels',
                    'severity': 'medium',
                    'weight': 0.2,
                    'prompt': 'Check if buttons, links, and interactive elements have appropriate ARIA labels.'
                },
                {
                    'id': 'color_contrast',
                    'name': 'Color Contrast',
                    'description': 'Text should have sufficient color contrast',
                    'severity': 'medium',
                    'weight': 0.15,
                    'prompt': 'Review inline styles and classes for potential color contrast issues.'
                },
                {
                    'id': 'keyboard_navigation',
                    'name': 'Keyboard Navigation',
                    'description': 'All interactive elements should be keyboard accessible',
                    'severity': 'high',
                    'weight': 0.1,
                    'prompt': 'Check if interactive elements have tabindex or are naturally keyboard accessible.'
                }
            ]
        },
        'seo': {
            'name': 'SEO Best Practices',
            'weight': 0.2,
            'checks': [
                {
                    'id': 'title_tag',
                    'name': 'Title Tag',
                    'description': 'Page must have a unique, descriptive title tag',
                    'severity': 'high',
                    'weight': 0.3,
                    'prompt': 'Does this page have a title tag? Is it descriptive and under 60 characters?'
                },
                {
                    'id': 'meta_description',
                    'name': 'Meta Description',
                    'description': 'Page should have a meta description',
                    'severity': 'high',
                    'weight': 0.25,
                    'prompt': 'Check for meta description tag. Is it present and under 160 characters?'
                },
                {
                    'id': 'h1_tag',
                    'name': 'H1 Tag',
                    'description': 'Page should have exactly one H1 tag',
                    'severity': 'medium',
                    'weight': 0.2,
                    'prompt': 'How many H1 tags are on this page? There should be exactly one.'
                },
                {
                    'id': 'canonical_url',
                    'name': 'Canonical URL',
                    'description': 'Page should have a canonical URL',
                    'severity': 'low',
                    'weight': 0.15,
                    'prompt': 'Is there a canonical link tag present?'
                },
                {
                    'id': 'image_optimization',
                    'name': 'Image Optimization',
                    'description': 'Images should have appropriate format and size',
                    'severity': 'medium',
                    'weight': 0.1,
                    'prompt': 'Review image tags for lazy loading attributes and appropriate formats.'
                }
            ]
        },
        'performance': {
            'name': 'Performance Optimization',
            'weight': 0.2,
            'checks': [
                {
                    'id': 'script_async',
                    'name': 'Async Scripts',
                    'description': 'Scripts should be loaded asynchronously when possible',
                    'severity': 'medium',
                    'weight': 0.3,
                    'prompt': 'Check script tags. Are they using async or defer attributes?'
                },
                {
                    'id': 'css_inline',
                    'name': 'Inline CSS',
                    'description': 'Critical CSS should be inline, non-critical external',
                    'severity': 'low',
                    'weight': 0.2,
                    'prompt': 'Analyze CSS loading. Is there excessive inline CSS?'
                },
                {
                    'id': 'lazy_loading',
                    'name': 'Lazy Loading',
                    'description': 'Images below fold should use lazy loading',
                    'severity': 'medium',
                    'weight': 0.25,
                    'prompt': 'Are images using loading="lazy" attribute?'
                },
                {
                    'id': 'resource_hints',
                    'name': 'Resource Hints',
                    'description': 'Use preload, prefetch for critical resources',
                    'severity': 'low',
                    'weight': 0.15,
                    'prompt': 'Check for link rel="preload" or rel="prefetch" tags.'
                },
                {
                    'id': 'compression',
                    'name': 'Resource Compression',
                    'description': 'Resources should be compressed',
                    'severity': 'medium',
                    'weight': 0.1,
                    'prompt': 'Review if inline scripts/styles appear minified.'
                }
            ]
        },
        'security': {
            'name': 'Security Headers',
            'weight': 0.15,
            'checks': [
                {
                    'id': 'csp',
                    'name': 'Content Security Policy',
                    'description': 'Page should have CSP meta tag',
                    'severity': 'high',
                    'weight': 0.3,
                    'prompt': 'Is there a Content-Security-Policy meta tag?'
                },
                {
                    'id': 'external_links',
                    'name': 'External Links Security',
                    'description': 'External links should have rel="noopener noreferrer"',
                    'severity': 'medium',
                    'weight': 0.25,
                    'prompt': 'Check external links for rel="noopener noreferrer" attributes.'
                },
                {
                    'id': 'form_validation',
                    'name': 'Form Validation',
                    'description': 'Forms should have proper validation',
                    'severity': 'high',
                    'weight': 0.2,
                    'prompt': 'Review forms for validation attributes and security measures.'
                },
                {
                    'id': 'https_resources',
                    'name': 'HTTPS Resources',
                    'description': 'All resources should load over HTTPS',
                    'severity': 'high',
                    'weight': 0.15,
                    'prompt': 'Check if all src/href attributes use HTTPS URLs.'
                },
                {
                    'id': 'input_sanitization',
                    'name': 'Input Sanitization',
                    'description': 'User inputs should be sanitized',
                    'severity': 'high',
                    'weight': 0.1,
                    'prompt': 'Review if there are any potential XSS vulnerabilities in the code.'
                }
            ]
        },
        'content_quality': {
            'name': 'Content Quality',
            'weight': 0.1,
            'checks': [
                {
                    'id': 'broken_links',
                    'name': 'Broken Links',
                    'description': 'No broken or empty links',
                    'severity': 'medium',
                    'weight': 0.3,
                    'prompt': 'Identify any links with empty href or href="#".'
                },
                {
                    'id': 'duplicate_content',
                    'name': 'Duplicate Content',
                    'description': 'Avoid duplicate text blocks',
                    'severity': 'low',
                    'weight': 0.2,
                    'prompt': 'Check for repeated paragraphs or content blocks.'
                },
                {
                    'id': 'readability',
                    'name': 'Content Readability',
                    'description': 'Content should be clear and well-structured',
                    'severity': 'low',
                    'weight': 0.25,
                    'prompt': 'Assess paragraph length and sentence structure for readability.'
                },
                {
                    'id': 'language_tag',
                    'name': 'Language Tag',
                    'description': 'HTML should have lang attribute',
                    'severity': 'medium',
                    'weight': 0.15,
                    'prompt': 'Does the HTML tag have a lang attribute?'
                },
                {
                    'id': 'content_structure',
                    'name': 'Content Structure',
                    'description': 'Content should use semantic HTML',
                    'severity': 'low',
                    'weight': 0.1,
                    'prompt': 'Review use of semantic tags like article, section, nav, aside.'
                }
            ]
        },
        'aem_specific': {
            'name': 'AEM Best Practices',
            'weight': 0.1,
            'checks': [
                {
                    'id': 'component_structure',
                    'name': 'Component Structure',
                    'description': 'AEM components should follow best practices',
                    'severity': 'medium',
                    'weight': 0.3,
                    'prompt': 'Review data-cq-* attributes and component structure.'
                },
                {
                    'id': 'clientlibs',
                    'name': 'Client Libraries',
                    'description': 'Proper use of AEM clientlibs',
                    'severity': 'low',
                    'weight': 0.25,
                    'prompt': 'Check for proper clientlib categories and dependencies.'
                },
                {
                    'id': 'edit_mode',
                    'name': 'Edit Mode Config',
                    'description': 'Components should have edit configurations',
                    'severity': 'low',
                    'weight': 0.2,
                    'prompt': 'Look for cq:editConfig or related AEM authoring configurations.'
                },
                {
                    'id': 'responsive_grid',
                    'name': 'Responsive Grid',
                    'description': 'Use AEM responsive grid system',
                    'severity': 'low',
                    'weight': 0.15,
                    'prompt': 'Check for responsive grid classes and breakpoints.'
                },
                {
                    'id': 'sling_models',
                    'name': 'Sling Models',
                    'description': 'Efficient use of Sling models',
                    'severity': 'low',
                    'weight': 0.1,
                    'prompt': 'Review data-sly-use for efficient model usage.'
                }
            ]
        }
    }

    @classmethod
    def get_all_rules(cls):
        """Get all compliance rules"""
        return cls.RULES

    @classmethod
    def get_category_rules(cls, category):
        """Get rules for a specific category"""
        return cls.RULES.get(category, {})

    @classmethod
    def get_total_checks(cls):
        """Get total number of checks across all categories"""
        total = 0
        for category in cls.RULES.values():
            total += len(category.get('checks', []))
        return total

    @classmethod
    def calculate_category_score(cls, results, category):
        """Calculate weighted score for a category"""
        category_data = cls.RULES.get(category)
        if not category_data:
            return 0

        checks = category_data.get('checks', [])
        total_weight = sum(check['weight'] for check in checks)
        weighted_score = 0

        for check in checks:
            check_result = results.get(check['id'], {})
            if check_result.get('passed', False):
                weighted_score += check['weight']

        return (weighted_score / total_weight) * 100 if total_weight > 0 else 0

    @classmethod
    def calculate_overall_score(cls, category_scores):
        """Calculate overall weighted compliance score"""
        total_weighted_score = 0

        for category, score in category_scores.items():
            category_weight = cls.RULES.get(category, {}).get('weight', 0)
            total_weighted_score += score * category_weight

        return round(total_weighted_score, 2)

    @classmethod
    def get_severity_counts(cls, results):
        """Count issues by severity"""
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}

        for category_name, category_data in cls.RULES.items():
            for check in category_data.get('checks', []):
                check_result = results.get(category_name, {}).get(check['id'], {})
                if not check_result.get('passed', True):
                    severity = check['severity']
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return severity_counts