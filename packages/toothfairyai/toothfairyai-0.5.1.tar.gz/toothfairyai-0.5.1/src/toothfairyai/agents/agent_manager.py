"""Agent manager for handling agent operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import Agent, AgentMode, ListResponse

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class AgentManager:
    """Manager for agent operations.

    This manager provides methods to create, update, and manage AI agents.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> agent = client.agents.create(
        ...     label="Customer Support",
        ...     mode="retriever",
        ...     interpolation_string="You are a helpful assistant...",
        ...     goals="Help customers with their questions",
        ...     temperature=0.7,
        ...     max_tokens=2000,
        ...     max_history=10,
        ...     top_k=10,
        ...     doc_top_k=5
        ... )
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the AgentManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def create(
        self,
        label: str,
        mode: AgentMode,
        interpolation_string: str,
        goals: str,
        temperature: float,
        max_tokens: int,
        max_history: int,
        top_k: int,
        doc_top_k: int,
        description: Optional[str] = None,
        pertinence_passage: Optional[str] = None,
        inhibition_passage: Optional[str] = None,
        default_answer: Optional[str] = None,
        no_knowledge_default_answer: Optional[str] = None,
        subject: Optional[str] = None,
        max_topics: Optional[int] = None,
        min_retrieval_score: Optional[float] = None,
        allowed_topics: Optional[List[str]] = None,
        static_docs: Optional[List[str]] = None,
        has_topics_context: Optional[bool] = None,
        topic_enhancer: Optional[bool] = None,
        key_words_for_knowledge_base: Optional[bool] = None,
        summarisation: Optional[bool] = None,
        compressor: Optional[bool] = None,
        has_memory: Optional[bool] = None,
        is_long_term_memory_enabled: Optional[bool] = None,
        has_functions: Optional[bool] = None,
        agent_functions: Optional[List[str]] = None,
        llm_provider: Optional[str] = None,
        llm_base_model: Optional[str] = None,
        function_calling_provider: Optional[str] = None,
        function_calling_model: Optional[str] = None,
        has_moderation: Optional[bool] = None,
        moderation_message: Optional[str] = None,
        has_ner: Optional[bool] = None,
        show_agent_name: Optional[bool] = None,
        hide_reasoning: Optional[bool] = None,
        plain_text_output: Optional[bool] = None,
        extended_output: Optional[bool] = None,
        show_citations: Optional[bool] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        placeholder_input_message: Optional[str] = None,
        message_on_launch: Optional[str] = None,
        disclaimer: Optional[str] = None,
        quick_questions: Optional[str] = None,
        prevent_widget_usage: Optional[bool] = None,
        allow_feedback: Optional[bool] = None,
        restricted_access: Optional[bool] = None,
        restricted_access_users: Optional[List[str]] = None,
        is_multi_language_enabled: Optional[bool] = None,
        advanced_language_detection: Optional[bool] = None,
        allow_email_to_agent: Optional[bool] = None,
        communication_services: Optional[List[str]] = None,
        charting: Optional[bool] = None,
        allow_images_upload: Optional[bool] = None,
        allow_audios_upload: Optional[bool] = None,
        allow_docs_upload: Optional[bool] = None,
        has_images: Optional[bool] = None,
        prompt_top_keywords: Optional[int] = None,
        agentic_rag: Optional[bool] = None,
        re_rank: Optional[bool] = None,
        blender: Optional[bool] = None,
        allow_internet_search: Optional[bool] = None,
        allow_deep_internet_search: Optional[bool] = None,
        has_code: Optional[bool] = None,
        allow_external_api: Optional[bool] = None,
        allow_images_generation: Optional[bool] = None,
        allow_videos_generation: Optional[bool] = None,
        chain_of_thoughts: Optional[bool] = None,
        agents_pool: Optional[List[str]] = None,
        max_planning_steps: Optional[int] = None,
        planning_instructions: Optional[str] = None,
        voice_name: Optional[str] = None,
        voice_instructions: Optional[str] = None,
        reasoning_budget: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
    ) -> Agent:
        """Create a new agent.

        Args:
            label: Human-readable name of the agent.
            mode: Operating mode (retriever, coder, chatter, planner, computer, voice).
            interpolation_string: System prompt template for the agent.
            goals: Primary objectives of the agent.
            temperature: Randomness level in responses (0.001-1.0).
            max_tokens: Maximum tokens in agent response.
            max_history: Maximum conversation history to maintain.
            top_k: Number of top results to consider for retrieval.
            doc_top_k: Number of top documents to retrieve.
            description: Detailed description of the agent's purpose.
            pertinence_passage: Text to improve response relevance.
            inhibition_passage: Text to prevent certain agent behaviors.
            default_answer: Default response when agent cannot provide an answer.
            no_knowledge_default_answer: Response when no relevant knowledge is found.
            subject: Subject matter expertise area.
            max_topics: Maximum number of topics to consider.
            min_retrieval_score: Minimum score threshold for retrieval results.
            allowed_topics: List of topic IDs the agent is restricted to.
            static_docs: List of document IDs always included in context.
            has_topics_context: Whether the agent considers topic context.
            topic_enhancer: Whether to enhance responses with topic information.
            key_words_for_knowledge_base: Whether to use keywords for knowledge base queries.
            summarisation: Whether the agent can summarize content.
            compressor: Whether to use content compression.
            has_memory: Whether the agent maintains conversation memory.
            is_long_term_memory_enabled: Whether long-term memory is enabled.
            has_functions: Whether the agent can execute functions.
            agent_functions: List of function IDs associated with the agent.
            llm_provider: LLM provider (e.g., 'openai', 'anthropic').
            llm_base_model: Base LLM model to use.
            function_calling_provider: Provider for function calling.
            function_calling_model: Model for function calling.
            has_moderation: Whether content moderation is enabled.
            moderation_message: Message shown when content is moderated.
            has_ner: Whether named entity recognition is enabled.
            show_agent_name: Whether to show agent name in responses.
            hide_reasoning: Whether to hide reasoning process.
            plain_text_output: Whether to output plain text only.
            extended_output: Whether to include extended output metadata.
            show_citations: Whether to show source citations.
            icon: Icon identifier for the agent.
            color: Hex color code for agent display.
            placeholder_input_message: Placeholder text in input field.
            message_on_launch: Welcome message on chat start.
            disclaimer: Disclaimer text.
            quick_questions: Semicolon-separated quick question suggestions.
            prevent_widget_usage: Whether to prevent widget usage.
            allow_feedback: Whether to allow user feedback.
            restricted_access: Whether access is restricted.
            restricted_access_users: List of user IDs with access.
            is_multi_language_enabled: Whether multi-language support is enabled.
            advanced_language_detection: Whether to use advanced language detection.
            allow_email_to_agent: Whether email channel is enabled.
            communication_services: List of enabled communication service IDs.
            charting: Whether the agent can create charts (TF models only).
            allow_images_upload: Whether image uploads are allowed.
            allow_audios_upload: Whether audio uploads are allowed.
            allow_docs_upload: Whether document uploads are allowed.
            has_images: Whether the agent can process images.
            prompt_top_keywords: Number of top keywords to extract from prompts.
            agentic_rag: Whether agentic RAG is enabled (retriever mode).
            re_rank: Whether to re-rank retrieval results (retriever mode).
            blender: Whether to blend multiple information sources (retriever mode).
            allow_internet_search: Whether internet search is allowed.
            allow_deep_internet_search: Whether deep internet search is allowed.
            has_code: Whether code execution is enabled.
            allow_external_api: Whether external API calls are allowed (coder mode).
            allow_images_generation: Whether image generation is allowed (chatter mode).
            allow_videos_generation: Whether video generation is allowed (chatter mode).
            chain_of_thoughts: Whether to show reasoning process (chatter mode).
            agents_pool: List of agent IDs for orchestration (planner mode).
            max_planning_steps: Maximum planning steps (planner/computer mode).
            planning_instructions: Instructions for planning process.
            voice_name: Voice name for TTS (voice mode).
            voice_instructions: Instructions for voice interactions (voice mode).
            reasoning_budget: Token budget for reasoning.
            reasoning_effort: Level of reasoning effort.

        Returns:
            The created Agent object.
        """
        data: Dict[str, Any] = {
            "label": label,
            "mode": mode,
            "interpolationString": interpolation_string,
            "goals": goals,
            "temperature": temperature,
            "maxTokens": max_tokens,
            "maxHistory": max_history,
            "topK": top_k,
            "docTopK": doc_top_k,
        }

        if description is not None:
            data["description"] = description
        if pertinence_passage is not None:
            data["pertinencePassage"] = pertinence_passage
        if inhibition_passage is not None:
            data["inhibitionPassage"] = inhibition_passage
        if default_answer is not None:
            data["defaultAnswer"] = default_answer
        if no_knowledge_default_answer is not None:
            data["noKnowledgeDefaultAnswer"] = no_knowledge_default_answer
        if subject is not None:
            data["subject"] = subject
        if max_topics is not None:
            data["maxTopics"] = max_topics
        if min_retrieval_score is not None:
            data["minRetrievalScore"] = min_retrieval_score
        if allowed_topics is not None:
            data["allowedTopics"] = allowed_topics
        if static_docs is not None:
            data["staticDocs"] = static_docs
        if has_topics_context is not None:
            data["hasTopicsContext"] = has_topics_context
        if topic_enhancer is not None:
            data["topicEnhancer"] = topic_enhancer
        if key_words_for_knowledge_base is not None:
            data["keyWordsForKnowledgeBase"] = key_words_for_knowledge_base
        if summarisation is not None:
            data["summarisation"] = summarisation
        if compressor is not None:
            data["compressor"] = compressor
        if has_memory is not None:
            data["hasMemory"] = has_memory
        if is_long_term_memory_enabled is not None:
            data["isLongTermMemoryEnabled"] = is_long_term_memory_enabled
        if has_functions is not None:
            data["hasFunctions"] = has_functions
        if agent_functions is not None:
            data["agentFunctions"] = agent_functions
        if llm_provider is not None:
            data["llmProvider"] = llm_provider
        if llm_base_model is not None:
            data["llmBaseModel"] = llm_base_model
        if function_calling_provider is not None:
            data["functionCallingProvider"] = function_calling_provider
        if function_calling_model is not None:
            data["functionCallingModel"] = function_calling_model
        if has_moderation is not None:
            data["hasModeration"] = has_moderation
        if moderation_message is not None:
            data["moderationMessage"] = moderation_message
        if has_ner is not None:
            data["hasNER"] = has_ner
        if show_agent_name is not None:
            data["showAgentName"] = show_agent_name
        if hide_reasoning is not None:
            data["hideReasoning"] = hide_reasoning
        if plain_text_output is not None:
            data["plainTextOutput"] = plain_text_output
        if extended_output is not None:
            data["extendedOutput"] = extended_output
        if show_citations is not None:
            data["showCitations"] = show_citations
        if icon is not None:
            data["icon"] = icon
        if color is not None:
            data["color"] = color
        if placeholder_input_message is not None:
            data["placeholderInputMessage"] = placeholder_input_message
        if message_on_launch is not None:
            data["messageOnLaunch"] = message_on_launch
        if disclaimer is not None:
            data["disclaimer"] = disclaimer
        if quick_questions is not None:
            data["quickQuestions"] = quick_questions
        if prevent_widget_usage is not None:
            data["preventWidgetUsage"] = prevent_widget_usage
        if allow_feedback is not None:
            data["allowFeedback"] = allow_feedback
        if restricted_access is not None:
            data["restrictedAccess"] = restricted_access
        if restricted_access_users is not None:
            data["restrictedAccessUsers"] = restricted_access_users
        if is_multi_language_enabled is not None:
            data["isMultiLanguageEnabled"] = is_multi_language_enabled
        if advanced_language_detection is not None:
            data["advancedLanguageDetection"] = advanced_language_detection
        if allow_email_to_agent is not None:
            data["allowEmailToAgent"] = allow_email_to_agent
        if communication_services is not None:
            data["communicationServices"] = communication_services
        if charting is not None:
            data["charting"] = charting
        if allow_images_upload is not None:
            data["allowImagesUpload"] = allow_images_upload
        if allow_audios_upload is not None:
            data["allowAudiosUpload"] = allow_audios_upload
        if allow_docs_upload is not None:
            data["allowDocsUpload"] = allow_docs_upload
        if has_images is not None:
            data["hasImages"] = has_images
        if prompt_top_keywords is not None:
            data["promptTopKeywords"] = prompt_top_keywords
        if agentic_rag is not None:
            data["agenticRAG"] = agentic_rag
        if re_rank is not None:
            data["reRank"] = re_rank
        if blender is not None:
            data["blender"] = blender
        if allow_internet_search is not None:
            data["allowInternetSearch"] = allow_internet_search
        if allow_deep_internet_search is not None:
            data["allowDeepInternetSearch"] = allow_deep_internet_search
        if has_code is not None:
            data["hasCode"] = has_code
        if allow_external_api is not None:
            data["allowExternalAPI"] = allow_external_api
        if allow_images_generation is not None:
            data["allowImagesGeneration"] = allow_images_generation
        if allow_videos_generation is not None:
            data["allowVideosGeneration"] = allow_videos_generation
        if chain_of_thoughts is not None:
            data["chainOfThoughts"] = chain_of_thoughts
        if agents_pool is not None:
            data["agentsPool"] = agents_pool
        if max_planning_steps is not None:
            data["maxPlanningSteps"] = max_planning_steps
        if planning_instructions is not None:
            data["planningInstructions"] = planning_instructions
        if voice_name is not None:
            data["voiceName"] = voice_name
        if voice_instructions is not None:
            data["voiceInstructions"] = voice_instructions
        if reasoning_budget is not None:
            data["reasoningBudget"] = reasoning_budget
        if reasoning_effort is not None:
            data["reasoningEffort"] = reasoning_effort

        response = self._client.request("POST", "/agent/create", data=data)
        return Agent.from_dict(response)

    def get(self, agent_id: str) -> Agent:
        """Get an agent by ID.

        Args:
            agent_id: ID of the agent to retrieve.

        Returns:
            The Agent object.
        """
        response = self._client.request("GET", f"/agent/get/{agent_id}")
        return Agent.from_dict(response)

    def update(
        self,
        agent_id: str,
        label: Optional[str] = None,
        description: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_history: Optional[int] = None,
        top_k: Optional[int] = None,
        doc_top_k: Optional[int] = None,
        **kwargs: Any,
    ) -> Agent:
        """Update an agent.

        Args:
            agent_id: ID of the agent to update.
            label: New label.
            description: New description.
            temperature: New temperature value.
            max_tokens: New max tokens value.
            max_history: New max history value.
            top_k: New top_k value.
            doc_top_k: New doc_top_k value.
            **kwargs: Additional fields to update.

        Returns:
            The updated Agent object.
        """
        data: Dict[str, Any] = {"id": agent_id}

        if label is not None:
            data["label"] = label
        if description is not None:
            data["description"] = description
        if temperature is not None:
            data["temperature"] = temperature
        if max_tokens is not None:
            data["maxTokens"] = max_tokens
        if max_history is not None:
            data["maxHistory"] = max_history
        if top_k is not None:
            data["topK"] = top_k
        if doc_top_k is not None:
            data["docTopK"] = doc_top_k

        data.update(kwargs)

        response = self._client.request("POST", "/agent/update", data=data)
        return Agent.from_dict(response)

    def delete(self, agent_id: str) -> Dict[str, bool]:
        """Delete an agent.

        Args:
            agent_id: ID of the agent to delete.

        Returns:
            A dictionary with success status.
        """
        self._client.request("DELETE", f"/agent/delete/{agent_id}")
        return {"success": True}

    def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListResponse:
        """List all agents.

        Args:
            limit: Maximum number of agents to return.
            offset: Number of agents to skip.

        Returns:
            A ListResponse containing the agents.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._client.request("GET", "/agent/list", params=params)

        items = []
        if isinstance(response, list):
            items = [Agent.from_dict(item) for item in response]
        elif isinstance(response, dict):
            items = [Agent.from_dict(item) for item in response.get("data", [])]

        return ListResponse(items=items)

    def get_by_mode(
        self,
        mode: AgentMode,
        limit: Optional[int] = None,
    ) -> List[Agent]:
        """Get agents by mode.

        Args:
            mode: Mode of agents to retrieve.
            limit: Maximum number of agents to return.

        Returns:
            A list of Agent objects with the specified mode.
        """
        result = self.list(limit=limit)
        return [agent for agent in result.items if agent.mode == mode]

    def search(self, search_term: str) -> List[Agent]:
        """Search agents by label.

        Args:
            search_term: Term to search for in agent labels.

        Returns:
            A list of matching Agent objects.
        """
        all_agents = self.list()
        search_lower = search_term.lower()
        return [agent for agent in all_agents.items if search_lower in agent.label.lower()]
