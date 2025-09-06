#!/usr/bin/env python3
"""Command-line interface for FM Global 8-34 ASRS Expert Agent."""

import asyncio
import sys
import uuid
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown

from pydantic_ai import Agent
from ..core.fm_global_agent import fm_global_agent
from ..core.dependencies import AgentDependencies
from ..config.settings import load_settings

console = Console()


async def stream_fm_global_interaction(user_input: str, conversation_history: List[str], deps: AgentDependencies) -> tuple[str, str]:
    """Stream FM Global agent interaction with real-time tool call display."""
    
    try:
        # Build context with conversation history
        context = "\n".join(conversation_history[-6:]) if conversation_history else ""
        
        prompt = f"""Previous conversation:
{context}

User: {user_input}

As an FM Global 8-34 ASRS expert, search the knowledge base and provide a comprehensive answer with specific table and figure references. Focus on practical guidance for ASRS fire protection design and cost optimization opportunities."""

        # Stream the agent execution
        async with fm_global_agent.iter(prompt, deps=deps) as run:
            
            response_text = ""
            
            async for node in run:
                
                # Handle user prompt node
                if Agent.is_user_prompt_node(node):
                    pass  # Clean start
                
                # Handle model request node - stream the thinking process
                elif Agent.is_model_request_node(node):
                    # Show assistant prefix at the start
                    console.print("[bold blue]🏭 FM Global Expert:[/bold blue] ", end="")
                
                # Handle model response node - stream response text
                elif Agent.is_model_response_node(node):
                    response_chunk = node.data.content[len(response_text):]
                    console.print(response_chunk, end="", flush=True)
                    response_text += response_chunk
                
                # Handle tool call node - show what tools are being used
                elif Agent.is_tool_call_node(node):
                    tool_name = node.data.tool_name
                    # Show user-friendly tool descriptions
                    tool_descriptions = {
                        'hybrid_search_fm_global': '🔍 Searching FM Global 8-34 database',
                        'semantic_search_fm_global': '🧠 Performing semantic search of FM Global content',
                        'get_fm_global_references': '📋 Finding relevant tables and figures',
                        'asrs_design_search': '🏗️ Comprehensive ASRS design analysis'
                    }
                    description = tool_descriptions.get(tool_name, f'Using {tool_name}')
                    console.print(f"\n[dim italic]{description}...[/dim italic]")
                
                # Handle tool result node - optionally show results
                elif Agent.is_tool_result_node(node):
                    # Show brief confirmation of results found
                    if hasattr(node.data, 'data') and node.data.data:
                        if isinstance(node.data.data, list) and len(node.data.data) > 0:
                            console.print(f"[dim italic]Found {len(node.data.data)} relevant results[/dim italic]")
            
            # Add final newline
            console.print("\n")
            
            return response_text, "success"
            
    except Exception as e:
        error_msg = f"Error during FM Global search: {str(e)}"
        console.print(f"[red]{error_msg}[/red]")
        return "", error_msg


async def main():
    """Main CLI function for FM Global Expert."""
    
    try:
        # Load settings
        settings = load_settings()
        
        # Initialize dependencies
        deps = AgentDependencies(settings=settings)
        await deps.initialize()
        
        # Display banner
        console.print(Panel.fit(
            "[bold blue]FM Global 8-34 ASRS Expert System[/bold blue]\n\n"
            "[white]Automated Storage & Retrieval Systems Fire Protection Expert[/white]\n"
            "[dim]Ask about FM Global 8-34 requirements, ASRS design, and cost optimization[/dim]\n\n"
            "[dim]Type 'exit' to quit, 'help' for commands[/dim]",
            border_style="blue"
        ))
        
        conversation_history = []
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold green]Ask FM Global Expert[/bold green]").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    console.print("[yellow]Thank you for using FM Global 8-34 ASRS Expert![/yellow]")
                    break
                
                elif user_input.lower() == 'help':
                    help_text = """
**FM Global 8-34 ASRS Expert Commands:**

• **help** - Show this help message
• **info** - Display system configuration
• **clear** - Clear the screen
• **exit/quit** - Exit the application

**Example Questions:**
• "What are the aisle width requirements for Class IV commodities?"
• "Show me Table 2-1 spacing requirements"
• "How can I reduce sprinkler system costs while maintaining compliance?"
• "What seismic bracing is required for high-rise racks?"
• "Find Figure 3-2 crane fire protection details"

**ASRS Topics Available:**
• Fire protection systems and sprinkler design
• Rack structural requirements and spacing
• Seismic design and bracing requirements
• Crane/SRM fire protection systems
• Storage classification and commodity types
• Cost optimization strategies
                    """
                    console.print(Markdown(help_text))
                    continue
                
                elif user_input.lower() == 'info':
                    info_text = f"""
**System Information:**
• **Provider**: {settings.llm_provider}
• **Model**: {settings.llm_model}
• **Database**: FM Global 8-34 Specialized Tables
• **Search**: Hybrid semantic + text search
• **Status**: Connected and ready
                    """
                    console.print(Markdown(info_text))
                    continue
                
                elif user_input.lower() == 'clear':
                    console.clear()
                    continue
                
                # Process the query
                response_text, status = await stream_fm_global_interaction(
                    user_input, conversation_history, deps
                )
                
                if status == "success" and response_text:
                    # Add to conversation history
                    conversation_history.append(f"User: {user_input}")
                    conversation_history.append(f"Assistant: {response_text}")
                    
                    # Keep conversation history manageable
                    if len(conversation_history) > 20:
                        conversation_history = conversation_history[-20:]
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit properly.[/yellow]")
                continue
            except Exception as e:
                console.print(f"[red]Unexpected error: {e}[/red]")
                continue
        
    except Exception as e:
        console.print(f"[red]Failed to start FM Global Expert: {e}[/red]")
        
        # Show helpful error messages
        if "tenant or user not found" in str(e).lower():
            console.print("[yellow]💡 Please check your DATABASE_URL in .env file[/yellow]")
        elif "api" in str(e).lower():
            console.print("[yellow]💡 Please check your LLM_API_KEY in .env file[/yellow]")
        
        sys.exit(1)
    
    finally:
        # Cleanup
        try:
            if 'deps' in locals():
                await deps.cleanup()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())