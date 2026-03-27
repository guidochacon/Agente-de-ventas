import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.quote import Quote
from models.lead import Lead
from config import settings

QUOTES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "quotes")


class QuoteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        service: str,
        details: str = "",
        lead_email: str | None = None,
        total_value: float | None = None,
        currency: str = "USD",
    ) -> Quote:
        os.makedirs(QUOTES_DIR, exist_ok=True)

        lead_id = None
        if lead_email:
            result = await self.db.execute(select(Lead).where(Lead.email == lead_email))
            lead = result.scalar_one_or_none()
            if lead:
                lead_id = lead.id

        quote = Quote(
            lead_id=lead_id,
            service=service,
            details=details,
            total_value=total_value,
            currency=currency,
            status="draft",
        )
        self.db.add(quote)
        await self.db.commit()
        await self.db.refresh(quote)

        # Generate PDF
        pdf_path = await self._generate_pdf(quote)
        if pdf_path:
            quote.pdf_path = pdf_path
            await self.db.commit()

        return quote

    async def _generate_pdf(self, quote: Quote) -> str | None:
        try:
            from jinja2 import Environment, FileSystemLoader
            template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "quotes")
            env = Environment(loader=FileSystemLoader(template_dir))
            template = env.get_template("base_quote.html")

            html = template.render(
                quote=quote,
                business_name=settings.agent_business_name,
                agent_name=settings.agent_name,
            )

            try:
                from weasyprint import HTML
                pdf_path = os.path.join(QUOTES_DIR, f"quote_{quote.id}.pdf")
                HTML(string=html).write_pdf(pdf_path)
                return pdf_path
            except ImportError:
                # WeasyPrint not available — save as HTML
                html_path = os.path.join(QUOTES_DIR, f"quote_{quote.id}.html")
                with open(html_path, "w") as f:
                    f.write(html)
                return html_path

        except Exception as e:
            print(f"[QUOTE] PDF generation error: {e}")
            return None

    async def get_quote(self, quote_id: str) -> Quote | None:
        result = await self.db.execute(select(Quote).where(Quote.id == quote_id))
        return result.scalar_one_or_none()
