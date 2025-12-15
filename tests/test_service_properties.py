"""
Property-based tests for AgentUIService.

Uses Hypothesis to verify correctness properties defined in the design document.
"""

import os
import tempfile
from hypothesis import given, strategies as st, settings, assume

import shutil

from ui.service import AgentUIService, AgentStateView, RunConfig, TaskFileInfo
from core.parser.aml import parse_aml, dump_aml
from core.state.models import AgentState, TodoItem
from core.agent import Agent


# Strategies for generating valid AML data
# Note: AML parser strips leading/trailing whitespace from content,
# so we generate pre-stripped content to match expected behavior.
agent_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P'), whitelist_characters=' _-'),
    min_size=1,
    max_size=50
).map(lambda x: x.strip()).filter(lambda x: len(x) > 0)

task_content_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S'), whitelist_characters=' '),
    min_size=1,
    max_size=100
).map(lambda x: x.strip()).filter(lambda x: len(x) > 0 and '\n' not in x)

task_status_strategy = st.sampled_from(["PENDING", "DONE"])

memory_entry_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S'), whitelist_characters=' '),
    min_size=1,
    max_size=200
).map(lambda x: x.strip()).filter(lambda x: len(x) > 0 and '\n' not in x)


@st.composite
def todo_item_strategy(draw):
    """Generate a valid TodoItem."""
    content = draw(task_content_strategy)
    status = draw(task_status_strategy)
    return TodoItem(content=content, status=status)


@st.composite
def agent_state_strategy(draw):
    """Generate a valid AgentState for testing."""
    name = draw(agent_name_strategy)
    todo_items = draw(st.lists(todo_item_strategy(), min_size=0, max_size=10))
    memory_items = draw(st.lists(memory_entry_strategy, min_size=0, max_size=10))
    
    return AgentState(
        agent={"name": name, "objective": "Test objective"},
        knowledge=[],
        memory=memory_items,
        code=[],
        todo=todo_items
    )


@settings(max_examples=100)
@given(agent_state_strategy())
def test_state_display_accuracy(state: AgentState):
    """
    **Feature: gradio-ui, Property 5: State Display Accuracy**
    **Validates: Requirements 5.1, 5.2, 5.3**
    
    For any loaded DNA file, the displayed state SHALL accurately reflect
    the Agent's current todo list and memory contents.
    """
    service = AgentUIService()
    
    # Create a temporary DNA file with the generated state
    aml_content = dump_aml(state)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(aml_content)
        temp_path = f.name
    
    try:
        # Get the state view through the service
        result = service.get_agent_state(temp_path)
        
        # Verify result is not None
        assert result is not None, "get_agent_state should return a valid AgentStateView"
        assert isinstance(result, AgentStateView), "Result should be an AgentStateView instance"
        
        # Property: Agent name matches
        expected_name = state.agent.get("name", os.path.basename(temp_path))
        assert result.agent_name == expected_name, \
            f"Agent name mismatch: expected '{expected_name}', got '{result.agent_name}'"
        
        # Property: Todo list length matches
        assert len(result.todo_list) == len(state.todo), \
            f"Todo list length mismatch: expected {len(state.todo)}, got {len(result.todo_list)}"
        
        # Property: Each todo item content and status matches
        for i, (expected_item, actual_item) in enumerate(zip(state.todo, result.todo_list)):
            assert actual_item["content"] == expected_item.content, \
                f"Todo item {i} content mismatch: expected '{expected_item.content}', got '{actual_item['content']}'"
            assert actual_item["status"] == expected_item.status, \
                f"Todo item {i} status mismatch: expected '{expected_item.status}', got '{actual_item['status']}'"
        
        # Property: Memory list matches
        assert result.memory == state.memory, \
            f"Memory mismatch: expected {state.memory}, got {result.memory}"
        
        # Property: is_running reflects service state
        assert result.is_running == service.is_running, \
            f"is_running mismatch: expected {service.is_running}, got {result.is_running}"
        
    finally:
        # Clean up temporary file
        os.unlink(temp_path)


