"""
Cognitive System for ECHO
Implements the 5-layer cognitive architecture
"""

import asyncio
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
import json
from pathlib import Path
import logging

from ..models.local_llm import LocalLLMAdapter, TaskCategory

logger = logging.getLogger(__name__)


class CognitiveLayer(Enum):
    """The 5 layers of cognitive architecture"""
    ROUTER = "intelligent_router"
    CONTEXT = "deep_context_engine"
    COUNCIL = "multi_agent_council"
    LEARNING = "learning_core"
    ANTICIPATION = "anticipation_engine"


@dataclass
class CognitiveRequest:
    """Request to be processed by cognitive system"""
    prompt: str
    context: Dict[str, Any]
    complexity: float
    requires_council: bool = False
    
    
@dataclass
class CognitiveResponse:
    """Response from cognitive system"""
    content: str
    reasoning: str
    confidence: float
    layers_used: List[CognitiveLayer]
    metadata: Dict[str, Any]


class CognitiveSystem:
    """
    5-Layer Cognitive Architecture for ECHO
    Provides advanced intelligence beyond simple prompt-response
    """
    
    def __init__(self, llm_adapter: LocalLLMAdapter):
        """Initialize the cognitive system"""
        self.llm = llm_adapter
        self.layers = {
            CognitiveLayer.ROUTER: IntelligentRouter(llm_adapter),
            CognitiveLayer.CONTEXT: DeepContextEngine(),
            CognitiveLayer.COUNCIL: MultiAgentCouncil(llm_adapter),
            CognitiveLayer.LEARNING: LearningCore(),
            CognitiveLayer.ANTICIPATION: AnticipationEngine()
        }
        self.memory = {}
        
    async def process(self, request: CognitiveRequest) -> CognitiveResponse:
        """
        Process a request through the cognitive layers
        
        This implements the full 5-layer architecture:
        1. Route through intelligent router
        2. Enrich with deep context
        3. Optionally engage multi-agent council
        4. Apply learned patterns
        5. Anticipate follow-up needs
        """
        layers_used = []
        
        # Layer 1: Intelligent Routing
        routing_result = await self.layers[CognitiveLayer.ROUTER].route(request)
        layers_used.append(CognitiveLayer.ROUTER)
        
        # Layer 2: Deep Context
        context_result = await self.layers[CognitiveLayer.CONTEXT].analyze(
            request, routing_result
        )
        layers_used.append(CognitiveLayer.CONTEXT)
        
        # Layer 3: Multi-Agent Council (if needed)
        if request.complexity > 0.7 or request.requires_council:
            council_result = await self.layers[CognitiveLayer.COUNCIL].deliberate(
                request, context_result
            )
            layers_used.append(CognitiveLayer.COUNCIL)
            final_content = council_result.consensus
        else:
            # Single agent response
            final_content = await self._generate_single_response(
                request, routing_result, context_result
            )
        
        # Layer 4: Learning
        learning_insights = await self.layers[CognitiveLayer.LEARNING].apply(
            request, final_content
        )
        if learning_insights:
            layers_used.append(CognitiveLayer.LEARNING)
        
        # Layer 5: Anticipation
        anticipations = await self.layers[CognitiveLayer.ANTICIPATION].predict(
            request, final_content
        )
        if anticipations:
            layers_used.append(CognitiveLayer.ANTICIPATION)
        
        return CognitiveResponse(
            content=final_content,
            reasoning=routing_result.reasoning,
            confidence=routing_result.confidence,
            layers_used=layers_used,
            metadata={
                "model_used": routing_result.selected_model,
                "complexity": request.complexity,
                "anticipations": anticipations,
                "learning_applied": bool(learning_insights)
            }
        )
    
    async def _generate_single_response(self, 
                                       request: CognitiveRequest,
                                       routing: Any,
                                       context: Any) -> str:
        """Generate response with single agent"""
        enhanced_prompt = f"""
Context: {json.dumps(context.relevant_context, indent=2)}

User Request: {request.prompt}

Please provide a comprehensive response considering the context.
"""
        
        response = ""
        async for token in self.llm.generate(
            prompt=enhanced_prompt,
            model=routing.selected_model,
            task_category=routing.task_category
        ):
            response += token
            
        return response


