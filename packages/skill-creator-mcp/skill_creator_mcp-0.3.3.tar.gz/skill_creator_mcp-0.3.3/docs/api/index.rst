API Reference
=============

This page contains the API reference documentation for skill-creator-mcp.

.. toctree::
   :maxdepth: 2

   server
   models
   utils
   resources
   prompts

MCP Tools
----------

Skill Creator MCP Server provides 16 tools organized into 4 categories.

Core Development Tools (6)
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: skill_creator_mcp.server.collect_requirements
.. autofunction:: skill_creator_mcp.server.init_skill
.. autofunction:: skill_creator_mcp.server.validate_skill
.. autofunction:: skill_creator_mcp.server.analyze_skill
.. autofunction:: skill_creator_mcp.server.refactor_skill
.. autofunction:: skill_creator_mcp.server.package_skill

Batch Operations (2)
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: skill_creator_mcp.server.batch_validate_skills_tool
.. autofunction:: skill_creator_mcp.server.batch_analyze_skills_tool

Health Check Tools (3)
~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: skill_creator_mcp.server.health_check_tool
.. autofunction:: skill_creator_mcp.server.quick_status_tool
.. autofunction:: skill_creator_mcp.server.is_healthy_tool

Phase 0 Verification Tools (5)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: skill_creator_mcp.server.check_client_capabilities
.. autofunction:: skill_creator_mcp.server.test_llm_sampling
.. autofunction:: skill_creator_mcp.server.test_user_elicitation
.. autofunction:: skill_creator_mcp.server.test_conversation_loop
.. autofunction:: skill_creator_mcp.server.test_requirement_completeness

Data Models
------------

Pydantic data models for type validation and serialization.

.. automodule:: skill_creator_mcp.models
   :members:
   :undoc-members:
   :show-inheritance:

Utility Functions
-----------------

Internal utility functions for file operations, validation, etc.

.. automodule:: skill_creator_mcp.utils
   :members:
   :undoc-members:
   :show-inheritance:

Resources
---------

MCP Resources (4) providing static content and templates.

.. automodule:: skill_creator_mcp.resources
   :members:
   :undoc-members:
   :show-inheritance:

Available Resources:

* ``http://skills/schema/templates`` - List all available skill templates
* ``http://skills/schema/templates/{type}`` - Get template content by type
* ``http://skills/schema/best-practices`` - Get Agent-Skills development best practices
* ``http://skills/schema/validation-rules`` - Get validation rules

Prompts
-------

MCP Prompts (3) providing reusable prompt templates.

.. automodule:: skill_creator_mcp.prompts
   :members:
   :undoc-members:
   :show-inheritance:

Available Prompts:

* ``create-skill`` - Create new skill prompt template
* ``validate-skill`` - Validate skill prompt template
* ``refactor-skill`` - Refactor skill prompt template

Tool Categories Reference
-------------------------

**Core Development Tools** (6):
  - ``collect_requirements`` - AI-driven requirement clarification
  - ``init_skill`` - Initialize new Agent-Skill project
  - ``validate_skill`` - Validate skill structure and content
  - ``analyze_skill`` - Analyze code quality and complexity
  - ``refactor_skill`` - Generate refactoring suggestions
  - ``package_skill`` - Package skill for distribution

**Batch Operations** (2):
  - ``batch_validate_skills_tool`` - Validate multiple skills concurrently
  - ``batch_analyze_skills_tool`` - Analyze multiple skills concurrently

**Health Check Tools** (3):
  - ``health_check_tool`` - Complete health check
  - ``quick_status_tool`` - Quick status summary
  - ``is_healthy_tool`` - Quick health check

**Phase 0 Verification Tools** (5):
  - ``check_client_capabilities`` - Check MCP client capabilities
  - ``test_llm_sampling`` - Test LLM Sampling ability
  - ``test_user_elicitation`` - Test user elicitation ability
  - ``test_conversation_loop`` - Test conversation loop ability
  - ``test_requirement_completeness`` - Test requirement completeness judgment
