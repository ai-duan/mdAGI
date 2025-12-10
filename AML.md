# AML Specification: Agent Markup Language

## 1. Overview
AML (Agent Markup Language) is a markup language specification for formally describing agent entities. It provides a complete and minimal state description framework for agents through five standardized dimensions.

## 2. Core Concepts

### 2.1 Five-Dimensional Model of Agents
The complete state of an agent can be described by and only by the following five dimensions:
- **agent**: Identity identification and role definition
- **knowledge**: Knowledge system and cognitive rules
- **memory**: State preservation and experience recording
- **code**: Behavioral capabilities and operational methods
- **todo**: Goal queue and task planning

### 2.2 Document-as-Entity Principle
An AML document itself is a complete state representation of an agent. Loading, parsing, and modifying the document correspond to instantiation, state reading, and evolution of the agent respectively.

## 3. Theoretical Foundation

### 3.1 Formal Definition
Let AML be a quintuple:
```
AML = ⟨A, K, M, C, T⟩
Where:
A ∈ Strings  (Identity description)
K ∈ KnowledgeBase (Knowledge collection)
M ∈ MemorySystem (Memory configuration)
C ∈ CapabilitySet (Capability collection)
T ∈ TaskQueue (Task queue)
```

### 3.2 Composition Algebra
Define composition operation ⊕:
```
AML₁ ⊕ AML₂ → AML₃
```
Satisfying:
1. Maintaining five-dimensional structure
2. Optionally inheriting parental characteristics
3. Potentially generating emergent properties

## 4. Specification Characteristics

### 4.1 Minimal Completeness
The five dimensions constitute a minimal complete set for describing agents. Reducing any dimension would result in incomplete state description.

### 4.2 Orthogonal Independence
Each dimension is semantically and functionally independent, allowing individual modification without affecting other dimensions.

### 4.3 Composability
AML entities support formal composition operations, enabling the generation of new entities through structured combination.

### 4.4 Self-Descriptiveness
AML documents contain their own state and behavior descriptions, supporting self-inspection and self-modification.

## 5. Standardization Goals

### 5.1 Interoperability
Provide a unified description format for agents across different platforms and systems, supporting cross-platform collaboration.

### 5.2 Portability
Plain text format ensures platform independence and toolchain compatibility of AML documents.

### 5.3 Extensibility
Support internal expansion of each dimension while maintaining the core five-dimensional model unchanged.

## 6. Theoretical Contributions

1. **Unified Description Framework**: Provides standardized state representation for various types of agents
2. **Formal Foundation**: Establishes algebraic theoretical foundation for agent composition
3. **Practical Guidance**: Offers reference specifications for the design and implementation of agent systems

## 7. Scope of Application
This specification applies to language model-based agent systems, task-oriented automation entities, and intelligent agents requiring standardized descriptions.

---

**AML: Formal Description Standard for Agents**