class IntelligentRouter:
    """Layer 1: Routes requests to appropriate models and strategies"""
    
    def __init__(self, llm_adapter: LocalLLMAdapter):
        self.llm = llm_adapter
        
    async def route(self, request: CognitiveRequest):
        """Analyze request and determine routing"""
        # Use LLM to understand intent (not just keywords)
        analysis_prompt = f"""
Analyze this request and determine:
1. Primary task category (reasoning/coding/debugging/etc)
2. Complexity level (0-1)
3. Best model to use
4. Whether multi-agent council is needed

Request: {request.prompt}

Respond in JSON format.
"""
        
        response = ""
        async for token in self.llm.generate(
            prompt=analysis_prompt,
            model="qwen2.5-coder:7b",  # Fast model for routing
            task_category=TaskCategory.REASONING
        ):
            response += token
        
        # Parse response (with fallback)
        try:
            import json
            data = json.loads(response)
            task_category = TaskCategory[data.get("category", "GENERAL").upper()]
            complexity = float(data.get("complexity", 0.5))
        except:
            # Fallback to simple classification
            task_category = TaskCategory.GENERAL
            complexity = 0.5
        
        selected_model = self.llm.select_model(task_category, complexity)
        
        class RoutingResult:
            def __init__(self):
                self.task_category = task_category
                self.selected_model = selected_model
                self.confidence = 0.8
                self.reasoning = "Intelligent routing based on request analysis"
                
        return RoutingResult()


class DeepContextEngine:
    """Layer 2: Provides deep contextual understanding"""
    
    async def analyze(self, request, routing_result):
        """Analyze context and enrich request"""
        # In full implementation, this would:
        # - Query vector database
        # - Build AST of relevant code
        # - Map dependencies
        # - Identify patterns
        
        class ContextResult:
            def __init__(self):
                self.relevant_context = {
                    "request_type": routing_result.task_category.value,
                    "inferred_intent": "User needs assistance with development task",
                    "suggested_approach": "Provide clear, actionable response"
                }
                
        return ContextResult()


class MultiAgentCouncil:
    """Layer 3: Multiple specialized agents collaborate"""
    
    def __init__(self, llm_adapter: LocalLLMAdapter):
        self.llm = llm_adapter
        self.agents = {
            "architect": "High-level design and structure",
            "implementer": "Detailed implementation",
            "reviewer": "Code review and quality",
            "security": "Security considerations",
            "performance": "Performance optimization"
        }
        
    async def deliberate(self, request, context):
        """Multiple agents discuss and reach consensus"""
        perspectives = {}
        
        # Gather perspectives from each agent
        for agent_name, agent_role in self.agents.items():
            agent_prompt = f"""
As the {agent_name} agent responsible for {agent_role}, 
provide your perspective on this request:

{request.prompt}

Context: {context.relevant_context}
"""
            
            response = ""
            async for token in self.llm.generate(
                prompt=agent_prompt,
                model="qwen2.5-coder:32b",
                task_category=TaskCategory.REASONING
            ):
                response += token
                
            perspectives[agent_name] = response
            
        # Synthesize consensus
        consensus_prompt = f"""
Synthesize these expert perspectives into a unified response:

{json.dumps(perspectives, indent=2)}

Provide a comprehensive solution that incorporates all viewpoints.
"""
        
        consensus = ""
        async for token in self.llm.generate(
            prompt=consensus_prompt,
            model="deepseek-r1:32b",
            task_category=TaskCategory.REASONING
        ):
            consensus += token
            
        class CouncilResult:
            def __init__(self):
                self.consensus = consensus
                self.perspectives = perspectives
                
        return CouncilResult()


class LearningCore:
    """Layer 4: Learns from interactions"""
    
    def __init__(self):
        self.learning_path = Path.home() / ".echo" / "learning"
        self.learning_path.mkdir(parents=True, exist_ok=True)
        self.patterns = {}
        
    async def apply(self, request, response):
        """Apply learned patterns"""
        # Store interaction for learning
        interaction = {
            "prompt": request.prompt,
            "response": response,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # In full implementation would:
        # - Identify patterns
        # - Store preferences
        # - Adapt future responses
        
        return {"patterns_applied": 0}


class AnticipationEngine:
    """Layer 5: Anticipates user needs"""
    
    async def predict(self, request, response):
        """Predict likely follow-up needs"""
        # In full implementation would:
        # - Analyze response
        # - Predict next steps
        # - Prepare suggestions
        
        anticipations = [
            "User might need help with testing",
            "Consider suggesting documentation",
            "Prepare for debugging questions"
        ]
        
        return anticipations