# Strategies for agent configuration testing
run_mode_strategy = st.sampled_from(["foreground", "background", "dual"])
loop_count_strategy = st.integers(min_value=1, max_value=10)


@settings(max_examples=100)
@given(agent_state_strategy(), run_mode_strategy, loop_count_strategy)
def test_agent_configuration_consistency(state: AgentState, mode: str, loop: int):
    """
    **Feature: gradio-ui, Property 1: Agent Configuration Consistency**
    **Validates: Requirements 1.1, 1.2, 1.3**
    
    For any valid DNA file path and run configuration (mode, loop count),
    when the Agent is started, the Agent's internal configuration SHALL
    match the specified parameters.
    """
    # Create a temporary DNA file with the generated state
    aml_content = dump_aml(state)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(aml_content)
        temp_path = f.name
    
    try:
        # Create Agent with specified configuration
        # Note: start_background=False to avoid starting background scheduler during tests
        agent = Agent(
            dna_file=temp_path,
            mode=mode,
            start_background=False
        )
        
        try:
            # Property: DNA file path matches
            assert agent.dna_file == temp_path, \
                f"DNA file mismatch: expected '{temp_path}', got '{agent.dna_file}'"
            
            # Property: Mode matches
            assert agent.mode == mode, \
                f"Mode mismatch: expected '{mode}', got '{agent.mode}'"
            
            # Property: For background/dual modes, meta_prompt should be loaded if .ai/meta.md exists
            if mode in ["background", "dual"]:
                if os.path.exists(".ai/meta.md"):
                    assert agent.meta_prompt is not None, \
                        "meta_prompt should be loaded for background/dual modes when .ai/meta.md exists"
            else:
                # For foreground mode, meta_prompt should be None
                assert agent.meta_prompt is None, \
                    f"meta_prompt should be None for foreground mode, got '{agent.meta_prompt}'"
            
            # Property: Agent state is loaded correctly
            assert agent.state is not None, "Agent state should be loaded"
            
            # Property: Agent name from state matches
            expected_name = state.agent.get("name")
            actual_name = agent.state.agent.get("name")
            assert actual_name == expected_name, \
                f"Agent name in state mismatch: expected '{expected_name}', got '{actual_name}'"
            
            # Property: RunConfig can be created with valid parameters
            config = RunConfig(file=temp_path, mode=mode, loop=loop)
            assert config.file == temp_path, "RunConfig file should match"
            assert config.mode == mode, "RunConfig mode should match"
            assert config.loop == loop, "RunConfig loop should match"
            
        finally:
            # Clean up Agent
            agent.stop()
    
    finally:
        # Clean up temporary file
        os.unlink(temp_path)


@st.composite
def task_file_state_strategy(draw):
    """Generate a valid AgentState for task file testing with controlled pending counts."""
    name = draw(agent_name_strategy)
    # Generate todo items with known pending/done distribution
    todo_items = draw(st.lists(todo_item_strategy(), min_size=0, max_size=10))
    
    return AgentState(
        agent={"name": name, "objective": "Test objective"},
        knowledge=[],
        memory=[],
        code=[],
        todo=todo_items
    )


@st.composite
def lowercase_filename_strategy(draw):
    """Generate valid lowercase .md filenames."""
    # Generate a base name with lowercase letters, digits, underscores, hyphens
    base = draw(st.text(
        alphabet=st.sampled_from('abcdefghijklmnopqrstuvwxyz0123456789_-'),
        min_size=1,
        max_size=20
    ).filter(lambda x: len(x) > 0 and x[0].isalpha()))
    return f"{base}.md"


