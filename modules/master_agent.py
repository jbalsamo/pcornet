"""
Master Agent Controller for managing specialized agents.
"""
from typing import Dict, Any, TypedDict
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, END
from .config import config
from .conversation_history import ConversationHistory
from .security import InputValidator, RateLimiter, InputValidationException, RateLimitException
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MasterAgentState(TypedDict):
    """State definition for the master agent."""
    messages: list
    user_input: str
    response: str
    error: str
    agent_type: str
    task_classification: str
    agent_responses: dict
    conversation_history: list

class MasterAgent:
    """Master Agent Controller for managing specialized agents."""
    
    def __init__(self):
        """Initialize the master agent with Azure OpenAI configuration."""
        self.llm = self._create_llm()
        self.graph = self._create_graph()
        self.specialized_agents = {}
        self.conversation_history = ConversationHistory(max_messages=config.max_conversation_messages)
        
        # Security components
        self.input_validator = InputValidator(max_length=config.max_input_length)
        self.rate_limiter = RateLimiter(
            max_calls=config.rate_limit_calls,
            time_window=config.rate_limit_period
        ) if config.rate_limit_enabled else None
        
        self._initialize_agents()
        
        # Load previous conversation history if available
        self._load_conversation_history()
    
    def _create_llm(self) -> AzureChatOpenAI:
        """Create Azure OpenAI LLM instance."""
        try:
            llm = AzureChatOpenAI(
                **config.get_azure_openai_kwargs(),
                temperature=1.0,
            )
            logger.info(f"Master Agent initialized with Azure OpenAI deployment: {config.chat_deployment}")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI: {e}")
            raise
    
    def _initialize_agents(self):
        """Initialize specialized agents."""
        try:
            # Import and initialize chat agent
            from .agents.chat_agent import ChatAgent
            
            self.specialized_agents = {
                "chat": ChatAgent()
            }
            
            logger.info("Chat agent initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Chat agent not available: {e}")
            self.specialized_agents = {}
            logger.info("Running with basic master agent only")
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow for the master agent."""
        workflow = StateGraph(MasterAgentState)
        
        # Add nodes
        workflow.add_node("classify_task", self._classify_task)
        workflow.add_node("route_to_agent", self._route_to_agent)
        workflow.add_node("synthesize_response", self._synthesize_response)
        workflow.add_node("handle_error", self._handle_error)
        
        # Set entry point
        workflow.set_entry_point("classify_task")
        
        # Add edges
        workflow.add_conditional_edges(
            "classify_task",
            self._should_continue_classification,
            {
                "route": "route_to_agent",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "route_to_agent",
            self._should_synthesize,
            {
                "synthesize": "synthesize_response",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("synthesize_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _classify_task(self, state: MasterAgentState) -> MasterAgentState:
        """Classify the user's task to determine which agent to use."""
        try:
            user_input = state.get("user_input", "")
            if not user_input.strip():
                state["error"] = "Empty input provided"
                return state
            
            # Use LLM to classify the task
            classification_prompt = f"""
            Classify the following user request into one of these categories:
            - chat: General conversation, questions, or assistance
            
            Note: Currently only the 'chat' category is available. Future categories may include:
            - analysis: Data analysis, file processing, or computational tasks
            - grading: Educational assessment, grading, or evaluation tasks
            - code_review: Code review, refactoring, or code quality analysis
            
            User request: "{user_input}"
            
            Respond with only the category name (currently should be 'chat').
            """
            
            messages = [
                {"role": "system", "content": "You are a task classifier. Respond with only the category name."},
                {"role": "user", "content": classification_prompt}
            ]
            
            # Convert to LangChain message format
            from langchain_core.messages import HumanMessage, SystemMessage
            langchain_messages = [
                SystemMessage(content=messages[0]["content"]),
                HumanMessage(content=messages[1]["content"])
            ]
            
            response = self.llm.invoke(langchain_messages)
            task_type = response.content.strip().lower()
            
            # Validate task type - only chat is available currently
            valid_types = ["chat"]
            if task_type not in valid_types:
                task_type = "chat"  # Default fallback
            
            state["task_classification"] = task_type
            state["agent_type"] = task_type
            state["messages"] = [
                {"role": "system", "content": f"You are handling a {task_type} task."},
                {"role": "user", "content": user_input}
            ]
            
            logger.info(f"Task classified as: {task_type}")
            return state
            
        except Exception as e:
            state["error"] = f"Error classifying task: {str(e)}"
            logger.error(f"Error in _classify_task: {e}")
            return state
    
    def _route_to_agent(self, state: MasterAgentState) -> MasterAgentState:
        """Route the task to the appropriate specialized agent."""
        try:
            agent_type = state.get("agent_type", "chat")
            user_input = state.get("user_input", "")
            
            if agent_type in self.specialized_agents:
                # Use specialized agent with conversation history
                specialized_agent = self.specialized_agents[agent_type]
                
                # Check if agent supports conversation history
                if hasattr(specialized_agent, 'process_with_history'):
                    response = specialized_agent.process_with_history(user_input, self.conversation_history)
                else:
                    # Fallback to original method
                    response = specialized_agent.process(user_input)
                
                state["agent_responses"] = {agent_type: response}
                logger.info(f"Task routed to {agent_type} agent")
            else:
                # Fallback to master agent direct processing with history
                history_messages = self.conversation_history.get_langchain_messages()
                
                # Add current user message
                from langchain_core.messages import HumanMessage, SystemMessage
                current_messages = [
                    SystemMessage(content=f"You are handling a {agent_type} task."),
                    HumanMessage(content=user_input)
                ]
                
                # Combine history with current message
                all_messages = history_messages + current_messages
                
                response = self.llm.invoke(all_messages)
                state["agent_responses"] = {"master": response.content}
                logger.info("Task handled by master agent directly with conversation history")
            
            return state
            
        except Exception as e:
            state["error"] = f"Error routing to agent: {str(e)}"
            logger.error(f"Error in _route_to_agent: {e}")
            return state
    
    def _synthesize_response(self, state: MasterAgentState) -> MasterAgentState:
        """Synthesize the final response from agent outputs."""
        try:
            agent_responses = state.get("agent_responses", {})
            
            if not agent_responses:
                state["error"] = "No agent responses to synthesize"
                return state
            
            # Use the primary agent response
            primary_response = list(agent_responses.values())[0]
            
            state["response"] = primary_response
            logger.info("Response synthesized successfully")
            return state
            
        except Exception as e:
            state["error"] = f"Error synthesizing response: {str(e)}"
            logger.error(f"Error in _synthesize_response: {e}")
            return state
    
    def _handle_error(self, state: MasterAgentState) -> MasterAgentState:
        """Handle errors in the workflow."""
        error_msg = state.get("error", "Unknown error occurred")
        state["response"] = f"I apologize, but I encountered an error: {error_msg}"
        logger.error(f"Handled error: {error_msg}")
        return state
    
    def _should_continue_classification(self, state: MasterAgentState) -> str:
        """Determine whether to continue after classification."""
        if state.get("error"):
            return "error"
        return "route"
    
    def _should_synthesize(self, state: MasterAgentState) -> str:
        """Determine whether to synthesize response after routing."""
        if state.get("error"):
            return "error"
        return "synthesize"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def chat(self, user_input: str, session_id: str = "default") -> str:
        """Main chat method to interact with the master agent.
        
        Args:
            user_input: The user's input message
            session_id: Session identifier for rate limiting (default: "default")
            
        Returns:
            The agent's response
            
        Raises:
            InputValidationException: If input validation fails
            RateLimitException: If rate limit is exceeded
        """
        start_time = time.time()
        success = True
        agent_type = "unknown"
        
        try:
            # Step 1: Validate input
            validation_result = self.input_validator.validate_input(user_input)
            if not validation_result["valid"]:
                raise InputValidationException(validation_result["error"])
            
            # Sanitize input
            user_input = self.input_validator.sanitize_input(user_input)
            
            # Step 2: Check rate limit
            if self.rate_limiter:
                rate_check = self.rate_limiter.check_rate_limit(session_id)
                if not rate_check["allowed"]:
                    raise RateLimitException(
                        f"Rate limit exceeded. Please try again in {rate_check['retry_after']} seconds."
                    )
            
            # Step 3: Add user message to conversation history
            self.conversation_history.add_user_message(user_input)
            
            # Step 4: Initialize state
            initial_state = {
                "messages": [],
                "user_input": user_input,
                "response": "",
                "error": "",
                "agent_type": "",
                "task_classification": "",
                "agent_responses": {},
                "conversation_history": self.conversation_history.get_messages_for_llm()
            }
            
            # Step 5: Run the graph
            result = self.graph.invoke(initial_state)
            agent_type = result.get("task_classification", "unknown")
            
            response = result.get("response", "No response generated")
            
            # Step 6: Add assistant response to conversation history
            self.conversation_history.add_assistant_message(response, agent_type)
            
            return response
            
        except (InputValidationException, RateLimitException) as e:
            # These are expected exceptions, don't log as errors
            logger.warning(f"Request blocked: {e}")
            raise
            
        except Exception as e:
            success = False
            error_response = f"I apologize, but I encountered an error: {str(e)}"
            # Still add the error response to history for context
            self.conversation_history.add_assistant_message(error_response, "error")
            
            logger.error(f"Error in chat method: {e}")
            return error_response
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the master agent configuration."""
        return {
            "endpoint": config.endpoint,
            "deployment": config.chat_deployment,
            "api_version": config.api_version,
            "model_type": "Azure OpenAI Master Agent",
            "specialized_agents": list(self.specialized_agents.keys())
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all managed agents."""
        status = {
            "master_agent": "active",
            "specialized_agents": {}
        }
        
        for agent_name, agent in self.specialized_agents.items():
            try:
                if hasattr(agent, 'get_status'):
                    status["specialized_agents"][agent_name] = agent.get_status()
                else:
                    status["specialized_agents"][agent_name] = "active"
            except Exception as e:
                status["specialized_agents"][agent_name] = f"error: {str(e)}"
        
        return status
    
    def get_conversation_history(self) -> Dict[str, Any]:
        """Get conversation history statistics and recent messages."""
        return {
            "stats": self.conversation_history.get_stats(),
            "recent_context": self.conversation_history.get_recent_context(10),
            "total_messages": len(self.conversation_history)
        }
    
    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history.clear_history()
        logger.info("Conversation history cleared by user request")
    
    def _load_conversation_history(self) -> None:
        """Load conversation history from disk on startup."""
        try:
            if self.conversation_history.load_from_disk():
                loaded_count = len(self.conversation_history)
                if loaded_count > 0:
                    logger.info(f"Restored previous conversation with {loaded_count} messages")
                    print(f"💾 Restored previous conversation with {loaded_count} messages")
            else:
                logger.info("Starting with fresh conversation history")
        except Exception as e:
            logger.warning(f"Could not load conversation history: {e}")
            print(f"⚠️  Could not restore previous conversation, starting fresh")
    
    def save_conversation_history(self) -> bool:
        """Save current conversation history to disk.
        
        Returns:
            True if save was successful, False otherwise
        """
        try:
            success = self.conversation_history.save_to_disk()
            if success:
                logger.info("Conversation history saved successfully")
            return success
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}")
            return False
    
    def shutdown(self) -> None:
        """Perform cleanup operations before shutdown."""
        logger.info("Shutting down Master Agent...")
        
        # Save conversation history
        if len(self.conversation_history) > 0:
            print("💾 Saving conversation history...")
            if self.save_conversation_history():
                print(f"✅ Saved {len(self.conversation_history)} messages for next session")
            else:
                print("⚠️  Could not save conversation history")
        
        logger.info("Master Agent shutdown complete")
