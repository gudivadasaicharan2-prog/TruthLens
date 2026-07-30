"""
Professional PDF Report Generator for TruthLens AI Forensics Platform

This module generates professional PDF reports for image authenticity analysis
using ReportLab. The report includes all analysis results, visualizations,
and explanations in a formatted document.

Report Sections:
1. TruthLens Logo/Header
2. Analysis Summary (filename, timestamp, analysis ID)
3. Verdict
4. Confidence
5. Risk Level
6. AI Probability
7. Module Contributions (table)
8. Evidence For AI
9. Evidence Against AI
10. Original Image
11. GradCAM Heatmap
12. GradCAM Overlay
13. Processing Time
14. Model Version
15. Threshold Used
16. Footer
"""

import os
from pathlib import Path
from datetime import datetime
import uuid
from typing import Dict, Any, Optional
from PIL import Image as PILImage

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image as RLImage, PageBreak, KeepTogether
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except Exception as e:
    REPORTLAB_AVAILABLE = False
    print(f"[Report Generator] ReportLab import failed: {e}")


class ReportGenerator:
    """
    Professional PDF report generator for image authenticity analysis.
    
    This class takes the complete analysis output from image_detector.py
    and generates a formatted PDF report with all relevant information.
    """
    
    def __init__(self, output_dir: str = "uploads/reports"):
        """
        Initialize the report generator.
        
        Args:
            output_dir: Directory to save generated PDF reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Page size and margins
        self.page_size = A4
        self.margins = (0.5 * inch, 0.5 * inch, 0.5 * inch, 0.5 * inch)
        
        # Setup styles
        self.styles = self._setup_styles()
        
        # Model version (can be updated)
        self.model_version = "v6.0 - Configurable Fusion"
        self.threshold_used = "0.40"  # Default threshold
    
    def _setup_styles(self):
        """
        Setup custom paragraph styles for the report.
        
        Returns:
            Dictionary of ParagraphStyle objects
        """
        if not REPORTLAB_AVAILABLE:
            return {}
        
        styles = getSampleStyleSheet()
        
        # Custom styles with unique names to avoid conflicts
        styles.add(ParagraphStyle(
            name='TruthLensHeaderTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='TruthLensHeaderSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#4a4a6a'),
            spaceAfter=24,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        styles.add(ParagraphStyle(
            name='TruthLensSectionTitle',
            parent=styles['Heading3'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a2e'),
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='TruthLensBodyText',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            fontName='Helvetica'
        ))
        
        styles.add(ParagraphStyle(
            name='TruthLensVerdictText',
            parent=styles['Heading2'],
            fontSize=20,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='TruthLensFooterText',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        return styles
    
    def _get_risk_level(self, ai_probability: float) -> str:
        """
        Determine risk level based on AI probability.
        
        Args:
            ai_probability: AI probability (0-100)
        
        Returns:
            Risk level string
        """
        if ai_probability >= 70:
            return "HIGH"
        elif ai_probability >= 40:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_verdict_color(self, verdict: str):
        """
        Get color for verdict display.
        
        Args:
            verdict: Analysis verdict string
        
        Returns:
            Color object for the verdict
        """
        if not REPORTLAB_AVAILABLE:
            return None
        
        verdict_lower = verdict.lower()
        if 'deepfake' in verdict_lower or 'ai generated' in verdict_lower:
            return colors.HexColor('#dc3545')  # Red
        elif 'suspicious' in verdict_lower:
            return colors.HexColor('#ffc107')  # Yellow
        else:
            return colors.HexColor('#28a745')  # Green
    
    def _create_header(self, story: list):
        """
        Add TruthLens logo/header to the report.
        
        Args:
            story: List of flowables to add to
        """
        # Title
        story.append(Paragraph("TruthLens AI Forensics Platform", self.styles['TruthLensHeaderTitle']))
        story.append(Paragraph("Image Authenticity Analysis Report", self.styles['TruthLensHeaderSubtitle']))
        story.append(Spacer(1, 0.2 * inch))
    
    def _create_analysis_summary(self, story: list, analysis_data: Dict[str, Any]):
        """
        Add analysis summary section to the report.
        
        Args:
            story: List of flowables to add to
            analysis_data: Complete analysis output from image_detector.py
        """
        if not REPORTLAB_AVAILABLE:
            return
        
        story.append(Paragraph("Analysis Summary", self.styles['TruthLensSectionTitle']))
        
        # Extract filename from image path if available
        filename = analysis_data.get('filename', 'Unknown')
        if '/' in filename or '\\' in filename:
            filename = filename.split('/')[-1].split('\\')[-1]
        
        # Generate analysis ID and timestamp
        analysis_id = analysis_data.get('analysis_id', str(uuid.uuid4())[:8])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Create summary table
        summary_data = [
            ['Filename:', filename],
            ['Analysis ID:', analysis_id],
            ['Timestamp:', timestamp],
            ['Image Type:', analysis_data.get('image_type', 'Unknown')]
        ]
        
        summary_table = Table(summary_data, colWidths=[1.5 * inch, 4 * inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.2 * inch))
    
    def _create_verdict_section(self, story: list, analysis_data: Dict[str, Any]):
        """
        Add verdict section to the report.
        
        Args:
            story: List of flowables to add to
            analysis_data: Complete analysis output from image_detector.py
        """
        if not REPORTLAB_AVAILABLE:
            return
        
        verdict = analysis_data.get('verdict', 'Unknown')
        confidence = analysis_data.get('confidence', 0.0)
        ai_probability = analysis_data.get('ai_probability', 0.0)
        
        story.append(Paragraph("Analysis Verdict", self.styles['TruthLensSectionTitle']))
        
        # Verdict with color
        verdict_style = ParagraphStyle(
            name='VerdictStyle',
            parent=self.styles['TruthLensVerdictText'],
            textColor=self._get_verdict_color(verdict)
        )
        story.append(Paragraph(verdict, verdict_style))
        
        # Confidence and AI probability
        confidence_data = [
            ['Confidence Score:', f"{confidence:.2%}"],
            ['AI Probability:', f"{ai_probability:.1f}%"],
            ['Risk Level:', self._get_risk_level(ai_probability)]
        ]
        
        confidence_table = Table(confidence_data, colWidths=[1.5 * inch, 4 * inch])
        confidence_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(confidence_table)
        story.append(Spacer(1, 0.2 * inch))
    
    def _create_module_contributions(self, story: list, analysis_data: Dict[str, Any]):
        """
        Add module contributions table to the report.
        
        Args:
            story: List of flowables to add to
            analysis_data: Complete analysis output from image_detector.py
        """
        if not REPORTLAB_AVAILABLE:
            return
        
        contributions = analysis_data.get('module_contributions', {})
        
        if not contributions:
            return
        
        story.append(Paragraph("Module Contributions", self.styles['TruthLensSectionTitle']))
        
        # Build contribution table
        contrib_data = [['Module', 'Score', 'Weight', 'Contribution']]
        
        # Main modules
        for module_name in ['whole_image', 'face', 'forensic']:
            if module_name in contributions:
                module_data = contributions[module_name]
                score = module_data.get('score', 0.0)
                weight = module_data.get('weight', 0.0)
                contribution = module_data.get('contribution', 0.0)
                
                display_name = module_name.replace('_', ' ').title()
                contrib_data.append([
                    display_name,
                    f"{score:.3f}",
                    f"{weight:.3f}",
                    f"{contribution:.3f}"
                ])
        
        contrib_table = Table(contrib_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
        contrib_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        story.append(contrib_table)
        story.append(Spacer(1, 0.2 * inch))
    
    def _create_evidence_sections(self, story: list, analysis_data: Dict[str, Any]):
        """
        Add evidence for and against AI sections to the report.
        
        Args:
            story: List of flowables to add to
            analysis_data: Complete analysis output from image_detector.py
        """
        if not REPORTLAB_AVAILABLE:
            return
        
        explanation = analysis_data.get('explanation', {})
        
        if not explanation:
            return
        
        # Evidence For AI
        story.append(Paragraph("Evidence For AI Generation", self.styles['TruthLensSectionTitle']))
        evidence_for = explanation.get('for_ai', [])
        if evidence_for:
            for evidence in evidence_for:
                story.append(Paragraph(f"• {evidence}", self.styles['TruthLensBodyText']))
        else:
            story.append(Paragraph("No significant evidence for AI generation detected.", self.styles['TruthLensBodyText']))
        
        story.append(Spacer(1, 0.1 * inch))
        
        # Evidence Against AI
        story.append(Paragraph("Evidence Against AI Generation", self.styles['TruthLensSectionTitle']))
        evidence_against = explanation.get('against_ai', [])
        if evidence_against:
            for evidence in evidence_against:
                story.append(Paragraph(f"• {evidence}", self.styles['TruthLensBodyText']))
        else:
            story.append(Paragraph("No significant evidence against AI generation detected.", self.styles['TruthLensBodyText']))
        
        story.append(Spacer(1, 0.2 * inch))
    
    def _add_image_to_report(self, story: list, image_path: str, caption: str, max_width: float = 4 * inch):
        """
        Add an image to the report with caption.
        
        Args:
            story: List of flowables to add to
            image_path: Path to the image file
            caption: Caption for the image
            max_width: Maximum width for the image
        """
        if not REPORTLAB_AVAILABLE:
            return
        
        if not image_path or not Path(image_path).exists():
            story.append(Paragraph(f"{caption} - Image not available", self.styles['TruthLensBodyText']))
            story.append(Spacer(1, 0.1 * inch))
            return
        
        try:
            # Load image and get dimensions
            img = PILImage.open(image_path)
            img_width, img_height = img.size
            
            # Calculate aspect ratio
            aspect_ratio = img_height / img_width
            
            # Resize if too large
            if img_width > max_width:
                img_width = max_width
                img_height = img_width * aspect_ratio
            
            # Add image to report
            rl_img = RLImage(image_path, width=img_width, height=img_height)
            story.append(rl_img)
            story.append(Paragraph(caption, self.styles['TruthLensBodyText']))
            story.append(Spacer(1, 0.2 * inch))
        except Exception as e:
            story.append(Paragraph(f"{caption} - Error loading image: {str(e)}", self.styles['TruthLensBodyText']))
            story.append(Spacer(1, 0.1 * inch))
    
    def _create_visualizations(self, story: list, analysis_data: Dict[str, Any], original_image_path: str):
        """
        Add image visualizations to the report.
        
        Args:
            story: List of flowables to add to
            analysis_data: Complete analysis output from image_detector.py
            original_image_path: Path to the original analyzed image
        """
        if not REPORTLAB_AVAILABLE:
            return
        
        story.append(Paragraph("Image Visualizations", self.styles['TruthLensSectionTitle']))
        
        # Original image
        self._add_image_to_report(story, original_image_path, "Original Image")
        
        # GradCAM Heatmap
        heatmap_path = analysis_data.get('heatmap_path')
        if heatmap_path:
            self._add_image_to_report(story, heatmap_path, "GradCAM Heatmap - Regions influencing AI detection")
        
        # GradCAM Overlay
        overlay_path = analysis_data.get('overlay_path')
        if overlay_path:
            self._add_image_to_report(story, overlay_path, "GradCAM Overlay - Heatmap blended with original image")
        
        story.append(Spacer(1, 0.2 * inch))
    
    def _create_technical_details(self, story: list, analysis_data: Dict[str, Any]):
        """
        Add technical details section to the report.
        
        Args:
            story: List of flowables to add to
            analysis_data: Complete analysis output from image_detector.py
        """
        if not REPORTLAB_AVAILABLE:
            return
        
        story.append(Paragraph("Technical Details", self.styles['TruthLensSectionTitle']))
        
        # Processing time (if available)
        processing_time = analysis_data.get('processing_time', 'N/A')
        
        tech_data = [
            ['Model Version:', self.model_version],
            ['Decision Threshold:', f"{self.threshold_used}"],
            ['Processing Time:', f"{processing_time}"]
        ]
        
        tech_table = Table(tech_data, colWidths=[1.5 * inch, 4 * inch])
        tech_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(tech_table)
        story.append(Spacer(1, 0.2 * inch))
    
    def _create_footer(self, canvas, doc):
        """
        Create footer for each page.
        
        Args:
            canvas: ReportLab canvas object
            doc: Document template
        """
        if not REPORTLAB_AVAILABLE:
            return
        
        canvas.saveState()
        
        # Footer text
        footer_text = "Generated by TruthLens AI Forensics Platform"
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawCentredString(
            doc.width / 2,
            0.3 * inch,
            footer_text
        )
        
        # Page number
        page_num = canvas.getPageNumber()
        canvas.drawRightString(
            doc.width + 0.5 * inch,
            0.3 * inch,
            f"Page {page_num}"
        )
        
        canvas.restoreState()
    
    def generate_report(
        self,
        analysis_data: Dict[str, Any],
        original_image_path: str,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Generate a professional PDF report from analysis data.
        
        Args:
            analysis_data: Complete analysis output from image_detector.py
            original_image_path: Path to the original analyzed image
            output_filename: Optional custom filename for the PDF
        
        Returns:
            Path to the generated PDF report
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab is not installed. Install with: pip install reportlab")
        
        # Generate filename if not provided
        if output_filename is None:
            image_name = Path(original_image_path).stem
            analysis_id = str(uuid.uuid4())[:8]
            output_filename = f"{image_name}_{analysis_id}_report.pdf"
        
        output_path = self.output_dir / output_filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=self.page_size,
            rightMargin=self.margins[0],
            leftMargin=self.margins[1],
            topMargin=self.margins[2],
            bottomMargin=self.margins[3]
        )
        
        # Build story (list of flowables)
        story = []
        
        # Add all sections
        self._create_header(story)
        self._create_analysis_summary(story, analysis_data)
        self._create_verdict_section(story, analysis_data)
        self._create_module_contributions(story, analysis_data)
        self._create_evidence_sections(story, analysis_data)
        self._create_visualizations(story, analysis_data, original_image_path)
        self._create_technical_details(story, analysis_data)
        
        # Build PDF with footer
        doc.build(story, onLaterPages=self._create_footer)
        
        return str(output_path)


def generate_report(
    analysis_data: Dict[str, Any],
    original_image_path: str,
    output_dir: str = "uploads/reports",
    output_filename: Optional[str] = None
) -> str:
    """
    Convenience function to generate a PDF report.
    
    Args:
        analysis_data: Complete analysis output from image_detector.py
        original_image_path: Path to the original analyzed image
        output_dir: Directory to save the report
        output_filename: Optional custom filename for the PDF
    
    Returns:
        Path to the generated PDF report
    """
    generator = ReportGenerator(output_dir)
    return generator.generate_report(analysis_data, original_image_path, output_filename)
