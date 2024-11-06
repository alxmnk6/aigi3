from typing import Optional
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.knowledge.agent import AgentKnowledge
from phi.storage.agent.postgres import PgAgentStorage
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.webscraper import WebScraper
from phi.tools.calculator import Calculator
from phi.tools.python_repl import PythonREPL
from phi.tools.file_manager import FileManager
from phi.tools.yfinance import YFinanceTools
from phi.tools.newspaper import Newspaper4k
from phi.tools.youtube_tools import YouTubeTools
from phi.tools.exa import ExaTools
from phi.tools.pdf import PDFTools
from phi.tools.email import EmailTools
from phi.tools.sql import SQLTools
from phi.tools.datetime import DatetimeTools
from phi.tools.image import ImageTools
from phi.tools.chart import ChartTools
from phi.tools.table import TableTools
from phi.tools.text import TextTools
from phi.tools.json import JsonTools
from phi.tools.xml import XmlTools
from phi.tools.csv import CsvTools
from phi.tools.api import ApiTools
from phi.vectordb.pgvector import PgVector, SearchType
from datetime import datetime

from agents.settings import agent_settings
from db.session import db_url

# Storage setup with both PgVector and Qdrant
example_agent_storage = PgAgentStorage(table_name="example_agent_sessions", db_url=db_url)
example_agent_knowledge = AgentKnowledge(
    vector_db=PgVector(
        table_name="example_agent_knowledge", 
        db_url=db_url, 
        search_type=SearchType.hybrid
    )
)

def get_finance_agent() -> Agent:
    return Agent(
        name="Finance Analyst",
        agent_id="finance-analyst",
        model=OpenAIChat(id=agent_settings.gpt_4),
        tools=[
            YFinanceTools(enable_all=True),
            Calculator(),
            DuckDuckGo(),
            PDFTools(),  # For financial reports
            SQLTools(),  # For data analysis
            ChartTools(),  # For technical analysis charts
            TableTools(),  # For financial data tables
            JsonTools(),   # For API responses
            ApiTools(),    # For external financial APIs
        ],
        description="You are a senior investment analyst specializing in market research, financial analysis, and quantitative modeling.",
        instructions=[
            "Financial Analysis Protocol:\n"
            "  - Conduct thorough market analysis using YFinance\n"
            "  - Provide quantitative insights with statistical backing\n"
            "  - Generate detailed technical analysis with clear explanations\n"
            "  - Process financial reports and SEC filings\n"
            "  - Perform SQL-based financial data analysis",
            
            "Data Presentation:\n"
            "  - Always use tables for numerical data\n"
            "  - Include relevant market indicators\n"
            "  - Cite sources and timestamps for market data\n"
            "  - Generate visualizations when appropriate",
            
            "Team Collaboration:\n"
            "  - Share market insights with Research Analyst\n"
            "  - Coordinate with Productivity Assistant for automation\n"
            "  - Maintain structured documentation for the team",
        ],
        markdown=True,
        show_tool_calls=True,
    )

def get_research_agent() -> Agent:
    return Agent(
        name="Research Analyst",
        agent_id="research-analyst",
        model=OpenAIChat(id=agent_settings.gpt_4),
        tools=[
            DuckDuckGo(),
            Newspaper4k(),
            ExaTools(start_published_date=datetime.now().strftime("%Y-%m-%d")),
            PDFTools(),
            WebScraper(),
            DatetimeTools(),
            TextTools(),    # For text analysis
            ImageTools(),   # For image processing
            XmlTools(),     # For structured data
            CsvTools(),     # For data processing
        ],
        description="You are a senior research analyst specializing in market intelligence, trend analysis, and competitive research.",
        instructions=[
            "Research Protocol:\n"
            "  - Conduct comprehensive web research\n"
            "  - Analyze news articles and reports\n"
            "  - Synthesize information from multiple sources\n"
            "  - Track temporal trends and patterns\n"
            "  - Monitor competitor activities",
            
            "Report Format:\n"
            "  - Structure as NYT-style articles\n"
            "  - Include executive summary\n"
            "  - Provide detailed citations\n"
            "  - Add timestamps for time-sensitive data",
            
            "Team Collaboration:\n"
            "  - Share research findings with Finance Analyst\n"
            "  - Coordinate with Productivity Assistant for report automation\n"
            "  - Maintain research database for the team",
        ],
        markdown=True,
        show_tool_calls=True,
    )

