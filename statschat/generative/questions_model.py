# from statschat.generative.llm import Inquirer
# from statschat.generative.question_model import QuestionRequest, EnhancedInquirer

# # Your existing code to create an Inquirer
# inquirer = Inquirer(**config)

# # Initialize the enhanced inquirer
# enhanced_inquirer = EnhancedInquirer()

# # Create a structured question
# request = QuestionRequest(
#     question_text="What was inflation in Kenya in December 2024?",
#     question_id="q123456"
# )

# # Process the question through the enhanced pipeline
# enhanced_docs, answer, response = enhanced_inquirer.process_question(inquirer, request)
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from statschat.generative.llm import Inquirer


class QuestionContext(BaseModel):
    """Contextual information about a question to improve retrieval and answer quality."""
    
    expected_domain: Optional[str] = Field(
        None, 
        description="The expected domain of the question (e.g., 'economics', 'demographics', 'health')"
    )
    time_period: Optional[str] = Field(
        None, 
        description="The time period the question is asking about (e.g., 'December 2024', '2019-2023')"
    )
    geographic_scope: Optional[str] = Field(
        None, 
        description="The geographic scope of the question (e.g., 'Kenya', 'Nairobi', 'East Africa')"
    )
    metrics_requested: List[str] = Field(
        default_factory=list,
        description="List of specific metrics being requested (e.g., 'inflation rate', 'population size')"
    )
    expected_document_type: Optional[str] = Field(
        None,
        description="Type of document likely to contain the answer (e.g., 'report', 'survey', 'bulletin')"
    )
    expected_recency: Optional[str] = Field(
        None,
        description="How recent the information should be ('latest_only', 'historical', 'specific_date')"
    )


class DocumentMetadata(BaseModel):
    """Enhanced metadata for retrieved documents to provide better context."""
    
    doc_id: str
    title: str
    date: str 
    publication_type: Optional[str] = None
    issuing_organization: Optional[str] = None
    url: str
    page_url: str
    relevance_score: float
    match_reason: str = Field(
        "",
        description="Explanation of why this document was matched to the query"
    )
    key_sections: List[str] = Field(
        default_factory=list,
        description="Sections in the document most relevant to the query"
    )
    confidence_level: float = Field(
        1.0,
        description="Confidence score (0-1) of this document containing the answer"
    )
    citation_format: Optional[str] = None
    time_period_covered: Optional[str] = None


class QuestionRequest(BaseModel):
    """A model representing a statistical question with enhanced context for better retrieval."""
    
    question_text: str = Field(..., description="The raw question text from the user")
    question_id: str = Field(..., description="Unique identifier for the question")
    timestamp: datetime = Field(default_factory=datetime.now)
    context: QuestionContext = Field(default_factory=QuestionContext)
    
    # Processing flags
    latest_filter: str = Field("on", description="Whether to filter to latest bulletins only")
    highlighting: bool = Field(True, description="Whether to enable text highlighting")
    latest_weight: float = Field(1.0, description="Weight factor for recent documents")
    
    def extract_context(self) -> None:
        """
        Analyzes the question text to extract contextual information.
        This helps improve document retrieval by providing additional query context.
        """
        # Extract geographic scope
        if "Kenya" in self.question_text:
            self.context.geographic_scope = "Kenya"
        
        # Extract time period
        import re
        date_pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})"
        year_pattern = r"\b(20\d{2})\b"
        
        date_match = re.search(date_pattern, self.question_text)
        if date_match:
            self.context.time_period = f"{date_match.group(1)} {date_match.group(2)}"
        else:
            year_match = re.search(year_pattern, self.question_text)
            if year_match:
                self.context.time_period = year_match.group(1)
        
        # Extract metrics
        metric_keywords = {
            "inflation": ["inflation", "CPI", "consumer price index"],
            "population": ["population", "census", "demographic"],
            "employment": ["employment", "unemployment", "labor force"],
            "economic": ["GDP", "economic growth", "economy"]
        }
        
        for category, keywords in metric_keywords.items():
            if any(keyword.lower() in self.question_text.lower() for keyword in keywords):
                self.context.metrics_requested.append(category)
        
        # Determine expected recency
        if "latest" in self.question_text.lower() or "current" in self.question_text.lower():
            self.context.expected_recency = "latest_only"
        elif re.search(r"\b\d{4}\b", self.question_text):
            self.context.expected_recency = "specific_date"
        else:
            self.context.expected_recency = "latest_only"  # Default assumption


