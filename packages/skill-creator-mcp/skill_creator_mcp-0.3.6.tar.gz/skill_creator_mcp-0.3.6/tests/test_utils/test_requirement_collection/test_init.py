"""测试模块导入和公开API.

验证 requirement_collection 模块的导入和公开接口。
"""



def test_module_imports():
    """测试模块可以正确导入."""
    from skill_creator_mcp.utils.requirement_collection import (
        check_requirement_completeness,
        get_next_static_question,
        get_static_questions,
        load_session_state,
        save_session_state,
        validate_requirement_answer,
    )

    # 验证函数可调用
    assert callable(check_requirement_completeness)
    assert callable(get_next_static_question)
    assert callable(get_static_questions)
    assert callable(load_session_state)
    assert callable(save_session_state)
    assert callable(validate_requirement_answer)


def test_module_all_exports():
    """测试 __all__ 导出列表."""
    from skill_creator_mcp.utils import requirement_collection

    expected_exports = [
        "load_session_state",
        "save_session_state",
        "validate_requirement_answer",
        "get_static_questions",
        "get_next_static_question",
        "check_requirement_completeness",
    ]

    assert hasattr(requirement_collection, "__all__")
    assert set(requirement_collection.__all__) == set(expected_exports)


def test_session_manager_functions():
    """测试会话管理函数可导入."""
    from skill_creator_mcp.utils.requirement_collection.session_manager import (
        load_session_state,
        save_session_state,
    )

    assert callable(load_session_state)
    assert callable(save_session_state)


def test_questions_functions():
    """测试问题函数可导入."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_next_static_question,
        get_static_questions,
    )

    assert callable(get_static_questions)
    assert callable(get_next_static_question)


def test_validation_functions():
    """测试验证函数可导入."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    assert callable(validate_requirement_answer)


def test_llm_services_functions():
    """测试 LLM 服务函数可导入."""
    from skill_creator_mcp.utils.requirement_collection.llm_services import (
        check_requirement_completeness,
    )

    assert callable(check_requirement_completeness)
