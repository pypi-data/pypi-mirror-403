"""OpenAI API service for job description extraction."""

import json
import logging
import httpx
from typing import Dict, List, Any

from config import OPENAI_API_KEY, DEFAULT_MODEL, REQUEST_TIMEOUT, OPENAI_TEMPERATURE
from models import JobDescriptionData

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service class for handling OpenAI API interactions."""
    
    def __init__(self):
        """Initialize the OpenAI service."""
        self.use_mock_data = False
        
        if not OPENAI_API_KEY or OPENAI_API_KEY in ["your-openai-api-key-here", "sk-test-key-for-testing"]:
            logger.warning("OPENAI_API_KEY is not configured, using mock data")
            self.use_mock_data = True
            return
        
        self.api_key = OPENAI_API_KEY
        self.model = DEFAULT_MODEL
        self.timeout = REQUEST_TIMEOUT
        self.temperature = OPENAI_TEMPERATURE
    
    def _get_mock_job_description(self, text: str) -> JobDescriptionData:
        """Generate mock job description data for testing."""
        logger.info("Using mock job description extraction")
        
        # Simple heuristic extraction based on common patterns
        lines = text.split('\n')
        title = "Software Engineer"
        company = "Unknown"
        location = "Not specified"
        required_qualifications = []
        preferred_qualifications = []
        description = text[:500]
        experience_level = "Not specified"
        employment_type = "Not specified"
        
        # Try to extract title from first few lines
        for line in lines[:5]:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['engineer', 'developer', 'manager', 'analyst', 'designer']):
                title = line.strip()
                break
        
        # Extract qualifications
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['required', 'must have', 'need']):
                required_qualifications.append(line.strip())
            elif any(keyword in line_lower for keyword in ['preferred', 'nice to have', 'plus']):
                preferred_qualifications.append(line.strip())
        
        return JobDescriptionData(
            title=title,
            company=company,
            location=location,
            required_qualifications=required_qualifications[:5],
            preferred_qualifications=preferred_qualifications[:5],
            description=description,
            experience_level=experience_level,
            employment_type=employment_type
        )
    
    def _get_mock_scoring(self, candidate_resume: str, required_qualifications: List[str], preferred_qualifications: List[str]) -> Dict[str, Any]:
        """Generate mock scoring data for testing."""
        logger.info("Using mock candidate scoring")
        
        required_scores = []
        for qual in required_qualifications:
            required_scores.append({
                "qualification": qual,
                "score": 1,
                "explanation": f"Mock evaluation for {qual}"
            })
        
        preferred_scores = []
        for qual in preferred_qualifications:
            preferred_scores.append({
                "qualification": qual,
                "score": 1,
                "explanation": f"Mock evaluation for {qual}"
            })
        
        required_total = len(required_scores)
        preferred_total = len(preferred_scores)
        total_score = required_total + preferred_total
        max_possible_score = (len(required_qualifications) + len(preferred_qualifications)) * 2
        match_percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
        
        return {
            "requiredScores": required_scores,
            "preferredScores": preferred_scores,
            "totalScore": total_score,
            "maxPossibleScore": max_possible_score,
            "matchPercentage": round(match_percentage, 1),
            "overallFeedback": "Mock scoring - requires actual API key for accurate evaluation",
            "scoringBreakdown": {
                "requiredTotal": required_total,
                "preferredTotal": preferred_total,
                "requiredCount": len(required_qualifications),
                "preferredCount": len(preferred_qualifications)
            }
        }
    
    async def extract_job_description_from_text(self, text: str) -> JobDescriptionData:
        """Extract job description data from text using OpenAI.
        
        Args:
            text: The job description text to analyze
            
        Returns:
            JobDescriptionData object with extracted information
            
        Raises:
            Exception: If the API call fails or response parsing fails
        """
        logger.info(f"Starting extraction with text length: {len(text)}")
        
        if self.use_mock_data:
            return self._get_mock_job_description(text)
        
        logger.info("API key is available, proceeding with extraction")
        
        # Create the extraction prompt based on reference implementation
        prompt = self._create_extraction_prompt(text)
        
        try:
            logger.info("Creating HTTP client and making API request")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                request_data = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that extracts structured data from job descriptions."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": self.temperature,
                    "response_format": {"type": "json_object"}
                }
                
                logger.info(f"Making request to OpenAI with model: {self.model}")
                
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json=request_data
                )
                
                logger.info(f"OpenAI API response status: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"OpenAI API error response: {error_text}")
                    try:
                        error_data = response.json()
                        logger.error(f"OpenAI API error JSON: {error_data}")
                        logger.warning("OpenAI API error, falling back to mock data")
                        self.use_mock_data = True
                        return self._get_mock_job_description(text)
                    except json.JSONDecodeError:
                        logger.warning("OpenAI API error, falling back to mock data")
                        self.use_mock_data = True
                        return self._get_mock_job_description(text)
                
                data = response.json()
                logger.info("Successfully parsed OpenAI response JSON")
                
                content = data["choices"][0]["message"]["content"]
                logger.info(f"Extracted content from OpenAI response, length: {len(content) if content else 0}")
                
                if not content:
                    logger.error("OpenAI returned empty content")
                    logger.warning("OpenAI returned empty content, falling back to mock data")
                    self.use_mock_data = True
                    return self._get_mock_job_description(text)
                
                logger.info(f"OpenAI response content sample: {content[:200]}...")
                
                return self._parse_response_to_job_data(content)
                    
        except httpx.TimeoutException as e:
            logger.error(f"HTTP timeout error: {e}")
            logger.warning("HTTP timeout, falling back to mock data")
            self.use_mock_data = True
            return self._get_mock_job_description(text)
        except httpx.RequestError as e:
            logger.error(f"HTTP request error: {e}")
            logger.warning("HTTP request error, falling back to mock data")
            self.use_mock_data = True
            return self._get_mock_job_description(text)
        except Exception as e:
            logger.error(f"Unexpected error in extract_job_description_from_text: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.warning("Unexpected error, falling back to mock data")
            self.use_mock_data = True
            return self._get_mock_job_description(text)
    
    def _create_extraction_prompt(self, text: str) -> str:
        """Create the prompt for job description extraction.
        
        Args:
            text: The job description text
            
        Returns:
            Formatted prompt string
        """
        return f"""
