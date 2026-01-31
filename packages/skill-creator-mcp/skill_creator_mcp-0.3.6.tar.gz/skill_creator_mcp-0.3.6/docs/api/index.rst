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

Skill Creator MCP Server provides 12 tools organized into 3 categories.

Skill Lifecycle Tools (4)
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: skill_creator_mcp.server.init_skill
.. autofunction:: skill_creator_mcp.server.validate_skill
.. autofunction:: skill_creator_mcp.server.analyze_skill
.. autofunction:: skill_creator_mcp.server.refactor_skill

Packaging Tools (1)
~~~~~~~~~~~~~~~~~~~

.. autofunction:: skill_creator_mcp.server.package_skill

Requirement Collection Tools (7)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: skill_creator_mcp.server.create_requirement_session_tool
.. autofunction:: skill_creator_mcp.server.get_requirement_session_tool
.. autofunction:: skill_creator_mcp.server.update_requirement_answer_tool
.. autofunction:: skill_creator_mcp.server.get_static_question_tool
.. autofunction:: skill_creator_mcp.server.generate_dynamic_question_tool
.. autofunction:: skill_creator_mcp.server.validate_answer_format_tool
.. autofunction:: skill_creator_mcp.server.check_requirement_completeness_tool

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

**Skill Lifecycle Tools** (4):
  - ``init_skill`` - Initialize new Agent-Skill project
  - ``validate_skill`` - Validate skill structure and content
  - ``analyze_skill`` - Analyze code quality and complexity
  - ``refactor_skill`` - Generate refactoring suggestions

**Packaging Tools** (1):
  - ``package_skill`` - Package skill for distribution (supports strict mode for Agent-Skill standard packaging)

**Requirement Collection Tools** (7):
  - ``create_requirement_session`` - Create requirement collection session
  - ``get_requirement_session`` - Get session state
  - ``update_requirement_answer`` - Update answer
  - ``get_static_question`` - Get static question
  - ``generate_dynamic_question`` - Generate dynamic question
  - ``validate_answer_format`` - Validate answer format
  - ``check_requirement_completeness`` - Check completeness
