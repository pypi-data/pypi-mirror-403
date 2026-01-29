#!/usr/bin/env python3
"""Edison Scientific MCP Server - Interface for interacting with Edison Scientific platform (former FutureHouse)."""

import os
import sys
import signal
import asyncio
import typer

from pathlib import Path
from datetime import timedelta
from typing import List, Dict, Any, Optional, Union
from importlib.metadata import version, PackageNotFoundError
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from eliot import start_action, Message
from fastmcp.server.tasks import TaskConfig, TaskMode


# Import Edison client components
from edison_client import EdisonClient, JobNames
from edison_client.models import (
    RuntimeConfig,
    TaskRequest,
)
from smithery.decorators import smithery 

# Configuration
DEFAULT_HOST = os.getenv("MCP_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("MCP_PORT", "3011"))
DEFAULT_TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")

# Get package version
try:
    __version__ = version("edison-mcp")
except PackageNotFoundError:
    __version__ = "unknown"

class EdisonResult(BaseModel):
    """Result from an Edison Scientific API call."""
    data: Any = Field(description="Response data from Edison Scientific")
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Operation description")
    task_id: Optional[str] = Field(default=None, description="Task ID for tracking")
    status: Optional[str] = Field(default=None, description="Task status")

class EdisonMCP(FastMCP):
    """Edison Scientific MCP Server with client-based tools that can be inherited and extended."""
    
    def __init__(
        self, 
        name: str = f"Edison Scientific MCP Server v{__version__}",
        api_key: Optional[str] = None,
        prefix: str = "edison_",
        task_mode: TaskMode = "required",
        poll_interval: timedelta = timedelta(seconds=10),
        **kwargs
    ):
        """Initialize the Edison Scientific tools with client and FastMCP functionality."""
        # Initialize FastMCP with the provided name and any additional kwargs
        super().__init__(name=name, **kwargs)
        
        # Get API credentials from environment if not provided
        # Support both EDISON_API_KEY (new) and FUTUREHOUSE_API_KEY (backward compatibility)
        futurehouse_key = os.getenv("FUTUREHOUSE_API_KEY", "")
        edison_key = os.getenv("EDISON_API_KEY", futurehouse_key)
        self.api_key = api_key or edison_key
        
        if not self.api_key:
            raise ValueError("Edison Scientific API key is required. Set EDISON_API_KEY (or FUTUREHOUSE_API_KEY for backward compatibility) environment variable or pass api_key parameter.")
        
        # Initialize our Edison client
        self.client = EdisonClient(api_key=self.api_key)
        self.task_config = TaskConfig(
            mode=task_mode,
            poll_interval=poll_interval,
        )
        self.prefix = prefix
        
        # Register our tools and resources
        self._register_edison_tools()
        self._register_edison_resources()
    
    def _register_edison_tools(self):
        """Register Edison Scientific-specific tools."""
        # Register model-specific tools
        
        
        self.tool(
            name=f"{self.prefix}chem_agent", 
            description="Request PHOENIX/MOLECULES model for chemistry tasks: synthesis planning, novel molecule design, and cheminformatics analysis",
            task=self.task_config,
        )(self.chem_agent)
        
        self.tool(
            name=f"{self.prefix}quick_search_agent", 
            description="Request CROW/LITERATURE model for concise scientific search: produces succinct answers citing scientific data sources",
            task=self.task_config,
        )(self.quick_search_agent)
        
        self.tool(
            name=f"{self.prefix}precedent_search_agent", 
            description="Request OWL/PRECEDENT model for precedent search: determines if anyone has done something in science",
            task=self.task_config,
        )(self.precedent_search_agent)
        
        self.tool(
            name=f"{self.prefix}deep_search_agent", 
            description="Request FALCON/LITERATURE model for deep search: produces long reports with many sources for literature reviews",
            task=self.task_config,
        )(self.deep_search_agent)
        
        self.tool(
            name=f"{self.prefix}data_analysis_agent",
            description="Request FINCH/ANALYSIS model for data analysis tasks: analyze datasets, perform statistical analysis, and generate insights",
            task=self.task_config,
        )(self.data_analysis_agent)
        
        # Register continuation tool
        self.tool(
            name=f"{self.prefix}continue_task", 
            description="Continue a previous task with a follow-up question",
            task=self.task_config,
        )(self.continue_task)
    
    def _register_edison_resources(self):
        """Register Edison Scientific-specific resources."""
        
        @self.resource(f"resource://{self.prefix}api-info")
        def get_api_info() -> str:
            """
            Get information about the Edison Scientific client capabilities and usage.
            
            This resource contains information about:
            - Available models and their capabilities
            - Authentication requirements
            - Task submission patterns
            
            Returns:
                Client information and usage guidelines
            """
            return f"""
            # Edison Scientific MCP Server
            
            ## Authentication
            - Uses Edison Scientific client with API key authentication
            - API key: {self.api_key[:8]}...
            
            ## Available Models
            
            ### PHOENIX (MOLECULES)
            - **Task Type**: Chemistry Tasks (Experimental)
            - **Description**: Synthesis planning, novel molecule design, and cheminformatics analysis
            - **Example Queries**:
              - "Show three examples of amide coupling reactions"
              - "Tell me how to synthesize safinamide & where to buy each reactant"
              - "Propose 3 novel compounds that could treat a disease"
            
            ### CROW (LITERATURE)
            - **Task Type**: Concise Scientific Search
            - **Description**: Produces succinct answers citing scientific data sources
            - **Example Queries**:
              - "What are likely mechanisms for age-related macular degeneration?"
              - "How compelling is genetic evidence for targeting PTH1R in small cell lung cancer?"
            
            ### OWL (PRECEDENT)
            - **Task Type**: Precedent Search
            - **Description**: Determines if anyone has done something in science
            - **Example Queries**:
              - "Has anyone developed efficient non-CRISPR methods for modifying DNA?"
              - "Has anyone used single-molecule footprinting to examine transcription factor binding?"
            
            ### FALCON (LITERATURE)
            - **Task Type**: Deep Search
            - **Description**: Produces long reports with many sources for literature reviews
            - **Example Queries**:
              - "What is the latest research on physiological benefits of coffee consumption?"
              - "What have been the most empirically effective treatments for Ulcerative Colitis?"
            
            ### FINCH (ANALYSIS)
            - **Task Type**: Data Analysis
            - **Description**: Analyze datasets, perform statistical analysis, and generate insights from data
            - **Example Queries**:
              - "Analyze this dataset and identify key trends"
              - "Perform statistical analysis on the correlation between variables"
              - "Generate insights from this experimental data"
            
            ## Usage
            
            ```python
            # Request a model
            result = await edison_chem_agent(query="Synthesize aspirin")
            result = await edison_quick_search_agent(query="What causes Alzheimer's disease?")
            result = await edison_precedent_search_agent(query="Has anyone used CRISPR for malaria treatment?")
            result = await edison_deep_search_agent(query="Review treatments for diabetes")
            result = await edison_data_analysis_agent(query="Analyze trends in this dataset")
            
            # Continue a previous task
            result = await edison_continue_task(
                previous_task_id="task_123",
                query="Tell me more about the third option",
                job_name="phoenix"
            )
            ```
            """
    
    async def chem_agent(
        self,
        query: str
    ) -> EdisonResult:
        """
        Request PHOENIX model for chemistry tasks: synthesis planning, novel molecule design, and cheminformatics analysis.
        
        Example queries:
        - "Show three examples of amide coupling reactions"
        - "Tell me how to synthesize safinamide & where to buy each reactant"
        - "Propose 3 novel compounds that could treat a disease caused by over-expression of DENND1A"
        
        Args:
            query: The chemistry question or task to submit
            
        Returns:
            EdisonResult containing PHOENIX response
        """
        with start_action(action_type="chem_agent", query=query[:100] + "..." if len(query) > 100 else query):
            try:
                # Create task request for PHOENIX
                task_data = TaskRequest(
                    name=JobNames.PHOENIX,
                    query=query,
                )
                
                # Submit and run task until completion
                task_responses = self.client.run_tasks_until_done(task_data)
                
                if len(task_responses) == 0:
                    raise Exception("No tasks returned from PHOENIX")
                
                actual_response = task_responses[-1]
                answer = getattr(actual_response, 'answer', None) or getattr(actual_response, 'formatted_answer', None) or ""
                
                return EdisonResult(
                    data={
                        "task_id": str(actual_response.task_id) if actual_response.task_id else None,
                        "status": actual_response.status,
                        "answer": answer,
                        "job_name": "phoenix",
                        "query": query
                    },
                    success=True,
                    message=f"PHOENIX task completed successfully with status: {actual_response.status}",
                    task_id=str(actual_response.task_id) if actual_response.task_id else None,
                    status=actual_response.status
                )
                
            except Exception as e:
                return EdisonResult(
                    data={"error": str(e), "job_name": "phoenix", "query": query},
                    success=False,
                    message=f"Failed to submit PHOENIX request: {str(e)}"
                )
    
    async def quick_search_agent(
        self,
        query: str
    ) -> EdisonResult:
        """
        Request CROW model for concise scientific search: produces succinct answers citing scientific data sources.
        
        Example queries:
        - "What are likely mechanisms by which mutations near HTRA1 might cause age-related macular degeneration?"
        - "How compelling is genetic evidence for targeting PTH1R in small cell lung cancer?"
        - "What factors limit the wavelengths of light detectable by mammalian eyes?"
        
        Args:
            query: The scientific question to submit
            
        Returns:
            EdisonResult containing CROW response
        """
        with start_action(action_type="quick_search_agent", query=query[:100] + "..." if len(query) > 100 else query):
            try:
                # Create task request for CROW
                task_data = TaskRequest(
                    name=JobNames.CROW,
                    query=query,
                )
                
                # Submit and run task until completion
                task_responses = self.client.run_tasks_until_done(task_data)
                
                if len(task_responses) == 0:
                    raise Exception("No tasks returned from CROW")
                
                actual_response = task_responses[-1]
                answer = getattr(actual_response, 'answer', None) or getattr(actual_response, 'formatted_answer', None) or ""
                
                return EdisonResult(
                    data={
                        "task_id": str(actual_response.task_id) if actual_response.task_id else None,
                        "status": actual_response.status,
                        "answer": answer,
                        "job_name": "crow",
                        "query": query
                    },
                    success=True,
                    message=f"CROW task completed successfully with status: {actual_response.status}",
                    task_id=str(actual_response.task_id) if actual_response.task_id else None,
                    status=actual_response.status
                )
                
            except Exception as e:
                return EdisonResult(
                    data={"error": str(e), "job_name": "crow", "query": query},
                    success=False,
                    message=f"Failed to submit CROW request: {str(e)}"
                )
    
    async def precedent_search_agent(
        self,
        query: str
    ) -> EdisonResult:
        """
        Request OWL model for precedent search: determines if anyone has done something in science.
        
        Example queries:
        - "Has anyone developed efficient non-CRISPR methods for modifying DNA?"
        - "Has anyone used single-molecule footprinting to examine transcription factor binding in human cells?"
        - "Has anyone studied using a RAG system to help make better diagnoses for patients?"
        
        Args:
            query: The precedent question to submit
            
        Returns:
            EdisonResult containing OWL response
        """
        with start_action(action_type="precedent_search_agent", query=query[:100] + "..." if len(query) > 100 else query):
            try:
                # Create task request for OWL
                task_data = TaskRequest(
                    name=JobNames.OWL,
                    query=query,
                )
                
                # Submit and run task until completion
                task_responses = self.client.run_tasks_until_done(task_data)
                
                if len(task_responses) == 0:
                    raise Exception("No tasks returned from OWL")
                
                actual_response = task_responses[-1]
                answer = getattr(actual_response, 'answer', None) or getattr(actual_response, 'formatted_answer', None) or ""
                
                return EdisonResult(
                    data={
                        "task_id": str(actual_response.task_id) if actual_response.task_id else None,
                        "status": actual_response.status,
                        "answer": answer,
                        "job_name": "owl",
                        "query": query
                    },
                    success=True,
                    message=f"OWL task completed successfully with status: {actual_response.status}",
                    task_id=str(actual_response.task_id) if actual_response.task_id else None,
                    status=actual_response.status
                )
                
            except Exception as e:
                return EdisonResult(
                    data={"error": str(e), "job_name": "owl", "query": query},
                    success=False,
                    message=f"Failed to submit OWL request: {str(e)}"
                )
    
    async def deep_search_agent(
        self,
        query: str
    ) -> EdisonResult:
        """
        Request FALCON model for deep search: produces long reports with many sources for literature reviews.
        
        Example queries:
        - "What is the latest research on physiological benefits of high levels of coffee consumption?"
        - "What genes have been most strongly implicated in causing age-related macular degeneration?"
        - "What have been the most empirically effective treatments for Ulcerative Colitis?"
        
        Args:
            query: The literature review question to submit
            
        Returns:
            EdisonResult containing FALCON response
        """
        with start_action(action_type="deep_search_agent", query=query[:100] + "..." if len(query) > 100 else query):
            try:
                # Create task request for FALCON
                task_data = TaskRequest(
                    name=JobNames.FALCON,
                    query=query,
                )
                
                # Submit and run task until completion
                task_responses = self.client.run_tasks_until_done(task_data)
                
                if len(task_responses) == 0:
                    raise Exception("No tasks returned from FALCON")
                
                actual_response = task_responses[-1]
                answer = getattr(actual_response, 'answer', None) or getattr(actual_response, 'formatted_answer', None) or ""
                
                return EdisonResult(
                    data={
                        "task_id": str(actual_response.task_id) if actual_response.task_id else None,
                        "status": actual_response.status,
                        "answer": answer,
                        "job_name": "falcon",
                        "query": query
                    },
                    success=True,
                    message=f"FALCON task completed successfully with status: {actual_response.status}",
                    task_id=str(actual_response.task_id) if actual_response.task_id else None,
                    status=actual_response.status
                )
                
            except Exception as e:
                return EdisonResult(
                    data={"error": str(e), "job_name": "falcon", "query": query},
                    success=False,
                    message=f"Failed to submit FALCON request: {str(e)}"
                )
    
    async def data_analysis_agent(
        self,
        query: str
    ) -> EdisonResult:
        """
        Request FINCH model for data analysis tasks: analyze datasets, perform statistical analysis, and generate insights.
        
        Example queries:
        - "Analyze this dataset and identify key trends"
        - "Perform statistical analysis on the correlation between variables X and Y"
        - "Generate insights from this experimental data and suggest next steps"
        
        Args:
            query: The data analysis question or task to submit
            
        Returns:
            EdisonResult containing FINCH response
        """
        with start_action(action_type="data_analysis_agent", query=query[:100] + "..." if len(query) > 100 else query):
            try:
                # Create task request for FINCH (ANALYSIS)
                task_data = TaskRequest(
                    name=JobNames.FINCH,
                    query=query,
                )
                
                # Submit and run task until completion
                task_responses = self.client.run_tasks_until_done(task_data)
                
                if len(task_responses) == 0:
                    raise Exception("No tasks returned from FINCH")
                
                actual_response = task_responses[-1]
                answer = getattr(actual_response, 'answer', None) or getattr(actual_response, 'formatted_answer', None) or ""
                
                return EdisonResult(
                    data={
                        "task_id": str(actual_response.task_id) if actual_response.task_id else None,
                        "status": actual_response.status,
                        "answer": answer,
                        "job_name": "finch",
                        "query": query
                    },
                    success=True,
                    message=f"FINCH task completed successfully with status: {actual_response.status}",
                    task_id=str(actual_response.task_id) if actual_response.task_id else None,
                    status=actual_response.status
                )
                
            except Exception as e:
                return EdisonResult(
                    data={"error": str(e), "job_name": "finch", "query": query},
                    success=False,
                    message=f"Failed to submit FINCH request: {str(e)}"
                )
    
    async def continue_task(
        self,
        previous_task_id: str,
        query: str,
        job_name: str
    ) -> EdisonResult:
        """
        Continue a previous task with a follow-up question.
        
        Args:
            previous_task_id: ID of the previous task to continue
            query: Follow-up question or task
            job_name: Name of the job (should match the original task)
            
        Returns:
            EdisonResult containing the continued task response
        """
        with start_action(action_type="continue_task", task_id=previous_task_id, job_name=job_name):
            try:
                # Create continued task data
                continued_job_data = {
                    "name": JobNames.from_string(job_name),
                    "query": query,
                    "runtime_config": {"continued_job_id": previous_task_id},
                }
                
                # Submit and run continued task until completion
                task_responses = self.client.run_tasks_until_done(continued_job_data)
                
                # run_tasks_until_done always returns a list
                if len(task_responses) == 0:
                    raise Exception("No tasks returned")
                
                # Take the last task response (most recent)
                actual_response = task_responses[-1]
                
                # Get the answer - different response types have different fields
                answer = getattr(actual_response, 'answer', None) or getattr(actual_response, 'formatted_answer', None) or ""
                
                return EdisonResult(
                    data={
                        "task_id": str(actual_response.task_id) if actual_response.task_id else None,
                        "status": actual_response.status,
                        "answer": answer,
                        "job_name": job_name,
                        "query": query,
                        "previous_task_id": previous_task_id
                    },
                    success=True,
                    message=f"Continued task completed successfully. Status: {actual_response.status}",
                    task_id=str(actual_response.task_id) if actual_response.task_id else None,
                    status=actual_response.status
                )
                
            except Exception as e:
                return EdisonResult(
                    data={"error": str(e), "previous_task_id": previous_task_id, "query": query},
                    success=False,
                    message=f"Failed to continue task: {str(e)}"
                )
    
# Create the MCP server instance lazily to avoid authentication during imports
def get_mcp_server():
    """Get or create the MCP server instance."""
    return EdisonMCP()

class GracefulShutdownHandler:
    """Handle graceful shutdown on SIGINT and SIGTERM."""
    
    def __init__(self):
        self.shutdown_requested = False
        self.original_sigint_handler = None
        self.original_sigterm_handler = None
    
    def register_handlers(self):
        """Register signal handlers for graceful shutdown."""
        self.original_sigint_handler = signal.signal(signal.SIGINT, self._signal_handler)
        self.original_sigterm_handler = signal.signal(signal.SIGTERM, self._signal_handler)
    
    def restore_handlers(self):
        """Restore original signal handlers."""
        if self.original_sigint_handler:
            signal.signal(signal.SIGINT, self.original_sigint_handler)
        if self.original_sigterm_handler:
            signal.signal(signal.SIGTERM, self.original_sigterm_handler)
    
    def _signal_handler(self, signum: int, frame):
        """Handle shutdown signals gracefully."""
        if self.shutdown_requested:
            # Force exit on second signal
            Message.log(message_type="shutdown", message="Force shutdown requested")
            sys.exit(1)
        
        self.shutdown_requested = True
        signame = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        Message.log(message_type="shutdown", message=f"Received {signame}, initiating graceful shutdown...")
        
        # Raise KeyboardInterrupt to trigger cleanup
        raise KeyboardInterrupt()

def run_with_graceful_shutdown(server: EdisonMCP, **kwargs):
    """Run the server with graceful shutdown handling.
    
    Args:
        server: The EdisonMCP server instance
        **kwargs: Additional arguments to pass to server.run()
    """
    shutdown_handler = GracefulShutdownHandler()
    
    try:
        shutdown_handler.register_handlers()
        Message.log(message_type="startup", message="Server starting with graceful shutdown enabled")
        server.run(**kwargs)
    except KeyboardInterrupt:
        Message.log(message_type="shutdown", message="Shutdown signal received, cleaning up...")
    except Exception as e:
        Message.log(message_type="error", message=f"Server error: {str(e)}")
        raise
    finally:
        shutdown_handler.restore_handlers()
        Message.log(message_type="shutdown", message="Server stopped")
class SmitheryConfigSchema(BaseModel):
    api_key: str = Field(..., description="Edison Scientific API key")

@smithery.server(config_schema=SmitheryConfigSchema)
def start_mcp_smithery(ctx: Context):
    """Start the Edison Scientific MCP server with Smithery configuration."""
    session_config = ctx.session_config
    return EdisonMCP(api_key=session_config.api_key)


# CLI application using typer
app = typer.Typer()

@app.command()
def main(
    host: str = typer.Option(DEFAULT_HOST, help="Host to bind to"),
    port: int = typer.Option(DEFAULT_PORT, help="Port to bind to"),
    transport: str = typer.Option(DEFAULT_TRANSPORT, help="Transport type")
):
    """Run the Edison Scientific MCP server."""
    run_with_graceful_shutdown(get_mcp_server(), transport=transport, host=host, port=port)

@app.command()
def stdio():
    """Run the Edison Scientific MCP server with stdio transport."""
    run_with_graceful_shutdown(get_mcp_server(), transport="stdio")

@app.command()
def http(
    host: str = typer.Option(DEFAULT_HOST, help="Host to bind to"),
    port: int = typer.Option(DEFAULT_PORT, help="Port to bind to")
):
    """Run the Edison Scientific MCP server with HTTP transport."""
    run_with_graceful_shutdown(get_mcp_server(), transport="http", host=host, port=port)


@app.command()
def sse(
    host: str = typer.Option(DEFAULT_HOST, help="Host to bind to"),
    port: int = typer.Option(DEFAULT_PORT, help="Port to bind to")
):
    """Run the Edison Scientific MCP server with SSE transport."""
    run_with_graceful_shutdown(get_mcp_server(), transport="sse", host=host, port=port)

def cli_app():
    """Entry point for the CLI application."""
    app()

def cli_app_stdio():
    """Entry point for stdio mode."""
    stdio()

def cli_app_sse():
    """Entry point for SSE mode."""
    sse()

def cli_app_http():
    """Entry point for HTTP mode."""
    http()

if __name__ == "__main__":
    app() 