from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.inquiry.completeness import CompletenessResult, InquiryCompletenessChecker
from app.inquiry.langgraph_workflow import LangGraphInquiryWorkflow
from app.inquiry.parser import OpenAIInquiryParser, RuleBasedInquiryParser
from app.inquiry.repository import InMemoryInquiryRepository
from app.inquiry.schemas import InquiryInput, InquiryRecord
from app.inquiry.service import InquiryIntakeService
from app.inquiry.workflow import InquiryProcessingWorkflow, InquiryWorkflowResult

app = FastAPI(
    title="AI Inquiry Processing Agent",
    version="1.0.0",
    description=(
        "Foreign-trade inquiry understanding, clarification, product matching, "
        "business tool execution, and English reply drafting."
    ),
)

repository = InMemoryInquiryRepository()
inquiry_intake = InquiryIntakeService(repository)


def build_inquiry_parser():
    settings = get_settings()
    if settings.inquiry_parser_provider.lower() == "openai" and settings.openai_api_key:
        return OpenAIInquiryParser(settings.openai_api_key, settings.inquiry_parser_model)
    return RuleBasedInquiryParser()


domain_workflow = InquiryProcessingWorkflow(repository, parser=build_inquiry_parser())
inquiry_graph = LangGraphInquiryWorkflow(domain_workflow)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/inquiries", response_model=InquiryRecord, status_code=status.HTTP_201_CREATED)
def create_inquiry(request: InquiryInput) -> InquiryRecord:
    return inquiry_intake.create(request)


@app.get("/inquiries/{inquiry_id}", response_model=InquiryRecord)
def get_inquiry(inquiry_id: str) -> InquiryRecord:
    record = inquiry_intake.get(inquiry_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    return record


@app.post("/inquiries/{inquiry_id}/parse", response_model=InquiryRecord)
def parse_inquiry(inquiry_id: str) -> InquiryRecord:
    record = inquiry_intake.parse(inquiry_id, build_inquiry_parser())
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    return record


@app.get("/inquiries/{inquiry_id}/completeness", response_model=CompletenessResult)
def check_inquiry_completeness(inquiry_id: str) -> CompletenessResult:
    record = inquiry_intake.get(inquiry_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    if record.structured is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Parse the inquiry before checking completeness",
        )
    return InquiryCompletenessChecker().check(record.structured)


@app.post("/inquiries/{inquiry_id}/process", response_model=InquiryWorkflowResult)
def process_inquiry(inquiry_id: str) -> InquiryWorkflowResult:
    result = inquiry_graph.invoke(inquiry_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    return result


frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/ui", StaticFiles(directory=frontend_dir, html=True), name="ui")


@app.get("/", include_in_schema=False)
def frontend_redirect() -> RedirectResponse:
    return RedirectResponse(url="/ui/")