class EnhancedInquirer:
    """
    Extension of the Inquirer class with improved question processing capabilities.
    This is designed to be used alongside the existing Inquirer class.
    """
    
    def process_question(self, inquirer, question_request: QuestionRequest):
        """
        Process a structured question request through the Inquirer system
        with enhanced metadata handling.
        
        Args:
            inquirer: An instance of the Inquirer class
            question_request: A QuestionRequest instance
        
        Returns:
            tuple: (enhanced_docs, answer_str, validated_response)
        """
        # Extract context to improve search 
        question_request.extract_context()
        
        # Determine if we should use latest filter based on context
        use_latest = question_request.latest_filter
        if question_request.context.expected_recency == "historical":
            use_latest = "off"
        
        # Get raw results from inquirer
        docs, answer_str, validated_response = inquirer.make_query(
            question_request.question_text,
            latest_filter=use_latest,
            highlighting=question_request.highlighting,
            latest_weight=question_request.latest_weight
        )
        
        # Enhance document metadata
        enhanced_docs = self._enhance_document_metadata(
            docs, 
            question_request,
            validated_response
        )
        
        return enhanced_docs, answer_str, validated_response
    
    def _enhance_document_metadata(self, docs, question_request, validated_response):
        """
        Enhance document metadata with additional context information.
        """
        enhanced_docs = []
        
        for i, doc in enumerate(docs):
            # Extract organization from URL or title
            org = "Unknown"
            if "knbs" in doc.get("url", "").lower():
                org = "Kenya National Bureau of Statistics"
            # elif "central_bank" in doc.get("url", "").lower():
            #     org = "Central Bank of Kenya"
            
            # Determine publication type
            pub_type = "Unknown"
            title = doc.get("title", "").lower()
            if "report" in title:
                pub_type = "Report"
            elif "bulletin" in title:
                pub_type = "Bulletin"
            elif "survey" in title:
                pub_type = "Survey"
            
            # Determine match reason
            match_reason = "Content similarity"
            if question_request.context.time_period and question_request.context.time_period in doc.get("date", ""):
                match_reason = f"Date match: {question_request.context.time_period}"
            
            # Calculate confidence based on score and position
            confidence = max(0.1, min(1.0, 1.0 - (doc.get("score", 0) * 0.2)))
            if i == 0:
                confidence = min(1.0, confidence + 0.2)  # Boost top result
            
            # Extract time period covered from document
            time_covered = doc.get("date", "Unknown")
            
            # Create citation format
            citation = f"{doc.get('title', 'Unknown')} ({doc.get('date', 'n.d.')})"
            
            # Create enhanced metadata
            enhanced_doc = dict(doc)
            enhanced_doc.update({
                "issuing_organization": org,
                "publication_type": pub_type,
                "match_reason": match_reason,
                "confidence_level": round(confidence, 2),
                "citation_format": citation,
                "time_period_covered": time_covered,
                "relevance_score": float(doc.get("score", 1.0))
            })
            
            # Add highlighting information if available
            if hasattr(validated_response, "highlighting1") and i == 0:
                enhanced_doc["key_sections"] = validated_response.highlighting1
            
            enhanced_docs.append(enhanced_doc)
        
        return enhanced_docs


# Example usage
if __name__ == "__main__":
    from statschat import load_config
    import logging
    import uuid
    
    logger = logging.getLogger(__name__)
    CONFIG = load_config(name="main")
    inquirer = Inquirer(**CONFIG["db"], **CONFIG["search"], logger=logger)
    
    # Create question request
    #question = "What was inflation in Kenya in December 2024?"
    #question = "What is the population sample size value of the Real Estate Survey in 2023?"
    question = "What proportion of women own land in Kenya?"
    request = QuestionRequest(
        question_text=question,
        question_id=str(uuid.uuid4()),
        latest_filter="off"
    )
    
    # Process with enhanced inquirer
    enhanced_inquirer = EnhancedInquirer()
    enhanced_docs, answer, response = enhanced_inquirer.process_question(inquirer, request)
    
    print("-------------------- QUESTION CONTEXT --------------------")
    print(f"Geographic scope: {request.context.geographic_scope}")
    print(f"Time period: {request.context.time_period}")
    print(f"Metrics requested: {request.context.metrics_requested}")
    
    print("-------------------- ENHANCED METADATA --------------------")
    for i, doc in enumerate(enhanced_docs[:2]):  # Show first two documents
        print(f"\nDocument {i+1}:")
        print(f"  Title: {doc.get('title')}")
        print(f"  Organization: {doc.get('issuing_organization')}")
        print(f"  Publication type: {doc.get('publication_type')}")
        print(f"  Confidence level: {doc.get('confidence_level')}")
        print(f"  Match reason: {doc.get('match_reason')}")
        print(f"  Citation: {doc.get('citation_format')}")
    
    print("\n-------------------- ANSWER --------------------")
    print(answer)