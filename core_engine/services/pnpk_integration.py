"""
Integration helper for combining main analysis with PNPK summary
"""

from typing import Dict, Any, Optional
from services.pnpk_summary_service import PNPKSummaryService


async def enrich_analysis_with_pnpk(
    analysis_result: Dict[str, Any],
    pnpk_service: PNPKSummaryService,
    auto_fetch: bool = True
) -> Dict[str, Any]:
    """
    Enrich main analysis result with PNPK summary if available
    
    Args:
        analysis_result: Result from analyze_lite_single or analyze_lite_batch
        pnpk_service: Initialized PNPKSummaryService instance
        auto_fetch: Automatically fetch PNPK summary for detected diagnosis
        
    Returns:
        Analysis result with added 'pnpk_summary' field if found
    """
    
    if not auto_fetch:
        return analysis_result
    
    # Extract diagnosis from analysis result
    diagnosis = None
    
    # Check different possible structures
    if 'klasifikasi' in analysis_result:
        klasifikasi = analysis_result['klasifikasi']
        if 'diagnosis' in klasifikasi:
            diagnosis = klasifikasi['diagnosis']
    elif 'parsed' in analysis_result:
        parsed = analysis_result['parsed']
        if 'diagnosis' in parsed:
            diagnosis = parsed['diagnosis']
    elif 'diagnosis' in analysis_result:
        diagnosis = analysis_result['diagnosis']
    
    if not diagnosis:
        return analysis_result
    
    # Try to fetch PNPK summary
    try:
        pnpk_summary = await pnpk_service.get_pnpk_summary(diagnosis, auto_match=True)
        
        if pnpk_summary:
            # Add PNPK summary to result
            analysis_result['pnpk_summary'] = {
                'available': True,
                'diagnosis': pnpk_summary['diagnosis'],
                'total_stages': pnpk_summary['total_stages'],
                'stages': pnpk_summary['stages']
            }
            
            # Add match info if available
            if 'match_info' in pnpk_summary:
                analysis_result['pnpk_summary']['match_info'] = pnpk_summary['match_info']
        else:
            # No PNPK found
            analysis_result['pnpk_summary'] = {
                'available': False,
                'message': f'No PNPK clinical pathway found for diagnosis: {diagnosis}'
            }
    
    except Exception as e:
        # Error fetching PNPK
        analysis_result['pnpk_summary'] = {
            'available': False,
            'error': str(e)
        }
    
    return analysis_result


def get_current_stage_suggestion(
    pnpk_stages: list,
    patient_data: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Suggest current stage based on patient data
    
    This is a placeholder for future enhancement where we analyze
    patient data (treatments given, days since admission, etc.)
    to suggest which PNPK stage the patient is currently at.
    
    Args:
        pnpk_stages: List of PNPK stages
        patient_data: Optional patient data (treatments, timeline, etc.)
        
    Returns:
        Suggested current stage or None
    """
    
    # For now, return None
    # Future implementation could analyze:
    # - Days since admission
    # - Treatments given (match with stage descriptions)
    # - Lab results
    # - Imaging results
    # etc.
    
    return None


def format_pnpk_for_display(pnpk_summary: Dict[str, Any]) -> str:
    """
    Format PNPK summary as readable text
    Useful for PDF export or text display
    
    Args:
        pnpk_summary: PNPK summary dict
        
    Returns:
        Formatted string
    """
    
    if not pnpk_summary.get('available'):
        return "PNPK clinical pathway not available for this diagnosis."
    
    output = []
    output.append(f"RINGKASAN PNPK: {pnpk_summary['diagnosis']}")
    output.append("=" * 70)
    
    if 'match_info' in pnpk_summary:
        match_info = pnpk_summary['match_info']
        output.append(f"Original Input: {match_info['original_input']}")
        output.append(f"Matched To: {match_info['matched_name']}")
        output.append(f"Confidence: {match_info['confidence']:.2%}")
        output.append("")
    
    output.append(f"Total Tahapan: {pnpk_summary['total_stages']}")
    output.append("")
    
    for stage in pnpk_summary['stages']:
        output.append(f"Tahap {stage['order']}: {stage['stage_name']}")
        output.append("-" * 70)
        output.append(stage['description'])
        output.append("")
    
    return "\n".join(output)


# Example usage in endpoint
"""
# In lite_endpoints.py or new integrated endpoint:

async def endpoint_analyze_with_pnpk(request_data: Dict[str, Any], db_pool) -> Dict[str, Any]:
    '''
    Analyze claim and auto-fetch PNPK summary
    '''
    from services.lite_service import analyze_lite_single
    from services.pnpk_summary_service import PNPKSummaryService
    from services.pnpk_integration import enrich_analysis_with_pnpk
    
    # Run main analysis
    analysis_result = analyze_lite_single(request_data)
    
    # Enrich with PNPK if database available
    if db_pool:
        pnpk_service = PNPKSummaryService(db_pool)
        analysis_result = await enrich_analysis_with_pnpk(
            analysis_result, 
            pnpk_service,
            auto_fetch=True
        )
    
    return analysis_result
"""