def get_productivity_agent() -> Agent:
    return Agent(
        name="Productivity Assistant",
        agent_id="productivity-assistant",
        model=OpenAIChat(id=agent_settings.gpt_4),
        tools=[
            PythonREPL(),
            FileManager(),
            Calculator(),
            YouTubeTools(),
            WebScraper(),
            EmailTools(),
            PDFTools(),
            SQLTools(),
            DatetimeTools(),
        ],
        description="You are a productivity expert specializing in task automation, workflow optimization, and information management.",
        instructions=[
            "Task Automation:\n"
            "  - Write Python scripts for repetitive tasks\n"
            "  - Process and analyze documents efficiently\n"
            "  - Automate data collection and reporting\n"
            "  - Create SQL queries for data analysis\n"
            "  - Manage email communications",
            
            "Document Management:\n"
            "  - Extract key information from documents\n"
            "  - Organize and categorize content\n"
            "  - Generate structured summaries\n"
            "  - Maintain version control",
            
            "Information Processing:\n"
            "  - Synthesize data from multiple sources\n"
            "  - Create actionable insights\n"
            "  - Maintain clear documentation\n"
            "  - Schedule and track deadlines",
            
            "Team Collaboration:\n"
            "  - Automate workflows for Finance and Research teams\n"
            "  - Create templates and documentation\n"
            "  - Maintain shared knowledge base",
        ],
        markdown=True,
        show_tool_calls=True,
    )

def get_example_agent(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Agent:
    finance_agent = get_finance_agent()
    research_agent = get_research_agent()
    productivity_agent = get_productivity_agent()
    
    return Agent(
        name="AIGI3 Super Agent",
        agent_id="aigi3-super-agent",
        session_id=session_id,
        user_id=user_id,
        model=OpenAIChat(
            id=model_id or agent_settings.gpt_4,
            max_tokens=agent_settings.default_max_completion_tokens,
            temperature=agent_settings.default_temperature,
        ),
        team=[finance_agent, research_agent, productivity_agent],
        tools=[
            DuckDuckGo(),
            WebScraper(),
            Calculator(),
            PythonREPL(),
            FileManager(),
            YFinanceTools(enable_all=True),
            YouTubeTools(),
            PDFTools(),
            EmailTools(),
            SQLTools(),
            DatetimeTools(),
        ],
        description="""You are AIGI3, an advanced AI agent team coordinator specializing in finance, research, and productivity.
        You orchestrate a team of specialized agents and have access to comprehensive market data, research tools, and automation capabilities.
        Your role is to ensure seamless collaboration between agents and deliver high-quality, integrated solutions.""",
        instructions=[
            "Team Coordination:\n"
            "  - Analyze requests and delegate tasks to appropriate specialized agents\n"
            "  - Ensure effective communication between agents\n"
            "  - Synthesize insights from multiple agents into cohesive outputs\n"
            "  - Monitor and maintain quality standards across all deliverables",
            
            "Financial Analysis:\n"
            "  - Coordinate Finance Analyst's market research with Research Analyst's findings\n"
            "  - Ensure comprehensive coverage of both technical and fundamental analysis\n"
            "  - Validate financial data accuracy across team outputs",
            
            "Research Integration:\n"
            "  - Combine market intelligence with financial analysis\n"
            "  - Ensure cross-validation of sources and findings\n"
            "  - Maintain consistent research standards across the team",
            
            "Knowledge Management:\n"
            "  - Coordinate knowledge sharing between agents\n"
            "  - Ensure proper documentation of all analyses and findings\n"
            "  - Maintain version control of shared resources",
            
            "Productivity Enhancement:\n"
            "  - Identify opportunities for workflow automation\n"
            "  - Streamline collaboration between agents\n"
            "  - Optimize resource utilization across the team",
            
            "Quality Control:\n"
            "  - Review and validate all agent outputs\n"
            "  - Ensure consistency in formatting and presentation\n"
            "  - Maintain audit trails for all team activities",
        ],
        markdown=True,
        show_tool_calls=True,
        add_datetime_to_instructions=True,
        storage=example_agent_storage,
        read_chat_history=True,
        knowledge=example_agent_knowledge,
        search_knowledge=True,
        monitoring=True,
        debug_mode=debug_mode,
        monitoring_config={
            "metrics": {
                "custom_metrics": {
                    "team_coordination_latency": {
                        "type": "Histogram",
                        "description": "Time taken for team coordination tasks",
                        "buckets": [0.1, 0.5, 1.0, 2.0, 5.0]
                    },
                    "agent_memory_usage": {
                        "type": "Gauge",
                        "description": "Memory usage per agent"
                    },
                    "knowledge_base_hits": {
                        "type": "Counter",
                        "description": "Knowledge base access patterns"
                    }
                }
            },
            "tracing": {
                "enabled": True,
                "sample_rate": 1.0
            }
        },
        coordination_patterns={
            "consensus": {
                "min_agreements": 2,
                "timeout": 30
            },
            "fallback": {
                "retry_count": 3,
                "backup_agent": "productivity-agent"
            }
        },
        streaming=True,
        stream_tokens=True,
        stream_template="{agent_name}: {message}",
        conversation_memory=True,
        memory_window=10,
        error_handling={
            "ui_friendly_errors": True,
            "retry_on_failure": True,
            "max_retries": 3,
            "error_messages": {
                "rate_limit": "Please wait a moment before sending another message.",
                "token_limit": "The message is too long. Please try a shorter message.",
                "api_error": "There was a temporary issue. Please try again."
            }
        }
    )
