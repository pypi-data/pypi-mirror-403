"""
Glyph Markup Example Snippets
==============================

Copy-pastable examples for docs and tests.
"""

# Basic examples
BASIC_TEXT = """\
$glyph-font-size-12
This is a simple paragraph with 12pt font.
$glyph
"""

BASIC_TWO_COLUMN = """\
$glyph-layout-col-2-font-size-11
This is a two-column section with 11pt font.

Second paragraph in the same section.
$glyph

This is back to single column.
"""

FORMATTED_HEADING = """\
$glyph-font-size-24-bold-align-center-space-after-12pt
Document Title
$glyph

$glyph-font-size-16-bold-space-before-10pt-space-after-6pt
Section Heading
$glyph

Body text goes here with normal formatting.
"""

# Domain-specific examples
ACADEMIC_PAPER = """\
$glyph-font-size-14-bold-align-center-space-after-12pt
The Impact of Tailwind-Style Markup on Document Generation
$glyph

$glyph-align-center-space-after-24pt
John Doe
University of Example
john.doe@example.edu
$glyph

$glyph-font-size-12-bold-space-before-12pt-space-after-6pt
Abstract
$glyph

$glyph-indent-left-36pt-indent-right-36pt-align-justify
This paper explores the application of Tailwind CSS-inspired utility classes to document markup languages. We demonstrate that composable, order-independent class tokens provide superior ergonomics for LLM-driven document generation compared to traditional markup languages.
$glyph

$glyph-font-size-12-bold-space-before-12pt-space-after-6pt
1. Introduction
$glyph

$glyph-align-justify-indent-first-line-36pt
Document generation has long relied on markup languages like LaTeX and Markdown. However, these systems were designed for human authorship, not machine generation. In this paper, we present Glyph Markup, a novel approach inspired by utility-first CSS frameworks.
$glyph

$glyph-align-justify-indent-first-line-36pt
The key insight is that LLMs benefit from declarative, composable utilities that can be combined in arbitrary order without syntactic constraints. This contrasts sharply with nested tag-based markup, which requires careful balancing and structural awareness.
$glyph
"""

BUSINESS_LETTER = """\
$glyph-align-right-space-after-12pt
Acme Corporation
123 Business St
New York, NY 10001
$glyph

$glyph-space-after-12pt
January 15, 2025
$glyph

$glyph-space-after-12pt
Jane Smith
456 Client Ave
Los Angeles, CA 90001
$glyph

$glyph-space-after-12pt
Dear Ms. Smith,
$glyph

$glyph-align-justify-space-after-12pt
Thank you for your interest in our services. We are pleased to present our proposal for your upcoming project.
$glyph

$glyph-align-justify-space-after-12pt
Our team has extensive experience in delivering high-quality solutions that meet and exceed client expectations. We are confident that we can provide the expertise and support you need to achieve your goals.
$glyph

$glyph-space-after-12pt
Please feel free to contact us if you have any questions.
$glyph

$glyph-space-after-12pt
Sincerely,

John Doe
CEO, Acme Corporation
$glyph
"""

RESUME = """\
$glyph-font-size-24-bold-align-center
John Doe
$glyph

$glyph-align-center-space-after-12pt
john.doe@email.com | (555) 123-4567 | linkedin.com/in/johndoe
$glyph

$glyph-font-size-14-bold-space-before-12pt-space-after-6pt
EXPERIENCE
$glyph

$glyph-bold
Senior Software Engineer
$glyph
$glyph-italic
Tech Company Inc. | 2020 - Present
$glyph

$glyph-space-before-6pt-space-after-6pt
• Led development of microservices architecture serving 1M+ users
• Improved system performance by 40% through optimization
• Mentored junior engineers and conducted code reviews
$glyph

$glyph-bold
Software Engineer
$glyph
$glyph-italic
Startup Co. | 2018 - 2020
$glyph

$glyph-space-before-6pt-space-after-6pt
• Built RESTful APIs using Python and Flask
• Implemented CI/CD pipelines reducing deployment time by 60%
• Collaborated with product team on feature development
$glyph

$glyph-font-size-14-bold-space-before-12pt-space-after-6pt
EDUCATION
$glyph

$glyph-bold
B.S. Computer Science
$glyph
$glyph-italic
University of Example | 2014 - 2018
$glyph

$glyph-font-size-14-bold-space-before-12pt-space-after-6pt
SKILLS
$glyph

Python, JavaScript, TypeScript, React, Node.js, Docker, Kubernetes, AWS, PostgreSQL, MongoDB
"""

# Multi-column examples
TWO_COLUMN_NEWSLETTER = """\
$glyph-font-name-calibri-font-size-11
$glyph-font-size-20-bold-align-center-space-after-12pt
Company Newsletter
$glyph

$glyph-align-center-italic-space-after-18pt
January 2025 Edition
$glyph

$glyph-layout-col-2
$glyph-font-size-13-bold-space-before-6pt-space-after-4pt
New Product Launch
$glyph

We are excited to announce the launch of our latest product, which features cutting-edge technology and innovative design. This product represents months of research and development, and we believe it will revolutionize the industry.

$glyph-font-size-13-bold-space-before-6pt-space-after-4pt
Team Updates
$glyph

Please welcome our new team members who joined us this month. We are thrilled to have such talented individuals joining our organization and look forward to their contributions.

$glyph-font-size-13-bold-space-before-6pt-space-after-4pt
Upcoming Events
$glyph

Mark your calendars for our annual company retreat scheduled for March 15-17. This will be a great opportunity for team building and strategic planning for the year ahead.
$glyph

$glyph-align-center-italic-space-before-12pt
For more information, visit our website or contact HR.
$glyph
"""

# Testing edge cases
NESTED_FORMATTING = """\
$glyph-font-size-12-align-justify
This paragraph has multiple formatting applied at the block level, including justified alignment and 12pt font size.
$glyph

$glyph-bold-italic-underline-color-FF0000
This text is bold, italic, underlined, and red.
$glyph

$glyph-highlight-yellow-bold
This text is highlighted in yellow and bold.
$glyph
"""

COMPLEX_INDENTATION = """\
$glyph-indent-left-36pt-space-after-6pt
This paragraph is indented 36pt from the left margin.
$glyph

$glyph-indent-hanging-36pt-space-after-6pt
This paragraph has a hanging indent of 36pt, where the first line is outdented relative to the rest of the paragraph.
$glyph

$glyph-indent-left-72pt-indent-first-line-36pt
This paragraph is indented 72pt from the left, with an additional 36pt first-line indent, creating a total first-line indent of 108pt.
$glyph
"""

PAGE_LAYOUT_EXAMPLES = """\
$glyph-section-size-letter-section-orientation-portrait-section-margin-all-1in
This document uses US Letter size (8.5" x 11") in portrait orientation with 1-inch margins on all sides.
$glyph

$glyph-section-margin-left-1_5in-section-margin-right-1_5in
This section has wider side margins (1.5 inches) while keeping default top and bottom margins.
$glyph
"""