@settings(max_examples=100)
@given(st.lists(
    st.tuples(lowercase_filename_strategy(), task_file_state_strategy()),
    min_size=0,
    max_size=5,
    unique_by=lambda x: x[0]  # Ensure unique filenames
))
def test_task_file_listing_completeness(file_states: list[tuple[str, AgentState]]):
    """
    **Feature: gradio-ui, Property 2: Task File Listing Completeness**
    **Validates: Requirements 2.1, 2.2**
    
    For any work directory containing task files, the list_task_files function
    SHALL return entries for all lowercase .md files, each with correct name
    and pending count.
    """
    # Create a temporary work directory
    test_work_dir = tempfile.mkdtemp()
    
    try:
        # Create task files in the temp directory
        expected_files: list[tuple[str, str, int]] = []  # (path, name, pending_count)
        
        for filename, state in file_states:
            filepath = os.path.join(test_work_dir, filename)
            aml_content = dump_aml(state)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(aml_content)
            
            # Calculate expected pending count
            pending_count = sum(1 for item in state.todo if item.status == "PENDING")
            agent_name = state.agent.get("name", filename)
            
            expected_files.append((filepath, agent_name, pending_count))
        
        # Create service with custom work directory
        service = AgentUIService()
        original_work_dir = service.WORK_DIR
        service.WORK_DIR = test_work_dir
        
        try:
            # Get the task file listing
            result = service.list_task_files()
            
            # Property: Result count matches expected file count
            assert len(result) == len(expected_files), \
                f"File count mismatch: expected {len(expected_files)}, got {len(result)}"
            
            # Create lookup for results by path
            result_by_path = {info.path: info for info in result}
            
            # Property: Each expected file is present with correct data
            for expected_path, expected_name, expected_pending in expected_files:
                assert expected_path in result_by_path, \
                    f"Expected file not found in results: {expected_path}"
                
                info = result_by_path[expected_path]
                
                # Property: Agent name matches
                assert info.name == expected_name, \
                    f"Agent name mismatch for {expected_path}: expected '{expected_name}', got '{info.name}'"
                
                # Property: Pending count matches
                assert info.pending_count == expected_pending, \
                    f"Pending count mismatch for {expected_path}: expected {expected_pending}, got {info.pending_count}"
            
            # Property: All results are TaskFileInfo instances
            for info in result:
                assert isinstance(info, TaskFileInfo), \
                    f"Result item should be TaskFileInfo, got {type(info)}"
        
        finally:
            # Restore original work directory
            service.WORK_DIR = original_work_dir
    
    finally:
        # Clean up temporary directory
        shutil.rmtree(test_work_dir)


@settings(max_examples=100)
@given(st.lists(
    st.tuples(
        st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=10),  # Uppercase names
        task_file_state_strategy()
    ),
    min_size=1,
    max_size=3,
    unique_by=lambda x: x[0]
))
def test_task_file_listing_excludes_uppercase(file_states: list[tuple[str, AgentState]]):
    """
    **Feature: gradio-ui, Property 2: Task File Listing Completeness (Exclusion)**
    **Validates: Requirements 2.1, 2.2**
    
    For any work directory, the list_task_files function SHALL only return
    lowercase .md files, excluding files with uppercase characters.
    """
    # Create a temporary work directory
    test_work_dir = tempfile.mkdtemp()
    
    try:
        # Create uppercase-named files (should be excluded)
        for filename_base, state in file_states:
            filename = f"{filename_base}.md"  # Uppercase filename
            filepath = os.path.join(test_work_dir, filename)
            aml_content = dump_aml(state)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(aml_content)
        
        # Create service with custom work directory
        service = AgentUIService()
        original_work_dir = service.WORK_DIR
        service.WORK_DIR = test_work_dir
        
        try:
            # Get the task file listing
            result = service.list_task_files()
            
            # Property: No uppercase files should be returned
            assert len(result) == 0, \
                f"Expected 0 files (uppercase should be excluded), got {len(result)}"
        
        finally:
            service.WORK_DIR = original_work_dir
    
    finally:
        shutil.rmtree(test_work_dir)
