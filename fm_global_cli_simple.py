#!/usr/bin/env python3
"""Simple CLI for FM Global 8-34 ASRS Expert Agent."""

import asyncio
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from rag_agent.core.fm_global_agent import fm_global_agent
from rag_agent.core.dependencies import AgentDependencies
from rag_agent.config.settings import load_settings

console = Console()

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
            "[dim]Type 'exit' to quit[/dim]",
            border_style="blue"
        ))
        
        conversation_history = []
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold green]Ask FM Global Expert[/bold green]").strip()
                
                if not user_input:
                    continue
                
                # Handle exit
                if user_input.lower() in ['exit', 'quit', 'q']:
                    console.print("[yellow]Thank you for using FM Global 8-34 ASRS Expert![/yellow]")
                    break
                
                # Build context
                context = "\n".join(conversation_history[-6:]) if conversation_history else ""
                
                prompt = f"""Previous conversation:
{context}

User: {user_input}

As an FM Global 8-34 ASRS expert, search the knowledge base and provide a comprehensive answer with specific table and figure references. Focus on practical guidance for ASRS fire protection design."""
                
                # Show thinking
                console.print("[dim italic]🔍 Searching FM Global 8-34 database...[/dim italic]")
                
                # Run the agent
                try:
                    result = await fm_global_agent.run(prompt, deps=deps)
                    # Extract the response text from AgentRunResult
                    if hasattr(result, 'output'):
                        response_text = result.output
                    elif hasattr(result, 'data'):
                        response_text = result.data
                    elif hasattr(result, 'content'):
                        response_text = result.content
                    elif hasattr(result, 'message'):
                        response_text = result.message
                    else:
                        # Parse from string representation if needed
                        result_str = str(result)
                        if "output='" in result_str:
                            response_text = result_str.split("output='")[1].rsplit("')", 1)[0]
                        else:
                            response_text = result_str
                    
                    # Display response
                    console.print(f"\n[bold blue]🏭 FM Global Expert:[/bold blue]\n{response_text}\n")
                except Exception as agent_error:
                    console.print(f"[red]Agent error: {agent_error}[/red]")
                    response_text = None
                
                # Add to conversation history if we got a response
                if response_text:
                    conversation_history.append(f"User: {user_input}")
                    conversation_history.append(f"Assistant: {response_text}")
                    
                    # Keep history manageable
                    if len(conversation_history) > 20:
                        conversation_history = conversation_history[-20:]
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit properly.[/yellow]")
                continue
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                continue
        
    except Exception as e:
        console.print(f"[red]Failed to start FM Global Expert: {e}[/red]")
        
        # Show helpful error messages
        if "tenant or user not found" in str(e).lower():
            console.print("[yellow]💡 Please check your DATABASE_URL in .env file[/yellow]")
        elif "api" in str(e).lower() or "model" in str(e).lower():
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