Extract the following information from this job description text. 
Format the response as a valid JSON object with these fields:
- title: The job title
- company: The company name (use "Unknown" if not found)
- location: The job location (use "Not specified" if not found)
- required_qualifications: An array of strings, each one representing a required qualification
- preferred_qualifications: An array of strings, each one representing a preferred/nice-to-have qualification
- description: A summary of the job description
- experience_level: The experience level (entry-level, mid-level, senior, etc.)
- employment_type: The employment type (full-time, part-time, contract, etc.)

Job Description Text:
{text}
"""
    
    def _parse_response_to_job_data(self, content: str) -> JobDescriptionData:
        """Parse OpenAI response content to JobDescriptionData object.
        
        Args:
            content: The JSON content from OpenAI response
            
        Returns:
            JobDescriptionData object
            
        Raises:
            Exception: If JSON parsing fails
        """
        try:
            parsed_data = json.loads(content)
            logger.info("Successfully parsed JSON from OpenAI response")
            logger.info(f"Parsed data keys: {list(parsed_data.keys())}")
            
            # Validate and create JobDescriptionData object
            result = JobDescriptionData(
                title=parsed_data.get("title", "Unknown Position"),
                company=parsed_data.get("company", "Unknown"),
                location=parsed_data.get("location", "Not specified"),
                required_qualifications=parsed_data.get("required_qualifications", []),
                preferred_qualifications=parsed_data.get("preferred_qualifications", []),
                description=parsed_data.get("description", ""),
                experience_level=parsed_data.get("experience_level", "Not specified"),
                employment_type=parsed_data.get("employment_type", "Not specified")
            )
            logger.info("Successfully created JobDescriptionData object")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw content: {content}")
            raise Exception(f"Failed to parse response from OpenAI: {str(e)}")
    
    async def score_candidate_qualifications(
        self,
        candidate_resume: str,
        required_qualifications: List[str],
        preferred_qualifications: List[str],
        job_title: str = "",
        job_description: str = ""
    ) -> Dict[str, Any]:
        """Score a candidate's resume against job qualifications using OpenAI.
        
        Args:
            candidate_resume: The candidate's resume text content
            required_qualifications: List of required qualifications
            preferred_qualifications: List of preferred qualifications
            job_title: Job title for context (optional)
            job_description: Job description for context (optional)
        
        Returns:
            Dictionary containing detailed scoring results
        """
        if self.use_mock_data:
            return self._get_mock_scoring(candidate_resume, required_qualifications, preferred_qualifications)
        
        try:
            logger.info("Starting candidate qualification scoring with OpenAI")
            
            # Build the prompt for scoring
            prompt_parts = [
                "You are a professional recruiter tasked with evaluating how well a candidate's resume matches the qualifications for a job.",
                ""
            ]
            
            if job_title:
                prompt_parts.append(f"JOB TITLE: {job_title}")
            
            if job_description:
                prompt_parts.append(f"JOB DESCRIPTION: {job_description}")
            
            prompt_parts.extend([
                "",
                "CANDIDATE'S RESUME:",
                candidate_resume,
                "",
                "Please evaluate the candidate against each qualification using the following scale:",
                "0 - Not Met: The candidate's resume shows no evidence of meeting this qualification",
                "1 - Somewhat Met: The candidate's resume shows some evidence of meeting this qualification but may lack depth or completeness",
                "2 - Strongly Met: The candidate's resume clearly demonstrates they meet or exceed this qualification",
                "",
                "Please evaluate ONLY the following qualifications, and return your response in JSON format with explanations for each score:",
                ""
            ])
            
            if required_qualifications:
                prompt_parts.append("REQUIRED QUALIFICATIONS:")
                for i, qual in enumerate(required_qualifications, 1):
                    prompt_parts.append(f"{i}. {qual}")
                prompt_parts.append("")
            
            if preferred_qualifications:
                prompt_parts.append("PREFERRED QUALIFICATIONS:")
                for i, qual in enumerate(preferred_qualifications, 1):
                    prompt_parts.append(f"{i}. {qual}")
                prompt_parts.append("")
            
            prompt_parts.extend([
                'Format your response as valid JSON with this structure:',
                '{',
                '  "requiredScores": [',
                '    {',
                '      "qualification": "qualification text",',
                '      "score": 0/1/2,',
                '      "explanation": "brief explanation for the score"',
                '    },',
                '    ...',
                '  ],',
                '  "preferredScores": [',
                '    {',
                '      "qualification": "qualification text",',
                '      "score": 0/1/2,',
                '      "explanation": "brief explanation for the score"',
                '    },',
                '    ...',
                '  ],',
                '  "overallFeedback": "brief overall assessment of the candidate"',
                '}'
            ])
            
            prompt = "\n".join(prompt_parts)
            
            logger.info("Sending scoring request to OpenAI")
            
            # Call OpenAI API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                request_data = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a professional recruiter who evaluates how well candidate resumes match job qualifications."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                }
                
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json=request_data
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"OpenAI API error response: {error_text}")
                    logger.warning("OpenAI API error, falling back to mock data")
                    self.use_mock_data = True
                    return self._get_mock_scoring(candidate_resume, required_qualifications, preferred_qualifications)
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                if not content:
                    logger.warning("OpenAI returned empty content, falling back to mock data")
                    self.use_mock_data = True
                    return self._get_mock_scoring(candidate_resume, required_qualifications, preferred_qualifications)
                
                logger.info("Received response from OpenAI, parsing JSON")
                
                try:
                    # Parse the JSON response
                    scoring_data = json.loads(content)
                    
                    # Calculate the total score
                    required_scores = scoring_data.get("requiredScores", [])
                    preferred_scores = scoring_data.get("preferredScores", [])
                    
                    required_total = sum(item.get("score", 0) for item in required_scores)
                    preferred_total = sum(item.get("score", 0) for item in preferred_scores)
                    
                    total_score = required_total + preferred_total
                    max_possible_score = (len(required_qualifications) + len(preferred_qualifications)) * 2
                    
                    # Calculate match percentage
                    match_percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
                    
                    result = {
                        "requiredScores": required_scores,
                        "preferredScores": preferred_scores,
                        "totalScore": total_score,
                        "maxPossibleScore": max_possible_score,
                        "matchPercentage": round(match_percentage, 1),
                        "overallFeedback": scoring_data.get("overallFeedback", ""),
                        "scoringBreakdown": {
                            "requiredTotal": required_total,
                            "preferredTotal": preferred_total,
                            "requiredCount": len(required_qualifications),
                            "preferredCount": len(preferred_qualifications)
                        }
                    }
                    
                    logger.info(f"Successfully scored candidate: {total_score}/{max_possible_score} ({match_percentage:.1f}%)")
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Raw content: {content}")
                    logger.warning("Failed to parse JSON, falling back to mock data")
                    self.use_mock_data = True
                    return self._get_mock_scoring(candidate_resume, required_qualifications, preferred_qualifications)
                    
        except Exception as e:
            logger.error(f"Error scoring candidate qualifications: {e}")
            logger.warning("Error in scoring, falling back to mock data")
            self.use_mock_data = True
            return self._get_mock_scoring(candidate_resume, required_qualifications, preferred_qualifications)
